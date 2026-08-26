"""Reading sales, their lines, payments and returns.

Writing a sale goes through :mod:`app.services.checkout`, which needs all of
it to land in one transaction.
"""

from app.core import db

_BASE = """
SELECT s.*,
       COALESCE(c.name, 'Walk-in customer') AS customer_name,
       c.phone AS customer_phone,
       c.code  AS customer_code,
       COALESCE(u.full_name, u.username, '') AS cashier,
       (SELECT COUNT(*) FROM sale_items i WHERE i.sale_id = s.id) AS item_count,
       COALESCE((SELECT SUM(r.total) FROM sale_returns r WHERE r.sale_id = s.id), 0)
           AS returned_total
FROM sales s
LEFT JOIN customers c ON c.id = s.customer_id
LEFT JOIN users u     ON u.id = s.user_id
"""


def get(sale_id: int):
    return db.one(_BASE + " WHERE s.id = ?", (sale_id,))


def get_by_invoice(invoice_no: str):
    return db.one(_BASE + " WHERE s.invoice_no = ?", ((invoice_no or "").strip(),))


def list_all(search: str = "", start: str | None = None, end: str | None = None,
             customer_id: int | None = None, status: str | None = None,
             limit: int | None = 500) -> list:
    clauses, params = [], []
    if search.strip():
        term = f"%{search.strip()}%"
        clauses.append("(s.invoice_no LIKE ? OR c.name LIKE ? OR c.phone LIKE ?)")
        params += [term, term, term]
    if start:
        clauses.append("s.created_at >= ?")
        params.append(start)
    if end:
        clauses.append("s.created_at < ?")
        params.append(end)
    if customer_id:
        clauses.append("s.customer_id = ?")
        params.append(customer_id)
    if status:
        clauses.append("s.status = ?")
        params.append(status)

    sql = _BASE + (" WHERE " + " AND ".join(clauses) if clauses else "")
    sql += " ORDER BY s.id DESC"
    if limit:
        sql += f" LIMIT {int(limit)}"
    return db.query(sql, tuple(params))


def items(sale_id: int) -> list:
    """Sale lines with how much of each has already been returned."""
    return db.query("""
        SELECT i.*,
               COALESCE((SELECT SUM(ri.qty) FROM return_items ri
                         WHERE ri.sale_item_id = i.id), 0) AS returned_qty
        FROM sale_items i WHERE i.sale_id = ? ORDER BY i.id
    """, (sale_id,))


def payments(sale_id: int) -> list:
    return db.query(
        "SELECT * FROM payments WHERE sale_id = ? ORDER BY id", (sale_id,))


def last_sale():
    return db.one(_BASE + " WHERE s.status = 'completed' ORDER BY s.id DESC LIMIT 1")


def returns_for(sale_id: int) -> list:
    return db.query(
        "SELECT r.*, COALESCE(u.full_name, u.username, '') AS who "
        "FROM sale_returns r LEFT JOIN users u ON u.id = r.user_id "
        "WHERE r.sale_id = ? ORDER BY r.id DESC", (sale_id,))


def list_returns(search: str = "", start: str | None = None, end: str | None = None,
                 limit: int = 300) -> list:
    clauses, params = [], []
    if search.strip():
        term = f"%{search.strip()}%"
        clauses.append("(r.return_no LIKE ? OR s.invoice_no LIKE ? OR c.name LIKE ?)")
        params += [term, term, term]
    if start:
        clauses.append("r.created_at >= ?")
        params.append(start)
    if end:
        clauses.append("r.created_at < ?")
        params.append(end)
    sql = ("SELECT r.*, s.invoice_no, COALESCE(c.name, 'Walk-in customer') AS customer_name, "
           "COALESCE(u.full_name, u.username, '') AS who, "
           "(SELECT COUNT(*) FROM return_items ri WHERE ri.return_id = r.id) AS item_count "
           "FROM sale_returns r "
           "LEFT JOIN sales s ON s.id = r.sale_id "
           "LEFT JOIN customers c ON c.id = r.customer_id "
           "LEFT JOIN users u ON u.id = r.user_id")
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += f" ORDER BY r.id DESC LIMIT {int(limit)}"
    return db.query(sql, tuple(params))


def return_items(return_id: int) -> list:
    return db.query("SELECT * FROM return_items WHERE return_id = ? ORDER BY id",
                    (return_id,))
