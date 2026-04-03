import sqlite3
from contextlib import contextmanager
from app.config import DB_PATH


@contextmanager
def get_db():
    """Yield a committed SQLite connection; roll back on any exception."""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
