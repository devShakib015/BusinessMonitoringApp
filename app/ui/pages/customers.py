"""The customer list."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QTableWidgetItem

from app.core import clock, settings
from app.export import excel
from app.repo import customers as customer_repo
from app.ui import theme
from app.ui.dialogs.customer_detail import CustomerDetail
from app.ui.dialogs.customer_picker import CustomerEditor
from app.ui.pages.base import Page
from app.ui.widgets.common import (Card, EmptyState, PageHeader, SearchField,
                                   StatCard, align_headers, button, hbox, table)


class CustomersPage(Page):
    def build(self) -> None:
        header = PageHeader("Customers",
                            "Regulars, accounts and anyone who buys on credit.")
        header.add_action(button("Export", "ghost", "download", self._export))
        header.add_action(button("Add customer", "primary", "customer_add",
                                 self._add, "Ctrl+N"))
        self.layout.addWidget(header)

        stats = hbox(spacing=14)
        self.stat_total = StatCard("Customers", icon_name="customers")
        self.stat_owing = StatCard("Owing money", icon_name="dues",
                                   accent=theme.hex_of("warning"))
        self.stat_balance = StatCard("Total outstanding", icon_name="cash",
                                     accent=theme.hex_of("danger"))
        for card in (self.stat_total, self.stat_owing, self.stat_balance):
            stats.addWidget(card)
        self.layout.addLayout(stats)

        filters = hbox(spacing=10)
        self.search = SearchField("Search name, phone or code…")
        self.search.textChanged.connect(self.refresh)
        filters.addWidget(self.search, 1)
        self.view = QComboBox()
        self.view.addItems(["All customers", "With a balance", "Retired"])
        self.view.setFixedWidth(170)
        self.view.currentIndexChanged.connect(self.refresh)
        filters.addWidget(self.view)
        self.layout.addLayout(filters)

        card = Card(padding=0, spacing=0)
        self.table = table(["Customer", "Code", "Phone", "Sales", "Last sale",
                            "Balance"], 0, 42)
        self.table.itemDoubleClicked.connect(lambda _: self._open())
        card.body.addWidget(self.table)
        self.empty = EmptyState(
            "customers", "No customers yet",
            "You only need customers for credit sales and regulars — "
            "walk-in sales work without one.")
        card.body.addWidget(self.empty)
        self.layout.addWidget(card, 1)

    def refresh(self) -> None:
        mode = self.view.currentText()
        rows = customer_repo.list_all(
            search=self.search.text(),
            active_only=mode != "Retired",
            with_due_only=mode == "With a balance")
        if mode == "Retired":
            rows = [row for row in rows if not row["is_active"]]

        everyone = customer_repo.list_all(active_only=True)
        owing = [row for row in everyone if int(row["balance"]) > 0]
        self.stat_total.set_value(str(len(everyone)))
        self.stat_owing.set_value(str(len(owing)),
                                  "on the credit book" if owing else "all settled up")
        self.stat_balance.set_value(settings.money(customer_repo.total_due()))

        self.table.setVisible(bool(rows))
        self.empty.setVisible(not rows)
        self.table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            balance = int(row["balance"])
            cells = [
                (row["name"], None),
                (row["code"], None),
                (row["phone"] or "—", None),
                (str(row["sale_count"]), Qt.AlignRight | Qt.AlignVCenter),
                (clock.pretty(row["last_sale_at"], False) or "—", None),
                (settings.money(balance) if balance else "—",
                 Qt.AlignRight | Qt.AlignVCenter),
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
                if column in (1, 2, 4):
                    cell.setForeground(theme.color("text_muted"))
                if column == 5 and balance:
                    cell.setForeground(theme.color("danger"))
                self.table.setItem(index, column, cell)
        align_headers(self.table)

    def _selected_id(self) -> int | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        item = self.table.item(rows[0].row(), 0)
        return item.data(Qt.UserRole) if item else None

    def _add(self) -> None:
        if CustomerEditor(self).exec():
            self.refresh()
            self.notify("Customer added.", "success")

    def _open(self) -> None:
        customer_id = self._selected_id()
        if customer_id is None:
            return
        dialog = CustomerDetail(self, customer_id, self.session.user_id)
        dialog.exec()
        if dialog.changed:
            self.refresh()
            self.window.refresh_page("dues")
            self.window.refresh_page("reports")

    def _export(self) -> None:
        rows = customer_repo.list_all()
        if not rows:
            self.notify("There is nothing to export.", "warning")
            return
        unit = 10 ** settings.decimals()
        data = [["Customer", "Code", "Phone", "Address", "Sales", "Last sale",
                 "Balance"]]
        for row in rows:
            data.append([row["name"], row["code"], row["phone"], row["address"],
                         row["sale_count"],
                         clock.pretty(row["last_sale_at"], False) or "",
                         int(row["balance"]) / unit])
        if excel.save_as(self, data, "customers"):
            self.notify(f"Exported {len(rows)} customers.", "success")
