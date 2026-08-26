"""The in-progress sale.

The previous version kept the open cart in a database table, so a half-built
invoice survived a crash into the next customer's sale and two windows would
fight over the same rows.  A cart is now plain in-memory state owned by the
sell screen; nothing reaches the database until checkout.
"""

from dataclasses import dataclass

from app.core import settings
from app.core.money import (apply_rate, extract_inclusive_tax, percent_of,
                            split_proportionally)
from app.core.quantity import ONE, multiply


@dataclass
class CartLine:
    """One line of the sale, priced independently of the others."""

    product_id: int | None
    name: str
    unit_price: int
    qty: int = ONE
    sku: str = ""
    unit: str = "pc"
    unit_cost: int = 0
    tax_rate: float = 0.0
    discount: int = 0          # line discount, minor units
    track_stock: bool = True
    stock: int = 0             # available at the time the line was added

    @property
    def gross(self) -> int:
        return multiply(self.unit_price, self.qty)

    @property
    def net(self) -> int:
        return max(0, self.gross - self.discount)

    @property
    def cost(self) -> int:
        return multiply(self.unit_cost, self.qty)


@dataclass
class Totals:
    subtotal: int = 0          # sum of line gross amounts
    line_discount: int = 0
    order_discount: int = 0
    discount: int = 0          # line + order
    net: int = 0               # subtotal - discount (tax-exclusive basis)
    tax: int = 0
    rounding: int = 0
    total: int = 0
    cost: int = 0
    item_count: int = 0
    quantity: int = 0

    @property
    def profit(self) -> int:
        return self.net - self.cost


class Cart:
    """Lines plus an order-level discount, with all the arithmetic in one place."""

    def __init__(self):
        self.lines: list[CartLine] = []
        self.customer_id: int | None = None
        self.customer_name: str = ""
        self.discount_percent: float = 0.0
        self.discount_amount: int = 0
        self.note: str = ""

    # ── Contents ──────────────────────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self.lines)

    @property
    def is_empty(self) -> bool:
        return not self.lines

    def find(self, product_id: int | None) -> CartLine | None:
        if product_id is None:
            return None
        for line in self.lines:
            if line.product_id == product_id:
                return line
        return None

    def add_product(self, product, qty: int = ONE) -> CartLine:
        """Add a product row, merging into an existing line for the same product."""
        existing = self.find(product["id"])
        if existing is not None:
            existing.qty += qty
            existing.stock = product["stock"]
            return existing

        line = CartLine(
            product_id=product["id"],
            name=product["name"],
            unit_price=int(product["sell_price"]),
            qty=qty,
            sku=product["sku"] or "",
            unit=product["unit"] or "pc",
            unit_cost=int(product["cost_price"]),
            tax_rate=float(product["tax_rate"]),
            track_stock=bool(product["track_stock"]),
            stock=int(product["stock"]),
        )
        self.lines.append(line)
        return line

    def add_custom(self, name: str, unit_price: int, qty: int = ONE) -> CartLine:
        """A one-off line for something not in the catalogue."""
        line = CartLine(product_id=None, name=name, unit_price=unit_price, qty=qty,
                        track_stock=False)
        self.lines.append(line)
        return line

    def remove(self, index: int) -> None:
        if 0 <= index < len(self.lines):
            del self.lines[index]

    def clear(self) -> None:
        self.lines.clear()
        self.customer_id = None
        self.customer_name = ""
        self.discount_percent = 0.0
        self.discount_amount = 0
        self.note = ""

    # ── Order discount ────────────────────────────────────────────────────────

    def set_discount_percent(self, percent: float) -> None:
        self.discount_percent = max(0.0, min(100.0, float(percent)))
        self.discount_amount = 0

    def set_discount_amount(self, amount: int) -> None:
        self.discount_amount = max(0, int(amount))
        self.discount_percent = 0.0

    def clear_discount(self) -> None:
        self.discount_percent = 0.0
        self.discount_amount = 0

    def _order_discount(self, after_line_discounts: int) -> int:
        if self.discount_percent:
            return min(after_line_discounts, percent_of(after_line_discounts,
                                                        self.discount_percent))
        return min(after_line_discounts, self.discount_amount)

    # ── Totals ────────────────────────────────────────────────────────────────

    def line_shares(self) -> list[int]:
        """Order discount spread across lines, adding up to exactly the discount."""
        net_values = [line.net for line in self.lines]
        return split_proportionally(self._order_discount(sum(net_values)), net_values)

    def totals(self) -> Totals:
        if not self.lines:
            return Totals()

        subtotal = sum(line.gross for line in self.lines)
        line_discount = sum(line.discount for line in self.lines)
        net_values = [line.net for line in self.lines]
        order_discount = self._order_discount(sum(net_values))
        shares = split_proportionally(order_discount, net_values)

        taxes = 0
        inclusive = settings.tax_inclusive()
        if settings.tax_enabled():
            for line, share in zip(self.lines, shares):
                if not line.tax_rate:
                    continue
                taxable = max(0, line.net - share)
                rate = line.tax_rate / 100.0
                if inclusive:
                    taxes += extract_inclusive_tax(taxable, rate)
                else:
                    taxes += apply_rate(taxable, rate)

        net = sum(net_values) - order_discount
        total = net if inclusive else net + taxes

        step = settings.get_int("pos.round_total_to", 0)
        rounding = 0
        if step > 0 and total:
            rounded = int(round(total / step)) * step
            rounding = rounded - total
            total = rounded

        return Totals(
            subtotal=subtotal,
            line_discount=line_discount,
            order_discount=order_discount,
            discount=line_discount + order_discount,
            net=net,
            tax=taxes,
            rounding=rounding,
            total=total,
            cost=sum(line.cost for line in self.lines),
            item_count=len(self.lines),
            quantity=sum(line.qty for line in self.lines),
        )

    # ── Validation ────────────────────────────────────────────────────────────

    def stock_problems(self) -> list[str]:
        """Lines asking for more than the shelf holds."""
        from app.core.quantity import format_qty
        from app.repo import products as product_repo

        problems = []
        for line in self.lines:
            if not line.track_stock or line.product_id is None:
                continue
            available = product_repo.stock_of(line.product_id)
            if line.qty > available:
                problems.append(
                    f"{line.name}: {format_qty(line.qty, line.unit)} requested, "
                    f"only {format_qty(available, line.unit)} in stock")
        return problems

    # ── Hold / resume ─────────────────────────────────────────────────────────

    def to_payload(self) -> dict:
        return {
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "discount_percent": self.discount_percent,
            "discount_amount": self.discount_amount,
            "note": self.note,
            "lines": [line.__dict__.copy() for line in self.lines],
        }

    @classmethod
    def from_payload(cls, payload: dict) -> "Cart":
        cart = cls()
        cart.customer_id = payload.get("customer_id")
        cart.customer_name = payload.get("customer_name", "")
        cart.discount_percent = float(payload.get("discount_percent") or 0)
        cart.discount_amount = int(payload.get("discount_amount") or 0)
        cart.note = payload.get("note", "")
        for raw in payload.get("lines", []):
            cart.lines.append(CartLine(**raw))
        return cart
