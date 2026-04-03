import os
from tkinter import filedialog

import pytz
from datetime import datetime
from num2words import num2words
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.colors import HexColor, Color

from app.config import IMAGE_PATH, TIMEZONE, BRAND_NAME, BRAND_ADDRESS, BRAND_CONTACT

# Register fonts once at module load time.
# Arial.ttf / Verdana.ttf must be resolvable by reportlab (system fonts or cwd).
try:
    pdfmetrics.registerFont(TTFont("Arial", "Arial.ttf"))
    pdfmetrics.registerFont(TTFont("Verdana", "Verdana.ttf"))
except Exception:
    pass  # Fonts may already be registered or unavailable – the PDF will fall back.

_PAGE_W = 595
_PAGE_H = 842
_MARGIN = 13


def create_invoice(
    invoice_number, invoice_date,
    customer_code, customer_name, customer_phone, customer_address,
    product_list,
    total_sales, discount_rate, discount_amount,
    net_sales, payment_amount, due_amount,
    previous_due, total_payable,
):
    """Generate a sales invoice PDF and prompt the user for a save location."""
    out_dir = filedialog.askdirectory()
    if not out_dir:
        return
    out_path = os.path.join(out_dir, f"{invoice_number}_{customer_name}.pdf")

    c = canvas.Canvas(out_path)
    c.setPageSize((_PAGE_W, _PAGE_H))

    blue = HexColor("#2b92c5")

    # ── Header ────────────────────────────────────────────────────────────────
    c.drawImage(IMAGE_PATH, 45, 770, width=60, height=67)

    c.setFillColor(colors.green)
    c.setFont("Verdana", 24)
    _centered(c, BRAND_NAME, "Verdana", 24, 813)

    c.setFillColor(colors.black)
    c.setFont("Verdana", 9)
    _centered(c, BRAND_ADDRESS, "Verdana", 9, 795)
    _centered(c, BRAND_CONTACT, "Verdana", 10, 780)

    # Invoice box
    for x1, y1, x2, y2 in [(45, 690, 550, 750)]:
        c.line(x1, y1, x2, y1)
        c.line(x1, y2, x2, y2)
        c.line(x1, y1, x1, y2)
        c.line(x2, y1, x2, y2)

    c.setFont("Verdana", 16)
    _centered(c, "INVOICE", "Verdana", 16, 756)

    c.setFont("Verdana", 10)
    c.drawString(55, 702, f"Invoice No: {invoice_number}")
    c.drawString(55 + 270, 702, f"Invoice Date: {invoice_date}")
    c.drawString(55, 717, f"PC: {customer_code}")
    c.drawString(55 + 270, 717, f"Phone: {customer_phone}")
    c.drawString(55, 732, f"PN: {customer_name}")
    c.drawString(55 + 270, 732, f"PA: {customer_address}")

    # ── Product table ─────────────────────────────────────────────────────────
    y = _PAGE_H - _MARGIN * 6
    box_left, box_right = 45, 550
    box_top, box_bottom = y, 230

    c.setFillColor(HexColor("#EAEAEC"))
    c.rect(box_left, box_bottom, 505, y - 250, fill=True, stroke=True)

    # Header row
    c.setFillColor(blue)
    c.rect(box_left, box_top - 20, 505, 20, fill=True, stroke=True)

    y -= _MARGIN
    c.setFillColor(colors.white)
    c.setFont("Verdana", 10)
    _col(c, "Product Name", "Arial", 10, box_left, 0,   200, y)
    _col(c, "Weight (g)",   "Arial", 10, box_left, 100, 280, y)
    _col(c, "Price",        "Arial", 10, box_left, 140, 340, y)
    _col(c, "Quantity",     "Arial", 10, box_left, 167, 400, y)
    _col(c, "Total Cost",   "Arial", 10, box_left, 180, 550, y)

    # Column separators
    for x_off in (200, 280, 340, 400):
        c.line(box_left + x_off, box_top, box_left + x_off, box_bottom)

    # Product rows
    c.setFillColor(colors.black)
    row_y = box_top - 35
    for idx, item in enumerate(product_list):
        c.drawString(box_left + 25, row_y, f"{idx + 1}. {item[0]}")
        c.drawString(box_left + 230, row_y, str(item[1]))
        c.drawString(box_left + 295, row_y, str(item[2]))
        c.drawString(box_left + 360, row_y, str(item[3]))
        c.drawString(box_left + 420, row_y, str(item[4]))
        row_y -= 15

    # ── Totals ────────────────────────────────────────────────────────────────
    b = box_bottom - 20
    _summary_row(c, "Total Sales:", str(total_sales), b);         b -= 20
    _summary_row(c, f"Discount: ({discount_rate}%)", f"({discount_amount})", b)
    b -= 8
    c.line(box_left + 200, b, 555, b);                            b -= 12
    _summary_row(c, "Net Sales:", str(net_sales), b);             b -= 20
    _summary_row(c, "Paying amount:", f"({payment_amount})", b)
    b -= 8
    c.line(box_left + 200, b, 555, b);                            b -= 12
    c.setFillColor(colors.red)
    _summary_row(c, "Due amount:", str(due_amount), b)
    c.setFillColor(colors.black)

    b -= 14
    amount_text = f"Amount in Words: {num2words(float(net_sales))}"
    c.setFont("Verdana", 10)
    tw = stringWidth(amount_text, "Arial", 10)
    c.drawString(box_left + 120 + (380 - tw) / 2, b - 10, amount_text)

    # Signature lines
    _signature(c, "Authorized Signature", box_left, b + 60)
    _signature(c, "Customer Signature",   box_left, b + 12)

    c.save()


