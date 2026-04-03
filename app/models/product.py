from app.database.connection import get_db


class ProductModel:

    MAIN_QUERY = "SELECT product, weight, price FROM products ORDER BY ID DESC"

    @staticmethod
    def get_all():
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(ProductModel.MAIN_QUERY)
            return cursor.fetchall()

    @staticmethod
    def get_all_names():
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT product FROM products")
            return [row[0] for row in cursor.fetchall()]

    @staticmethod
    def get_all_ids():
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ID FROM products")
            return [row[0] for row in cursor.fetchall()]

    @staticmethod
    def search(query):
        param = f"%{query}%"
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT product, weight, price FROM products "
                "WHERE product LIKE ? ORDER BY ID DESC",
                (param,),
            )
            return cursor.fetchall()

    @staticmethod
    def get_by_name(name):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT product, weight, price FROM products WHERE product=?", (name,)
            )
            return cursor.fetchone()

    @staticmethod
    def get_id_by_name(name):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ID FROM products WHERE product=?", (name,))
            result = cursor.fetchone()
            return result[0] if result else None

    @staticmethod
    def get_available_stock(product_id):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sum(Quantity) FROM stocks WHERE product_id=?",
                (int(product_id),),
            )
            added = cursor.fetchone()[0] or 0
            cursor.execute(
                "SELECT sum(quantity) FROM stocks_removed WHERE product_ID=?",
                (int(product_id),),
            )
            removed = cursor.fetchone()[0] or 0
        return max(0, int(added) - int(removed))

    @staticmethod
    def add(name, weight, price):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO products(product, weight, price) VALUES (?, ?, ?)",
                (name, int(weight), float(price)),
            )

    @staticmethod
    def update(old_name, name, weight, price):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE products SET product=?, weight=?, price=? WHERE product=?",
                (name, int(weight), float(price), old_name),
            )

    @staticmethod
    def delete(name):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE product=?", (name,))

    @staticmethod
    def get_details(product_id):
        """Returns (name, weight, selling_price, cost_price, total_added, total_sold, remaining)."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE ID=?", (int(product_id),))
            row = cursor.fetchone()
            name, weight, selling_price = row[1], row[2], row[3]

            cursor.execute(
                "SELECT sum(quantity), sum(price) FROM stocks WHERE product_id=?",
                (int(product_id),),
            )
            stock_row = cursor.fetchone()
            total_added      = stock_row[0] or 0
            total_stock_price = stock_row[1] or 0

            cost_price = (
                float(total_stock_price) / float(total_added) if total_added else 0.0
            )

            cursor.execute(
                "SELECT sum(quantity) FROM stocks_removed WHERE product_id=?",
                (int(product_id),),
            )
            total_sold = cursor.fetchone()[0] or 0

        remaining = int(total_added) - int(total_sold)
        return (name, weight, selling_price, f"{cost_price:.2f}", total_added, total_sold, remaining)

    @staticmethod
    def get_full_by_name(name):
        """Returns (id, product, weight, price) for the named product."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE product=?", (name,))
            return cursor.fetchone()
