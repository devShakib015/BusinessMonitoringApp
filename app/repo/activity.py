"""Append-only audit trail for actions worth answering questions about later."""

from contextlib import contextmanager

from app.core import clock, db

_muted = False


@contextmanager
def muted():
    """Stop recording — used while seeding sample data, which is not real work."""
    global _muted
    previous, _muted = _muted, True
    try:
        yield
    finally:
        _muted = previous


def record(user_id: int | None, action: str, detail: str = "",
           when: str | None = None) -> None:
    if _muted:
        return
    db.execute(
        "INSERT INTO activity_log(user_id, action, detail, created_at) VALUES (?, ?, ?, ?)",
        (user_id, action, detail, when or clock.stamp()))


def recent(limit: int = 200) -> list:
    return db.query(
        "SELECT a.*, COALESCE(u.full_name, u.username, 'Deleted user') AS who "
        "FROM activity_log a LEFT JOIN users u ON u.id = a.user_id "
        "ORDER BY a.id DESC LIMIT ?", (limit,))
