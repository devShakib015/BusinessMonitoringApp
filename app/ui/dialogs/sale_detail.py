"""Looking at a past sale, and the things you can do to it."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QLineEdit,
                               QTableWidgetItem)

from app import config
from app.core import clock, settings
from app.core.quantity import format_qty
from app.printing import invoice_pdf, receipt
from app.repo import payments as payment_repo, sales as sale_repo
from app.services import checkout, returns
from app.ui import theme
from app.ui.dialogs.base import Dialog
from app.ui.widgets.common import (Badge, QuantityEdit, align_headers, clear_layout,
                                   hbox, label, table, vbox)


class SaleDetail(Dialog):
    def __init__(self, parent, sale_id: int, user_id: int | None = None,
                 is_admin: bool = False):
        sale = sale_repo.get(sale_id)
        super().__init__(parent, sale["invoice_no"],
                         f"{clock.pretty(sale['created_at'])}  ·  "
                         f"{sale['customer_name']}"
                         + (f"  ·  served by {sale['cashier']}" if sale["cashier"] else ""),
                         640)
        self.sale_id = sale_id
        self.user_id = user_id
        self.is_admin = is_admin
        self.changed = False

        self._status = Badge("", "")
        status_row = hbox(spacing=8)
        status_row.addWidget(self._status)
        status_row.addStretch(1)
        self.body.addLayout(status_row)

        self._items = table(["Item", "Qty", "Unit price", "Returned", "Amount"], 0, 34)
        self._items.setMinimumHeight(200)
        self.body.addWidget(self._items)

        self._totals = vbox(spacing=3)
        self.body.addLayout(self._totals)

        self.add_button("Print receipt", "ghost", self._print)
        self.add_button("Save PDF", "ghost", self._pdf)
        self._return_button = self.add_button("Return items", "", self._return)
        if is_admin:
            self._void_button = self.add_button("Void sale", "danger", self._void)
        self.add_cancel("Close")
        self._reload()

    def _reload(self) -> None:
        sale = sale_repo.get(self.sale_id)
        voided = sale["status"] == "void"
        self._status.setText("VOIDED" if voided else "Completed")
        self._status.set_tone("danger" if voided else "success")

        items = sale_repo.items(self.sale_id)
        self._items.setRowCount(len(items))
        for index, item in enumerate(items):
            returned = int(item["returned_qty"])
            cells = [
                (item["name"], None),
                (format_qty(int(item["qty"]), item["unit"]),
                 Qt.AlignRight | Qt.AlignVCenter),
                (settings.money(int(item["unit_price"])),
                 Qt.AlignRight | Qt.AlignVCenter),
                (format_qty(returned, item["unit"]) if returned else "—",
                 Qt.AlignRight | Qt.AlignVCenter),
                (settings.money(int(item["total"])), Qt.AlignRight | Qt.AlignVCenter),
            ]
            for column, (text, alignment) in enumerate(cells):
                cell = QTableWidgetItem(text)
                if alignment:
                    cell.setTextAlignment(alignment)
                if column == 3 and returned:
                    cell.setForeground(theme.color("warning"))
                self._items.setItem(index, column, cell)
        align_headers(self._items)

        clear_layout(self._totals)

        rows = [("Subtotal", settings.money(int(sale["subtotal"])), False)]
        if sale["discount"]:
            rows.append(("Discount", f"-{settings.money(int(sale['discount']))}", False))
        if sale["tax"]:
            rows.append((settings.tax_label(), settings.money(int(sale["tax"])), False))
        rows.append(("Total", settings.money(int(sale["total"])), True))
        for payment in sale_repo.payments(self.sale_id):
            rows.append((f"Paid — {payment_repo.label(payment['method'])}",
                         settings.money(int(payment["amount"])), False))
        if int(sale["due"]):
            rows.append(("Balance on account", settings.money(int(sale["due"])), False))
        if int(sale["returned_total"]):
            rows.append(("Returned", f"-{settings.money(int(sale['returned_total']))}",
                         False))
        for caption, value, strong in rows:
            line = hbox(spacing=8)
            line.addWidget(label(caption, "GrandTotalLabel" if strong else "TotalRowLabel"))
            line.addStretch(1)
            line.addWidget(label(value, "GrandTotalValue" if strong else "TotalRowValue"))
            self._totals.addLayout(line)

        can_return = bool(returns.returnable_lines(self.sale_id)) and not voided
        self._return_button.setEnabled(can_return)
        if self.is_admin:
            self._void_button.setEnabled(not voided)

    def _print(self) -> None:
        try:
            receipt.print_receipt(self, self.sale_id, copy_label="REPRINT")
        except Exception as error:
            self.show_error(f"Could not print: {error}")

    def _pdf(self) -> None:
        sale = sale_repo.get(self.sale_id)
        path, _ = QFileDialog.getSaveFileName(
            self, "Save invoice",
            f"{config.documents_dir()}/{invoice_pdf.default_filename(sale)}",
            "PDF files (*.pdf)")
        if not path:
            return
        try:
            invoice_pdf.build(self.sale_id, path)
            self.clear_error()
        except Exception as error:
            self.show_error(f"Could not save the invoice: {error}")

    def _return(self) -> None:
        dialog = ReturnDialog(self, self.sale_id, self.user_id)
        if dialog.exec():
            self.changed = True
            self._reload()

    def _void(self) -> None:
        dialog = VoidDialog(self, self.sale_id, self.user_id)
        if dialog.exec():
            self.changed = True
            self._reload()


class ReturnDialog(Dialog):
    """Take items back from a sale."""

    def __init__(self, parent, sale_id: int, user_id: int | None = None):
        sale = sale_repo.get(sale_id)
        super().__init__(parent, "Return items",
                         f"From {sale['invoice_no']}. Enter how much of each line "
                         f"is coming back.", 600)
        self.sale_id = sale_id
        self.user_id = user_id
        self.lines = returns.returnable_lines(sale_id)
        self._editors: list[tuple] = []

        self._table = table(["Item", "Sold", "Returning", "Refund", "Back to shelf"],
                            0, 44)
        self._table.setRowCount(len(self.lines))
        for index, line in enumerate(self.lines):
            self._table.setItem(index, 0, QTableWidgetItem(line.name))
            sold = QTableWidgetItem(format_qty(line.max_qty, line.unit))
            sold.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._table.setItem(index, 1, sold)

            qty_editor = QuantityEdit()
            qty_editor.setText("")
            qty_editor.setPlaceholderText("0")
            qty_editor.textChanged.connect(self._recalculate)
            self._table.setCellWidget(index, 2, qty_editor)

            amount = QTableWidgetItem(settings.money(0))
            amount.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._table.setItem(index, 3, amount)

            restock = QCheckBox()
            restock.setChecked(True)
            restock.setEnabled(line.product_id is not None)
            self._table.setCellWidget(index, 4, restock)
            self._editors.append((qty_editor, restock))

        self.body.addWidget(self._table)

        self._method = QComboBox()
        self._method.addItem("Refund in cash", "cash")
        if sale["customer_id"]:
            self._method.addItem("Credit to their account", "due")
        self._reason = QLineEdit()
        self._reason.setPlaceholderText("Why is it coming back?")
        self.body.addWidget(self.row(self.field("Refund as", self._method),
                                     self.field("Reason", self._reason)))

        self._summary = label("", "GrandTotalLabel")
        self.body.addWidget(self._summary)

        self.add_cancel()
        self._confirm = self.add_button("Record return", "primary", self._save,
                                        default=True)
        self._recalculate()

    def _collect(self) -> list:
        chosen = []
        for line, (qty_editor, restock) in zip(self.lines, self._editors):
            text = qty_editor.text().strip()
            if not text:
                line.qty = 0
                continue
            qty = qty_editor.value_or_none()
            line.qty = min(qty or 0, line.max_qty)
            line.restock = restock.isChecked()
            if line.qty > 0:
                chosen.append(line)
        return chosen

    def _recalculate(self) -> None:
        chosen = self._collect()
        for index, line in enumerate(self.lines):
            self._table.item(index, 3).setText(settings.money(line.total))
        total = sum(line.total for line in chosen)
        self._summary.setText(f"Refund total: {settings.money(total)}")
        self._confirm.setEnabled(bool(chosen))

    def _save(self) -> None:
        chosen = self._collect()
        try:
            _number, total = returns.commit(
                self.sale_id, chosen, method=self._method.currentData(),
                reason=self._reason.text(), user_id=self.user_id)
        except returns.ReturnError as error:
            self.show_error(str(error))
            return
        self.refunded = total
        self.accept()


class VoidDialog(Dialog):
    """Cancel a sale outright."""

    def __init__(self, parent, sale_id: int, user_id: int | None = None):
        sale = sale_repo.get(sale_id)
        super().__init__(parent, "Void this sale?",
                         f"{sale['invoice_no']} for {settings.money(int(sale['total']))} "
                         f"will be cancelled and its stock returned to the shelf. "
                         f"The record stays, marked as voided.", 460)
        self.sale_id = sale_id
        self.user_id = user_id

        self._reason = QLineEdit()
        self._reason.setPlaceholderText("Rung up twice, wrong customer, …")
        self.body.addWidget(self.field("Reason", self._reason))

        self.add_cancel()
        self.add_button("Void sale", "danger", self._save, default=True)
        self._reason.setFocus()

    def _save(self) -> None:
        try:
            checkout.void_sale(self.sale_id, self._reason.text(), self.user_id)
        except checkout.CheckoutError as error:
            self.show_error(str(error))
            return
        self.accept()
