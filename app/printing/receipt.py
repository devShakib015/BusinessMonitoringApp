"""Thermal receipts.

Receipts are laid out as a narrow HTML document and sent straight to the
printer through Qt, so an 80mm roll printer installed on the shop's computer
works with no driver-specific code.  The same document exports to PDF for
shops that email or archive their receipts.
"""

from PySide6.QtCore import QMarginsF, QSizeF
from PySide6.QtGui import QPageLayout, QPageSize, QTextDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter

from app.core import clock, settings
from app.core.money import format_plain
from app.core.quantity import format_qty
from app.repo import payments as payment_repo, sales as sale_repo

WIDTHS = {"58mm": 48.0, "80mm": 72.0}


def _escape(text: str) -> str:
    return (str(text or "").replace("&", "&amp;")
            .replace("<", "&lt;").replace(">", "&gt;"))


def build_html(sale_id: int, *, copy_label: str = "") -> str:
    """The receipt for one sale, as a self-contained HTML document."""
    sale = sale_repo.get(sale_id)
    if sale is None:
        raise ValueError("That sale no longer exists.")

    items = sale_repo.items(sale_id)
    paid_rows = sale_repo.payments(sale_id)
    decimals = settings.decimals()
    symbol = settings.symbol()

    def amount(minor: int) -> str:
        return format_plain(minor, decimals)

    shop_lines = [line for line in (
        settings.get("shop.address"),
        settings.get("shop.phone") and f"Tel: {settings.get('shop.phone')}",
        settings.get("shop.email"),
        settings.get("shop.tax_id") and
        f"{settings.tax_label()} Reg: {settings.get('shop.tax_id')}",
    ) if line]

    rows = []
    for item in items:
        qty = format_qty(int(item["qty"]), item["unit"])
        rows.append(
            f"<tr><td colspan='2' class='item'>{_escape(item['name'])}</td></tr>"
            f"<tr><td class='qty'>{qty} &times; {amount(int(item['unit_price']))}</td>"
            f"<td class='money'>{amount(int(item['total']))}</td></tr>")

    def total_row(caption: str, value: str, strong: bool = False) -> str:
        cls = "grand" if strong else "sum"
        return (f"<tr class='{cls}'><td>{_escape(caption)}</td>"
                f"<td class='money'>{value}</td></tr>")

    totals = [total_row("Subtotal", amount(int(sale["subtotal"])))]
    if sale["discount"]:
        totals.append(total_row("Discount", f"-{amount(int(sale['discount']))}"))
    if sale["tax"]:
        totals.append(total_row(settings.tax_label(), amount(int(sale["tax"]))))
    if sale["rounding"]:
        totals.append(total_row("Rounding", amount(int(sale["rounding"]))))
    totals.append(total_row(f"TOTAL ({symbol})", amount(int(sale["total"])), True))

    for payment in paid_rows:
        totals.append(total_row(f"Paid ({payment_repo.label(payment['method'])})",
                                amount(int(payment["amount"]))))
    if sale["due"]:
        totals.append(total_row("Balance due", amount(int(sale["due"]))))

    meta = [f"Receipt: {_escape(sale['invoice_no'])}",
            f"Date: {clock.pretty(sale['created_at'])}"]
    if settings.get_bool("receipt.show_cashier") and sale["cashier"]:
        meta.append(f"Served by: {_escape(sale['cashier'])}")
    if sale["customer_id"]:
        meta.append(f"Customer: {_escape(sale['customer_name'])}")

    footer = settings.get("shop.receipt_footer")
    banner = (f"<div class='copy'>{_escape(copy_label)}</div>" if copy_label else "")

    return f"""
<html><head><meta charset="utf-8"><style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 8pt; color: #000; }}
  .shop {{ font-size: 12pt; font-weight: bold; text-align: center; }}
  .sub {{ text-align: center; font-size: 7pt; }}
  .copy {{ text-align: center; font-size: 7pt; font-weight: bold;
           border: 1px solid #000; padding: 2px; margin: 4px 0; }}
  .rule {{ border-top: 1px dashed #000; margin: 6px 0; }}
  table {{ width: 100%; border-collapse: collapse; }}
  td {{ padding: 0; font-size: 8pt; }}
  td.item {{ font-weight: bold; padding-top: 3px; }}
  td.qty {{ color: #000; }}
  td.money {{ text-align: right; }}
  tr.sum td {{ padding-top: 2px; }}
  tr.grand td {{ font-size: 11pt; font-weight: bold; padding: 4px 0; }}
  .meta {{ font-size: 7pt; }}
  .thanks {{ text-align: center; font-size: 8pt; margin-top: 8px; }}
  .tiny {{ text-align: center; font-size: 6pt; color: #444; margin-top: 6px; }}
</style></head><body>
  <div class="shop">{_escape(settings.get('shop.name'))}</div>
  {''.join(f"<div class='sub'>{_escape(line)}</div>" for line in shop_lines)}
  {banner}
  <div class="rule"></div>
  <div class="meta">{'<br>'.join(meta)}</div>
  <div class="rule"></div>
  <table>{''.join(rows)}</table>
  <div class="rule"></div>
  <table>{''.join(totals)}</table>
  <div class="rule"></div>
  <div class="thanks">{_escape(footer)}</div>
  <div class="tiny">{len(items)} item(s) &middot; ShopDesk POS</div>
</body></html>"""


