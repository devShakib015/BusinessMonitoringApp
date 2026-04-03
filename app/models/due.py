from app.database.connection import get_db


class DueModel:

    MAIN_QUERY = (
        "SELECT customers.customer_code, customers.first_name, customers.phone, "
        "duesPaid.amount, duesPaid.created_at "
        "FROM duesPaid INNER JOIN customers ON duesPaid.customer_id=customers.ID "
        "ORDER BY duesPaid.ID DESC"
    )

    @staticmethod
    def get_all():
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(DueModel.MAIN_QUERY)
            return cursor.fetchall()

    @staticmethod
    def search(query):
        param = f"%{query}%"
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT customers.customer_code, customers.first_name, customers.phone, "
                "duesPaid.amount, duesPaid.created_at "
                "FROM duesPaid INNER JOIN customers ON duesPaid.customer_id=customers.ID "
                "WHERE customers.customer_code LIKE ? OR customers.first_name LIKE ? "
                "OR customers.phone LIKE ? OR duesPaid.created_at LIKE ? "
                "ORDER BY duesPaid.ID DESC",
                (param, param, param, param),
            )
            return cursor.fetchall()

    @staticmethod
    def add(customer_id, amount):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO duesPaid(customer_id, amount) VALUES (?, ?)",
                (int(customer_id), float(amount)),
            )

    @staticmethod
    def get_net_due(customer_id):
        """Total due accrued minus total due paid for the given customer."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sum(due_amount) FROM sales WHERE customer_id=?",
                (int(customer_id),),
            )
            total_due = cursor.fetchone()[0] or 0.0
            cursor.execute(
                "SELECT sum(amount) FROM duesPaid WHERE customer_id=?",
                (int(customer_id),),
            )
            total_paid = cursor.fetchone()[0] or 0.0
        return float(total_due) - float(total_paid)

    @staticmethod
    def get_last_payment_date():
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT created_at FROM duesPaid ORDER BY ID DESC LIMIT 1"
            )
            result = cursor.fetchone()
            return result[0] if result else None

    @staticmethod
    def get_period_stats(date_filter):
        """Returns (sum_amount,) for payments matching date_filter."""
        param = f"%{date_filter}%"
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sum(amount) FROM duesPaid WHERE created_at LIKE ?",
                (param,),
            )
            return cursor.fetchone()
