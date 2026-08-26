"""Dialogs that belong to the sell screen."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QButtonGroup, QFileDialog, QLineEdit, QListWidget,
                               QListWidgetItem, QRadioButton)

from app import config
from app.core import clock, settings
from app.core.quantity import ONE, format_qty
from app.printing import invoice_pdf, receipt
from app.repo import sales as sale_repo
from app.services import held
from app.ui import theme
from app.ui.dialogs.base import Dialog
from app.ui.widgets.common import (MoneyEdit, QuantityEdit, button, hbox, label,
                                   vbox)


class DiscountDialog(Dialog):
    """Take a percentage or a flat amount off the whole sale."""

    def __init__(self, parent, cart):
        super().__init__(parent, "Discount",
                         "Applies to the whole sale and is shared across the "
                         "lines, so tax and returns stay correct.", 420)
        self.cart = cart

        self._percent_mode = QRadioButton("Percentage")
        self._amount_mode = QRadioButton("Fixed amount")
        group = QButtonGroup(self)
        group.addButton(self._percent_mode)
        group.addButton(self._amount_mode)

        self._percent = QLineEdit()
        self._percent.setPlaceholderText("0")
        self._percent.setAlignment(Qt.AlignRight)
        self._amount = MoneyEdit()

        if cart.discount_amount:
            self._amount_mode.setChecked(True)
            self._amount.set_value(cart.discount_amount)
        else:
            self._percent_mode.setChecked(True)
            if cart.discount_percent:
                self._percent.setText(f"{cart.discount_percent:g}")

        self.body.addWidget(self._percent_mode)
        self.body.addWidget(self.field("Percent off (%)", self._percent))
        self.body.addWidget(self._amount_mode)
        self.body.addWidget(self.field(f"Amount off ({settings.symbol()})", self._amount))

        quick = hbox(spacing=6)
        for value in (5, 10, 15, 20):
            chip = button(f"{value}%", "ghost")
            chip.clicked.connect(lambda _=False, v=value: self._quick(v))
            quick.addWidget(chip)
        self.body.addLayout(quick)

        self.add_button("Remove discount", "ghost", self._remove)
        self.add_cancel()
        self.add_button("Apply", "primary", self._apply, default=True)
        self._percent.setFocus()
        self._percent.selectAll()

    def _quick(self, percent: int) -> None:
        self._percent_mode.setChecked(True)
        self._percent.setText(str(percent))
        self._apply()

    def _remove(self) -> None:
        self.cart.clear_discount()
        self.accept()

    def _apply(self) -> None:
        if self._percent_mode.isChecked():
            try:
                percent = float(self._percent.text().strip() or 0)
            except ValueError:
                self.show_error("Enter the discount as a number, for example 10.")
                return
            if not 0 <= percent <= 100:
                self.show_error("A percentage discount has to be between 0 and 100.")
                return
            self.cart.set_discount_percent(percent)
        else:
            amount = self._amount.value_or_none()
            if amount is None:
                self.show_error("Enter the discount amount.")
                return
            if amount > self.cart.totals().subtotal:
                self.show_error("The discount is more than the sale is worth.")
                return
            self.cart.set_discount_amount(amount)
        self.accept()


class LineEditorDialog(Dialog):
    """Change the quantity, price or discount of one line."""

    def __init__(self, parent, line, allow_price_change: bool):
        super().__init__(parent, line.name, "Adjust this line.", 400)
        self.line = line

        self._qty = QuantityEdit()
        self._qty.set_value(line.qty)
        self._price = MoneyEdit()
        self._price.set_value(line.unit_price)
        self._price.setEnabled(allow_price_change)
        self._discount = MoneyEdit()
        self._discount.set_value(line.discount)

        stock_hint = ("Not stock tracked" if not line.track_stock
                      else f"{format_qty(line.stock, line.unit)} in stock")
        self.body.addWidget(self.field(f"Quantity ({line.unit})", self._qty, stock_hint))
        self.body.addWidget(self.field(
            f"Unit price ({settings.symbol()})", self._price,
            "" if allow_price_change else "Only an admin can change the price."))
        self.body.addWidget(self.field(
            f"Line discount ({settings.symbol()})", self._discount))

        self.add_button("Remove line", "danger", self._remove)
        self.add_cancel()
        self.add_button("Save", "primary", self._save, default=True)
        self.removed = False
        self._qty.setFocus()
        self._qty.selectAll()

    def _remove(self) -> None:
        self.removed = True
        self.accept()

    def _save(self) -> None:
        qty = self._qty.value_or_none()
        price = self._price.value_or_none()
        discount = self._discount.value_or_none()
        if qty is None or qty <= 0:
            self.show_error("Quantity must be greater than zero.")
            return
        if price is None or price < 0:
            self.show_error("Enter a valid price.")
            return
        if discount is None or discount < 0:
            self.show_error("Enter a valid discount.")
            return
        if discount > price * qty // 1000:
            self.show_error("The discount is bigger than the line itself.")
            return
        self.line.qty = qty
        self.line.unit_price = price
        self.line.discount = discount
        self.accept()


class CustomItemDialog(Dialog):
    """Sell something that is not in the catalogue."""

    def __init__(self, parent):
        super().__init__(parent, "One-off item",
                         "For something you sell once and do not want to add to "
                         "the catalogue. It is not stock tracked.", 400)
        self.name = ""
        self.price = 0
        self.qty = ONE

        self._name = QLineEdit()
        self._name.setPlaceholderText("Photocopy, delivery charge, repair…")
        self._price = MoneyEdit()
        self._qty = QuantityEdit()
        self._qty.set_value(ONE)

        self.body.addWidget(self.field("Description", self._name))
        self.body.addWidget(self.row(
            self.field(f"Price ({settings.symbol()})", self._price),
            self.field("Quantity", self._qty)))

        self.add_cancel()
        self.add_button("Add to sale", "primary", self._add, default=True)
        self._name.setFocus()

    def _add(self) -> None:
        name = self._name.text().strip()
        price = self._price.value_or_none()
        qty = self._qty.value_or_none()
        if not name:
            self.show_error("Give the item a description.")
            return
        if price is None or price <= 0:
            self.show_error("Enter a price greater than zero.")
            return
        if qty is None or qty <= 0:
            self.show_error("Enter a quantity greater than zero.")
            return
        self.name, self.price, self.qty = name, price, qty
        self.accept()


class HeldSalesDialog(Dialog):
    """Pick up a sale that was parked earlier."""

    def __init__(self, parent):
        super().__init__(parent, "Held sales",
                         "Sales set aside to be finished later.", 480)
        self.resume_id = None

        self._list = QListWidget()
        self._list.setMinimumHeight(240)
        self._list.itemActivated.connect(lambda _: self._resume())
        self._list.setStyleSheet(
            f"QListWidget {{ background: {theme.hex_of('surface')};"
            f" border: 1px solid {theme.hex_of('border')}; border-radius: 10px; }}"
            f"QListWidget::item {{ padding: 10px 12px;"
            f" border-bottom: 1px solid {theme.hex_of('border')}; }}")
        self.body.addWidget(self._list)

        self.add_button("Discard", "danger", self._discard)
        self.add_cancel("Close")
        self.add_button("Resume", "primary", self._resume, default=True)
        self._reload()

    def _reload(self) -> None:
        self._list.clear()
        for row in held.list_all():
            item = QListWidgetItem(
                f"{row['label']}\nHeld {clock.pretty(row['created_at'])}"
                + (f" by {row['who']}" if row["who"] else ""))
            item.setData(Qt.UserRole, row["id"])
            self._list.addItem(item)
        if self._list.count():
            self._list.setCurrentRow(0)
        else:
            self.show_error("Nothing is on hold right now.")

    def _resume(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        self.resume_id = item.data(Qt.UserRole)
        self.accept()

    def _discard(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        held.discard(item.data(Qt.UserRole))
        self.clear_error()
        self._reload()


class SaleCompleteDialog(Dialog):
    """Confirmation after a sale, with the change to hand back and receipt actions."""

    def __init__(self, parent, result):
        super().__init__(parent, "Sale complete", "", 420)
        self.result = result
        self.start_new = False

        summary = vbox(spacing=4)
        summary.addWidget(label(result.invoice_no, "SectionTitle"))
        summary.addWidget(label(f"Total {settings.money(result.total)}", "Muted"))
        self.body.addLayout(summary)

        if result.change > 0:
            box = vbox(spacing=2)
            box.addWidget(label("CHANGE DUE", "StatLabel"))
            change = label(settings.money(result.change), "ChangeValue")
            box.addWidget(change)
            holder = self.field("", _wrap(box))
            self.body.addWidget(holder)

        if result.due > 0:
            note = label(f"{settings.money(result.due)} added to the customer's "
                         f"account.", "Muted")
            note.setWordWrap(True)
            self.body.addWidget(note)

        actions = hbox(spacing=8)
        actions.addWidget(button("Print receipt", "soft", "print", self._print))
        actions.addWidget(button("Save PDF invoice", "ghost", "download", self._pdf))
        self.body.addLayout(actions)

        self.add_button("New sale", "primary", self._next, default=True)

    def _print(self) -> None:
        try:
            receipt.print_receipt(self, self.result.sale_id)
        except Exception as error:  # printer problems must not lose the sale
            self.show_error(f"Could not print: {error}")

    def _pdf(self) -> None:
        sale = sale_repo.get(self.result.sale_id)
        path, _ = QFileDialog.getSaveFileName(
            self, "Save invoice",
            f"{config.documents_dir()}/{invoice_pdf.default_filename(sale)}",
            "PDF files (*.pdf)")
        if not path:
            return
        try:
            invoice_pdf.build(self.result.sale_id, path)
            self.show_error("")
            self.clear_error()
        except Exception as error:
            self.show_error(f"Could not save the invoice: {error}")

    def _next(self) -> None:
        self.start_new = True
        self.accept()


def _wrap(layout):
    from PySide6.QtWidgets import QFrame
    holder = QFrame()
    holder.setObjectName("CardFlat")
    outer = vbox(holder, (14, 12, 14, 12), 0)
    outer.addLayout(layout)
    return holder
