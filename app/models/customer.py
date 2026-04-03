from app.database.connection import get_db


class CustomerModel:

    MAIN_QUERY = (
        "SELECT customer_code, first_name, last_name, address, phone "
        "FROM customers ORDER BY ID DESC"
    )

    @staticmethod
    def get_all():
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(CustomerModel.MAIN_QUERY)
            return cursor.fetchall()

    @staticmethod
    def search(query):
        param = f"%{query}%"
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT customer_code, first_name, last_name, address, phone "
                "FROM customers "
                "WHERE first_name LIKE ? OR last_name LIKE ? "
                "OR address LIKE ? OR phone LIKE ? "
                "ORDER BY ID DESC",
                (param, param, param, param),
            )
            return cursor.fetchall()

    @staticmethod
    def get_by_code(code):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM customers WHERE customer_code=?", (int(code),)
            )
            return cursor.fetchall()

    @staticmethod
    def get_id_by_code(code):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT ID FROM customers WHERE customer_code=?", (int(code),)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    @staticmethod
    def get_next_code():
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT customer_code FROM customers ORDER BY customer_code DESC LIMIT 1"
            )
            result = cursor.fetchone()
            return (result[0] + 1) if result else 1001

    @staticmethod
    def add(code, first_name, last_name, address, phone):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO customers(customer_code, first_name, last_name, address, phone) "
                "VALUES (?, ?, ?, ?, ?)",
                (int(code), first_name, last_name, address, phone),
            )

    @staticmethod
    def update(code, first_name, last_name, address, phone):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE customers SET first_name=?, last_name=?, address=?, phone=? "
                "WHERE customer_code=?",
                (first_name, last_name, address, phone, int(code)),
            )

    @staticmethod
    def delete(code):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM customers WHERE customer_code=?", (int(code),)
            )

    @staticmethod
    def get_financial_summary(customer_id):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sum(sale_amount), sum(paid_amount), sum(due_amount) "
                "FROM sales WHERE customer_id=?",
                (int(customer_id),),
            )
            sales_row = cursor.fetchone()
            cursor.execute(
                "SELECT sum(amount) FROM duesPaid WHERE customer_id=?",
                (int(customer_id),),
            )
            due_paid_row = cursor.fetchone()

        total_sales = float(sales_row[0] or 0)
        total_paid  = float(sales_row[1] or 0)
        total_due   = float(sales_row[2] or 0)
        total_due_paid = float(due_paid_row[0] or 0)

        return {
            "total_sales": total_sales,
            "total_paid":  total_paid,
            "total_due":   total_due,
            "total_due_paid": total_due_paid,
            "net_due": total_due - total_due_paid,
        }
