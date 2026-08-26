"""Returns and refunds.

A shop that cannot take something back is not running a till, it is running a
one-way door.  A return re-stocks what came back, refunds in cash or credits
the customer's account, and never lets more come back than went out.
"""

from dataclasses import dataclass

from app.core import clock, db, settings
from app.core.quantity import format_qty, multiply
from app.repo import activity, sales as sale_repo


class ReturnError(Exception):
    """A return that must not be saved, with a cashier-facing message."""


@dataclass
class ReturnLine:
    sale_item_id: int
    product_id: int | None
    name: str
    unit: str
    unit_price: int
    qty: int                 # thousandths being returned
    max_qty: int             # thousandths still returnable
    restock: bool = True

    @property
    def total(self) -> int:
        return multiply(self.unit_price, self.qty)


def returnable_lines(sale_id: int) -> list[ReturnLine]:
    """Every line of a sale with the quantity still eligible to come back."""
    lines = []
    for item in sale_repo.items(sale_id):
        remaining = int(item["qty"]) - int(item["returned_qty"])
        if remaining <= 0:
            continue
        # Refund at what the customer actually paid per unit, after discounts.
        effective_price = (int(item["total"]) * 1000 // int(item["qty"])
                           if item["qty"] else 0)
        lines.append(ReturnLine(
            sale_item_id=item["id"],
            product_id=item["product_id"],
            name=item["name"],
            unit=item["unit"],
            unit_price=effective_price,
            qty=0,
            max_qty=remaining,
        ))
    return lines


def commit(sale_id: int, lines: list[ReturnLine], *, method: str = "cash",
           reason: str = "", user_id: int | None = None):
    """Record a return against a sale."""
    sale = sale_repo.get(sale_id)
    if sale is None:
        raise ReturnError("That sale no longer exists.")
    if sale["status"] == "void":
        raise ReturnError("This sale was voided, so there is nothing to return.")

    chosen = [line for line in lines if line.qty > 0]
    if not chosen:
        raise ReturnError("Choose at least one item and a quantity to return.")

    for line in chosen:
        if line.qty > line.max_qty:
            raise ReturnError(
                f"{line.name}: only {format_qty(line.max_qty, line.unit)} "
                f"of that line can still be returned.")

    if method == "due" and sale["customer_id"] is None:
        raise ReturnError(
            "A walk-in sale has no account to credit. Refund in cash instead.")

    total = sum(line.total for line in chosen)
    now = clock.stamp()

    with db.transaction() as conn:
        return_no = settings.next_document_number("return", conn)
        cursor = conn.execute(
            "INSERT INTO sale_returns(return_no, sale_id, customer_id, user_id, total, "
            "method, reason, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (return_no, sale_id, sale["customer_id"], user_id, total, method,
             reason.strip(), now))
        return_id = cursor.lastrowid

        for line in chosen:
            conn.execute(
                "INSERT INTO return_items(return_id, sale_item_id, product_id, name, "
                "qty, unit_price, total, restock) VALUES (?,?,?,?,?,?,?,?)",
                (return_id, line.sale_item_id, line.product_id, line.name,
                 line.qty, line.unit_price, line.total, int(line.restock)))

            if line.restock and line.product_id is not None:
                conn.execute(
                    "INSERT INTO stock_movements(product_id, qty, unit_cost, reason, "
                    "ref_table, ref_id, note, user_id, created_at) "
                    "VALUES (?,?,0,'return','sale_returns',?,?,?,?)",
                    (line.product_id, line.qty, return_id, return_no, user_id, now))

        if method == "due":
            # Crediting the account is a payment against the customer's balance.
            conn.execute(
                "INSERT INTO payments(sale_id, customer_id, amount, method, kind, "
                "reference, note, user_id, created_at) "
                "VALUES (?,?,?,'due','due',?,'Return credit',?,?)",
                (sale_id, sale["customer_id"], total, return_no, user_id, now))
        else:
            conn.execute(
                "INSERT INTO payments(sale_id, customer_id, amount, method, kind, "
                "reference, note, user_id, created_at) "
                "VALUES (?,?,?,?,'refund',?,'',?,?)",
                (sale_id, sale["customer_id"], -total, method, return_no, user_id, now))

    activity.record(user_id, "sale.return",
                    f"{return_no} against {sale['invoice_no']} · "
                    f"{settings.money(total)}")
    return return_no, total
