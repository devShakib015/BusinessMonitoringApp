"""The day close — what the till should hold at the end of trading."""

from datetime import date

from app.core import clock, settings
from app.repo import payments as payment_repo, reports
from app.ui import theme
from app.ui.dialogs.base import Dialog
from app.ui.widgets.common import MoneyEdit, divider, hbox, label


class DayCloseDialog(Dialog):
    def __init__(self, parent, day: date | None = None):
        day = day or date.today()
        super().__init__(parent, "Day close",
                         f"Summary for {day.strftime('%A, %d %B %Y')}.", 460)
        start, end = clock.day_bounds(day)
        summary = reports.summary(start, end)
        methods = {row["method"]: row for row in reports.payment_mix(start, end)}
        cash = methods.get("cash")
        self._expected = (int(cash["received"]) - int(cash["refunded"])) if cash else 0

        self._line("Transactions", str(summary["sale_count"]))
        self._line("Gross sales", settings.money(summary["total"]))
        if summary["discount"]:
            self._line("Discounts given", f"-{settings.money(summary['discount'])}")
        if summary["returns"]:
            self._line("Refunds", f"-{settings.money(summary['returns'])}")
        self._line("Net sales", settings.money(summary["net_sales"]), strong=True)
        self.body.addWidget(divider())

        for method, row in methods.items():
            net = int(row["received"]) - int(row["refunded"])
            self._line(f"{payment_repo.label(method)} taken", settings.money(net))
        if summary["due"]:
            self._line("Left on credit", settings.money(summary["due"]))
        if summary["due_collected"]:
            self._line("Credit collected", settings.money(summary["due_collected"]))
        self.body.addWidget(divider())

        self._line("Cash expected in drawer", settings.money(self._expected),
                   strong=True)

        self._counted = MoneyEdit()
        self._counted.textChanged.connect(self._compare)
        self.body.addWidget(self.field("Cash counted", self._counted,
                                       "Enter what is actually in the drawer."))
        self._difference = label("", "TotalRowValue")
        self.body.addWidget(self._difference)

        self.add_cancel("Close")

    def _line(self, caption: str, value: str, strong: bool = False) -> None:
        row = hbox(spacing=8)
        row.addWidget(label(caption, "GrandTotalLabel" if strong else "TotalRowLabel"))
        row.addStretch(1)
        row.addWidget(label(value, "GrandTotalLabel" if strong else "TotalRowValue"))
        holder = label("")
        holder.setLayout(row)
        self.body.addWidget(holder)

    def _compare(self) -> None:
        counted = self._counted.value_or_none()
        if counted is None or not self._counted.text().strip():
            self._difference.setText("")
            return
        difference = counted - self._expected
        if difference == 0:
            self._difference.setText("The drawer balances exactly.")
            self._difference.setStyleSheet(f"color: {theme.hex_of('success')};")
        else:
            word = "over" if difference > 0 else "short"
            self._difference.setText(
                f"{settings.money(abs(difference))} {word}.")
            self._difference.setStyleSheet(
                f"color: {theme.hex_of('warning' if difference > 0 else 'danger')};")
