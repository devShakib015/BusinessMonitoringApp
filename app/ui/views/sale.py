from tkinter import *
from tkinter import ttk, messagebox

from app.ui.widgets import Widgets
from app.ui.controller import AppController
from app.models.sale import SaleModel
from app.utils.excel import export_to_excel


class SaleView:
    """Displays the full sales list with search, reset, and a per-sale details popup."""

    def __init__(self, parent, widgets: Widgets, right: int, down: int, ctrl: AppController):
        self._parent = parent
        self._w = widgets
        self._right = right
        self._down = down
        self._trv: ttk.Treeview | None = None
        self._build()

    def refresh(self):
        self._populate(SaleModel.get_all())

    # ── UI construction ───────────────────────────────────────────────────────

    def _build(self):
        r, d = self._right, self._down
        list_frame = self._w.frame(self._parent, "Sales List", 0, 0)

        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.columnconfigure(1, weight=1)
        list_frame.columnconfigure(2, weight=1)
        list_frame.columnconfigure(3, weight=1)

        self._trv = ttk.Treeview(
            list_frame,
            columns=(1, 2, 3, 4, 5, 6, 7),
            show="headings",
            height=int(0.023 * d),
            padding=5,
            style="Custom.Treeview",
        )
        self._trv.grid(row=0, column=0, columnspan=4, sticky=NSEW)

        headers = ["Invoice Number", "Customer Name", "Customer Phone",
                   "Net Amount", "Paid Amount", "Due Amount", "Date Added"]
        widths  = [0.10, 0.10, 0.13, 0.10, 0.10, 0.10, 0.13]
        for i, (h, w) in enumerate(zip(headers, widths), 1):
            self._trv.heading(i, text=h)
            self._trv.column(i, anchor=CENTER, width=int(w * r))

        self._total_entry = self._w.entry(
            list_frame, "Total items in the list", 1, 2,
            self._w._font_size * 2)
        self._total_entry.config(state="disabled")

        self._search_entry = ttk.Entry(
            list_frame, width=self._w._font_size * 2,
            justify=LEFT, font=f"Verdana {self._w._font_size} bold")
        self._search_entry.grid(row=1, column=0, pady=5, sticky=W + E, columnspan=2)

        self._w.button(list_frame, "Search", 2, 1, W + E, command=self._on_search)
        self._w.button(list_frame, "Reset",  2, 0, W + E, command=self._on_reset)
        self._w.button(list_frame, "Generate Excel List", 2, 2, W + E,
                       command=self._export)
        self._w.button(list_frame, "Details of selected Sales", 2, 3, W + E,
                       command=self._show_details)

        self._populate(SaleModel.get_all())

    def _populate(self, data: list):
        self._trv.delete(*self._trv.get_children())
        for row in data:
            self._trv.insert("", "end", values=row)
        self._total_entry.config(state="normal")
        self._total_entry.delete(0, END)
        self._total_entry.insert(0, str(len(data)))
        self._total_entry.config(state="disabled")
        self._current_data = data

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_search(self):
        self._populate(SaleModel.search(self._search_entry.get()))

    def _on_reset(self):
        self._populate(SaleModel.get_all())

    def _export(self):
        export_to_excel(self._current_data)

    def _show_details(self):
        try:
            iid   = self._trv.selection()[0]
            item  = self._trv.item(iid)["values"]
            sale_code   = item[0]
            cust_name   = item[1]
            cust_phone  = str(item[2])
            net_total   = item[3]
            paid_total  = item[4]
            due_total   = item[5]

            products = SaleModel.get_products_for_sale(sale_code)
            total_without_discount = sum(float(p[4]) for p in products)

            discount_pct = (
                f"{((total_without_discount - float(net_total)) / total_without_discount) * 100:.2f}%"
                if total_without_discount else "0.00%"
            )

            win = Toplevel()
            win.title(f"{sale_code} Information")
            win.configure(bg="#F5F7FA")
            win.columnconfigure(0, weight=1)
            win.rowconfigure(0, weight=1)

            from app.config import ICON_PATH
            try:
                win.iconbitmap(ICON_PATH)
            except Exception:
                pass

            sf = self._w.frame(win, "Sales Information", 0, 0)
            sf.columnconfigure(1, weight=1)
            w  = self._w

            entries = {}
            for label, row in (
                ("Sales Code", 0), ("Customer Name", 1), ("Customer Phone", 2),
                ("Total Sales", 4), ("Discount", 5), ("Net Total Sales", 6),
                ("Paid amount", 7), ("Due Total", 8),
            ):
                entries[label] = w.entry(sf, label, row, 0, w._font_size * 2)

            # Products sub-treeview
            st = ttk.Treeview(sf, columns=(1, 2, 3, 4, 5),
                               show="headings", height=int(0.006 * self._down),
                               padding=5, style="Custom.Treeview")
            st.grid(row=3, column=0, columnspan=3, pady=10)
            for i, h in enumerate(["Product", "Weight", "Price", "Quantity", "Total Cost"], 1):
                st.heading(i, text=h)
                st.column(i, anchor=CENTER, width=[100, 80, 90, 80, 100][i - 1])
            for p in products:
                st.insert("", "end", values=p)

            values = {
                "Sales Code": sale_code, "Customer Name": cust_name,
                "Customer Phone": cust_phone, "Total Sales": total_without_discount,
                "Discount": discount_pct, "Net Total Sales": net_total,
                "Paid amount": paid_total, "Due Total": due_total,
            }
            for label, entry in entries.items():
                entry.insert(0, values[label])
                entry.config(state="disabled")

            win.mainloop()

        except (IndexError, TclError):
            messagebox.showerror("Selection Error",
                                 "You didn't select any sales from the list.")
