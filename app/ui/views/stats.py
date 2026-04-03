from tkinter import *
from tkinter import ttk

import pytz
from datetime import datetime

from app.ui.widgets import Widgets
from app.ui.controller import AppController
from app.models.sale import SaleModel
from app.models.due import DueModel
from app.models.stock import StockModel


class StatsView:
    """Statistics tab – shows totals (sales, payments, dues, gross profit) for a date period."""

    def __init__(self, parent, widgets: Widgets, right: int, down: int, ctrl: AppController):
        self._parent = parent
        self._w = widgets
        self._right = right
        self._down = down

        tz = pytz.timezone("asia/dhaka")
        self._current_period = str(datetime.now(tz).year)

        self._stats_frame = None
        self._build()

    def refresh(self):
        self._load_stats(self._current_period)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build(self):
        search_frame = self._w.frame(self._parent, "Search by year, month or day", 0, 0)
        self._search_entry = self._w.entry(
            search_frame, "Date", 0, 0, self._w._font_size * 2)

        self._w.button(search_frame, "Search", 1, 1, W + E,
                       command=self._on_search)

        self._load_stats(self._current_period)

    def _load_stats(self, period: str):
        self._current_period = period

        # Destroy old results frame and recreate
        if self._stats_frame:
            self._stats_frame.destroy()

        self._stats_frame = self._w.frame(
            self._parent, f"Stats for particular time - {period}", 0, 1)
        self._stats_frame.columnconfigure(0, weight=1)
        self._stats_frame.columnconfigure(1, weight=1)

        sales_row   = SaleModel.get_period_stats(period)
        net_sales   = float(sales_row[0] or 0)
        net_paid    = float(sales_row[1] or 0)

        due_row     = DueModel.get_period_stats(period)
        net_due_paid = float(due_row[0] or 0)

        total_payment = net_paid + net_due_paid
        total_due     = net_sales - total_payment
        cost_of_sales = self._calculate_cost_of_sales(period)
        gross_profit  = net_sales - cost_of_sales

        w = self._w
        f = self._stats_frame

        e_sales   = w.entry(f, "Total Sales",          1, 0, w._font_size * 2)
        e_cost    = w.entry(f, "Total Cost of Sales",  2, 0, w._font_size * 2)
        e_profit  = w.entry(f, "Total Gross Profit",   3, 0, w._font_size * 2)
        sep = ttk.Separator(f, orient=HORIZONTAL)
        sep.grid(row=4, columnspan=2, sticky="ew", pady=20)
        e_payment = w.entry(f, "Total Payment Got",    5, 0, w._font_size * 2)
        e_due     = w.entry(f, "Total Dues",           6, 0, w._font_size * 2)

        for entry, value in (
            (e_sales,   f"{net_sales:.2f}"),
            (e_cost,    str(cost_of_sales)),
            (e_profit,  f"{gross_profit:.2f}"),
            (e_payment, str(total_payment)),
            (e_due,     f"{total_due:.2f}"),
        ):
            entry.insert(0, value)
            entry.config(state="disabled")

    @staticmethod
    def _calculate_cost_of_sales(period: str) -> float:
        avg_costs    = StockModel.get_avg_cost_per_product()
        qty_sold     = StockModel.get_quantity_sold_per_product(period)
        total_cost   = 0.0
        if qty_sold:
            for i, row in enumerate(qty_sold):
                if i < len(avg_costs) and avg_costs[i][0] is not None:
                    total_cost += float(avg_costs[i][0]) * float(row[0])
        return total_cost

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_search(self):
        query = self._search_entry.get().strip()
        if query:
            self._load_stats(query)