PIXELS_PER_MM = 96 / 25.4
MARGIN_MM = 3.0


def _document(sale_id: int, copy_label: str = "") -> tuple[QTextDocument, float, float]:
    """Build the receipt and measure how long the paper needs to be."""
    width_mm = WIDTHS.get(settings.get("receipt.format"), 72.0)
    document = QTextDocument()
    document.setHtml(build_html(sale_id, copy_label=copy_label))
    # Lay the receipt out on one very long page to measure it, then shrink the
    # page to what it actually needs.  Printing scales the document page onto
    # the paper, so a page left oversized would print the whole receipt tiny.
    width_px = width_mm * PIXELS_PER_MM
    document.setPageSize(QSizeF(width_px, 100_000))
    content_px = document.documentLayout().documentSize().height()
    document.setPageSize(QSizeF(width_px, content_px))

    height_mm = max(60.0, content_px / PIXELS_PER_MM + 2 * MARGIN_MM)
    return document, width_mm, height_mm


def _configure(printer: QPrinter, width_mm: float, height_mm: float) -> None:
    # A roll printer feeds exactly as much paper as the page is long, so the
    # page is cut to the receipt rather than left at A4 length.
    printer.setPageSize(QPageSize(QSizeF(width_mm + 2 * MARGIN_MM, height_mm),
                                  QPageSize.Millimeter, "Receipt",
                                  QPageSize.ExactMatch))
    printer.setPageMargins(QMarginsF(MARGIN_MM, MARGIN_MM, MARGIN_MM, MARGIN_MM),
                           QPageLayout.Millimeter)
    printer.setFullPage(False)


def print_receipt(parent, sale_id: int, *, ask: bool = True,
                  copy_label: str = "") -> bool:
    """Send a receipt to a printer.  Returns False if the user cancelled."""
    document, width_mm, height_mm = _document(sale_id, copy_label)
    printer = QPrinter(QPrinter.HighResolution)
    _configure(printer, width_mm, height_mm)

    if ask:
        dialog = QPrintDialog(printer, parent)
        dialog.setWindowTitle("Print receipt")
        if dialog.exec() != QPrintDialog.Accepted:
            return False
    document.print_(printer)
    return True


def save_pdf(sale_id: int, path: str, copy_label: str = "") -> str:
    document, width_mm, height_mm = _document(sale_id, copy_label)
    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(path)
    _configure(printer, width_mm, height_mm)
    document.print_(printer)
    return path
