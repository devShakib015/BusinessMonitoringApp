"""Products, categories and the derived stock level.

Stock is never stored as a column.  It is the sum of the product's rows in
``stock_movements``, so every unit that ever entered or left the shop has a
row explaining why — which is what makes a stock discrepancy investigable
instead of just wrong.
"""

from app.core import clock, db

_BASE = """
SELECT p.*,
       c.name AS category_name,
       COALESCE((SELECT SUM(m.qty) FROM stock_movements m
                 WHERE m.product_id = p.id), 0) AS stock
FROM products p
LEFT JOIN categories c ON c.id = p.category_id
"""


def _clean(value: str | None) -> str | None:
    """Empty codes are stored as NULL so the unique index ignores them."""
    value = (value or "").strip()
    return value or None


# ── Reads ─────────────────────────────────────────────────────────────────────

def get(product_id: int):
    return db.one(_BASE + " WHERE p.id = ?", (product_id,))


def get_by_barcode(barcode: str):
    code = _clean(barcode)
    if not code:
        return None
    return db.one(_BASE + " WHERE p.barcode = ? AND p.is_active = 1", (code,))


def get_by_sku(sku: str):
    code = _clean(sku)
    if not code:
        return None
    return db.one(_BASE + " WHERE p.sku = ? AND p.is_active = 1", (code,))


def list_all(search: str = "", category_id: int | None = None,
             active_only: bool = False, low_stock_only: bool = False,
             limit: int | None = None) -> list:
    clauses, params = [], []
    if active_only:
        clauses.append("p.is_active = 1")
    if category_id:
        clauses.append("p.category_id = ?")
        params.append(category_id)
    if search.strip():
        term = f"%{search.strip()}%"
        clauses.append("(p.name LIKE ? OR p.sku LIKE ? OR p.barcode LIKE ?)")
        params += [term, term, term]

    sql = _BASE + (" WHERE " + " AND ".join(clauses) if clauses else "")
    if low_stock_only:
        sql += (" AND " if clauses else " WHERE ")
        sql += "p.track_stock = 1 AND stock <= p.low_stock_level"
    sql += " ORDER BY p.name COLLATE NOCASE"
    if limit:
        sql += f" LIMIT {int(limit)}"
    return db.query(sql, tuple(params))


def search_for_sale(term: str, limit: int = 40) -> list:
    """Matches for the sell screen: exact barcode first, then name/SKU."""
    term = term.strip()
    if not term:
        return db.query(_BASE + " WHERE p.is_active = 1 ORDER BY p.name COLLATE NOCASE "
                        f"LIMIT {int(limit)}")
    like = f"%{term}%"
    return db.query(
        _BASE + " WHERE p.is_active = 1 AND "
        "(p.barcode = ? OR p.sku = ? OR p.name LIKE ? OR p.sku LIKE ? OR p.barcode LIKE ?) "
        "ORDER BY (p.barcode = ?) DESC, (p.sku = ?) DESC, "
        "(p.name LIKE ?) DESC, p.name COLLATE NOCASE "
        f"LIMIT {int(limit)}",
        (term, term, like, like, like, term, term, f"{term}%"))


def stock_of(product_id: int) -> int:
    return db.scalar("SELECT COALESCE(SUM(qty), 0) FROM stock_movements WHERE product_id = ?",
                     (product_id,), default=0)


def count_active() -> int:
    return db.scalar("SELECT COUNT(*) FROM products WHERE is_active = 1", default=0)


def low_stock(limit: int | None = None) -> list:
    return list_all(active_only=True, low_stock_only=True, limit=limit)


def is_referenced(product_id: int) -> bool:
    """True when history depends on this product and it must not be deleted."""
    return bool(db.scalar(
        "SELECT EXISTS(SELECT 1 FROM sale_items WHERE product_id = ?)",
        (product_id,), default=0))


def code_taken(field: str, value: str, exclude_id: int | None = None) -> bool:
    code = _clean(value)
    if not code or field not in ("sku", "barcode"):
        return False
    row = db.one(f"SELECT id FROM products WHERE {field} = ?", (code,))
    return bool(row) and row["id"] != exclude_id


def name_taken(name: str, exclude_id: int | None = None) -> bool:
    row = db.one("SELECT id FROM products WHERE name = ? COLLATE NOCASE", (name.strip(),))
    return bool(row) and row["id"] != exclude_id


# ── Writes ────────────────────────────────────────────────────────────────────

def create(*, name: str, sku: str = "", barcode: str = "", category_id: int | None = None,
           unit: str = "pc", cost_price: int = 0, sell_price: int = 0,
           tax_rate: float = 0.0, track_stock: bool = True, low_stock_level: int = 0,
           is_active: bool = True, note: str = "") -> int:
    now = clock.stamp()
    return db.execute(
        "INSERT INTO products(sku, barcode, name, category_id, unit, cost_price, "
        "sell_price, tax_rate, track_stock, low_stock_level, is_active, note, "
        "created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (_clean(sku), _clean(barcode), name.strip(), category_id, unit.strip() or "pc",
         int(cost_price), int(sell_price), float(tax_rate), int(track_stock),
         int(low_stock_level), int(is_active), note.strip(), now, now))


def update(product_id: int, **fields) -> None:
    allowed = ("sku", "barcode", "name", "category_id", "unit", "cost_price",
               "sell_price", "tax_rate", "track_stock", "low_stock_level",
               "is_active", "note")
    values = {}
    for key, value in fields.items():
        if key not in allowed:
            continue
        if key in ("sku", "barcode"):
            value = _clean(value)
        elif key in ("track_stock", "is_active"):
            value = int(bool(value))
        elif key in ("cost_price", "sell_price", "low_stock_level"):
            value = int(value)
        elif key == "tax_rate":
            value = float(value)
        elif isinstance(value, str):
            value = value.strip()
        values[key] = value
    if not values:
        return
    values["updated_at"] = clock.stamp()
    assignments = ", ".join(f"{key} = ?" for key in values)
    db.execute(f"UPDATE products SET {assignments} WHERE id = ?",
               (*values.values(), product_id))


def set_active(product_id: int, active: bool) -> None:
    update(product_id, is_active=active)


def delete(product_id: int) -> None:
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))


# ── Categories ────────────────────────────────────────────────────────────────

def categories() -> list:
    return db.query(
        "SELECT c.id, c.name, "
        "(SELECT COUNT(*) FROM products p WHERE p.category_id = c.id) AS product_count "
        "FROM categories c ORDER BY c.name COLLATE NOCASE")


def category_id_for(name: str) -> int | None:
    """Find or create a category by name."""
    name = name.strip()
    if not name:
        return None
    row = db.one("SELECT id FROM categories WHERE name = ? COLLATE NOCASE", (name,))
    if row:
        return row["id"]
    return db.execute("INSERT INTO categories(name) VALUES (?)", (name,))


def rename_category(category_id: int, name: str) -> None:
    db.execute("UPDATE categories SET name = ? WHERE id = ?", (name.strip(), category_id))


def delete_category(category_id: int) -> None:
    db.execute("DELETE FROM categories WHERE id = ?", (category_id,))
