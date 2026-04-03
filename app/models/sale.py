from app.database.connection import get_db


class SaleModel:

    MAIN_QUERY = (
        "SELECT sales.sale_code, customers.first_name, customers.phone, "
        "sales.sale_amount, sales.paid_amount, sales.due_amount, sales.created_at "
        "FROM sales INNER JOIN customers ON sales.customer_id=customers.ID "
        "ORDER BY sales.created_at DESC"
    )

    @staticmethod
    def get_all():
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(SaleModel.MAIN_QUERY)
            return cursor.fetchall()

    @staticmethod
    def search(query):
        param = f"%{query}%"
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sales.sale_code, customers.first_name, customers.phone, "
                "sales.sale_amount, sales.paid_amount, sales.due_amount, sales.created_at "
                "FROM sales INNER JOIN customers ON sales.customer_id=customers.ID "
                "WHERE sales.sale_code LIKE ? OR customers.first_name LIKE ? "
                "OR customers.phone LIKE ? OR sales.created_at LIKE ? "
                "ORDER BY sales.created_at DESC",
                (param, param, param, param),
            )
            return cursor.fetchall()

    @staticmethod
    def add(sale_code, customer_id, sale_amount, paid_amount, due_amount, invoice_items):
        """
        Persist a new sale and move invoice_items into stocks_removed atomically.
        invoice_items: list of (product_id, quantity)
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sales(sale_code, customer_id, sale_amount, paid_amount, due_amount) "
                "VALUES (?, ?, ?, ?, ?)",
                (int(sale_code), int(customer_id),
                 float(sale_amount), float(paid_amount), float(due_amount)),
            )
            records = [(pid, qty, int(sale_code)) for pid, qty in invoice_items]
            cursor.executemany(
                "INSERT INTO stocks_removed(product_ID, quantity, sale_code) VALUES (?, ?, ?)",
                records,
            )

    @staticmethod
    def get_products_for_sale(sale_code):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT products.product, products.weight, products.price, "
                "stocks_removed.quantity, "
                "(products.price * stocks_removed.quantity) "
                "FROM stocks_removed "
                "JOIN products ON stocks_removed.product_id=products.ID "
                "WHERE stocks_removed.sale_code=?",
                (int(sale_code),),
            )
            return cursor.fetchall()

    @staticmethod
    def get_date(sale_code):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT created_at FROM sales WHERE sale_code=?", (int(sale_code),)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    @staticmethod
    def get_period_stats(date_filter):
        """Returns (sum_sale_amount, sum_paid_amount) for period matching date_filter."""
        param = f"%{date_filter}%"
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sum(sale_amount), sum(paid_amount) FROM sales WHERE created_at LIKE ?",
                (param,),
            )
            return cursor.fetchone()

    @staticmethod
    def get_customer_previous_due(customer_id):
        """Returns net previously accrued due for a customer (before current sale)."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sum(due_amount) FROM sales WHERE customer_id=?",
                (int(customer_id),),
            )
            total_due = cursor.fetchone()[0] or 0
            cursor.execute(
                "SELECT sum(amount) FROM duesPaid WHERE customer_id=?",
                (int(customer_id),),
            )
            total_paid = cursor.fetchone()[0] or 0
        return float(total_due) - float(total_paid)


class InvoiceItemModel:
    """Temporary table used while building an invoice before it is saved."""

    @staticmethod
    def get_all():
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoice_items")
            return cursor.fetchall()

    @staticmethod
    def get_total():
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT total_cost FROM invoice_items")
            rows = cursor.fetchall()
        return sum(float(r[0]) for r in rows)

    @staticmethod
    def add(name, price, quantity, total_cost):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO invoice_items VALUES (?, ?, ?, ?)",
                (name, float(price), int(quantity), float(total_cost)),
            )

    @staticmethod
    def delete_by_name(name):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT rowid FROM invoice_items WHERE name=?", (name,)
            )
            result = cursor.fetchone()
            if result:
                cursor.execute(
                    "DELETE FROM invoice_items WHERE rowid=?", (result[0],)
                )

    @staticmethod
    def clear():
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM invoice_items")

    @staticmethod
    def get_product_ids_and_quantities():
        """Returns list of (product_id, quantity) for the current invoice items."""
        from app.models.product import ProductModel
        items = InvoiceItemModel.get_all()
        result = []
        for item in items:
            name, _price, qty, _total = item
            pid = ProductModel.get_id_by_name(name)
            if pid:
                result.append((pid, int(qty)))
        return result
