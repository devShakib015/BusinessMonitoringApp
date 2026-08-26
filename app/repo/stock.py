"""The stock ledger.

Every change in stock is an entry with a reason and, where relevant, a link
back to the sale or return that caused it.
"""

from app.core import clock, db

REASONS = ("opening", "purchase", "sale", "return", "adjustment", "damage", "void")

REASON_LABELS = {
    "opening": "Opening stock",
    "purchase": "Purchase",
    "sale": "Sold",
    "return": "Customer return",
    "adjustment": "Adjustment",
    "damage": "Damaged / lost",
    "void": "Voided sale",
}


def add_movement(product_id: int, qty: int, reason: str, *, unit_cost: int = 0,
                 ref_table: str | None = None, ref_id: int | None = None,
                 note: str = "", user_id: int | None = None) -> int:
    """Record a signed quantity change.  ``qty`` is in thousandths."""
    if reason not in REASONS:
        raise ValueError(f"unknown stock reason: {reason}")
    return db.execute(
        "INSERT INTO stock_movements(product_id, qty, unit_cost, reason, ref_table, "
        "ref_id, note, user_id, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (product_id, int(qty), int(unit_cost), reason, ref_table, ref_id,
         note.strip(), user_id, clock.stamp()))


def receive(product_id: int, qty: int, unit_cost: int, *, note: str = "",
            user_id: int | None = None, reason: str = "purchase") -> int:
    """Stock coming in.  Refreshes the product's cost price from what was paid."""
    movement_id = add_movement(product_id, abs(int(qty)), reason, unit_cost=unit_cost,
                               note=note, user_id=user_id)
    if unit_cost > 0:
        db.execute("UPDATE products SET cost_price = ?, updated_at = ? WHERE id = ?",
                   (int(unit_cost), clock.stamp(), product_id))
    return movement_id


def adjust_to(product_id: int, counted_qty: int, *, note: str = "",
              user_id: int | None = None) -> int | None:
    """Correct stock to a counted figure, writing only the difference."""
    from app.repo import products
    current = products.stock_of(product_id)
    delta = int(counted_qty) - int(current)
    if delta == 0:
        return None
    return add_movement(product_id, delta, "adjustment", note=note, user_id=user_id)


def history(product_id: int, limit: int = 200) -> list:
    return db.query(
        "SELECT m.*, COALESCE(u.full_name, u.username, '') AS who "
        "FROM stock_movements m LEFT JOIN users u ON u.id = m.user_id "
        "WHERE m.product_id = ? ORDER BY m.id DESC LIMIT ?", (product_id, limit))


def recent(limit: int = 200) -> list:
    return db.query(
        "SELECT m.*, p.name AS product_name, p.unit AS unit, "
        "COALESCE(u.full_name, u.username, '') AS who "
        "FROM stock_movements m "
        "JOIN products p ON p.id = m.product_id "
        "LEFT JOIN users u ON u.id = m.user_id "
        "ORDER BY m.id DESC LIMIT ?", (limit,))


def stock_value() -> tuple[int, int]:
    """``(retail_value, cost_value)`` of everything currently on the shelf."""
    row = db.one("""
        SELECT COALESCE(SUM(stock * p.sell_price), 0) / 1000 AS retail,
               COALESCE(SUM(stock * p.cost_price), 0) / 1000 AS cost
        FROM (SELECT p2.id, COALESCE(SUM(m.qty), 0) AS stock
              FROM products p2 LEFT JOIN stock_movements m ON m.product_id = p2.id
              WHERE p2.is_active = 1 GROUP BY p2.id) s
        JOIN products p ON p.id = s.id
        WHERE s.stock > 0
    """)
    return (int(row["retail"] or 0), int(row["cost"] or 0)) if row else (0, 0)
