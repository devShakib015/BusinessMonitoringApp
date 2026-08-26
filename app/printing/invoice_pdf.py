"""A4 PDF invoices.

Printed for customers who need a document rather than a till receipt --
credit sales, business customers, anything that goes in a file.
"""

import os

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdf_canvas

from app import config
from app.core import clock, settings
from app.core.money import format_plain
from app.core.quantity import format_qty
from app.repo import payments as payment_repo, sales as sale_repo

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
INK = HexColor("#101828")
MUTED = HexColor("#667085")
LINE = HexColor("#E2E6EC")


def money_symbol() -> str:
    """A symbol the PDF fonts can actually draw.

    ReportLab's built-in fonts cover Latin-1 only, so ``৳``, ``₹`` and ``₦``
    come out as a black box.  Where that would happen the currency code is
    printed instead -- ``BDT 120.00`` reads correctly everywhere.
    """
    symbol = settings.symbol()
    try:
        symbol.encode("cp1252")
    except (UnicodeEncodeError, LookupError):
        return settings.get("currency.code") or ""
    return symbol


def money(minor: int) -> str:
    symbol = money_symbol()
    body = format_plain(abs(int(minor)), settings.decimals())
    sign = "-" if int(minor) < 0 else ""
    if not symbol:
        return f"{sign}{body}"
    separator = " " if len(symbol) > 1 else ""
    return f"{sign}{symbol}{separator}{body}"


def default_filename(sale) -> str:
    who = (sale["customer_name"] or "walk-in").replace(" ", "-")
    return f"{sale['invoice_no']}-{who}.pdf"


def build(sale_id: int, path: str | None = None) -> str:
    """Write the invoice and return the file path."""
    sale = sale_repo.get(sale_id)
    if sale is None:
        raise ValueError("That sale no longer exists.")
    items = sale_repo.items(sale_id)
    payments = sale_repo.payments(sale_id)

    path = path or os.path.join(config.documents_dir(), default_filename(sale))
    accent = HexColor(_accent_hex())
    canvas = pdf_canvas.Canvas(path, pagesize=A4)
    canvas.setTitle(f"Invoice {sale['invoice_no']}")
    canvas.setAuthor(settings.get("shop.name"))

    y = _header(canvas, sale, accent)
    y = _parties(canvas, sale, y)
    y = _items_table(canvas, items, y)
    y = _totals(canvas, sale, payments, y, accent)
    _footer(canvas, sale)
    canvas.showPage()
    canvas.save()
    return path


# ── Sections ──────────────────────────────────────────────────────────────────

def _header(canvas, sale, accent) -> float:
    canvas.setFillColor(accent)
    canvas.rect(0, PAGE_H - 6, PAGE_W, 6, stroke=0, fill=1)

    y = PAGE_H - MARGIN - 6 * mm
    logo = settings.get("shop.logo")
    text_x = MARGIN
    if logo and os.path.exists(logo):
        try:
            canvas.drawImage(logo, MARGIN, y - 14 * mm, width=20 * mm, height=20 * mm,
                             preserveAspectRatio=True, mask="auto")
            text_x = MARGIN + 25 * mm
        except Exception:
            text_x = MARGIN

    canvas.setFillColor(INK)
    canvas.setFont("Helvetica-Bold", 18)
    canvas.drawString(text_x, y, settings.get("shop.name"))

    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(MUTED)
    line_y = y - 5.5 * mm
    for line in (settings.get("shop.address"), settings.get("shop.phone"),
                 settings.get("shop.email"), settings.get("shop.website")):
        if line:
            canvas.drawString(text_x, line_y, line)
            line_y -= 4.4 * mm

    canvas.setFont("Helvetica-Bold", 22)
    canvas.setFillColor(accent)
    canvas.drawRightString(PAGE_W - MARGIN, y, "INVOICE")

    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(PAGE_W - MARGIN, y - 6 * mm, sale["invoice_no"])
    canvas.drawRightString(PAGE_W - MARGIN, y - 10.5 * mm,
                           clock.pretty(sale["created_at"]))
    if sale["status"] == "void":
        canvas.setFillColor(HexColor("#DC2626"))
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawRightString(PAGE_W - MARGIN, y - 15.5 * mm, "VOIDED")

    return min(line_y, y - 16 * mm) - 6 * mm


def _parties(canvas, sale, y) -> float:
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.7)
    canvas.line(MARGIN, y, PAGE_W - MARGIN, y)
    y -= 8 * mm

    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN, y, "BILL TO")
    canvas.drawString(PAGE_W / 2, y, "PAYMENT")

    canvas.setFont("Helvetica-Bold", 11)
    canvas.setFillColor(INK)
    canvas.drawString(MARGIN, y - 6 * mm, sale["customer_name"])

    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(MUTED)
    detail_y = y - 11 * mm
    for line in (sale["customer_phone"], _customer_address(sale)):
        if line:
            canvas.drawString(MARGIN, detail_y, line)
            detail_y -= 4.4 * mm

    methods = {payment_repo.label(row["method"]) for row in sale_repo.payments(sale["id"])}
    canvas.setFont("Helvetica", 9)
    canvas.drawString(PAGE_W / 2, y - 6 * mm,
                      ", ".join(sorted(methods)) if methods else "Unpaid")
    if int(sale["due"]) > 0:
        canvas.setFillColor(HexColor("#DC2626"))
        canvas.drawString(PAGE_W / 2, y - 10.5 * mm,
                          f"Balance carried: {money(int(sale['due']))}")

    return min(detail_y, y - 16 * mm) - 4 * mm


