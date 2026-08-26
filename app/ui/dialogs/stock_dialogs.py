"""Receiving stock and correcting stock counts."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QCompleter, QLineEdit

from app.core import settings
from app.core.quantity import format_qty
from app.repo import products as product_repo, stock as stock_repo
from app.ui.dialogs.base import Dialog
from app.ui.widgets.common import MoneyEdit, QuantityEdit, label


class _ProductPicker(QComboBox):
    """Type-ahead list of active products."""

    def __init__(self, parent=None, product_id: int | None = None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.completer().setFilterMode(Qt.MatchContains)
        for row in product_repo.list_all(active_only=True):
            suffix = f"  ·  {format_qty(int(row['stock']), row['unit'])}"
            self.addItem(f"{row['name']}{suffix}", row["id"])
        if product_id is not None:
            index = self.findData(product_id)
            if index >= 0:
                self.setCurrentIndex(index)

    def product_id(self) -> int | None:
        index = self.findText(self.currentText())
        if index >= 0:
            return self.itemData(index)
        return self.currentData()


class ReceiveStockDialog(Dialog):
    """Book in a delivery."""

    def __init__(self, parent, product_id: int | None = None):
        super().__init__(parent, "Receive stock",
                         "Booking in a delivery updates the shelf count and the "
                         "product's cost price.", 460)
        self._product = _ProductPicker(self, product_id)
        self._product.currentIndexChanged.connect(self._show_current)
        self._qty = QuantityEdit()
        self._cost = MoneyEdit()
        self._note = QLineEdit()
        self._note.setPlaceholderText("Supplier, invoice number, anything useful")
        self._current = label("", "Faint")

        self.body.addWidget(self.field("Product", self._product))
        self.body.addWidget(self._current)
        self.body.addWidget(self.row(
            self.field("Quantity received", self._qty),
            self.field(f"Cost per unit ({settings.symbol()})", self._cost)))
        self.body.addWidget(self.field("Note", self._note))

        self.add_cancel()
        self.add_button("Add to stock", "primary", self._save, default=True)
        self._show_current()
        self._qty.setFocus()

    def _show_current(self) -> None:
        product_id = self._product.product_id()
        product = product_repo.get(product_id) if product_id else None
        if product is None:
            self._current.setText("")
            return
        self._current.setText(
            f"In stock now: {format_qty(int(product['stock']), product['unit'])}   ·   "
            f"last cost {settings.money(int(product['cost_price']))}")
        if not self._cost.text().strip():
            self._cost.set_value(int(product["cost_price"]))

    def _save(self) -> None:
        product_id = self._product.product_id()
        qty = self._qty.value_or_none()
        cost = self._cost.value_or_none()
        if not product_id:
            self.show_error("Choose a product.")
            return
        if not qty or qty <= 0:
            self.show_error("Enter how many came in.")
            return
        if cost is None or cost < 0:
            self.show_error("Enter the cost per unit.")
            return

        session = getattr(self.parent(), "session", None)
        stock_repo.receive(product_id, qty, cost, note=self._note.text(),
                           user_id=session.user_id if session else None)
        self.accept()


class AdjustStockDialog(Dialog):
    """Correct the count after a physical stocktake, or write off damage."""

    def __init__(self, parent, product_id: int | None = None):
        super().__init__(parent, "Stock count",
                         "Enter what is actually on the shelf. The difference is "
                         "recorded so the change can be explained later.", 460)
        self._product = _ProductPicker(self, product_id)
        self._product.currentIndexChanged.connect(self._show_current)
        self._counted = QuantityEdit()
        self._reason = QComboBox()
        self._reason.addItem("Stock count correction", "adjustment")
        self._reason.addItem("Damaged or lost", "damage")
        self._note = QLineEdit()
        self._note.setPlaceholderText("What happened?")
        self._current = label("", "Faint")

        self.body.addWidget(self.field("Product", self._product))
        self.body.addWidget(self._current)
        self.body.addWidget(self.row(
            self.field("Counted quantity", self._counted),
            self.field("Reason", self._reason)))
        self.body.addWidget(self.field("Note", self._note))

        self.add_cancel()
        self.add_button("Save count", "primary", self._save, default=True)
        self._show_current()
        self._counted.setFocus()

    def _show_current(self) -> None:
        product_id = self._product.product_id()
        product = product_repo.get(product_id) if product_id else None
        if product is None:
            self._current.setText("")
            return
        self._current.setText(
            f"System says: {format_qty(int(product['stock']), product['unit'])}")
        self._counted.set_value(int(product["stock"]))

    def _save(self) -> None:
        product_id = self._product.product_id()
        counted = self._counted.value_or_none()
        if not product_id:
            self.show_error("Choose a product.")
            return
        if counted is None or counted < 0:
            self.show_error("Enter the counted quantity.")
            return

        session = getattr(self.parent(), "session", None)
        product = product_repo.get(product_id)
        difference = counted - int(product["stock"])
        if difference == 0:
            self.show_error("That matches the system count — nothing to change.")
            return

        reason = self._reason.currentData()
        note = self._note.text() or (
            "Counted correction" if reason == "adjustment" else "Written off")
        stock_repo.add_movement(product_id, difference, reason, note=note,
                                user_id=session.user_id if session else None)
        self.accept()
