"""Money received and refunded."""

from app.core import clock, db

METHOD_LABELS = {
    "cash": "Cash",
    "card": "Card",
    "mobile": "Mobile",
    "bank": "Bank transfer",
    "due": "On account",
}


def label(method: str) -> str:
    return METHOD_LABELS.get(method, method.title() if method else "")


def record(*, amount: int, kind: str, method: str = "cash", sale_id: int | None = None,
           customer_id: int | None = None, reference: str = "", note: str = "",
           user_id: int | None = None) -> int:
    return db.execute(
        "INSERT INTO payments(sale_id, customer_id, amount, method, kind, reference, "
        "note, user_id, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (sale_id, customer_id, int(amount), method, kind, reference.strip(),
         note.strip(), user_id, clock.stamp()))


def collect_due(customer_id: int, amount: int, *, method: str = "cash",
                note: str = "", user_id: int | None = None) -> int:
    """Take a payment against a customer's outstanding balance."""
    if amount <= 0:
        raise ValueError("Payment amount must be greater than zero.")
    return record(amount=amount, kind="due", method=method, customer_id=customer_id,
                  note=note, user_id=user_id)


def list_all(start: str | None = None, end: str | None = None,
             kind: str | None = None, limit: int = 500) -> list:
    clauses, params = [], []
    if start:
        clauses.append("p.created_at >= ?")
        params.append(start)
    if end:
        clauses.append("p.created_at < ?")
        params.append(end)
    if kind:
        clauses.append("p.kind = ?")
        params.append(kind)
    sql = ("SELECT p.*, s.invoice_no, COALESCE(c.name, 'Walk-in customer') AS customer_name, "
           "COALESCE(u.full_name, u.username, '') AS who "
           "FROM payments p "
           "LEFT JOIN sales s ON s.id = p.sale_id "
           "LEFT JOIN customers c ON c.id = p.customer_id "
           "LEFT JOIN users u ON u.id = p.user_id")
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += f" ORDER BY p.id DESC LIMIT {int(limit)}"
    return db.query(sql, tuple(params))


def totals_by_method(start: str, end: str) -> list:
    return db.query(
        "SELECT method, kind, SUM(amount) AS total, COUNT(*) AS count "
        "FROM payments WHERE created_at >= ? AND created_at < ? "
        "GROUP BY method, kind ORDER BY total DESC", (start, end))


def recent_for_customer(customer_id: int, limit: int = 50) -> list:
    return db.query(
        "SELECT p.*, COALESCE(u.full_name, u.username, '') AS who FROM payments p "
        "LEFT JOIN users u ON u.id = p.user_id "
        "WHERE p.customer_id = ? AND p.kind = 'due' ORDER BY p.id DESC LIMIT ?",
        (customer_id, limit))
