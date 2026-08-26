"""Aggregate queries behind the dashboard and reports screens."""

from app.core import clock, db


def summary(start: str, end: str) -> dict:
    """Headline figures for a period. Bounds are ``>= start`` and ``< end``."""
    sales = db.one("""
        SELECT COUNT(*)                    AS sale_count,
               COALESCE(SUM(subtotal), 0)  AS gross,
               COALESCE(SUM(discount), 0)  AS discount,
               COALESCE(SUM(tax), 0)       AS tax,
               COALESCE(SUM(total), 0)     AS total,
               COALESCE(SUM(paid), 0)      AS paid,
               COALESCE(SUM(due), 0)       AS due,
               COALESCE(SUM(cost_total), 0) AS cost
        FROM sales WHERE status = 'completed' AND created_at >= ? AND created_at < ?
    """, (start, end))

    returns_total = db.scalar(
        "SELECT COALESCE(SUM(total), 0) FROM sale_returns "
        "WHERE created_at >= ? AND created_at < ?", (start, end), default=0)
    due_collected = db.scalar(
        "SELECT COALESCE(SUM(amount), 0) FROM payments "
        "WHERE kind = 'due' AND created_at >= ? AND created_at < ?",
        (start, end), default=0)
    items_sold = db.scalar("""
        SELECT COALESCE(SUM(i.qty), 0) FROM sale_items i JOIN sales s ON s.id = i.sale_id
        WHERE s.status = 'completed' AND s.created_at >= ? AND s.created_at < ?
    """, (start, end), default=0)
    voided = db.scalar(
        "SELECT COUNT(*) FROM sales WHERE status = 'void' "
        "AND created_at >= ? AND created_at < ?", (start, end), default=0)

    data = dict(sales) if sales else {}
    data.update(
        returns=int(returns_total),
        due_collected=int(due_collected),
        items_sold=int(items_sold),
        voided=int(voided),
    )
    data["net_sales"] = int(data.get("total", 0)) - int(returns_total)
    data["profit"] = (int(data.get("total", 0)) - int(data.get("tax", 0))
                      - int(data.get("cost", 0)) - int(returns_total))
    data["cash_in"] = int(data.get("paid", 0)) + int(due_collected) - int(returns_total)
    data["average_sale"] = (int(data.get("total", 0)) // int(data["sale_count"])
                            if data.get("sale_count") else 0)
    return data


def daily_series(start: str, end: str) -> list:
    return db.query("""
        SELECT DATE(created_at) AS day,
               COUNT(*)                AS sale_count,
               COALESCE(SUM(total), 0) AS total,
               COALESCE(SUM(total - tax - cost_total), 0) AS profit
        FROM sales WHERE status = 'completed' AND created_at >= ? AND created_at < ?
        GROUP BY DATE(created_at) ORDER BY day
    """, (start, end))


def hourly_series(start: str, end: str) -> list:
    return db.query("""
        SELECT CAST(STRFTIME('%H', created_at) AS INTEGER) AS hour,
               COUNT(*) AS sale_count, COALESCE(SUM(total), 0) AS total
        FROM sales WHERE status = 'completed' AND created_at >= ? AND created_at < ?
        GROUP BY hour ORDER BY hour
    """, (start, end))


def top_products(start: str, end: str, limit: int = 10, by: str = "revenue") -> list:
    order = "revenue DESC" if by == "revenue" else "qty DESC"
    return db.query(f"""
        SELECT i.product_id, i.name, i.unit,
               SUM(i.qty)                                AS qty,
               SUM(i.total)                              AS revenue,
               SUM(i.total - i.tax - (i.unit_cost * i.qty / 1000)) AS profit
        FROM sale_items i JOIN sales s ON s.id = i.sale_id
        WHERE s.status = 'completed' AND s.created_at >= ? AND s.created_at < ?
        GROUP BY i.product_id, i.name ORDER BY {order} LIMIT ?
    """, (start, end, limit))


def sales_by_cashier(start: str, end: str) -> list:
    return db.query("""
        SELECT COALESCE(u.full_name, u.username, 'Unknown') AS cashier,
               COUNT(*) AS sale_count, COALESCE(SUM(s.total), 0) AS total
        FROM sales s LEFT JOIN users u ON u.id = s.user_id
        WHERE s.status = 'completed' AND s.created_at >= ? AND s.created_at < ?
        GROUP BY s.user_id ORDER BY total DESC
    """, (start, end))


def payment_mix(start: str, end: str) -> list:
    return db.query("""
        SELECT method,
               COALESCE(SUM(CASE WHEN kind IN ('sale', 'due') THEN amount ELSE 0 END), 0)
                   AS received,
               COALESCE(SUM(CASE WHEN kind = 'refund' THEN -amount ELSE 0 END), 0)
                   AS refunded,
               COUNT(*) AS count
        FROM payments WHERE created_at >= ? AND created_at < ?
        GROUP BY method ORDER BY received DESC
    """, (start, end))


def today_snapshot() -> dict:
    from datetime import date
    start, end = clock.day_bounds(date.today())
    return summary(start, end)


def dead_stock(days: int = 30, limit: int = 20) -> list:
    """Active, in-stock products with no sale in the given window."""
    cutoff = db.scalar("SELECT DATETIME('now', 'localtime', ?)", (f"-{int(days)} days",))
    return db.query("""
        SELECT p.id, p.name, p.unit, p.sell_price,
               COALESCE((SELECT SUM(m.qty) FROM stock_movements m
                         WHERE m.product_id = p.id), 0) AS stock,
               (SELECT MAX(s.created_at) FROM sale_items i
                JOIN sales s ON s.id = i.sale_id
                WHERE i.product_id = p.id AND s.status = 'completed') AS last_sold_at
        FROM products p
        WHERE p.is_active = 1 AND p.track_stock = 1
        AND stock > 0
        AND (last_sold_at IS NULL OR last_sold_at < ?)
        ORDER BY stock * p.sell_price DESC LIMIT ?
    """, (cutoff, limit))
