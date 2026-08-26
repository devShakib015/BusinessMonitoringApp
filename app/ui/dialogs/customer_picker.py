"""Choosing (or quickly creating) the customer a sale belongs to."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit, QListWidget, QListWidgetItem

from app.core import settings
from app.repo import customers as customer_repo
from app.ui import theme
from app.ui.dialogs.base import Dialog
from app.ui.widgets.common import MoneyEdit, SearchField


class CustomerPicker(Dialog):
    """Returns the chosen customer row, or ``None`` for a walk-in sale."""

    def __init__(self, parent, allow_walk_in: bool = True, with_due_only: bool = False):
        super().__init__(parent, "Choose customer",
                         "Search by name, phone or code. Leave it as a walk-in "
                         "if the customer does not need an account.", 520)
        self.selected = None
        self._with_due_only = with_due_only

        self._search = SearchField("Search name, phone or code…")
        self._search.textChanged.connect(self._reload)
        self._search.installEventFilter(self)
        self.body.addWidget(self._search)

        self._list = QListWidget()
        self._list.setMinimumHeight(260)
        self._list.itemActivated.connect(lambda _: self._choose())
        self._list.setStyleSheet(
            f"QListWidget {{ background: {theme.hex_of('surface')};"
            f" border: 1px solid {theme.hex_of('border')}; border-radius: 10px; }}"
            f"QListWidget::item {{ padding: 9px 12px;"
            f" border-bottom: 1px solid {theme.hex_of('border')}; }}"
            f"QListWidget::item:selected {{ background: {theme.hex_of('selection')};"
            f" color: {theme.hex_of('text')}; }}")
        self.body.addWidget(self._list)

        if allow_walk_in:
            self.add_button("Walk-in", "ghost", self._walk_in)
        self.add_button("New customer", on_click=self._create)
        self.add_cancel()
        self.add_button("Select", "primary", self._choose, default=True)

        self._reload()
        self._search.setFocus()

    def _reload(self) -> None:
        self._list.clear()
        rows = customer_repo.list_all(search=self._search.text(), active_only=True,
                                      with_due_only=self._with_due_only, limit=80)
        for row in rows:
            balance = int(row["balance"])
            detail = f"{row['code']} · {row['phone'] or 'no phone'}"
            if balance > 0:
                detail += f"  ·  owes {settings.money(balance)}"
            item = QListWidgetItem(f"{row['name']}\n{detail}")
            item.setData(Qt.UserRole, row["id"])
            self._list.addItem(item)
        if self._list.count():
            self._list.setCurrentRow(0)

    def eventFilter(self, source, event):  # noqa: N802 - Qt naming
        if source is self._search and event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key_Down, Qt.Key_Up):
                self._list.setFocus()
                return True
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self._choose()
                return True
        return super().eventFilter(source, event)

    def _choose(self) -> None:
        item = self._list.currentItem()
        if item is None:
            self.show_error("No customer matches that search.")
            return
        self.selected = customer_repo.get(item.data(Qt.UserRole))
        self.accept()

    def _walk_in(self) -> None:
        self.selected = None
        self.accept()

    def _create(self) -> None:
        editor = CustomerEditor(self, prefill=self._search.text())
        if editor.exec() and editor.customer_id:
            self.selected = customer_repo.get(editor.customer_id)
            self.accept()


class CustomerEditor(Dialog):
    """Add or edit a customer."""

    def __init__(self, parent, customer=None, prefill: str = ""):
        editing = customer is not None
        super().__init__(parent, "Edit customer" if editing else "New customer",
                         "Only a name is required." if not editing else "", 480)
        self.customer = customer
        self.customer_id = customer["id"] if editing else None

        self._name = QLineEdit(customer["name"] if editing else prefill.strip())
        self._name.setPlaceholderText("Full name or shop name")
        self._code = QLineEdit(customer["code"] if editing
                               else customer_repo.suggest_code())
        self._phone = QLineEdit(customer["phone"] if editing else "")
        self._phone.setPlaceholderText("Optional")
        self._address = QLineEdit(customer["address"] if editing else "")
        self._address.setPlaceholderText("Optional")
        self._limit = MoneyEdit()
        self._limit.set_value(int(customer["credit_limit"]) if editing else 0)

        self.body.addWidget(self.field("Name", self._name))
        self.body.addWidget(self.row(
            self.field("Customer code", self._code),
            self.field("Phone", self._phone)))
        self.body.addWidget(self.field("Address", self._address))
        self.body.addWidget(self.field(
            f"Credit limit ({settings.symbol()})", self._limit,
            "How much they may owe at once. 0 means no limit."))

        self.add_cancel()
        self.add_button("Save customer", "primary", self._save, default=True)
        self._name.setFocus()

    def _save(self) -> None:
        name = self._name.text().strip()
        if not name:
            self.show_error("Enter the customer's name.")
            return
        code = self._code.text().strip() or customer_repo.suggest_code()
        if customer_repo.code_taken(code, self.customer_id):
            self.show_error(f"Customer code {code} is already used.")
            return
        limit = self._limit.value_or_none()
        if limit is None:
            self.show_error("Credit limit must be a number.")
            return

        fields = dict(name=name, code=code, phone=self._phone.text(),
                      address=self._address.text(), credit_limit=limit)
        if self.customer_id:
            customer_repo.update(self.customer_id, **fields)
        else:
            self.customer_id = customer_repo.create(**fields)
        self.accept()
