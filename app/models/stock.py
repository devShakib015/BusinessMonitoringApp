from app.database.connection import get_db


class StockModel:

    MAIN_QUERY = (
        "SELECT stocks.ID, products.product, stocks.Quantity, stocks.Price, "
        "round(stocks.price_per_product, 2), stocks.created_at "
        "FROM stocks INNER JOIN products ON stocks.product_id=products.ID "
        "ORDER BY stocks.created_at DESC"
    )

    @staticmethod
    def get_all():
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(StockModel.MAIN_QUERY)
            return cursor.fetchall()

    @staticmethod
    def search(query):
        param = f"%{query}%"
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT stocks.ID, products.product, stocks.Quantity, stocks.price, "
                "round(stocks.price_per_product, 2), stocks.created_at "
                "FROM stocks INNER JOIN products ON stocks.product_id=products.ID "
                "WHERE products.product LIKE ? OR stocks.created_at LIKE ? "
                "ORDER BY stocks.created_at DESC",
                (param, param),
            )
            return cursor.fetchall()

    @staticmethod
    def add(product_id, quantity, price):
        price_per_product = float(price) / float(quantity)
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO stocks(product_id, Quantity, Price, price_per_product) "
                "VALUES (?, ?, ?, ?)",
                (int(product_id), int(quantity), float(price), price_per_product),
            )

    @staticmethod
    def update(stock_id, quantity, price):
        price_per_product = float(price) / float(quantity)
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE stocks SET Quantity=?, Price=?, price_per_product=? WHERE ID=?",
                (int(quantity), float(price), price_per_product, int(stock_id)),
            )

    @staticmethod
    def delete(stock_id):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM stocks WHERE ID=?", (int(stock_id),))

    @staticmethod
    def get_by_id(stock_id):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT Quantity, Price FROM stocks WHERE ID=?", (int(stock_id),)
            )
            return cursor.fetchone()

    @staticmethod
    def get_daily_sold(date):
        param = f"%{date}%"
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT products.ID, products.product, products.weight, products.price, "
                "sum(stocks_removed.quantity) "
                "FROM stocks_removed "
                "JOIN products ON stocks_removed.product_id=products.ID "
                "WHERE stocks_removed.created_at LIKE ? "
                "GROUP BY stocks_removed.product_id",
                (param,),
            )
            return cursor.fetchall()

    @staticmethod
    def get_avg_cost_per_product():
        """Returns list of (avg_cost,) per product, ordered by product_id."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT round(sum(price)/sum(quantity), 2) "
                "FROM stocks GROUP BY product_id"
            )
            return cursor.fetchall()

    @staticmethod
    def get_quantity_sold_per_product(date_filter):
        param = f"%{date_filter}%"
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sum(quantity) FROM stocks_removed "
                "WHERE created_at LIKE ? GROUP BY product_id",
                (param,),
            )
            return cursor.fetchall()
