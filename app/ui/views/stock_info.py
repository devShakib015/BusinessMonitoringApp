from tkinter import *
from tkinter import ttk

import pytz
from datetime import datetime

from app.ui.widgets import Widgets
from app.ui.controller import AppController
from app.models.stock import StockModel
from app.utils.excel import export_to_excel


class StockInfoView:
    """Daily stock-management tab – shows products sold on a given date."""

    def __init__(self, parent, widgets: Widgets, right: int, down: int, ctrl: AppController):
        self._parent = parent
        self._w = widgets
        self._right = right
        self._down = down
        self._trv_frame = None

        tz = pytz.timezone("asia/dhaka")
        self._today = str(datetime.now(tz).date())
        self._build()

    def refresh(self):
        self._load(self._today)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build(self):
        search_frame = self._w.frame(self._parent, "Search by date", 0, 0)

        self._search_entry = self._w.entry(
            search_frame, "Search", 0, 0, self._w._font_size * 2)
        self._w.button(search_frame, "Search", 1, 1, W + E,
                       command=self._on_search)
        self._w.button(search_frame, "Reset", 1, 0, W + E,
                       command=self._on_reset)

        self._load(self._today)

    def _load(self, date: str):
        if self._trv_frame:
            self._trv_frame.destroy()

        self._trv_frame = self._w.frame(
            self._parent, f"Stock Management - {date}", 0, 1)
        self._trv_frame.rowconfigure(0, weight=1)
        self._trv_frame.columnconfigure(0, weight=1)
        self._trv_frame.columnconfigure(1, weight=1)

        r, d = self._right, self._down
        trv = ttk.Treeview(
            self._trv_frame,
            columns=(1, 2, 3, 4, 5),
            show="headings",
            height=int(0.023 * d),
            padding=5,
            style="Custom.Treeview",
        )
        trv.grid(row=0, column=0, columnspan=2, sticky=NSEW)

        for col, header, width_frac in (
            (1, "ID",          0.06),
            (2, "Product",     0.10),
            (3, "Weight",      0.10),
            (4, "Price",       0.10),
            (5, "Stock Sold",  0.10),
        ):
            trv.heading(col, text=header)
            trv.column(col, anchor=CENTER, width=int(width_frac * r))

        data = StockModel.get_daily_sold(date)
        for row in data:
            trv.insert("", "end", values=row)

        total_entry = self._w.entry(
            self._trv_frame, "Total items in the list", 1, 0,
            self._w._font_size * 2)
        total_entry.insert(0, str(len(data)))
        total_entry.config(state="disabled")

        self._w.button(
            self._trv_frame, "Generate Excel List", 2, 1, W + E,
            command=lambda: export_to_excel(data))

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_search(self):
        query = self._search_entry.get().strip()
        if query:
            self._load(query)

    def _on_reset(self):
        self._load(self._today)
