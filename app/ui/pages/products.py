"""The catalogue."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QTableWidgetItem

from app.core import settings
from app.core.money import format_plain
from app.core.quantity import format_qty
from app.export import excel
from app.repo import products as product_repo
from app.ui import theme
from app.ui.dialogs.product_editor import ProductEditor
from app.ui.pages.base import Page
from app.ui.widgets.common import (Card, EmptyState, PageHeader, SearchField,
                                   align_headers, button, hbox, label, table)

HEADERS = ["Product", "Barcode", "Category", "Cost", "Price", "Margin", "Stock",
           "Status"]


class ProductsPage(Page):
    def build(self) -> None:
        header = PageHeader("Products", "Everything the shop sells.")
        header.add_action(button("Export", "ghost", "download", self._export))
        header.add_action(button("Add product", "primary", "plus", self._add,
                                 "Ctrl+N"))
        self.layout.addWidget(header)

        filters = hbox(spacing=10)
        self.search = SearchField("Search name, SKU or barcode…")
        self.search.textChanged.connect(self.refresh)
        filters.addWidget(self.search, 1)

        self.category = QComboBox()
        self.category.setFixedWidth(180)
        self.category.currentIndexChanged.connect(self.refresh)
        filters.addWidget(self.category)

        self.view = QComboBox()
        self.view.addItems(["All products", "Low stock", "Out of stock", "Retired"])
        self.view.setFixedWidth(160)
        self.view.currentIndexChanged.connect(self.refresh)
        filters.addWidget(self.view)
        self.layout.addLayout(filters)

        card = Card(padding=0, spacing=0)
        self.table = table(HEADERS, 0, 42)
        self.table.itemDoubleClicked.connect(lambda _: self._edit())
        card.body.addWidget(self.table)
        self.empty = EmptyState("products", "No products yet",
                                "Add your first product to start selling.")
        card.body.addWidget(self.empty)
        self.layout.addWidget(card, 1)

        self.summary = label("", "Faint")
        self.layout.addWidget(self.summary)

    # ── Data ──────────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        self._reload_categories()
        rows = self._rows()
        self.table.setVisible(bool(rows))
        self.empty.setVisible(not rows)
        self.table.setRowCount(len(rows))

        decimals = settings.decimals()
        for index, row in enumerate(rows):
            stock = int(row["stock"])
            cost, price = int(row["cost_price"]), int(row["sell_price"])
            margin = f"{(price - cost) * 100 / price:.0f}%" if price else "—"

            cells = [
                (row["name"], None),
                (row["barcode"] or "—", None),
                (row["category_name"] or "—", None),
                (format_plain(cost, decimals), Qt.AlignRight | Qt.AlignVCenter),
                (format_plain(price, decimals), Qt.AlignRight | Qt.AlignVCenter),
                (margin, Qt.AlignRight | Qt.AlignVCenter),
                (format_qty(stock, row["unit"]) if row["track_stock"] else "—",
                 Qt.AlignRight | Qt.AlignVCenter),
                (self._status_text(row), Qt.AlignCenter),
            ]
            for column, (text, alignment) in enumerate(cells):
                cell = QTableWidgetItem(text)
                if alignment:
                    cell.setTextAlignment(alignment)
                if column == 0:
                    cell.setData(Qt.UserRole, row["id"])
                    font = cell.font()
                    font.setBold(True)
                    cell.setFont(font)
                if column in (1, 2, 5):
                    cell.setForeground(theme.color("text_muted"))
                if column == 6 and row["track_stock"]:
                    if stock <= 0:
                        cell.setForeground(theme.color("danger"))
                    elif stock <= int(row["low_stock_level"]):
                        cell.setForeground(theme.color("warning"))
                if column == 7:
                    cell.setForeground(self._status_color(row))
                self.table.setItem(index, column, cell)

        align_headers(self.table)
        low = len(product_repo.low_stock())
        self.summary.setText(
            f"{len(rows)} shown · {product_repo.count_active()} active · "
            f"{low} at or below their low-stock level")

    def _rows(self):
        mode = self.view.currentText()
        category_id = self.category.currentData()
        rows = product_repo.list_all(
            search=self.search.text(), category_id=category_id,
            active_only=mode in ("Low stock", "Out of stock"),
            low_stock_only=mode == "Low stock")
        if mode == "Out of stock":
            rows = [row for row in rows if row["track_stock"] and int(row["stock"]) <= 0]
        elif mode == "Retired":
            rows = [row for row in rows if not row["is_active"]]
        elif mode == "All products":
            pass
        return rows

    def _reload_categories(self) -> None:
        current = self.category.currentData()
        self.category.blockSignals(True)
        self.category.clear()
        self.category.addItem("All categories", None)
        for row in product_repo.categories():
            self.category.addItem(f"{row['name']}  ({row['product_count']})", row["id"])
        index = self.category.findData(current)
        self.category.setCurrentIndex(max(0, index))
        self.category.blockSignals(False)

    def _status_text(self, row) -> str:
        if not row["is_active"]:
            return "Retired"
        if not row["track_stock"]:
            return "Available"
        stock = int(row["stock"])
        if stock <= 0:
            return "Out of stock"
        if stock <= int(row["low_stock_level"]):
            return "Low"
        return "In stock"

    def _status_color(self, row):
        text = self._status_text(row)
        return theme.color({"Out of stock": "danger", "Low": "warning",
                            "Retired": "text_faint"}.get(text, "success"))

    # ── Actions ───────────────────────────────────────────────────────────────

    def _selected_id(self) -> int | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        item = self.table.item(rows[0].row(), 0)
        return item.data(Qt.UserRole) if item else None

    def _add(self) -> None:
        dialog = ProductEditor(self)
        if dialog.exec():
            self.refresh()
            self.window.refresh_page("stock")
            self.notify("Product added.", "success")

    def _edit(self) -> None:
        product_id = self._selected_id()
        if product_id is None:
            return
        dialog = ProductEditor(self, product_repo.get(product_id))
        if dialog.exec():
            self.refresh()
            self.window.refresh_page("stock")
            self.notify("Product deleted." if dialog.deleted else "Product updated.",
                        "success")

    def _export(self) -> None:
        rows = self._rows()
        if not rows:
            self.notify("There is nothing to export.", "warning")
            return
        decimals = settings.decimals()
        data = [HEADERS[:-1] + ["Unit", "Low stock level", "Active"]]
        for row in rows:
            data.append([
                row["name"], row["barcode"] or "", row["category_name"] or "",
                float(format_plain(int(row["cost_price"]), decimals, grouping=False)),
                float(format_plain(int(row["sell_price"]), decimals, grouping=False)),
                "", format_qty(int(row["stock"])), row["unit"],
                format_qty(int(row["low_stock_level"])),
                "yes" if row["is_active"] else "no",
            ])
        path = excel.save_as(self, data, "products")
        if path:
            self.notify(f"Exported {len(rows)} products.", "success")
