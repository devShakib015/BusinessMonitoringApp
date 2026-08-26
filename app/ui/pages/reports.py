"""What the shop actually did: sales, profit, best sellers, and the day close."""

from datetime import timedelta

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import QComboBox, QDateEdit, QTableWidgetItem

from app.core import clock, settings
from app.export import excel
from app.repo import customers as customer_repo, payments as payment_repo, reports
from app.ui import theme
from app.ui.pages.base import Page
from app.ui.widgets.chart import BarChart, BarList
from app.ui.widgets.common import (Card, PageHeader, StatCard, align_headers, button,
                                   clear_layout, hbox, label, table, vbox)

RANGES = {"Today": 0, "Yesterday": -1, "Last 7 days": 6, "Last 30 days": 29,
          "This month": "month", "Last 90 days": 89}


class ReportsPage(Page):
    def build(self) -> None:
        header = PageHeader("Reports", "How the shop is doing.")
        header.add_action(button("Export", "ghost", "download", self._export))
        header.add_action(button("Day close", "primary", "clock", self._day_close))
        self.layout.addWidget(header)

        filters = hbox(spacing=10)
        self.range = QComboBox()
        self.range.addItems(list(RANGES))
        self.range.setCurrentText("Last 7 days")
        self.range.setFixedWidth(140)
        self.range.currentIndexChanged.connect(self._range_changed)
        filters.addWidget(self.range)

        self.start = QDateEdit(QDate.currentDate().addDays(-6))
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
        filters.addStretch(1)
        self.layout.addLayout(filters)

        row_one = hbox(spacing=14)
        self.stat_sales = StatCard("Net sales", icon_name="cash")
        self.stat_profit = StatCard("Gross profit", icon_name="up",
                                    accent=theme.hex_of("success"))
        self.stat_count = StatCard("Transactions", icon_name="sales")
        self.stat_average = StatCard("Average sale", icon_name="reports")
        for card in (self.stat_sales, self.stat_profit, self.stat_count,
                     self.stat_average):
            row_one.addWidget(card)
        self.layout.addLayout(row_one)

        row_two = hbox(spacing=14)
        self.stat_items = StatCard("Items sold", icon_name="products")
        self.stat_returns = StatCard("Refunded", icon_name="back",
                                     accent=theme.hex_of("danger"))
        self.stat_credit = StatCard("Sold on credit", icon_name="dues",
                                    accent=theme.hex_of("warning"))
        self.stat_collected = StatCard("Credit collected", icon_name="check",
                                       accent=theme.hex_of("success"))
        for card in (self.stat_items, self.stat_returns, self.stat_credit,
                     self.stat_collected):
            row_two.addWidget(card)
        self.layout.addLayout(row_two)

        middle = hbox(spacing=14)

        trend = Card()
        trend.body.addWidget(label("Sales trend", "SectionTitle"))
        self.chart = BarChart()
        trend.body.addWidget(self.chart)
        middle.addWidget(trend, 3)

        sellers = Card()
        sellers.body.addWidget(label("Best sellers", "SectionTitle"))
        self.top = BarList()
        sellers.body.addWidget(self.top)
        sellers.body.addStretch(1)
        middle.addWidget(sellers, 2)
        self.layout.addLayout(middle, 1)

        bottom = hbox(spacing=14)

        payments = Card()
        payments.body.addWidget(label("How customers paid", "SectionTitle"))
        self.payments = table(["Method", "Received", "Refunded", "Count"], 0, 32)
        self.payments.setMaximumHeight(190)
        payments.body.addWidget(self.payments)
        bottom.addWidget(payments, 1)

        attention = Card()
        attention.body.addWidget(label("Needs attention", "SectionTitle"))
        self.attention = vbox(spacing=8)
        attention.body.addLayout(self.attention)
        attention.body.addStretch(1)
        bottom.addWidget(attention, 1)
        self.layout.addLayout(bottom, 1)

    # ── Range ─────────────────────────────────────────────────────────────────

    def _range_changed(self) -> None:
        preset = RANGES[self.range.currentText()]
        today = QDate.currentDate()
        self.start.blockSignals(True)
        self.end.blockSignals(True)
        if preset == "month":
            self.start.setDate(QDate(today.year(), today.month(), 1))
            self.end.setDate(today)
        elif preset == -1:
            self.start.setDate(today.addDays(-1))
            self.end.setDate(today.addDays(-1))
        else:
            self.start.setDate(today.addDays(-preset))
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

    # ── Data ──────────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        start, end = self._bounds()
        summary = reports.summary(start, end)

        self.stat_sales.set_value(
            settings.money(summary["net_sales"]),
            f"{settings.money(summary['total'])} before refunds"
            if summary["returns"] else "")
        margin = (summary["profit"] * 100 // summary["net_sales"]
                  if summary["net_sales"] else 0)
        self.stat_profit.set_value(settings.money(summary["profit"]),
                                   f"{margin}% margin" if summary["net_sales"] else "")
        self.stat_count.set_value(str(summary["sale_count"]),
                                  f"{summary['voided']} voided" if summary["voided"] else "")
        self.stat_average.set_value(settings.money(summary["average_sale"]))
        self.stat_items.set_value(f"{summary['items_sold'] / 1000:g}")
        self.stat_returns.set_value(settings.money(summary["returns"]))
        self.stat_credit.set_value(settings.money(summary["due"]))
        self.stat_collected.set_value(settings.money(summary["due_collected"]))

        self._render_trend(start, end)
        self._render_top(start, end)
        self._render_payments(start, end)
        self._render_attention()

    def _render_trend(self, start: str, end: str) -> None:
        span = (self.end.date().toPython() - self.start.date().toPython()).days
        if span <= 1:
            rows = reports.hourly_series(start, end)
            points = [(f"{int(row['hour']):02d}", int(row["total"])) for row in rows]
        else:
            rows = reports.daily_series(start, end)
            by_day = {row["day"]: int(row["total"]) for row in rows}
            points = []
            day = self.start.date().toPython()
            last = self.end.date().toPython()
            while day <= last:
                key = day.strftime("%Y-%m-%d")
                points.append((day.strftime("%d %b" if span <= 31 else "%d/%m"),
                               by_day.get(key, 0)))
                day += timedelta(days=1)
        self.chart.set_points(points)

    def _render_top(self, start: str, end: str) -> None:
        rows = reports.top_products(start, end, limit=6)
        self.top.set_rows([
            (row["name"], int(row["revenue"]),
             f"{int(row['qty']) / 1000:g} {row['unit']} · "
             f"{settings.money(int(row['revenue']))}")
            for row in rows])

    def _render_payments(self, start: str, end: str) -> None:
        rows = reports.payment_mix(start, end)
        self.payments.setRowCount(len(rows))
        for index, row in enumerate(rows):
            cells = [
                (payment_repo.label(row["method"]), None),
                (settings.money(int(row["received"])), Qt.AlignRight | Qt.AlignVCenter),
                (settings.money(int(row["refunded"])) if row["refunded"] else "—",
                 Qt.AlignRight | Qt.AlignVCenter),
                (str(row["count"]), Qt.AlignRight | Qt.AlignVCenter),
            ]
            for column, (text, alignment) in enumerate(cells):
                cell = QTableWidgetItem(text)
                if alignment:
                    cell.setTextAlignment(alignment)
                if column == 2 and row["refunded"]:
                    cell.setForeground(theme.color("danger"))
                self.payments.setItem(index, column, cell)
        align_headers(self.payments)

    def _render_attention(self) -> None:
        clear_layout(self.attention)

        from app.repo import products as product_repo
        low = product_repo.low_stock(limit=5)
        owing = customer_repo.list_all(active_only=True, with_due_only=True)
        stale = reports.dead_stock(days=30, limit=3)

        lines = []
        if low:
            lines.append(("alert", "warning",
                          f"{len(low)} product(s) at or below reorder level: "
                          + ", ".join(row["name"] for row in low[:3])
                          + ("…" if len(low) > 3 else "")))
        if owing:
            lines.append(("dues", "danger",
                          f"{len(owing)} customer(s) owe "
                          f"{settings.money(customer_repo.total_due())}"))
        if stale:
            lines.append(("clock", "text_muted",
                          "Not sold in 30 days: "
                          + ", ".join(row["name"] for row in stale)))
        if not lines:
            lines.append(("check", "success", "Nothing needs your attention."))

        for icon_name, tone, text in lines:
            from app.ui import icons
            row = hbox(spacing=9)
            badge = label("")
            badge.setPixmap(icons.pixmap(icon_name, theme.hex_of(tone), 16))
            badge.setFixedWidth(20)
            row.addWidget(badge, 0, Qt.AlignTop)
            message = label(text)
            message.setWordWrap(True)
            row.addWidget(message, 1)
            holder = label("")
            holder.setLayout(row)
            self.attention.addWidget(holder)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _day_close(self) -> None:
        from app.ui.dialogs.day_close import DayCloseDialog
        DayCloseDialog(self, self.end.date().toPython()).exec()

    def _export(self) -> None:
        start, end = self._bounds()
        summary = reports.summary(start, end)
        unit = 10 ** settings.decimals()
        data = [["Measure", "Value"]]
        for caption, value in (
            ("Transactions", summary["sale_count"]),
            ("Gross sales", summary["total"] / unit),
            ("Refunds", summary["returns"] / unit),
            ("Net sales", summary["net_sales"] / unit),
            ("Discounts given", summary["discount"] / unit),
            (settings.tax_label(), summary["tax"] / unit),
            ("Cost of goods", summary["cost"] / unit),
            ("Gross profit", summary["profit"] / unit),
            ("Sold on credit", summary["due"] / unit),
            ("Credit collected", summary["due_collected"] / unit),
            ("Items sold", summary["items_sold"] / 1000),
        ):
            data.append([caption, value])

        data.append([])
        data.append(["Day", "Sales", "Profit"])
        for row in reports.daily_series(start, end):
            data.append([row["day"], int(row["total"]) / unit,
                         int(row["profit"]) / unit])

        data.append([])
        data.append(["Best sellers", "Quantity", "Revenue"])
        for row in reports.top_products(start, end, limit=20):
            data.append([row["name"], int(row["qty"]) / 1000,
                         int(row["revenue"]) / unit])

        if excel.save_as(self, data, "report"):
            self.notify("Report exported.", "success")
