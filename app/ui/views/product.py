from tkinter import *
from tkinter import ttk, messagebox

from app.ui.widgets import Widgets
from app.ui.controller import AppController
from app.models.product import ProductModel
from app.utils.excel import export_to_excel


class ProductView:
    """
    Add Product tab.

    Left panels  – form to add a new product + search bar.
    Right panel  – live product list with edit / delete / details actions.
    """

    def __init__(self, parent, widgets: Widgets, right: int, down: int, ctrl: AppController):
        self._parent = parent
        self._w = widgets
        self._right = right
        self._down = down
        self._ctrl = ctrl
        self._trv: ttk.Treeview | None = None
        self._build()

    def refresh(self):
        self._populate(ProductModel.get_all())

    # ── UI construction ───────────────────────────────────────────────────────

    def _build(self):
        r, d = self._right, self._down
        w = self._w

        # ── Right: product list ───────────────────────────────────────────────
        list_frame = w.frame(self._parent, "Products List", 0, 1, rowspan=2)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.columnconfigure(1, weight=1)
        list_frame.columnconfigure(2, weight=1)
        self._trv = ttk.Treeview(
            list_frame, columns=(1, 2, 3),
            show="headings", height=int(0.020 * d),
            padding=5, style="Custom.Treeview",
        )
        self._trv.grid(row=0, column=0, columnspan=3, sticky=NSEW)

        for col, header, width_frac in (
            (1, "Name",       0.17),
            (2, "Weight (g)", 0.17),
            (3, "Price (BDT)", 0.17),
        ):
            self._trv.heading(col, text=header)
            self._trv.column(col, anchor=CENTER, width=int(width_frac * r))

        self._list_total = w.entry(list_frame, "Total items in the list", 2, 1,
                                   w._font_size * 2)
        self._list_total.config(state="disabled")

        w.button(list_frame, "Delete selected product", 1, 0, W + E, command=self._delete)
        w.button(list_frame, "Edit selected Product",   1, 1, W + E, command=self._edit)
        w.button(list_frame, "Details",                 1, 2, W + E, command=self._details)

        # ── Left top: add form ────────────────────────────────────────────────
        add_frame = w.frame(self._parent, "Add New Product", 0, 0)
        self._e_name   = w.entry(add_frame, "Product Name", 0, 0, w._font_size * 2)
        self._e_weight = w.entry(add_frame, "Weight",       1, 0, w._font_size * 2)
        self._e_price  = w.entry(add_frame, "Price",        2, 0, w._font_size * 2)
        w.button(add_frame, "Add Product", 4, 1, W + E, command=self._add)

        # ── Left bottom: search ───────────────────────────────────────────────
        search_frame = w.frame(self._parent, "Search by name", 1, 0)
        self._search_entry = w.entry(search_frame, "Search Product", 0, 0, w._font_size * 2)
        w.button(search_frame, "Search", 1, 1, W + E, command=self._on_search)
        w.button(search_frame, "Reset",  1, 0, W + E, command=self._on_reset)

        self._populate(ProductModel.get_all())

    def _populate(self, data: list):
        self._trv.delete(*self._trv.get_children())
        for row in data:
            self._trv.insert("", "end", values=row)
        self._list_total.config(state="normal")
        self._list_total.delete(0, END)
        self._list_total.insert(0, str(len(data)))
        self._list_total.config(state="disabled")
        self._current_data = data

    # ── CRUD actions ──────────────────────────────────────────────────────────

    def _add(self):
        name   = self._e_name.get().strip().capitalize()
        weight = self._e_weight.get().strip()
        price  = self._e_price.get().strip()

        if not all([name, weight, price]):
            messagebox.showerror("Insert Error", "Please fill in all fields.")
            return

        if not messagebox.askyesno("Confirm Save Product",
                                   "Are you sure you want to save this product?"):
            return

        try:
            ProductModel.add(name, weight, price)
            messagebox.showinfo("Save Successful", "Product saved successfully.")
            for e in (self._e_name, self._e_weight, self._e_price):
                e.delete(0, END)
            self._ctrl.on_product_changed()
        except Exception:
            messagebox.showerror("Products Error",
                                 "Failed to add product. The name may already exist.")
            for e in (self._e_name, self._e_weight, self._e_price):
                e.delete(0, END)

    def _delete(self):
        try:
            iid  = self._trv.selection()[0]
            name = self._trv.item(iid)["values"][0]
        except IndexError:
            messagebox.showerror("Selection Error",
                                 "Please select a product from the list first.")
            return

        if not messagebox.askyesno("Confirm Delete",
                                   "Are you sure you want to delete this product?"):
            return
        ProductModel.delete(name)
        self._ctrl.on_product_changed()

    def _edit(self):
        try:
            iid  = self._trv.selection()[0]
            name = self._trv.item(iid)["values"][0]
        except IndexError:
            messagebox.showerror("Selection Error", "Please select a product first.")
            return

        row = ProductModel.get_by_name(name)
        if not row:
            return

        win = Toplevel()
        win.title("Edit Product")
        from app.config import ICON_PATH
        try:
            win.iconbitmap(ICON_PATH)
        except Exception:
            pass

        frame = self._w.frame(win, "Edit Product", 0, 0)
        w = self._w

        e_name   = w.entry(frame, "Product Name", 0, 0, 30)
        e_weight = w.entry(frame, "Weight (g)",   1, 0, 30)
        e_price  = w.entry(frame, "Price (BDT)",  2, 0, 30)

        e_name.insert(0, row[0])
        e_weight.insert(0, row[1])
        e_price.insert(0, row[2])

        def save():
            if not messagebox.askyesno("Confirm Edit",
                                        "Are you sure you want to save these changes?"):
                return
            try:
                ProductModel.update(
                    name,
                    e_name.get().strip().capitalize(),
                    e_weight.get().strip(),
                    e_price.get().strip(),
                )
                messagebox.showinfo("Edit Successful", "Product updated successfully.")
                self._ctrl.on_product_changed()
                win.destroy()
            except Exception:
                messagebox.showerror("Edit Error", "Failed to update the product.")

        w.button(frame, "Save Changes", 4, 1, W + E, command=save)
        win.mainloop()

    def _details(self):
        try:
            iid  = self._trv.selection()[0]
            name = self._trv.item(iid)["values"][0]
        except IndexError:
            messagebox.showerror("Selection Error", "Please select a product first.")
            return

        full = ProductModel.get_full_by_name(name)
        if not full:
            return
        prod_id = full[0]
        weight  = full[2]
        price   = full[3]

        from app.database.connection import get_db
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sum(Quantity), sum(Price) FROM stocks WHERE product_id=?",
                (prod_id,))
            stock_row = cursor.fetchone()
            total_added = stock_row[0] or 0
            total_price_added = stock_row[1] or 0

            cursor.execute(
                "SELECT sum(quantity) FROM stocks_removed WHERE product_id=? "
                "GROUP BY product_id",
                (prod_id,))
            removed_row = cursor.fetchone()
            total_removed = removed_row[0] if removed_row else 0

        available = int(total_added) - int(total_removed)
        price_removed = float(total_removed) * float(price)

        win = Toplevel()
        win.title(f"{name} Details")
        from app.config import ICON_PATH
        try:
            win.iconbitmap(ICON_PATH)
        except Exception:
            pass

        frame = self._w.frame(win, "Product Details", 0, 0)
        w = self._w
        entries = [
            ("Product",                  name),
            ("Weight",                   weight),
            ("Price",                    price),
            ("Total Stock Added",        total_added),
            ("Total Price of Stock Added", total_price_added),
            ("Total Stock Sold",          total_removed),
            ("Total Price of Stock Sold", price_removed),
            ("Total Stock Available",     available),
        ]
        for i, (label, value) in enumerate(entries):
            e = w.entry(frame, label, i, 0, w._font_size * 2)
            e.insert(0, value)
            e.config(state="disabled")

        win.mainloop()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _on_search(self):
        self._populate(ProductModel.search(self._search_entry.get()))

    def _on_reset(self):
        self._populate(ProductModel.get_all())
