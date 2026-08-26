"""Customers and their outstanding balance.

A sale does not need a customer -- a walk-in is the common case and attaching
one is optional.  Customers exist so a shop can put a sale "on the book" and
collect later, which is how most neighbourhood shops actually trade.
"""

from app.core import clock, db

_BALANCE = """
COALESCE((SELECT SUM(s.due) FROM sales s
          WHERE s.customer_id = c.id AND s.status = 'completed'), 0)
- COALESCE((SELECT SUM(p.amount) FROM payments p
            WHERE p.customer_id = c.id AND p.kind = 'due'), 0)
"""

_BASE = f"""
SELECT c.*, ({_BALANCE}) AS balance,
       (SELECT COUNT(*) FROM sales s WHERE s.customer_id = c.id AND s.status = 'completed')
           AS sale_count,
       (SELECT MAX(s.created_at) FROM sales s WHERE s.customer_id = c.id) AS last_sale_at
FROM customers c
"""


def get(customer_id: int):
    return db.one(_BASE + " WHERE c.id = ?", (customer_id,))


def get_by_code(code: str):
    return db.one(_BASE + " WHERE c.code = ? COLLATE NOCASE", ((code or "").strip(),))


def list_all(search: str = "", active_only: bool = False,
             with_due_only: bool = False, limit: int | None = None) -> list:
    clauses, params = [], []
    if active_only:
        clauses.append("c.is_active = 1")
    if search.strip():
        term = f"%{search.strip()}%"
        clauses.append("(c.name LIKE ? OR c.phone LIKE ? OR c.code LIKE ?)")
        params += [term, term, term]
    sql = _BASE + (" WHERE " + " AND ".join(clauses) if clauses else "")
    if with_due_only:
        sql += (" AND " if clauses else " WHERE ") + "balance > 0"
    sql += " ORDER BY c.name COLLATE NOCASE"
    if limit:
        sql += f" LIMIT {int(limit)}"
    return db.query(sql, tuple(params))


def search(term: str, limit: int = 25) -> list:
    return list_all(search=term, active_only=True, limit=limit)


def balance_of(customer_id: int) -> int:
    row = db.one(f"SELECT ({_BALANCE}) AS balance FROM customers c WHERE c.id = ?",
                 (customer_id,))
    return int(row["balance"] or 0) if row else 0


def total_due() -> int:
    return db.scalar(
        "SELECT COALESCE((SELECT SUM(due) FROM sales WHERE status = 'completed' "
        "AND customer_id IS NOT NULL), 0) - "
        "COALESCE((SELECT SUM(amount) FROM payments WHERE kind = 'due'), 0)",
        default=0)


def count_with_due() -> int:
    return len(list_all(with_due_only=True))


def code_taken(code: str, exclude_id: int | None = None) -> bool:
    row = db.one("SELECT id FROM customers WHERE code = ? COLLATE NOCASE",
                 ((code or "").strip(),))
    return bool(row) and row["id"] != exclude_id


def suggest_code() -> str:
    """Next free numeric code, so the cashier never has to invent one."""
    highest = db.scalar(
        "SELECT MAX(CAST(code AS INTEGER)) FROM customers "
        "WHERE code GLOB '[0-9]*' AND CAST(code AS INTEGER) > 0", default=0) or 0
    return str(int(highest) + 1).zfill(4)


def create(*, name: str, code: str = "", phone: str = "", address: str = "",
           credit_limit: int = 0, note: str = "", is_active: bool = True) -> int:
    return db.execute(
        "INSERT INTO customers(code, name, phone, address, credit_limit, is_active, "
        "note, created_at) VALUES (?,?,?,?,?,?,?,?)",
        ((code or "").strip() or suggest_code(), name.strip(), phone.strip(),
         address.strip(), int(credit_limit), int(is_active), note.strip(),
         clock.stamp()))


def update(customer_id: int, **fields) -> None:
    allowed = ("code", "name", "phone", "address", "credit_limit", "is_active", "note")
    values = {}
    for key, value in fields.items():
        if key not in allowed:
            continue
        if key in ("credit_limit", "is_active"):
            value = int(value)
        elif isinstance(value, str):
            value = value.strip()
        values[key] = value
    if not values:
        return
    assignments = ", ".join(f"{key} = ?" for key in values)
    db.execute(f"UPDATE customers SET {assignments} WHERE id = ?",
               (*values.values(), customer_id))


def is_referenced(customer_id: int) -> bool:
    return bool(db.scalar(
        "SELECT EXISTS(SELECT 1 FROM sales WHERE customer_id = ?)",
        (customer_id,), default=0))


def delete(customer_id: int) -> None:
    db.execute("DELETE FROM customers WHERE id = ?", (customer_id,))


def ledger(customer_id: int, limit: int = 200) -> list:
    """Sales and payments for one customer, newest first."""
    return db.query("""
        SELECT created_at, kind, reference, detail, amount FROM (
            SELECT s.created_at AS created_at, 'sale' AS kind,
                   s.invoice_no AS reference,
                   CASE WHEN s.due > 0 THEN 'Credit sale' ELSE 'Paid sale' END AS detail,
                   s.due AS amount
            FROM sales s WHERE s.customer_id = ? AND s.status = 'completed'
            UNION ALL
            SELECT p.created_at, 'payment', COALESCE(p.reference, ''),
                   'Payment received (' || p.method || ')', -p.amount
            FROM payments p WHERE p.customer_id = ? AND p.kind = 'due'
        ) ORDER BY created_at DESC, kind LIMIT ?
    """, (customer_id, customer_id, limit))