def create_due_invoice(
    invoice_date,
    customer_code, customer_name, customer_phone, customer_address,
    previous_due, payment_amount, current_due,
):
    """Generate a due-payment invoice PDF."""
    tz = pytz.timezone(TIMEZONE)
    due_code = datetime.now(tz).strftime("%Y%m%d%H%M%S")
    parts = customer_name.split()
    fname = parts[0] if parts else customer_name
    lname = parts[1] if len(parts) > 1 else ""
    filename = f"{customer_code}_{due_code}_{fname}_{lname}_due_payment.pdf"

    out_dir = filedialog.askdirectory()
    if not out_dir:
        return
    out_path = os.path.join(out_dir, filename)

    c = canvas.Canvas(out_path)
    c.setPageSize((_PAGE_W, _PAGE_H))

    blue = HexColor("#2b92c5")
    x = 4 * _MARGIN

    # ── Header ────────────────────────────────────────────────────────────────
    c.drawImage(IMAGE_PATH, 45, 770, width=60, height=67)

    c.setFont("Verdana", 24)
    _centered(c, BRAND_NAME, "Verdana", 24, 813)
    c.setFillColor(colors.black)

    c.setFont("Verdana", 9)
    _centered(c, BRAND_ADDRESS, "Verdana", 9, 795)
    _centered(c, BRAND_CONTACT, "Verdana", 10, 780)

    for x1, y1, x2, y2 in [(45, 690, 550, 750)]:
        c.line(x1, y1, x2, y1); c.line(x1, y2, x2, y2)
        c.line(x1, y1, x1, y2); c.line(x2, y1, x2, y2)

    c.setFont("Verdana", 16)
    _centered(c, "DUE INVOICE", "Verdana", 16, 756)

    c.setFont("Verdana", 10)
    c.drawString(x + 270, 702, f"Invoice Date: {invoice_date}")
    c.drawString(55, 717, f"PC: {customer_code}")
    c.drawString(55, 732, f"PN: {customer_name}")
    c.drawString(x + 270, 717, f"Phone: {customer_phone}")
    c.drawString(x + 270, 732, f"PA: {customer_address}")

    # ── Summary box ───────────────────────────────────────────────────────────
    y = _PAGE_H - _MARGIN * 6
    c.setFillColor(HexColor("#EAEAEC"))
    c.rect(x, y - 400, 490, 360, fill=True, stroke=True)

    c.setFont("Verdana", 15)
    c.setFillColor(colors.black)
    row_y = y - 100

    c.drawString(x + 100, row_y - 40, "Previous Due: ")
    c.drawString(x + 350, row_y - 40, str(previous_due))
    row_y -= 25

    c.drawString(x + 100, row_y - 40, "Due Payment Now: ")
    c.drawString(x + 350, row_y - 40, f"({payment_amount})")
    row_y -= 50

    c.line(x + 50, row_y - 27, x + 430, row_y - 27)
    row_y -= 10

    c.drawString(x + 100, row_y - 40, "Current Due: ")
    c.setFillColor(colors.red)
    c.drawString(x + 350, row_y - 40, str(current_due))

    c.setFillColor(colors.black)
    sig_y = (y - 400) - 80
    _signature(c, "Authorized Signature", x + 10, sig_y)
    _signature(c, "Customer Signature",   x + 320, sig_y)

    c.save()


# ── Private helpers ───────────────────────────────────────────────────────────

def _centered(c, text, font, size, y):
    tw = stringWidth(text, font, size)
    c.drawString(int((_PAGE_W - tw) / 2), y, text)


def _col(c, text, font, size, box_left, x_offset, center_range, y):
    tw = stringWidth(text, font, size)
    c.drawString(box_left + x_offset + (center_range - tw) / 2, y, text)


def _summary_row(c, label, value, y):
    box_left = 45
    lw = stringWidth(label, "Arial", 10)
    c.drawString(box_left + 130 + (380 - lw) / 2, y, label)
    vw = stringWidth(value, "Arial", 10)
    c.drawString(box_left + 170 + (555 - vw) / 2, y, value)


def _signature(c, text, x, y):
    tw = stringWidth(text, "Verdana", 10)
    c.drawString(x, y, text)
    c.line(x - 5, y + 22, x + tw + 5, y + 22)
