"""Money handling.

Every amount in the database is stored as an **integer number of minor units**
(paisa, cents, fils...).  Floating point is never used for money: 0.1 + 0.2 is
not 0.3, and a till that is off by a paisa a hundred times a day is a till the
shopkeeper stops trusting.

The number of decimals is a shop setting, so this module takes it as an
argument rather than assuming two.
"""

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

__all__ = [
    "parse_amount",
    "format_amount",
    "format_plain",
    "to_minor",
    "from_minor",
    "percent_of",
    "apply_rate",
    "extract_inclusive_tax",
    "split_proportionally",
]


def _quantum(decimals: int) -> Decimal:
    return Decimal(1).scaleb(-decimals)


def parse_amount(text, decimals: int = 2) -> int:
    """Parse user input into minor units.

    Accepts ``"1,250.50"``, ``"1250,50"``, ``" 12 "`` and plain numbers.
    Raises ``ValueError`` on anything else so callers can show a field error.
    """
    if text is None:
        raise ValueError("empty amount")
    if isinstance(text, (int, float, Decimal)):
        raw = Decimal(str(text))
    else:
        cleaned = str(text).strip().replace(" ", "")
        if not cleaned:
            raise ValueError("empty amount")
        # Treat a lone comma as a decimal separator, otherwise as a grouping mark.
        if cleaned.count(",") == 1 and "." not in cleaned:
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
        try:
            raw = Decimal(cleaned)
        except InvalidOperation as exc:
            raise ValueError(f"not a valid amount: {text!r}") from exc
    return int(raw.quantize(_quantum(decimals), rounding=ROUND_HALF_UP).scaleb(decimals))


def to_minor(value, decimals: int = 2) -> int:
    """Alias of :func:`parse_amount` for non user-facing conversions."""
    return parse_amount(value, decimals)


def from_minor(minor: int, decimals: int = 2) -> Decimal:
    """Exact decimal value of ``minor`` units."""
    return (Decimal(int(minor)) * _quantum(decimals)).quantize(_quantum(decimals))


def format_plain(minor: int, decimals: int = 2, grouping: bool = True) -> str:
    """``125050 -> '1,250.50'`` — no currency symbol."""
    value = from_minor(minor, decimals)
    pattern = f",.{decimals}f" if grouping else f".{decimals}f"
    return format(value, pattern)


def format_amount(minor: int, symbol: str = "", decimals: int = 2,
                  grouping: bool = True) -> str:
    """``125050 -> '৳1,250.50'``.  Negative amounts read ``-৳12.00``."""
    body = format_plain(abs(int(minor)), decimals, grouping)
    sign = "-" if int(minor) < 0 else ""
    return f"{sign}{symbol}{body}" if symbol else f"{sign}{body}"


def percent_of(minor: int, percent) -> int:
    """Percentage of an amount, rounded half-up to the nearest minor unit."""
    pct = Decimal(str(percent))
    return int((Decimal(int(minor)) * pct / Decimal(100)).quantize(
        Decimal(1), rounding=ROUND_HALF_UP))


def apply_rate(minor: int, rate) -> int:
    """Multiply an amount by a rate (``0.15`` -> 15%), rounding half-up."""
    return int((Decimal(int(minor)) * Decimal(str(rate))).quantize(
        Decimal(1), rounding=ROUND_HALF_UP))


def extract_inclusive_tax(minor: int, rate) -> int:
    """Tax already contained in a tax-inclusive amount.

    At 15%, a ৳115 shelf price contains ৳15 of tax, not ৳17.25.
    """
    rate = Decimal(str(rate))
    if rate <= 0 or minor <= 0:
        return 0
    base = (Decimal(int(minor)) / (Decimal(1) + rate)).quantize(
        Decimal(1), rounding=ROUND_HALF_UP)
    return int(minor) - int(base)


def split_proportionally(total: int, weights) -> list[int]:
    """Split ``total`` across ``weights`` so the parts add up exactly.

    Used to spread an invoice-level discount over its lines: naive per-line
    rounding loses or invents a unit, which then makes the receipt disagree
    with the sale total.  Any rounding remainder is handed to the largest
    lines, one unit at a time.
    """
    weights = [int(w) for w in weights]
    weight_sum = sum(weights)
    if weight_sum <= 0 or total == 0:
        return [0] * len(weights)

    exact = [Decimal(total) * Decimal(w) / Decimal(weight_sum) for w in weights]
    parts = [int(e.to_integral_value(rounding=ROUND_HALF_UP)) for e in exact]

    drift = total - sum(parts)
    if drift:
        step = 1 if drift > 0 else -1
        order = sorted(range(len(parts)), key=lambda i: weights[i], reverse=True)
        i = 0
        while drift != 0 and order:
            idx = order[i % len(order)]
            parts[idx] += step
            drift -= step
            i += 1
    return parts
