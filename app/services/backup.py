"""Backups.

Shop data is the shop's livelihood, so backing it up is a one-click action in
the app rather than a folder the owner is expected to know about.  Copies are
made with SQLite's online backup API, which is safe while the database is open
and in WAL mode (a plain file copy is not).
"""

import os
import shutil
import sqlite3
from datetime import datetime

from app.core import db


def folder() -> str:
    """Where backups live: beside the database that is currently open.

    Deriving it from the live database rather than from a global path keeps a
    restored or relocated shop's backups with it -- and keeps the test suite
    out of the real user's data directory.
    """
    path = os.path.join(os.path.dirname(db.path()), "backups")
    os.makedirs(path, exist_ok=True)
    return path


def create(label: str = "manual") -> str:
    """Write a consistent snapshot into the backups folder; returns its path."""
    safe = "".join(ch for ch in label if ch.isalnum() or ch in "-_") or "manual"
    name = f"shopdesk-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{safe}.db"
    target = os.path.join(folder(), name)

    destination = sqlite3.connect(target)
    try:
        db.connect().backup(destination)
    finally:
        destination.close()
    return target


def list_backups() -> list[dict]:
    directory = folder()
    entries = []
    for name in os.listdir(directory):
        if not name.endswith(".db"):
            continue
        path = os.path.join(directory, name)
        info = os.stat(path)
        entries.append({
            "name": name,
            "path": path,
            "size": info.st_size,
            "created_at": datetime.fromtimestamp(info.st_mtime),
        })
    return sorted(entries, key=lambda e: e["created_at"], reverse=True)


def prune(keep: int = 20) -> int:
    """Delete all but the newest ``keep`` backups; returns how many went."""
    removed = 0
    for entry in list_backups()[keep:]:
        try:
            os.remove(entry["path"])
            removed += 1
        except OSError:
            pass
    return removed


def restore(path: str) -> None:
    """Replace the live database with a backup, after safeguarding the current one."""
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    _verify(path)

    create("before-restore")
    live = db.path()
    db.close()
    for suffix in ("-wal", "-shm"):
        sidecar = live + suffix
        if os.path.exists(sidecar):
            os.remove(sidecar)
    shutil.copy2(path, live)
    db.connect(live)


def export_copy(destination: str) -> str:
    """Save a snapshot to a location the user picked (USB stick, cloud folder)."""
    source = create("export")
    shutil.copy2(source, destination)
    return destination


def _verify(path: str) -> None:
    """Refuse to restore anything that is not a healthy ShopDesk database."""
    probe = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        if probe.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("That backup file is damaged and cannot be restored.")
        tables = {row[0] for row in probe.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")}
        if not {"sales", "products", "settings"} <= tables:
            raise ValueError("That file is not a ShopDesk backup.")
    finally:
        probe.close()
