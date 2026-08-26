"""Committing a sale.

Everything a completed sale touches -- the invoice number, the sale header,
its lines, the payment, and the stock that left the shelf -- is written inside
one transaction.  Either the shop sold it and the stock moved, or neither
happened.
"""

from dataclasses import dataclass

from app.core import clock, db, settings
from app.repo import activity, customers as customer_repo
from app.services.cart import Cart, Totals


class CheckoutError(Exception):
    """A sale that must not be saved, with a message meant for the cashier."""


@dataclass
class SaleResult:
    sale_id: int
    invoice_no: str
    total: int
    paid: int
    due: int
    change: int
    method: str


def validate(cart: Cart, *, tendered: int, method: str) -> Totals:
    """Check a cart is sellable and return its totals.  Raises CheckoutError."""
    if cart.is_empty:
        raise CheckoutError("Add at least one item before taking payment.")

    totals = cart.totals()
    if totals.total < 0:
        raise CheckoutError("The total cannot be negative. Check the discount.")

    if tendered < 0:
        raise CheckoutError("Payment amount cannot be negative.")

    if not settings.get_bool("pos.allow_negative_stock"):
        problems = cart.stock_problems()
        if problems:
            raise CheckoutError("Not enough stock:\n\n  " + "\n  ".join(problems))

    paid = min(tendered, totals.total) if method != "due" else 0
    due = totals.total - paid
    if due > 0 and cart.customer_id is None:
        raise CheckoutError(
            "This sale is not fully paid.\n\n"
            "Attach a customer to put the balance on their account, "
            "or collect the full amount.")

    if due > 0 and cart.customer_id is not None:
        limit = _credit_limit(cart.customer_id)
        if limit:
            projected = customer_repo.balance_of(cart.customer_id) + due
            if projected > limit:
                raise CheckoutError(
                    f"This would put {cart.customer_name or 'the customer'} at "
                    f"{settings.money(projected)}, over their "
                    f"{settings.money(limit)} credit limit.")
    return totals


def commit(cart: Cart, *, tendered: int, method: str = "cash",
           user_id: int | None = None, when: str | None = None) -> SaleResult:
    """Persist the cart as a completed sale.

    ``when`` overrides the sale timestamp; it exists so sample data can be
    spread across past dates through the same code path a real sale takes.
    """
    totals = validate(cart, tendered=tendered, method=method)

    paid = min(tendered, totals.total) if method != "due" else 0
    due = totals.total - paid
    change = max(0, tendered - paid) if method == "cash" else 0
    shares = cart.line_shares()
    inclusive = settings.tax_inclusive()
    tax_on = settings.tax_enabled()

    with db.transaction() as conn:
        invoice_no = settings.next_document_number("invoice", conn)
        now = when or clock.stamp()

        cursor = conn.execute(
            "INSERT INTO sales(invoice_no, customer_id, user_id, subtotal, discount, "
            "tax, rounding, total, paid, due, cost_total, status, note, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,'completed',?,?)",
            (invoice_no, cart.customer_id, user_id, totals.subtotal, totals.discount,
             totals.tax, totals.rounding, totals.total, paid, due, totals.cost,
             cart.note, now))
        sale_id = cursor.lastrowid

        for line, share in zip(cart.lines, shares):
            taxable = max(0, line.net - share)
            if tax_on and line.tax_rate:
                from app.core.money import apply_rate, extract_inclusive_tax
                line_tax = (extract_inclusive_tax(taxable, line.tax_rate / 100.0)
                            if inclusive else apply_rate(taxable, line.tax_rate / 100.0))
            else:
                line_tax = 0
            line_total = taxable if inclusive else taxable + line_tax

            conn.execute(
                "INSERT INTO sale_items(sale_id, product_id, name, sku, unit, unit_price, "
                "unit_cost, qty, line_discount, tax_rate, tax, total) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (sale_id, line.product_id, line.name, line.sku, line.unit,
                 line.unit_price, line.unit_cost, line.qty, line.discount + share,
                 line.tax_rate if tax_on else 0.0, line_tax, line_total))

            if line.product_id is not None and line.track_stock:
                conn.execute(
                    "INSERT INTO stock_movements(product_id, qty, unit_cost, reason, "
                    "ref_table, ref_id, note, user_id, created_at) "
                    "VALUES (?,?,?,'sale','sales',?,?,?,?)",
                    (line.product_id, -line.qty, line.unit_cost, sale_id,
                     invoice_no, user_id, now))

        if paid > 0:
            conn.execute(
                "INSERT INTO payments(sale_id, customer_id, amount, method, kind, "
                "reference, note, user_id, created_at) VALUES (?,?,?,?,'sale',?,'',?,?)",
                (sale_id, cart.customer_id, paid, method, invoice_no, user_id, now))

    activity.record(user_id, "sale.create",
                    f"{invoice_no} · {settings.money(totals.total)}")

    return SaleResult(sale_id=sale_id, invoice_no=invoice_no, total=totals.total,
                      paid=paid, due=due, change=change, method=method)


def void_sale(sale_id: int, reason: str, user_id: int | None = None) -> None:
    """Reverse a completed sale, putting its stock back."""
    from app.repo import sales as sale_repo

    sale = sale_repo.get(sale_id)
    if sale is None:
        raise CheckoutError("That sale no longer exists.")
    if sale["status"] == "void":
        raise CheckoutError("This sale has already been voided.")
    if sale_repo.returns_for(sale_id):
        raise CheckoutError(
            "This sale has returns recorded against it, so it cannot be voided. "
            "Reverse the returns first.")
    if not reason.strip():
        raise CheckoutError("Please give a reason for voiding this sale.")

    now = clock.stamp()
    with db.transaction() as conn:
        conn.execute(
            "UPDATE sales SET status = 'void', voided_at = ?, voided_by = ?, "
            "void_reason = ? WHERE id = ?", (now, user_id, reason.strip(), sale_id))
        for item in conn.execute(
                "SELECT product_id, qty, unit_cost FROM sale_items WHERE sale_id = ?",
                (sale_id,)).fetchall():
            if item["product_id"] is None:
                continue
            conn.execute(
                "INSERT INTO stock_movements(product_id, qty, unit_cost, reason, "
                "ref_table, ref_id, note, user_id, created_at) "
                "VALUES (?,?,?,'void','sales',?,?,?,?)",
                (item["product_id"], item["qty"], item["unit_cost"], sale_id,
                 f"Void {sale['invoice_no']}", user_id, now))
        conn.execute("DELETE FROM payments WHERE sale_id = ?", (sale_id,))

    activity.record(user_id, "sale.void", f"{sale['invoice_no']} · {reason.strip()}")


def _credit_limit(customer_id: int) -> int:
    row = db.one("SELECT credit_limit FROM customers WHERE id = ?", (customer_id,))
    return int(row["credit_limit"]) if row else 0
