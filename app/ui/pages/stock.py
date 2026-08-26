"""Stock levels and the movement ledger."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTabWidget, QTableWidgetItem

from app.core import clock, settings
from app.core.quantity import format_qty
from app.export import excel
from app.repo import products as product_repo, stock as stock_repo
from app.ui import theme
from app.ui.dialogs.stock_dialogs import AdjustStockDialog, ReceiveStockDialog
from app.ui.pages.base import Page
from app.ui.widgets.common import (Card, PageHeader, SearchField, StatCard,
                                   align_headers, button, hbox, table)


class StockPage(Page):
    def build(self) -> None:
        header = PageHeader("Stock", "What is on the shelf, and how it got there.")
        header.add_action(button("Export", "ghost", "download", self._export))
        header.add_action(button("Stock count", "", "edit", self._adjust))
        header.add_action(button("Receive stock", "primary", "plus", self._receive,
                                 "Ctrl+N"))
        self.layout.addWidget(header)

        stats = hbox(spacing=14)
        self.stat_value = StatCard("Stock value at cost", icon_name="stock")
        self.stat_retail = StatCard("Retail value", icon_name="tag")
        self.stat_low = StatCard("Need reordering", icon_name="alert",
                                 accent=theme.hex_of("warning"))
        self.stat_out = StatCard("Out of stock", icon_name="close",
                                 accent=theme.hex_of("danger"))
        for card in (self.stat_value, self.stat_retail, self.stat_low, self.stat_out):
            stats.addWidget(card)
        self.layout.addLayout(stats)

        self.search = SearchField("Search products…")
        self.search.textChanged.connect(self.refresh)
        self.layout.addWidget(self.search)

        tabs = QTabWidget()
        self.levels = table(
            ["Product", "Category", "In stock", "Reorder at", "Cost value",
             "Retail value", "Status"], 0, 40)
        self.levels.itemDoubleClicked.connect(lambda _: self._receive_selected())
        tabs.addTab(self._wrap(self.levels), "Stock levels")

        self.movements = table(
            ["When", "Product", "Change", "Reason", "Note", "By"], 1, 38)
        tabs.addTab(self._wrap(self.movements), "Movements")
        self.layout.addWidget(tabs, 1)

    def _wrap(self, widget):
        card = Card(padding=0, spacing=0)
        card.body.addWidget(widget)
        return card

    # ── Data ──────────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        self._render_stats()
        self._render_levels()
        self._render_movements()

    def _render_stats(self) -> None:
        retail, cost = stock_repo.stock_value()
        low = product_repo.low_stock()
        out = [row for row in product_repo.list_all(active_only=True)
               if row["track_stock"] and int(row["stock"]) <= 0]

        self.stat_value.set_value(settings.money(cost), "What it cost you")
        self.stat_retail.set_value(settings.money(retail),
                                   f"{settings.money(retail - cost)} of margin")
        self.stat_low.set_value(str(len(low)),
                                "at or below their reorder level")
        self.stat_out.set_value(str(len(out)), "cannot be sold right now")

    def _render_levels(self) -> None:
        rows = [row for row in product_repo.list_all(search=self.search.text(),
                                                     active_only=True)
                if row["track_stock"]]
        self.levels.setRowCount(len(rows))
        for index, row in enumerate(rows):
            stock = int(row["stock"])
            low = int(row["low_stock_level"])
            status = ("Out of stock" if stock <= 0 else
                      "Reorder" if stock <= low else "Healthy")
            cells = [
                (row["name"], None),
                (row["category_name"] or "—", None),
                (format_qty(stock, row["unit"]), Qt.AlignRight | Qt.AlignVCenter),
                (format_qty(low, row["unit"]), Qt.AlignRight | Qt.AlignVCenter),
                (settings.money(stock * int(row["cost_price"]) // 1000),
                 Qt.AlignRight | Qt.AlignVCenter),
                (settings.money(stock * int(row["sell_price"]) // 1000),
                 Qt.AlignRight | Qt.AlignVCenter),
                (status, Qt.AlignCenter),
            ]
            for column, (text, alignment) in enumerate(cells):
                cell = QTableWidgetItem(text)
                if alignment:
                    cell.setTextAlignment(alignment)
                if column == 0:
                    cell.setData(Qt.UserRole, row["id"])
                if column in (1, 3):
                    cell.setForeground(theme.color("text_muted"))
                if column == 6:
                    cell.setForeground(theme.color(
                        {"Out of stock": "danger", "Reorder": "warning"}
                        .get(status, "success")))
                self.levels.setItem(index, column, cell)
        align_headers(self.levels)

    def _render_movements(self) -> None:
        rows = stock_repo.recent(300)
        term = self.search.text().strip().lower()
        if term:
            rows = [row for row in rows if term in row["product_name"].lower()]
        self.movements.setRowCount(len(rows))
        for index, row in enumerate(rows):
            change = int(row["qty"])
            cells = [
                (clock.pretty(row["created_at"]), None),
                (row["product_name"], None),
                (f"{'+' if change > 0 else ''}{format_qty(change, row['unit'])}",
                 Qt.AlignRight | Qt.AlignVCenter),
                (stock_repo.REASON_LABELS.get(row["reason"], row["reason"]), None),
                (row["note"] or "—", None),
                (row["who"] or "—", None),
            ]
            for column, (text, alignment) in enumerate(cells):
                cell = QTableWidgetItem(text)
                if alignment:
                    cell.setTextAlignment(alignment)
                if column == 2:
                    cell.setForeground(theme.color("success" if change > 0 else "danger"))
                if column in (0, 4, 5):
                    cell.setForeground(theme.color("text_muted"))
                self.movements.setItem(index, column, cell)
        align_headers(self.movements)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _selected_product(self) -> int | None:
        rows = self.levels.selectionModel().selectedRows()
        if not rows:
            return None
        item = self.levels.item(rows[0].row(), 0)
        return item.data(Qt.UserRole) if item else None

    def _receive(self) -> None:
        self._open(ReceiveStockDialog(self), "Stock received.")

    def _receive_selected(self) -> None:
        self._open(ReceiveStockDialog(self, self._selected_product()),
                   "Stock received.")

    def _adjust(self) -> None:
        self._open(AdjustStockDialog(self, self._selected_product()),
                   "Stock count saved.")

    def _open(self, dialog, message: str) -> None:
        if dialog.exec():
            self.refresh()
            self.window.refresh_page("products")
            self.notify(message, "success")

    def _export(self) -> None:
        rows = [row for row in product_repo.list_all(active_only=True)
                if row["track_stock"]]
        if not rows:
            self.notify("There is nothing to export.", "warning")
            return
        data = [["Product", "Category", "Unit", "In stock", "Reorder at",
                 "Cost value", "Retail value"]]
        for row in rows:
            stock = int(row["stock"])
            data.append([
                row["name"], row["category_name"] or "", row["unit"],
                float(format_qty(stock)), float(format_qty(int(row["low_stock_level"]))),
                stock * int(row["cost_price"]) / 1000 / (10 ** settings.decimals()),
                stock * int(row["sell_price"]) / 1000 / (10 ** settings.decimals()),
            ])
        if excel.save_as(self, data, "stock"):
            self.notify(f"Exported {len(rows)} products.", "success")
