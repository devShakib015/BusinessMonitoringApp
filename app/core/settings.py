"""Shop configuration, stored in the database rather than in source.

The previous version hard-coded the shop name, address and phone number in
``config.py``, so every download printed someone else's details on its
invoices.  Everything a shop needs to make the app its own now lives here and
is editable from the Settings screen.
"""

from app.core import db

DEFAULTS: dict[str, str] = {
    # Shop identity -- printed on invoices and receipts
    "shop.name": "My Shop",
    "shop.address": "",
    "shop.phone": "",
    "shop.email": "",
    "shop.website": "",
    "shop.tax_id": "",
    "shop.logo": "",
    "shop.receipt_footer": "Thank you for shopping with us!",

    # Money
    "currency.symbol": "$",
    "currency.code": "USD",
    "currency.decimals": "2",

    # Tax
    "tax.enabled": "0",
    "tax.label": "VAT",
    "tax.rate": "0",
    "tax.inclusive": "0",

    # Numbering
    "invoice.prefix": "INV-",
    "invoice.pad": "5",
    "return.prefix": "RET-",

    # Selling behaviour
    "pos.allow_negative_stock": "0",
    "pos.default_payment": "cash",
    "pos.payment_methods": "cash,card,mobile,bank",
    "pos.round_total_to": "0",
    "pos.print_after_sale": "0",
    "pos.confirm_before_save": "0",
    "pos.low_stock_warning": "1",

    # Printing
    "receipt.format": "80mm",
    "receipt.show_logo": "1",
    "receipt.show_cashier": "1",

    # Appearance
    "app.theme": "light",
    "app.setup_complete": "0",
    "app.accent": "indigo",
}

_cache: dict[str, str] | None = None


def load() -> dict[str, str]:
    global _cache
    if _cache is None:
        stored = {row["key"]: row["value"] for row in db.query("SELECT key, value FROM settings")}
        _cache = {**DEFAULTS, **stored}
    return _cache


def invalidate() -> None:
    global _cache
    _cache = None


def get(key: str, default: str | None = None) -> str:
    value = load().get(key)
    if value is None:
        return default if default is not None else DEFAULTS.get(key, "")
    return value


def get_int(key: str, default: int = 0) -> int:
    try:
        return int(str(get(key)).strip() or default)
    except (TypeError, ValueError):
        return default


def get_float(key: str, default: float = 0.0) -> float:
    try:
        return float(str(get(key)).strip() or default)
    except (TypeError, ValueError):
        return default


def get_bool(key: str, default: bool = False) -> bool:
    value = str(get(key, "1" if default else "0")).strip().lower()
    return value in ("1", "true", "yes", "on")


def get_list(key: str) -> list[str]:
    return [part.strip() for part in get(key).split(",") if part.strip()]


def set_value(key: str, value) -> None:
    set_many({key: value})


def set_many(values: dict[str, object]) -> None:
    rows = [(key, "" if value is None else str(value)) for key, value in values.items()]
    with db.transaction() as conn:
        conn.executemany(
            "INSERT INTO settings(key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value", rows)
    invalidate()


# ── Convenience accessors used all over the UI ────────────────────────────────

def decimals() -> int:
    return max(0, min(4, get_int("currency.decimals", 2)))


def symbol() -> str:
    return get("currency.symbol")


def money(minor: int, with_symbol: bool = True) -> str:
    from app.core.money import format_amount
    return format_amount(minor, symbol() if with_symbol else "", decimals())


def tax_enabled() -> bool:
    return get_bool("tax.enabled")


def tax_label() -> str:
    return get("tax.label") or "Tax"


def default_tax_rate() -> float:
    return get_float("tax.rate", 0.0)


def tax_inclusive() -> bool:
    return get_bool("tax.inclusive")


def is_setup_complete() -> bool:
    return get_bool("app.setup_complete")


def next_document_number(kind: str = "invoice", conn=None) -> str:
    """``INV-00042`` — atomic, gap-free within a transaction."""
    prefix = get(f"{kind}.prefix", "INV-" if kind == "invoice" else "RET-")
    pad = get_int("invoice.pad", 5)
    value = db.next_counter(kind, conn)
    return f"{prefix}{str(value).zfill(pad)}"
