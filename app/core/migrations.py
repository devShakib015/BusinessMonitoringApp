"""Schema creation and versioned upgrades.

The database is built by the app on first run rather than shipped as a binary
file, so a fresh download starts with an empty till and no stranger's data.
``PRAGMA user_version`` records which migrations have run; each new schema
change is appended as a new numbered step and never edited in place.
"""

import sqlite3

SCHEMA_V1 = """
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT    NOT NULL,
    full_name     TEXT    NOT NULL DEFAULT '',
    role          TEXT    NOT NULL DEFAULT 'cashier'
                          CHECK (role IN ('admin', 'cashier')),
    is_active     INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT    NOT NULL,
    last_login_at TEXT
);

CREATE TABLE settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE counters (
    name  TEXT PRIMARY KEY,
    value INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE
);

CREATE TABLE products (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sku             TEXT    COLLATE NOCASE,
    barcode         TEXT    COLLATE NOCASE,
    name            TEXT    NOT NULL COLLATE NOCASE,
    category_id     INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    unit            TEXT    NOT NULL DEFAULT 'pc',
    cost_price      INTEGER NOT NULL DEFAULT 0,
    sell_price      INTEGER NOT NULL DEFAULT 0,
    tax_rate        REAL    NOT NULL DEFAULT 0,
    track_stock     INTEGER NOT NULL DEFAULT 1,
    low_stock_level INTEGER NOT NULL DEFAULT 0,
    is_active       INTEGER NOT NULL DEFAULT 1,
    note            TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL,
    updated_at      TEXT    NOT NULL
);
CREATE UNIQUE INDEX idx_products_sku     ON products(sku)     WHERE sku IS NOT NULL;
CREATE UNIQUE INDEX idx_products_barcode ON products(barcode) WHERE barcode IS NOT NULL;
CREATE INDEX        idx_products_name    ON products(name);
CREATE INDEX        idx_products_active  ON products(is_active);

CREATE TABLE stock_movements (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    qty        INTEGER NOT NULL,
    unit_cost  INTEGER NOT NULL DEFAULT 0,
    reason     TEXT    NOT NULL CHECK (reason IN
                       ('opening', 'purchase', 'sale', 'return',
                        'adjustment', 'damage', 'void')),
    ref_table  TEXT,
    ref_id     INTEGER,
    note       TEXT    NOT NULL DEFAULT '',
    user_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TEXT    NOT NULL
);
CREATE INDEX idx_movements_product ON stock_movements(product_id);
CREATE INDEX idx_movements_created ON stock_movements(created_at);
CREATE INDEX idx_movements_ref     ON stock_movements(ref_table, ref_id);

CREATE TABLE customers (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    code         TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    name         TEXT    NOT NULL COLLATE NOCASE,
    phone        TEXT    NOT NULL DEFAULT '',
    address      TEXT    NOT NULL DEFAULT '',
    credit_limit INTEGER NOT NULL DEFAULT 0,
    is_active    INTEGER NOT NULL DEFAULT 1,
    note         TEXT    NOT NULL DEFAULT '',
    created_at   TEXT    NOT NULL
);
CREATE INDEX idx_customers_phone ON customers(phone);
CREATE INDEX idx_customers_name  ON customers(name);

CREATE TABLE sales (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no   TEXT    NOT NULL UNIQUE,
    customer_id  INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    user_id      INTEGER REFERENCES users(id) ON DELETE SET NULL,
    subtotal     INTEGER NOT NULL DEFAULT 0,
    discount     INTEGER NOT NULL DEFAULT 0,
    tax          INTEGER NOT NULL DEFAULT 0,
    rounding     INTEGER NOT NULL DEFAULT 0,
    total        INTEGER NOT NULL DEFAULT 0,
    paid         INTEGER NOT NULL DEFAULT 0,
    due          INTEGER NOT NULL DEFAULT 0,
    cost_total   INTEGER NOT NULL DEFAULT 0,
    status       TEXT    NOT NULL DEFAULT 'completed'
                         CHECK (status IN ('completed', 'void')),
    note         TEXT    NOT NULL DEFAULT '',
    created_at   TEXT    NOT NULL,
    voided_at    TEXT,
    voided_by    INTEGER REFERENCES users(id) ON DELETE SET NULL,
    void_reason  TEXT    NOT NULL DEFAULT ''
);
CREATE INDEX idx_sales_created  ON sales(created_at);
CREATE INDEX idx_sales_customer ON sales(customer_id);
CREATE INDEX idx_sales_status   ON sales(status);

CREATE TABLE sale_items (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id       INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    product_id    INTEGER REFERENCES products(id) ON DELETE SET NULL,
    name          TEXT    NOT NULL,
    sku           TEXT    NOT NULL DEFAULT '',
    unit          TEXT    NOT NULL DEFAULT 'pc',
    unit_price    INTEGER NOT NULL DEFAULT 0,
    unit_cost     INTEGER NOT NULL DEFAULT 0,
    qty           INTEGER NOT NULL,
    line_discount INTEGER NOT NULL DEFAULT 0,
    tax_rate      REAL    NOT NULL DEFAULT 0,
    tax           INTEGER NOT NULL DEFAULT 0,
    total         INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_sale_items_sale    ON sale_items(sale_id);
CREATE INDEX idx_sale_items_product ON sale_items(product_id);

CREATE TABLE payments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id     INTEGER REFERENCES sales(id) ON DELETE CASCADE,
    customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    amount      INTEGER NOT NULL,
    method      TEXT    NOT NULL DEFAULT 'cash',
    kind        TEXT    NOT NULL CHECK (kind IN ('sale', 'due', 'refund')),
    reference   TEXT    NOT NULL DEFAULT '',
    note        TEXT    NOT NULL DEFAULT '',
    user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at  TEXT    NOT NULL
);
CREATE INDEX idx_payments_customer ON payments(customer_id);
CREATE INDEX idx_payments_sale     ON payments(sale_id);
CREATE INDEX idx_payments_created  ON payments(created_at);

CREATE TABLE sale_returns (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    return_no   TEXT    NOT NULL UNIQUE,
    sale_id     INTEGER REFERENCES sales(id) ON DELETE SET NULL,
    customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    total       INTEGER NOT NULL DEFAULT 0,
    method      TEXT    NOT NULL DEFAULT 'cash'
                        CHECK (method IN ('cash', 'due')),
    reason      TEXT    NOT NULL DEFAULT '',
    created_at  TEXT    NOT NULL
);
CREATE INDEX idx_returns_sale    ON sale_returns(sale_id);
CREATE INDEX idx_returns_created ON sale_returns(created_at);

CREATE TABLE return_items (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    return_id    INTEGER NOT NULL REFERENCES sale_returns(id) ON DELETE CASCADE,
    sale_item_id INTEGER REFERENCES sale_items(id) ON DELETE SET NULL,
    product_id   INTEGER REFERENCES products(id) ON DELETE SET NULL,
    name         TEXT    NOT NULL,
    qty          INTEGER NOT NULL,
    unit_price   INTEGER NOT NULL DEFAULT 0,
    total        INTEGER NOT NULL DEFAULT 0,
    restock      INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX idx_return_items_return ON return_items(return_id);
CREATE INDEX idx_return_items_item   ON return_items(sale_item_id);

CREATE TABLE held_sales (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    label      TEXT    NOT NULL DEFAULT '',
    payload    TEXT    NOT NULL,
    user_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TEXT    NOT NULL
);

CREATE TABLE activity_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action     TEXT    NOT NULL,
    detail     TEXT    NOT NULL DEFAULT '',
    created_at TEXT    NOT NULL
);
CREATE INDEX idx_activity_created ON activity_log(created_at);
"""


def _apply_v1(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_V1)


#: ``(version, upgrade)`` pairs applied in order.  Append only.
MIGRATIONS: list[tuple[int, callable]] = [
    (1, _apply_v1),
]

LATEST = MIGRATIONS[-1][0]


def current_version(conn: sqlite3.Connection) -> int:
    return int(conn.execute("PRAGMA user_version").fetchone()[0])


def migrate(conn: sqlite3.Connection) -> int:
    """Bring the database up to :data:`LATEST`; returns the resulting version."""
    version = current_version(conn)
    if version > LATEST:
        raise RuntimeError(
            f"This database was created by a newer version of the app "
            f"(schema {version}, this build understands {LATEST}). "
            f"Please update before opening it.")

    for target, upgrade in MIGRATIONS:
        if target <= version:
            continue
        conn.execute("BEGIN")
        try:
            upgrade(conn)
            conn.execute(f"PRAGMA user_version = {target}")
        except BaseException:
            conn.rollback()
            raise
        conn.commit()
        version = target
    return version
