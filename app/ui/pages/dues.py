"""The credit book: who owes what, and collecting it."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTabWidget, QTableWidgetItem

from app.core import clock, settings
from app.export import excel
from app.repo import customers as customer_repo, payments as payment_repo
from app.ui import theme
from app.ui.dialogs.customer_detail import CustomerDetail, TakePaymentDialog
from app.ui.pages.base import Page
from app.ui.widgets.common import (Card, EmptyState, PageHeader, SearchField,
                                   StatCard, align_headers, button, hbox, table)


class DuesPage(Page):
    def build(self) -> None:
        header = PageHeader("Credit book",
                            "Money customers still owe, and payments as they come in.")
        header.add_action(button("Export", "ghost", "download", self._export))
        header.add_action(button("Take payment", "primary", "cash", self._collect,
                                 "Ctrl+N"))
        self.layout.addWidget(header)

        stats = hbox(spacing=14)
        self.stat_total = StatCard("Total outstanding", icon_name="dues",
                                   accent=theme.hex_of("danger"))
        self.stat_people = StatCard("Customers owing", icon_name="customers")
        self.stat_collected = StatCard("Collected today", icon_name="cash",
                                       accent=theme.hex_of("success"))
        for card in (self.stat_total, self.stat_people, self.stat_collected):
            stats.addWidget(card)
        self.layout.addLayout(stats)

        self.search = SearchField("Search customers…")
        self.search.textChanged.connect(self.refresh)
        self.layout.addWidget(self.search)

        tabs = QTabWidget()
        self.table = table(["Customer", "Phone", "Balance", "Credit limit",
                            "Last sale"], 0, 42)
        self.table.itemDoubleClicked.connect(lambda _: self._open())
        outstanding = Card(padding=0, spacing=0)
        outstanding.body.addWidget(self.table)
        self.empty = EmptyState("check", "Nobody owes you anything",
                                "Credit sales appear here until they are paid off.")
        outstanding.body.addWidget(self.empty)
        tabs.addTab(outstanding, "Outstanding")

        self.payments = table(["When", "Customer", "Amount", "Method", "Note",
                               "Taken by"], 1, 38)
        history = Card(padding=0, spacing=0)
        history.body.addWidget(self.payments)
        tabs.addTab(history, "Payments received")
        self.layout.addWidget(tabs, 1)

    def refresh(self) -> None:
        rows = customer_repo.list_all(search=self.search.text(), active_only=True,
                                      with_due_only=True)
        rows = sorted(rows, key=lambda row: -int(row["balance"]))

        from datetime import date
        start, end = clock.day_bounds(date.today())
        collected = sum(int(row["amount"]) for row in
                        payment_repo.list_all(start, end, kind="due"))

        self.stat_total.set_value(settings.money(customer_repo.total_due()))
        self.stat_people.set_value(str(len(rows)))
        self.stat_collected.set_value(settings.money(collected))

        self.table.setVisible(bool(rows))
        self.empty.setVisible(not rows)
        self.table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            balance = int(row["balance"])
            limit = int(row["credit_limit"])
            over = limit and balance > limit
            cells = [
                (row["name"], None),
                (row["phone"] or "—", None),
                (settings.money(balance), Qt.AlignRight | Qt.AlignVCenter),
                (settings.money(limit) if limit else "none",
                 Qt.AlignRight | Qt.AlignVCenter),
                (clock.pretty(row["last_sale_at"], False) or "—", None),
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
                if column == 2:
                    cell.setForeground(theme.color("danger" if over else "text"))
                if column in (1, 3, 4):
                    cell.setForeground(theme.color("text_muted"))
                self.table.setItem(index, column, cell)
        align_headers(self.table)

        history = payment_repo.list_all(kind="due", limit=250)
        self.payments.setRowCount(len(history))
        for index, row in enumerate(history):
            cells = [
                (clock.pretty(row["created_at"]), None),
                (row["customer_name"], None),
                (settings.money(int(row["amount"])), Qt.AlignRight | Qt.AlignVCenter),
                (payment_repo.label(row["method"]), None),
                (row["note"] or "—", None),
                (row["who"] or "—", None),
            ]
            for column, (text, alignment) in enumerate(cells):
                cell = QTableWidgetItem(text)
                if alignment:
                    cell.setTextAlignment(alignment)
                if column == 2:
                    cell.setForeground(theme.color("success"))
                if column in (0, 4, 5):
                    cell.setForeground(theme.color("text_muted"))
                self.payments.setItem(index, column, cell)
        align_headers(self.payments)

    def _selected_id(self) -> int | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        item = self.table.item(rows[0].row(), 0)
        return item.data(Qt.UserRole) if item else None

    def _open(self) -> None:
        customer_id = self._selected_id()
        if customer_id is None:
            return
        dialog = CustomerDetail(self, customer_id, self.session.user_id)
        dialog.exec()
        if dialog.changed:
            self._after_change()

    def _collect(self) -> None:
        customer_id = self._selected_id()
        if customer_id is None:
            from app.ui.dialogs.customer_picker import CustomerPicker
            picker = CustomerPicker(self, allow_walk_in=False, with_due_only=True)
            if not picker.exec() or picker.selected is None:
                return
            customer_id = picker.selected["id"]

        customer = customer_repo.get(customer_id)
        if int(customer["balance"]) <= 0:
            self.notify(f"{customer['name']} has nothing outstanding.", "warning")
            return
        dialog = TakePaymentDialog(self, customer, self.session.user_id)
        if dialog.exec():
            self._after_change()
            self.notify(f"{settings.money(dialog.amount_paid)} received from "
                        f"{customer['name']}.", "success")

    def _after_change(self) -> None:
        self.refresh()
        self.window.refresh_page("customers")
        self.window.refresh_page("reports")

    def _export(self) -> None:
        rows = customer_repo.list_all(active_only=True, with_due_only=True)
        if not rows:
            self.notify("Nobody owes you anything.", "warning")
            return
        unit = 10 ** settings.decimals()
        data = [["Customer", "Phone", "Balance", "Credit limit", "Last sale"]]
        for row in rows:
            data.append([row["name"], row["phone"], int(row["balance"]) / unit,
                         int(row["credit_limit"]) / unit,
                         clock.pretty(row["last_sale_at"], False) or ""])
        if excel.save_as(self, data, "credit-book"):
            self.notify("Credit book exported.", "success")