def _customer_address(sale) -> str:
    if not sale["customer_id"]:
        return ""
    from app.repo import customers as customer_repo
    row = customer_repo.get(sale["customer_id"])
    return row["address"] if row else ""


def _items_table(canvas, items, y) -> float:
    decimals = settings.decimals()
    columns = [
        ("#", MARGIN + 3, "left"),
        ("DESCRIPTION", MARGIN + 14 * mm, "left"),
        ("QTY", PAGE_W - MARGIN - 78 * mm, "right"),
        ("PRICE", PAGE_W - MARGIN - 50 * mm, "right"),
        ("AMOUNT", PAGE_W - MARGIN - 3, "right"),
    ]

    canvas.setFillColor(HexColor("#F4F6F8"))
    canvas.rect(MARGIN, y - 8 * mm, PAGE_W - 2 * MARGIN, 8 * mm, stroke=0, fill=1)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(MUTED)
    for title, x, align in columns:
        (canvas.drawRightString if align == "right" else canvas.drawString)(
            x, y - 5.4 * mm, title)
    y -= 8 * mm

    canvas.setFont("Helvetica", 9)
    for index, item in enumerate(items, start=1):
        row_height = 7.5 * mm
        if y - row_height < MARGIN + 60 * mm:
            canvas.showPage()
            y = PAGE_H - MARGIN
        canvas.setFillColor(INK)
        canvas.drawString(MARGIN + 3, y - 5 * mm, str(index))
        canvas.drawString(MARGIN + 14 * mm, y - 5 * mm, item["name"][:52])
        canvas.drawRightString(PAGE_W - MARGIN - 78 * mm, y - 5 * mm,
                               format_qty(int(item["qty"]), item["unit"]))
        canvas.drawRightString(PAGE_W - MARGIN - 50 * mm, y - 5 * mm,
                               format_plain(int(item["unit_price"]), decimals))
        canvas.drawRightString(PAGE_W - MARGIN - 3, y - 5 * mm,
                               format_plain(int(item["total"]), decimals))
        canvas.setStrokeColor(LINE)
        canvas.line(MARGIN, y - row_height, PAGE_W - MARGIN, y - row_height)
        y -= row_height

    return y - 6 * mm


def _totals(canvas, sale, payments, y, accent) -> float:
    decimals = settings.decimals()
    right = PAGE_W - MARGIN - 3
    left = PAGE_W - MARGIN - 62 * mm

    def row(caption, value, bold=False, color=INK):
        nonlocal y
        canvas.setFont("Helvetica-Bold" if bold else "Helvetica", 10 if bold else 9)
        canvas.setFillColor(color)
        canvas.drawString(left, y, caption)
        canvas.drawRightString(right, y, value)
        y -= 5.4 * mm

    row("Subtotal", format_plain(int(sale["subtotal"]), decimals))
    if sale["discount"]:
        row("Discount", f"-{format_plain(int(sale['discount']), decimals)}")
    if sale["tax"]:
        row(settings.tax_label(), format_plain(int(sale["tax"]), decimals))
    if sale["rounding"]:
        row("Rounding", format_plain(int(sale["rounding"]), decimals))

    y -= 1 * mm
    canvas.setFillColor(accent)
    canvas.rect(left - 4 * mm, y - 3 * mm, PAGE_W - MARGIN - left + 4 * mm, 9 * mm,
                stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(left, y, f"TOTAL ({money_symbol()})")
    canvas.drawRightString(right, y, format_plain(int(sale["total"]), decimals))
    y -= 9 * mm

    for payment in payments:
        row(f"Paid — {payment_repo.label(payment['method'])}",
            format_plain(int(payment["amount"]), decimals))
    if int(sale["due"]) > 0:
        row("Balance due", format_plain(int(sale["due"]), decimals), True,
            HexColor("#DC2626"))
    return y


def _footer(canvas, sale) -> None:
    canvas.setStrokeColor(LINE)
    canvas.line(MARGIN, MARGIN + 12 * mm, PAGE_W - MARGIN, MARGIN + 12 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN, MARGIN + 7 * mm, settings.get("shop.receipt_footer"))
    canvas.drawRightString(PAGE_W - MARGIN, MARGIN + 7 * mm,
                           f"Served by {sale['cashier'] or '—'}")
    canvas.setFont("Helvetica", 7)
    canvas.drawString(MARGIN, MARGIN + 3 * mm,
                      f"Generated by {config.APP_NAME} {config.APP_VERSION}")


def _accent_hex() -> str:
    from app.ui.theme import ACCENTS
    return ACCENTS.get(settings.get("app.accent"), ACCENTS["indigo"])
