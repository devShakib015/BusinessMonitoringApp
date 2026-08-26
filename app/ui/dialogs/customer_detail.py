"""A customer's account: what they bought, what they paid, what they owe."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QLineEdit, QTableWidgetItem

from app.core import clock, settings
from app.repo import customers as customer_repo
from app.services import dues
from app.ui import theme
from app.ui.dialogs.base import Dialog
from app.ui.dialogs.customer_picker import CustomerEditor
from app.ui.widgets.common import (MoneyEdit, align_headers, button, hbox, label,
                                   table, vbox)


class TakePaymentDialog(Dialog):
    """Collect money against an outstanding balance."""

    def __init__(self, parent, customer, user_id: int | None = None):
        super().__init__(parent, "Take payment",
                         f"{customer['name']} owes "
                         f"{settings.money(int(customer['balance']))}.", 420)
        self.customer = customer
        self.user_id = user_id
        self.amount_paid = 0

        balance = int(customer["balance"])
        self._amount = MoneyEdit()
        self._amount.set_value(balance)
        self._method = QComboBox()
        for method in settings.get_list("pos.payment_methods"):
            if method != "due":
                self._method.addItem(method.title(), method)
        self._note = QLineEdit()
        self._note.setPlaceholderText("Optional")

        self.body.addWidget(self.row(
            self.field(f"Amount ({settings.symbol()})", self._amount),
            self.field("Method", self._method)))

        quick = hbox(spacing=6)
        for caption, value in (("Full amount", balance), ("Half", balance // 2)):
            chip = button(caption, "ghost")
            chip.clicked.connect(lambda _=False, v=value: self._amount.set_value(v))
            quick.addWidget(chip)
        quick.addStretch(1)
        self.body.addLayout(quick)
        self.body.addWidget(self.field("Note", self._note))

        self.add_cancel()
        self.add_button("Record payment", "primary", self._save, default=True)
        self._amount.setFocus()
        self._amount.selectAll()

    def _save(self) -> None:
        amount = self._amount.value_or_none()
        if amount is None:
            self.show_error("Enter the amount received.")
            return
        try:
            dues.collect(self.customer["id"], amount,
                         method=self._method.currentData(),
                         note=self._note.text(), user_id=self.user_id)
        except dues.DueError as error:
            self.show_error(str(error))
            return
        self.amount_paid = amount
        self.accept()


class CustomerDetail(Dialog):
    """Everything about one customer, with the actions that belong to them."""

    def __init__(self, parent, customer_id: int, user_id: int | None = None):
        customer = customer_repo.get(customer_id)
        super().__init__(parent, customer["name"],
                         f"{customer['code']}  ·  {customer['phone'] or 'no phone'}"
                         + (f"  ·  {customer['address']}" if customer["address"] else ""),
                         620)
        self.customer_id = customer_id
        self.user_id = user_id
        self.changed = False

        self._headline = vbox(spacing=2)
        self.body.addLayout(self._headline)
        self._balance = label("", "GrandTotalValue")
        self._headline.addWidget(label("OUTSTANDING BALANCE", "StatLabel"))
        self._headline.addWidget(self._balance)
        self._meta = label("", "Faint")
        self._headline.addWidget(self._meta)

        self._ledger = table(["Date", "Reference", "Detail", "Amount"], 2, 34)
        self._ledger.setMinimumHeight(260)
        self.body.addWidget(self._ledger)

        self.add_button("Edit details", "ghost", self._edit)
        self._pay_button = self.add_button("Take payment", "primary", self._pay)
        self.add_cancel("Close")
        self._reload()

    def _reload(self) -> None:
        customer = customer_repo.get(self.customer_id)
        balance = int(customer["balance"])
        self._balance.setText(settings.money(balance))
        self._balance.setStyleSheet(
            f"color: {theme.hex_of('danger' if balance > 0 else 'success')};")
        self._meta.setText(
            f"{customer['sale_count']} sale(s)  ·  last "
            f"{clock.pretty(customer['last_sale_at'], False) or 'never'}"
            + (f"  ·  credit limit {settings.money(int(customer['credit_limit']))}"
               if customer["credit_limit"] else "  ·  no credit limit"))
        self._pay_button.setEnabled(balance > 0)

        entries = customer_repo.ledger(self.customer_id)
        self._ledger.setRowCount(len(entries))
        for index, entry in enumerate(entries):
            amount = int(entry["amount"])
            cells = [
                (clock.pretty(entry["created_at"], False), None),
                (entry["reference"] or "—", None),
                (entry["detail"], None),
                (settings.money(amount), Qt.AlignRight | Qt.AlignVCenter),
            ]
            for column, (text, alignment) in enumerate(cells):
                cell = QTableWidgetItem(text)
                if alignment:
                    cell.setTextAlignment(alignment)
                if column == 3:
                    cell.setForeground(theme.color("danger" if amount > 0 else "success"))
                if column in (0, 1):
                    cell.setForeground(theme.color("text_muted"))
                self._ledger.setItem(index, column, cell)
        align_headers(self._ledger)

    def _pay(self) -> None:
        customer = customer_repo.get(self.customer_id)
        dialog = TakePaymentDialog(self, customer, self.user_id)
        if dialog.exec():
            self.changed = True
            self._reload()

    def _edit(self) -> None:
        customer = customer_repo.get(self.customer_id)
        if CustomerEditor(self, customer).exec():
            self.changed = True
            self.setWindowTitle(customer_repo.get(self.customer_id)["name"])
            self._reload()
