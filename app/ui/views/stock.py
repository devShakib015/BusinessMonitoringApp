from tkinter import *
from tkinter import ttk, messagebox

from app.ui.widgets import Widgets
from app.ui.controller import AppController
from app.models.stock import StockModel
from app.models.product import ProductModel


class StockView:
    """
    Add Stock tab.

    Left panels  – form to add stock for a product + search bar.
    Right panel  – live stock list with edit / delete actions.
    """

    def __init__(self, parent, widgets: Widgets, right: int, down: int, ctrl: AppController):
        self._parent = parent
        self._w = widgets
        self._right = right
        self._down = down
        self._ctrl = ctrl
        self._trv: ttk.Treeview | None = None
        self._current_product_id: int | None = None
        self._build()

    def refresh(self):
        self._populate_list(StockModel.get_all())
        self._refresh_combo()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build(self):
        r, d = self._right, self._down
        w = self._w

        # ── Right: stock list ─────────────────────────────────────────────────
        list_frame = w.frame(self._parent, "List of stocks", 0, 1, rowspan=2)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.columnconfigure(1, weight=1)
        self._trv = ttk.Treeview(
            list_frame, columns=(1, 2, 3, 4, 5, 6),
            show="headings", height=int(0.020 * d),
            padding=5, style="Custom.Treeview",
        )
        self._trv.grid(row=0, column=0, columnspan=2, sticky=NSEW)

        for col, header, width_frac in (
            (1, "Stock ID",        0.050),
            (2, "Product Name",    0.090),
            (3, "Quantity",        0.050),
            (4, "Price",           0.090),
            (5, "Price Per Unit",  0.090),
            (6, "Added Date",      0.120),
        ):
            self._trv.heading(col, text=header)
            self._trv.column(col, anchor=CENTER, width=int(width_frac * r))

        self._list_total = w.entry(list_frame, "Total items in the list", 2, 0,
                                   w._font_size * 2)
        self._list_total.config(state="disabled")

        self._list_total_price = w.entry(list_frame, "Total Price Of Stocks", 3, 0,
                                         w._font_size * 2)
        self._list_total_price.config(state="disabled")

        w.button(list_frame, "Delete selected stock", 1, 0, W + E, command=self._delete)
        w.button(list_frame, "Edit selected Stock",   1, 1, W + E, command=self._edit)

        # ── Left top: add stock form ──────────────────────────────────────────
        self._add_frame = w.frame(self._parent, "Add stocks", 0, 0)
        self._build_add_section()

        # ── Left bottom: search ───────────────────────────────────────────────
        search_frame = w.frame(self._parent, "Search by product name or Date", 1, 0)
        self._search_entry = w.entry(search_frame, "Search Stock", 0, 0, w._font_size * 2)
        w.button(search_frame, "Search Stock", 1, 1, W + E, command=self._on_search)
        w.button(search_frame, "Reset Stock",  1, 0, W + E, command=self._on_reset)

        self._populate_list(StockModel.get_all())

    def _build_add_section(self):
        """(Re)builds the product combobox and add-stock fields."""
        for child in self._add_frame.winfo_children():
            child.destroy()

        w = self._w
        products = ProductModel.get_all_names()

        Label(
            self._add_frame, text="Product:",
            font=f"Verdana {w._font_size} bold",
            bg="#F5F7FA", fg="#2D2D2D",
        ).grid(row=0, column=0, sticky=E, padx=10)

        self._product_combo = ttk.Combobox(
            self._add_frame, values=products,
            width=w._font_size * 2,
            font=f"Verdana {w._font_size} bold",
        )
        self._product_combo.set("Choose one...")
        self._product_combo.bind("<<ComboboxSelected>>", self._on_product_selected)
        self._product_combo.grid(row=0, column=1, pady=5)

        self._e_name     = w.entry(self._add_frame, "Name",         1, 0,
                                    w._font_size * 2, state="disabled")
        self._e_quantity = w.entry(self._add_frame, "Quantity",      2, 0, w._font_size * 2)
        self._e_price    = w.entry(self._add_frame, "Price (BDT)",   3, 0, w._font_size * 2)
        self._btn_add    = w.button(self._add_frame, "Add stock", 4, 1, W + E,
                                    state="disabled", command=self._add_stock)

    def _populate_list(self, data: list):
        self._trv.delete(*self._trv.get_children())
        for row in data:
            self._trv.insert("", "end", values=row)

        total_price = sum(float(row[3]) for row in data) if data else 0.0

        self._list_total.config(state="normal")
        self._list_total.delete(0, END)
        self._list_total.insert(0, str(len(data)))
        self._list_total.config(state="disabled")

        self._list_total_price.config(state="normal")
        self._list_total_price.delete(0, END)
        self._list_total_price.insert(0, f"{total_price:.2f}")
        self._list_total_price.config(state="disabled")
        self._current_data = data

    def _refresh_combo(self):
        products = ProductModel.get_all_names()
        self._product_combo["values"] = products

    # ── Add stock ─────────────────────────────────────────────────────────────

    def _on_product_selected(self, _event):
        name = self._product_combo.get()
        self._current_product_id = ProductModel.get_id_by_name(name)
        self._e_name.config(state="normal")
        self._e_name.delete(0, END)
        self._e_name.insert(0, name)
        self._e_name.config(state="disabled")
        self._e_quantity.delete(0, END)
        self._e_price.delete(0, END)
        self._btn_add.config(state="normal")

    def _add_stock(self):
        if self._current_product_id is None:
            messagebox.showerror("Error", "Please select a product.")
            return
        try:
            qty   = int(self._e_quantity.get())
            price = float(self._e_price.get())
        except ValueError:
            messagebox.showerror("Adding Stock Error",
                                 "Please insert valid quantity and price.")
            self._e_quantity.delete(0, END)
            self._e_price.delete(0, END)
            return

        if not messagebox.askyesno("Confirm Adding Stock",
                                   "Are you sure you want to add this stock?"):
            return

        StockModel.add(self._current_product_id, qty, price)
        for e in (self._e_name, self._e_quantity, self._e_price):
            e.config(state="normal")
            e.delete(0, END)
        self._e_name.config(state="disabled")
        self._btn_add.config(state="disabled")
        self._ctrl.on_stock_changed()

    # ── Delete ────────────────────────────────────────────────────────────────

    def _delete(self):
        try:
            iid      = self._trv.selection()[0]
            stock_id = self._trv.item(iid)["values"][0]
        except IndexError:
            messagebox.showerror("Selection Error",
                                 "Please select a stock entry from the list first.")
            return

        if not messagebox.askyesno("Confirm Delete",
                                   "Are you sure you want to delete this stock?"):
            return
        StockModel.delete(stock_id)
        self._ctrl.on_stock_changed()

    # ── Edit ──────────────────────────────────────────────────────────────────

    def _edit(self):
        try:
            iid      = self._trv.selection()[0]
            stock_id = self._trv.item(iid)["values"][0]
            name     = self._trv.item(iid)["values"][1]
        except IndexError:
            messagebox.showerror("Selection Error", "Please select a stock entry first.")
            return

        row = StockModel.get_by_id(stock_id)
        if not row:
            return

        win = Toplevel()
        win.title("Edit Stock")
        from app.config import ICON_PATH
        try:
            win.iconbitmap(ICON_PATH)
        except Exception:
            pass

        frame = self._w.frame(win, "Edit Stock", 0, 0)
        w = self._w

        e_name = w.entry(frame, "Name",     0, 0, 30)
        e_qty  = w.entry(frame, "Quantity", 1, 0, 30)
        e_price = w.entry(frame, "Price",   2, 0, 30)

        e_name.insert(0, name)
        e_qty.insert(0, row[0])
        e_price.insert(0, row[1])
        e_name.config(state="disabled")

        def save():
            if not messagebox.askyesno("Confirm Edit",
                                        "Are you sure you want to save these changes?"):
                return
            try:
                StockModel.update(stock_id, e_qty.get(), e_price.get())
                messagebox.showinfo("Edit Successful", "Stock updated successfully.")
                self._ctrl.on_stock_changed()
                win.destroy()
            except Exception:
                messagebox.showerror("Edit Error", "Failed to update stock.")

        w.button(frame, "Save Changes", 4, 1, W + E, command=save)
        win.mainloop()

    # ── Search ────────────────────────────────────────────────────────────────

    def _on_search(self):
        self._populate_list(StockModel.search(self._search_entry.get()))

    def _on_reset(self):
        self._populate_list(StockModel.get_all())
