"""Parked sales.

A customer goes back for the milk they forgot; the queue behind them should
not have to wait.  Holding a cart writes it aside as JSON and hands the till
back, ready for the next person.
"""

import json

from app.core import clock, db
from app.services.cart import Cart


def hold(cart: Cart, label: str = "", user_id: int | None = None) -> int:
    if cart.is_empty:
        raise ValueError("There is nothing to hold.")
    return db.execute(
        "INSERT INTO held_sales(label, payload, user_id, created_at) VALUES (?,?,?,?)",
        (label.strip() or _auto_label(cart), json.dumps(cart.to_payload()),
         user_id, clock.stamp()))


def list_all() -> list:
    return db.query(
        "SELECT h.*, COALESCE(u.full_name, u.username, '') AS who FROM held_sales h "
        "LEFT JOIN users u ON u.id = h.user_id ORDER BY h.id DESC")


def count() -> int:
    return db.scalar("SELECT COUNT(*) FROM held_sales", default=0)


def resume(held_id: int) -> Cart:
    row = db.one("SELECT payload FROM held_sales WHERE id = ?", (held_id,))
    if row is None:
        raise ValueError("That held sale is no longer there.")
    cart = Cart.from_payload(json.loads(row["payload"]))
    db.execute("DELETE FROM held_sales WHERE id = ?", (held_id,))
    return cart


def discard(held_id: int) -> None:
    db.execute("DELETE FROM held_sales WHERE id = ?", (held_id,))


def _auto_label(cart: Cart) -> str:
    if cart.customer_name:
        return cart.customer_name
    first = cart.lines[0].name
    extra = len(cart.lines) - 1
    return f"{first} +{extra} more" if extra else first
