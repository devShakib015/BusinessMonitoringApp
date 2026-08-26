"""SQLite access layer.

One connection is shared for the life of the process, guarded by a re-entrant
lock so a background export cannot interleave with a checkout.  WAL mode keeps
reads from blocking the write that commits a sale.
"""

import sqlite3
import threading
from contextlib import contextmanager

from app import config
from app.core import migrations

_lock = threading.RLock()
_conn: sqlite3.Connection | None = None
_depth = 0
_path: str | None = None


def connect(path: str | None = None) -> sqlite3.Connection:
    """Open (once) and return the shared connection, running migrations."""
    global _conn, _path
    with _lock:
        if _conn is None:
            _path = path or config.db_path()
            _conn = sqlite3.connect(_path, check_same_thread=False, timeout=10.0)
            _conn.row_factory = sqlite3.Row
            _conn.execute("PRAGMA journal_mode = WAL")
            _conn.execute("PRAGMA foreign_keys = ON")
            _conn.execute("PRAGMA synchronous = NORMAL")
            _conn.execute("PRAGMA busy_timeout = 10000")
            migrations.migrate(_conn)
        return _conn


def close() -> None:
    global _conn, _path
    with _lock:
        if _conn is not None:
            try:
                _conn.execute("PRAGMA optimize")
                _conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            except sqlite3.Error:
                pass
            _conn.close()
        _conn = None
        _path = None


def path() -> str:
    return _path or config.db_path()


def reset_for_tests(path_: str) -> None:
    """Point the module at a throwaway database (used by the test suite)."""
    close()
    connect(path_)


@contextmanager
def transaction():
    """Atomic unit of work; nesting joins the outermost transaction.

    A sale writes to ``sales``, ``sale_items``, ``payments``, ``counters`` and
    ``stock_movements``.  Half of that landing would leave stock that never
    sold, so every write path goes through here.
    """
    global _depth
    conn = connect()
    with _lock:
        outermost = _depth == 0
        if outermost:
            conn.execute("BEGIN IMMEDIATE")
        _depth += 1
        try:
            yield conn
        except BaseException:
            _depth -= 1
            if _depth == 0:
                conn.rollback()
            raise
        else:
            _depth -= 1
            if _depth == 0:
                conn.commit()


def query(sql: str, params: tuple | dict = ()) -> list[sqlite3.Row]:
    with _lock:
        return connect().execute(sql, params).fetchall()


def one(sql: str, params: tuple | dict = ()) -> sqlite3.Row | None:
    with _lock:
        return connect().execute(sql, params).fetchone()


def scalar(sql: str, params: tuple | dict = (), default=None):
    row = one(sql, params)
    if row is None or row[0] is None:
        return default
    return row[0]


def execute(sql: str, params: tuple | dict = ()) -> int:
    """Run a single writing statement in its own transaction; returns rowid."""
    with transaction() as conn:
        cursor = conn.execute(sql, params)
        return cursor.lastrowid


def execute_many(sql: str, seq) -> None:
    with transaction() as conn:
        conn.executemany(sql, seq)


def next_counter(name: str, conn: sqlite3.Connection | None = None) -> int:
    """Atomically increment and return a named counter (invoice numbers)."""
    target = conn or connect()
    target.execute(
        "INSERT INTO counters(name, value) VALUES (?, 0) "
        "ON CONFLICT(name) DO NOTHING", (name,))
    target.execute("UPDATE counters SET value = value + 1 WHERE name = ?", (name,))
    return int(target.execute(
        "SELECT value FROM counters WHERE name = ?", (name,)).fetchone()[0])


def table_is_empty(table: str) -> bool:
    return scalar(f"SELECT COUNT(*) FROM {table}", default=0) == 0
