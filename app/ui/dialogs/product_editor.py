"""Adding and editing catalogue products."""

from PySide6.QtWidgets import QCheckBox, QComboBox, QLineEdit, QPlainTextEdit

from app.core import settings
from app.core.quantity import format_qty
from app.repo import products as product_repo, stock as stock_repo
from app.ui.dialogs.base import Dialog
from app.ui.widgets.common import MoneyEdit, QuantityEdit

UNITS = ["pc", "kg", "g", "litre", "ml", "pack", "box", "bag", "btl", "can",
         "pair", "metre", "dozen"]


class ProductEditor(Dialog):
    def __init__(self, parent, product=None):
        editing = product is not None
        super().__init__(parent, "Edit product" if editing else "New product",
                         "" if editing else "Only a name and a selling price are "
                                            "required to start selling.", 560)
        self.product = product
        self.product_id = product["id"] if editing else None

        self._name = QLineEdit(product["name"] if editing else "")
        self._name.setPlaceholderText("What the customer asks for")
        self._sku = QLineEdit(product["sku"] if editing else "")
        self._sku.setPlaceholderText("Optional")
        self._barcode = QLineEdit(product["barcode"] if editing else "")
        self._barcode.setPlaceholderText("Scan into this box")

        self._category = QComboBox()
        self._category.setEditable(True)
        self._category.addItem("")
        for row in product_repo.categories():
            self._category.addItem(row["name"])
        if editing and product["category_name"]:
            self._category.setCurrentText(product["category_name"])

        self._unit = QComboBox()
        self._unit.setEditable(True)
        self._unit.addItems(UNITS)
        self._unit.setCurrentText(product["unit"] if editing else "pc")

        self._cost = MoneyEdit()
        self._sell = MoneyEdit()
        self._tax = QLineEdit(str(product["tax_rate"] if editing
                                  else settings.default_tax_rate()))
        if editing:
            self._cost.set_value(int(product["cost_price"]))
            self._sell.set_value(int(product["sell_price"]))

        self._track = QCheckBox("Track stock for this product")
        self._track.setChecked(bool(product["track_stock"]) if editing else True)
        self._low = QuantityEdit()
        self._low.set_value(int(product["low_stock_level"]) if editing else 0)

        self._opening = QuantityEdit()
        self._opening.setPlaceholderText("0")
        self._active = QCheckBox("Available to sell")
        self._active.setChecked(bool(product["is_active"]) if editing else True)
        self._note = QPlainTextEdit(product["note"] if editing else "")
        self._note.setPlaceholderText("Optional note — supplier, shelf, anything")
        self._note.setFixedHeight(56)

        self.body.addWidget(self.field("Product name", self._name))
        self.body.addWidget(self.row(
            self.field("Barcode", self._barcode),
            self.field("SKU / item code", self._sku)))
        self.body.addWidget(self.row(
            self.field("Category", self._category),
            self.field("Sold by", self._unit)))
        self.body.addWidget(self.row(
            self.field(f"Cost price ({settings.symbol()})", self._cost,
                       "What you pay"),
            self.field(f"Selling price ({settings.symbol()})", self._sell,
                       "What the customer pays")))
        if settings.tax_enabled():
            self.body.addWidget(self.field(
                f"{settings.tax_label()} rate (%)", self._tax))
        self.body.addWidget(self._track)
        self.body.addWidget(self.row(
            self.field("Warn when stock reaches", self._low),
            self.field("Opening stock" if not editing else "Current stock",
                       self._opening if not editing else self._stock_display(product))))
        self.body.addWidget(self._active)
        self.body.addWidget(self.field("Note", self._note))

        if editing:
            self.add_button("Delete", "danger", self._delete)
        self.add_cancel()
        self.add_button("Save product", "primary", self._save, default=True)
        self._name.setFocus()
        self.deleted = False

    def _stock_display(self, product):
        field = QLineEdit(format_qty(int(product["stock"]), product["unit"]))
        field.setEnabled(False)
        field.setToolTip("Change stock from the Stock screen so the reason is recorded.")
        return field

    def _save(self) -> None:
        name = self._name.text().strip()
        if not name:
            self.show_error("Give the product a name.")
            return
        if product_repo.name_taken(name, self.product_id):
            self.show_error(f"There is already a product called “{name}”.")
            return
        for field, value in (("sku", self._sku.text()), ("barcode", self._barcode.text())):
            if product_repo.code_taken(field, value, self.product_id):
                self.show_error(f"That {field} is already used by another product.")
                return

        cost = self._cost.value_or_none()
        sell = self._sell.value_or_none()
        if cost is None or sell is None:
            self.show_error("Cost and selling price must both be numbers.")
            return
        if sell <= 0:
            self.show_error("Enter a selling price greater than zero.")
            return
        try:
            tax_rate = float(self._tax.text().strip() or 0)
        except ValueError:
            self.show_error("The tax rate must be a number, for example 15.")
            return
        low = self._low.value_or_none()
        if low is None:
            self.show_error("The low-stock level must be a number.")
            return

        fields = dict(
            name=name, sku=self._sku.text(), barcode=self._barcode.text(),
            category_id=product_repo.category_id_for(self._category.currentText()),
            unit=self._unit.currentText().strip() or "pc",
            cost_price=cost, sell_price=sell, tax_rate=tax_rate,
            track_stock=self._track.isChecked(), low_stock_level=low,
            is_active=self._active.isChecked(), note=self._note.toPlainText())

        if self.product_id:
            product_repo.update(self.product_id, **fields)
        else:
            self.product_id = product_repo.create(**fields)
            opening = self._opening.value_or_none() or 0
            if opening:
                stock_repo.add_movement(self.product_id, opening, "opening",
                                        unit_cost=cost, note="Opening stock")
        self.accept()

    def _delete(self) -> None:
        if product_repo.is_referenced(self.product_id):
            self.show_error(
                "This product appears on past sales, so deleting it would break "
                "that history. Untick “Available to sell” to retire it instead.")
            return
        parent = self.parent()
        if hasattr(parent, "window") and not parent.window.confirm(
                "Delete this product?", "This cannot be undone.", "Delete", True):
            return
        product_repo.delete(self.product_id)
        self.deleted = True
        self.accept()
