"""User accounts and sign-in."""

from app.core import clock, db
from app.core.security import Session, hash_password, verify_password

ROLES = ("admin", "cashier")


def count() -> int:
    return db.scalar("SELECT COUNT(*) FROM users", default=0)


def has_any() -> bool:
    return count() > 0


def list_all(include_inactive: bool = True) -> list:
    sql = ("SELECT id, username, full_name, role, is_active, created_at, last_login_at "
           "FROM users")
    if not include_inactive:
        sql += " WHERE is_active = 1"
    return db.query(sql + " ORDER BY role = 'cashier', username COLLATE NOCASE")


def get(user_id: int):
    return db.one("SELECT * FROM users WHERE id = ?", (user_id,))


def get_by_username(username: str):
    return db.one("SELECT * FROM users WHERE username = ? COLLATE NOCASE",
                  (username.strip(),))


def username_taken(username: str, exclude_id: int | None = None) -> bool:
    row = get_by_username(username)
    return bool(row) and row["id"] != exclude_id


def create(username: str, password: str, full_name: str = "",
           role: str = "cashier", is_active: bool = True) -> int:
    if role not in ROLES:
        raise ValueError(f"unknown role: {role}")
    return db.execute(
        "INSERT INTO users(username, password_hash, full_name, role, is_active, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (username.strip(), hash_password(password), full_name.strip(),
         role, int(is_active), clock.stamp()))


def update(user_id: int, *, full_name: str, role: str, is_active: bool) -> None:
    if role not in ROLES:
        raise ValueError(f"unknown role: {role}")
    db.execute("UPDATE users SET full_name = ?, role = ?, is_active = ? WHERE id = ?",
               (full_name.strip(), role, int(is_active), user_id))


def set_password(user_id: int, password: str) -> None:
    db.execute("UPDATE users SET password_hash = ? WHERE id = ?",
               (hash_password(password), user_id))


def delete(user_id: int) -> None:
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))


def admin_count(exclude_id: int | None = None) -> int:
    sql = "SELECT COUNT(*) FROM users WHERE role = 'admin' AND is_active = 1"
    params: tuple = ()
    if exclude_id is not None:
        sql += " AND id != ?"
        params = (exclude_id,)
    return db.scalar(sql, params, default=0)


def authenticate(username: str, password: str) -> Session | None:
    """Return a session on success, ``None`` on bad credentials."""
    row = get_by_username(username)
    if row is None or not row["is_active"]:
        return None
    if not verify_password(password, row["password_hash"]):
        return None
    db.execute("UPDATE users SET last_login_at = ? WHERE id = ?",
               (clock.stamp(), row["id"]))
    return Session(user_id=row["id"], username=row["username"],
                   full_name=row["full_name"], role=row["role"])
