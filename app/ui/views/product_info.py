from tkinter import *
from tkinter import ttk

from app.ui.widgets import Widgets
from app.ui.controller import AppController
from app.models.product import ProductModel
from app.utils.excel import export_to_excel


class ProductInfoView:
    """Read-only summary of all products: selling price, cost price, stock levels."""

    def __init__(self, parent, widgets: Widgets, right: int, down: int, ctrl: AppController):
        self._parent = parent
        self._w = widgets
        self._right = right
        self._down = down
        self._trv: ttk.Treeview | None = None
        self._build()

    def refresh(self):
        self._populate()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build(self):
        r, d = self._right, self._down

        self._parent.rowconfigure(0, weight=1)
        self._parent.columnconfigure(0, weight=1)
        self._parent.columnconfigure(1, weight=1)

        self._trv = ttk.Treeview(
            self._parent,
            columns=(1, 2, 3, 4, 5, 6, 7),
            show="headings",
            height=int(0.025 * d),
            padding=5,
            style="Custom.Treeview",
        )
        self._trv.grid(row=0, column=0, columnspan=2, sticky=NSEW)

        headers = [
            "Name", "Weight", "Selling Price", "Cost Price",
            "Total Stock Added", "Total Stock Sold", "Remaining Stock",
        ]
        widths = [0.10, 0.07, 0.10, 0.10, 0.10, 0.10, 0.10]
        for i, (h, w) in enumerate(zip(headers, widths), 1):
            self._trv.heading(i, text=h)
            self._trv.column(i, anchor=CENTER, width=int(w * r))

        self._total_entry = self._w.entry(
            self._parent, "Total items in the list", 1, 0,
            self._w._font_size * 2)
        self._total_entry.config(state="disabled")

        self._w.button(
            self._parent, "Generate Excel List", 2, 1, W + E,
            command=self._export)

        self._populate()

    def _populate(self):
        self._trv.delete(*self._trv.get_children())
        ids = ProductModel.get_all_ids()
        rows = [ProductModel.get_details(pid) for pid in ids]
        for row in rows:
            self._trv.insert("", "end", values=row)
        self._total_entry.config(state="normal")
        self._total_entry.delete(0, END)
        self._total_entry.insert(0, str(len(rows)))
        self._total_entry.config(state="disabled")
        self._current_data = rows

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _export(self):
        export_to_excel(self._current_data)
