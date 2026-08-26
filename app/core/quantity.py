"""Quantities are stored as integer thousandths.

A shop that sells rice by the kilo needs ``1.5`` to be a real quantity, and a
shop that sells bottles needs ``2`` to print as ``2`` and not ``2.000``.  One
integer scale covers both without floats creeping into stock arithmetic.
"""

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

SCALE = 1000
ONE = SCALE

__all__ = ["SCALE", "ONE", "parse_qty", "format_qty", "qty_to_decimal", "multiply"]


def parse_qty(text) -> int:
    """Parse user input into thousandths.  Raises ``ValueError`` if invalid."""
    if text is None:
        raise ValueError("empty quantity")
    if isinstance(text, (int, float, Decimal)):
        raw = Decimal(str(text))
    else:
        cleaned = str(text).strip().replace(",", ".")
        if not cleaned:
            raise ValueError("empty quantity")
        try:
            raw = Decimal(cleaned)
        except InvalidOperation as exc:
            raise ValueError(f"not a valid quantity: {text!r}") from exc
    return int((raw * SCALE).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def qty_to_decimal(qty: int) -> Decimal:
    return (Decimal(int(qty)) / Decimal(SCALE)).normalize()


def format_qty(qty: int, unit: str = "") -> str:
    """``1500 -> '1.5'``, ``2000 -> '2'``, ``2000 with unit 'kg' -> '2 kg'``."""
    value = Decimal(int(qty)) / Decimal(SCALE)
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    if text in ("", "-"):
        text = "0"
    return f"{text} {unit}".strip() if unit else text


def multiply(unit_price: int, qty: int) -> int:
    """Line total in minor units for ``qty`` thousandths at ``unit_price``."""
    return int((Decimal(int(unit_price)) * Decimal(int(qty)) / Decimal(SCALE))
               .quantize(Decimal(1), rounding=ROUND_HALF_UP))
