"""Past sales and returns."""

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import QComboBox, QDateEdit, QTabWidget, QTableWidgetItem

from app.core import clock, settings
from app.export import excel
from app.repo import sales as sale_repo
from app.ui import theme
from app.ui.dialogs.sale_detail import SaleDetail
from app.ui.pages.base import Page
from app.ui.widgets.common import (Card, EmptyState, PageHeader, SearchField,
                                   StatCard, align_headers, button, hbox, label, table)

RANGES = {
    "Today": 0, "Last 7 days": 6, "Last 30 days": 29, "Last 90 days": 89,
    "All time": None,
}


class SalesPage(Page):
    def build(self) -> None:
        header = PageHeader("Sales", "Every transaction, with its receipt.")
        header.add_action(button("Export", "ghost", "download", self._export))
        self.layout.addWidget(header)

        stats = hbox(spacing=14)
        self.stat_count = StatCard("Sales in view", icon_name="sales")
        self.stat_total = StatCard("Value", icon_name="cash")
        self.stat_average = StatCard("Average sale", icon_name="reports")
        self.stat_due = StatCard("Left on account", icon_name="dues",
                                 accent=theme.hex_of("warning"))
        for card in (self.stat_count, self.stat_total, self.stat_average, self.stat_due):
            stats.addWidget(card)
        self.layout.addLayout(stats)

        filters = hbox(spacing=10)
        self.search = SearchField("Search invoice number, customer or phone…")
        self.search.textChanged.connect(self.refresh)
        filters.addWidget(self.search, 1)

        self.range = QComboBox()
        self.range.addItems(list(RANGES))
        self.range.setCurrentText("Last 30 days")
        self.range.setFixedWidth(140)
        self.range.currentIndexChanged.connect(self._range_changed)
        filters.addWidget(self.range)

        self.start = QDateEdit(QDate.currentDate().addDays(-29))
        self.end = QDateEdit(QDate.currentDate())
        for field in (self.start, self.end):
            field.setCalendarPopup(True)
            field.setDisplayFormat("dd MMM yyyy")
            field.setFixedWidth(122)
            field.dateChanged.connect(self.refresh)
        filters.addWidget(label("from", "Faint"))
        filters.addWidget(self.start)
        filters.addWidget(label("to", "Faint"))
        filters.addWidget(self.end)
        self.layout.addLayout(filters)

        tabs = QTabWidget()
        self.table = table(["Invoice", "When", "Customer", "Items", "Total", "Paid",
                            "Due", "Status"], 2, 40)
        self.table.itemDoubleClicked.connect(lambda _: self._open())
        sales_card = Card(padding=0, spacing=0)
        sales_card.body.addWidget(self.table)
        self.empty = EmptyState("sales", "No sales in this period",
                                "Change the dates, or make a sale on the till.")
        sales_card.body.addWidget(self.empty)
        tabs.addTab(sales_card, "Sales")

        self.returns = table(["Return", "When", "Invoice", "Customer", "Items",
                              "Refund", "Method"], 3, 38)
        returns_card = Card(padding=0, spacing=0)
        returns_card.body.addWidget(self.returns)
        tabs.addTab(returns_card, "Returns")
        self.layout.addWidget(tabs, 1)

    # ── Data ──────────────────────────────────────────────────────────────────

    def _range_changed(self) -> None:
        days = RANGES[self.range.currentText()]
        today = QDate.currentDate()
        self.start.blockSignals(True)
        self.end.blockSignals(True)
        if days is None:
            self.start.setDate(QDate(2000, 1, 1))
        else:
            self.start.setDate(today.addDays(-days))
        self.end.setDate(today)
        self.start.blockSignals(False)
        self.end.blockSignals(False)
        self.refresh()

    def _bounds(self) -> tuple[str, str]:
        start = self.start.date().toPython()
        end = self.end.date().toPython()
        if end < start:
            start, end = end, start
        return clock.range_bounds(start, end)

    def refresh(self) -> None:
        start, end = self._bounds()
        rows = sale_repo.list_all(search=self.search.text(), start=start, end=end)
        live = [row for row in rows if row["status"] == "completed"]

        total = sum(int(row["total"]) for row in live)
        due = sum(int(row["due"]) for row in live)
        self.stat_count.set_value(str(len(live)),
                                  f"{len(rows) - len(live)} voided" if len(rows) != len(live)
                                  else "")
        self.stat_total.set_value(settings.money(total))
        self.stat_average.set_value(settings.money(total // len(live) if live else 0))
        self.stat_due.set_value(settings.money(due))

        self.table.setVisible(bool(rows))
        self.empty.setVisible(not rows)
        self.table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            voided = row["status"] == "void"
            returned = int(row["returned_total"])
            status = "Voided" if voided else ("Partly returned" if returned else "Completed")
            cells = [
                (row["invoice_no"], None),
                (clock.pretty(row["created_at"]), None),
                (row["customer_name"], None),
                (str(row["item_count"]), Qt.AlignRight | Qt.AlignVCenter),
                (settings.money(int(row["total"])), Qt.AlignRight | Qt.AlignVCenter),
                (settings.money(int(row["paid"])), Qt.AlignRight | Qt.AlignVCenter),
                (settings.money(int(row["due"])) if row["due"] else "—",
                 Qt.AlignRight | Qt.AlignVCenter),
                (status, Qt.AlignCenter),
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
                if column in (1, 3):
                    cell.setForeground(theme.color("text_muted"))
                if column == 6 and row["due"]:
                    cell.setForeground(theme.color("warning"))
                if column == 7:
                    cell.setForeground(theme.color(
                        "danger" if voided else "warning" if returned else "success"))
                if voided and column in (0, 2, 4):
                    cell.setForeground(theme.color("text_faint"))
                self.table.setItem(index, column, cell)
        align_headers(self.table)

        refunds = sale_repo.list_returns(search=self.search.text(), start=start, end=end)
        self.returns.setRowCount(len(refunds))
        for index, row in enumerate(refunds):
            cells = [
                (row["return_no"], None),
                (clock.pretty(row["created_at"]), None),
                (row["invoice_no"] or "—", None),
                (row["customer_name"], None),
                (str(row["item_count"]), Qt.AlignRight | Qt.AlignVCenter),
                (settings.money(int(row["total"])), Qt.AlignRight | Qt.AlignVCenter),
                ("Cash refund" if row["method"] == "cash" else "Account credit", None),
            ]
            for column, (text, alignment) in enumerate(cells):
                cell = QTableWidgetItem(text)
                if alignment:
                    cell.setTextAlignment(alignment)
                if column == 5:
                    cell.setForeground(theme.color("danger"))
                if column in (1, 4, 6):
                    cell.setForeground(theme.color("text_muted"))
                self.returns.setItem(index, column, cell)
        align_headers(self.returns)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _open(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        item = self.table.item(rows[0].row(), 0)
        dialog = SaleDetail(self, item.data(Qt.UserRole), self.session.user_id,
                            self.session.is_admin)
        dialog.exec()
        if dialog.changed:
            self.refresh()
            self.window.refresh_page("reports")
            self.window.refresh_page("dues")
            self.window.refresh_page("products")

    def _export(self) -> None:
        start, end = self._bounds()
        rows = sale_repo.list_all(search=self.search.text(), start=start, end=end)
        if not rows:
            self.notify("There is nothing to export.", "warning")
            return
        unit = 10 ** settings.decimals()
        data = [["Invoice", "Date", "Customer", "Items", "Subtotal", "Discount",
                 settings.tax_label(), "Total", "Paid", "Due", "Status", "Cashier"]]
        for row in rows:
            data.append([
                row["invoice_no"], row["created_at"], row["customer_name"],
                row["item_count"], int(row["subtotal"]) / unit,
                int(row["discount"]) / unit, int(row["tax"]) / unit,
                int(row["total"]) / unit, int(row["paid"]) / unit,
                int(row["due"]) / unit, row["status"], row["cashier"],
            ])
        if excel.save_as(self, data, "sales"):
            self.notify(f"Exported {len(rows)} sales.", "success")
