from tkinter import *
from tkinter import ttk, messagebox

from app.ui.widgets import Widgets
from app.ui.controller import AppController
from app.models.customer import CustomerModel
from app.utils.excel import export_to_excel


class CustomerView:
    """
    Add Customer tab.

    Left panels  – form to add a new customer + search bar.
    Right panel  – live customer list with edit / delete / details actions.
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
        self._populate(CustomerModel.get_all())

    # ── UI construction ───────────────────────────────────────────────────────

    def _build(self):
        r, d = self._right, self._down
        w = self._w

        # ── Right: customer list ──────────────────────────────────────────────
        list_frame = w.frame(self._parent, "Customer List", 0, 1, rowspan=2)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.columnconfigure(1, weight=1)
        list_frame.columnconfigure(2, weight=1)
        self._trv = ttk.Treeview(
            list_frame, columns=(1, 2, 3, 4, 5),
            show="headings", height=int(0.020 * d),
            padding=5, style="Custom.Treeview",
        )
        self._trv.grid(row=0, column=0, columnspan=3, sticky=NSEW)

        for col, header in enumerate(
            ["Code", "First Name", "Last Name", "Address", "Phone"], 1
        ):
            self._trv.heading(col, text=header)
            self._trv.column(col, anchor=CENTER, width=int(0.10 * r))

        self._list_total = w.entry(list_frame, "Total items in the list", 2, 1,
                                   w._font_size * 2)
        self._list_total.config(state="disabled")

        w.button(list_frame, "Generate Excel List",      2, 0, W + E, command=self._export)
        w.button(list_frame, "Delete selected Customer", 1, 0, W + E, command=self._delete)
        w.button(list_frame, "Edit selected Customer",   1, 1, W + E, command=self._edit)
        w.button(list_frame, "Details",                  1, 2, W + E, command=self._details)

        # ── Left top: add form ────────────────────────────────────────────────
        add_frame = w.frame(self._parent, "Add New Customer", 0, 0)
        self._e_fname   = w.entry(add_frame, "First Name", 0, 0, w._font_size * 2)
        self._e_lname   = w.entry(add_frame, "Last Name",  1, 0, w._font_size * 2)
        self._e_address = w.entry(add_frame, "Address",    2, 0, w._font_size * 2)
        self._e_phone   = w.entry(add_frame, "Phone",      3, 0, w._font_size * 2)
        w.button(add_frame, "Add Customer", 4, 1, W + E, command=self._add)

        # ── Left bottom: search ───────────────────────────────────────────────
        search_frame = w.frame(self._parent, "Search by name, address or phone", 1, 0)
        self._search_entry = w.entry(search_frame, "Search Customer", 0, 0, w._font_size * 2)
        w.button(search_frame, "Search", 1, 1, W + E, command=self._on_search)
        w.button(search_frame, "Reset",  1, 0, W + E, command=self._on_reset)

        self._populate(CustomerModel.get_all())

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
        fname   = self._e_fname.get().strip().capitalize()
        lname   = self._e_lname.get().strip().capitalize()
        address = self._e_address.get().strip().capitalize()
        phone   = self._e_phone.get().strip()

        if not all([fname, lname, address, phone]):
            messagebox.showerror("Insert Error",
                                 "Please fill in all fields with valid input.")
            return

        code = CustomerModel.get_next_code()
        if not messagebox.askyesno("Confirm Save Customer",
                                   "Are you sure you want to save this customer?"):
            self._clear_add_form()
            return

        try:
            CustomerModel.add(code, fname, lname, address, phone)
            messagebox.showinfo("Save Successful",
                                f"Customer saved. New customer code: {code}.")
            self._clear_add_form()
            self._ctrl.on_customer_changed()
        except Exception:
            messagebox.showerror("Customer Error", "Failed to add customer.")

    def _delete(self):
        try:
            iid  = self._trv.selection()[0]
            code = self._trv.item(iid)["values"][0]
        except IndexError:
            messagebox.showerror("Selection Error",
                                 "Please select a customer from the list first.")
            return

        if not messagebox.askyesno("Confirm Delete",
                                   "Are you sure you want to delete this customer?"):
            return
        CustomerModel.delete(code)
        self._ctrl.on_customer_changed()

    def _edit(self):
        try:
            iid  = self._trv.selection()[0]
            code = self._trv.item(iid)["values"][0]
        except IndexError:
            messagebox.showerror("Selection Error", "Please select a customer first.")
            return

        rows = CustomerModel.get_by_code(code)
        if not rows:
            return
        cust = rows[0]

        win = Toplevel()
        win.title("Edit Customer")
        from app.config import ICON_PATH
        try:
            win.iconbitmap(ICON_PATH)
        except Exception:
            pass

        frame = self._w.frame(win, "Edit Customer", 0, 0)
        w = self._w

        e_fn = w.entry(frame, "First Name", 0, 0, 30)
        e_ln = w.entry(frame, "Last Name",  1, 0, 30)
        e_ad = w.entry(frame, "Address",    2, 0, 30)
        e_ph = w.entry(frame, "Phone",      3, 0, 30)

        e_fn.insert(0, cust[2]); e_ln.insert(0, cust[3])
        e_ad.insert(0, cust[4]); e_ph.insert(0, cust[5])

        def save():
            if not messagebox.askyesno("Confirm Edit",
                                        "Are you sure you want to save these changes?"):
                return
            CustomerModel.update(
                code,
                e_fn.get().strip().capitalize(),
                e_ln.get().strip().capitalize(),
                e_ad.get().strip().capitalize(),
                e_ph.get().strip(),
            )
            messagebox.showinfo("Edit Successful", "Customer updated successfully.")
            self._ctrl.on_customer_changed()
            win.destroy()

        w.button(frame, "Save Changes", 4, 1, W + E, command=save)
        win.mainloop()

    def _details(self):
        try:
            iid  = self._trv.selection()[0]
            code = self._trv.item(iid)["values"][0]
        except IndexError:
            messagebox.showerror("Selection Error", "Please select a customer first.")
            return

        rows = CustomerModel.get_by_code(code)
        if not rows:
            return
        cust    = rows[0]
        c_id    = cust[0]
        c_name  = f"{cust[2]} {cust[3]}"
        summary = CustomerModel.get_financial_summary(c_id)

        win = Toplevel()
        win.title(f"{c_name} Details")
        from app.config import ICON_PATH
        try:
            win.iconbitmap(ICON_PATH)
        except Exception:
            pass

        frame = self._w.frame(win, "Customer Details", 0, 0)
        w = self._w

        entries = [
            ("Customer Code",     code),
            ("Name",              c_name),
            ("Address",           cust[4]),
            ("Phone",             cust[5]),
            ("Total Sales",       f"{summary['total_sales']:.2f}"),
            ("Total Paid",        summary["total_paid"]),
            ("Total Due Occurred", f"{summary['total_due']:.2f}"),
            ("Total Due Paid",     summary["total_due_paid"]),
            ("Net Due",            f"{summary['net_due']:.2f}"),
        ]
        for i, (label, value) in enumerate(entries):
            e = w.entry(frame, label, i, 1, w._font_size * 2)
            e.insert(0, value)
            e.config(state="disabled")

        win.mainloop()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _clear_add_form(self):
        for e in (self._e_fname, self._e_lname, self._e_address, self._e_phone):
            e.delete(0, END)

    def _export(self):
        export_to_excel(self._current_data)

    def _on_search(self):
        self._populate(CustomerModel.search(self._search_entry.get()))

    def _on_reset(self):
        self._populate(CustomerModel.get_all())
