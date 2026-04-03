from tkinter import *
from tkinter import ttk, messagebox

from app.ui.widgets import Widgets
from app.ui.controller import AppController
from app.models.due import DueModel
from app.models.customer import CustomerModel
from app.utils.invoice import create_due_invoice


class DueView:
    """
    Due Payment tab.

    Left panel  – form to look up a customer, enter a payment amount,
                  and optionally generate a due-payment invoice.
    Right panel – scrollable list of all due payments.
    """

    def __init__(self, parent, widgets: Widgets, right: int, down: int, ctrl: AppController):
        self._parent = parent
        self._w = widgets
        self._right = right
        self._down = down
        self._ctrl = ctrl

        # Runtime state
        self._current_customer_id: int | None = None
        self._current_customer_code: str = ""
        self._last_payment_amount: float = 0.0

        self._build()

    def refresh(self):
        self._populate_list(DueModel.get_all())

    # ── UI construction ───────────────────────────────────────────────────────

    def _build(self):
        r, d = self._right, self._down
        w = self._w

        # ── Right: due list ──────────────────────────────────────────────────
        list_frame = w.frame(self._parent, "Paying Dues List", 0, 1, rowspan=2)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.columnconfigure(1, weight=1)
        self._trv = ttk.Treeview(
            list_frame, columns=(1, 2, 3, 4, 5),
            show="headings", height=int(0.020 * d),
            padding=5, style="Custom.Treeview",
        )
        self._trv.grid(row=0, column=0, columnspan=2, sticky=NSEW)

        for col, header, width_frac in (
            (1, "Code",       0.07),
            (2, "Name",       0.10),
            (3, "Phone",      0.10),
            (4, "Due Amount", 0.07),
            (5, "Date",       0.13),
        ):
            self._trv.heading(col, text=header)
            self._trv.column(col, anchor=CENTER, width=int(width_frac * r))

        self._list_total = w.entry(list_frame, "Total items in the list", 1, 0,
                                   w._font_size * 2)
        self._list_total.config(state="disabled")

        # ── Left top: pay due form ────────────────────────────────────────────
        pay_frame = w.frame(self._parent, "Pay Due", 0, 0)

        self._code_search = w.entry(pay_frame, "Customer Code", 0, 0, w._font_size * 2)
        w.button(pay_frame, "Search", 1, 1, W + E, command=self._search_customer)

        self._e_code    = w.entry(pay_frame, "Code",          2, 0, w._font_size * 2)
        self._e_name    = w.entry(pay_frame, "Name",          3, 0, w._font_size * 2)
        self._e_phone   = w.entry(pay_frame, "Phone",         4, 0, w._font_size * 2)
        self._e_net_due = w.entry(pay_frame, "Net Due",       5, 0, w._font_size * 2)
        self._e_amount  = w.entry(pay_frame, "Paying Amount", 6, 0, w._font_size * 2)

        for e in (self._e_code, self._e_name, self._e_phone):
            e.config(state="disabled")
        self._e_net_due.config(state="disabled", foreground="red")

        self._btn_pay = w.button(pay_frame, "Pay Due", 7, 1, W + E, state="disabled",
                                 command=self._pay_due)
        self._btn_invoice = w.button(pay_frame, "Generate Due Invoice", 8, 1, W + E,
                                     state="disabled", command=self._gen_invoice)

        # ── Left bottom: search ───────────────────────────────────────────────
        search_frame = w.frame(self._parent, "Search by code, name, phone or date", 1, 0)
        self._search_entry = w.entry(search_frame, "Search", 0, 0, w._font_size * 2)
        w.button(search_frame, "Search", 1, 1, W + E, command=self._on_search)
        w.button(search_frame, "Reset",  1, 0, W + E, command=self._on_reset)

        self._populate_list(DueModel.get_all())

    def _populate_list(self, data: list):
        self._trv.delete(*self._trv.get_children())
        for row in data:
            self._trv.insert("", "end", values=row)
        self._list_total.config(state="normal")
        self._list_total.delete(0, END)
        self._list_total.insert(0, str(len(data)))
        self._list_total.config(state="disabled")

    # ── Pay Due form logic ────────────────────────────────────────────────────

    def _set_customer_fields(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for e in (self._e_code, self._e_name, self._e_phone):
            e.config(state=state)
        self._e_net_due.config(state=state, foreground="red")

    def _clear_customer_fields(self):
        self._set_customer_fields(True)
        for e in (self._e_code, self._e_name, self._e_phone,
                  self._e_net_due, self._e_amount):
            e.delete(0, END)
        self._set_customer_fields(False)

    def _search_customer(self):
        try:
            code = int(self._code_search.get())
        except ValueError:
            messagebox.showerror("Customer Error", "Please enter a valid numeric customer code.")
            self._code_search.delete(0, END)
            return

        rows = CustomerModel.get_by_code(code)
        if not rows:
            messagebox.showerror("Customer Error",
                                 "Customer not found. Please check the code.")
            self._code_search.delete(0, END)
            return

        cust        = rows[0]
        c_id        = cust[0]
        c_code      = cust[1]
        c_name      = f"{cust[2]} {cust[3]}"
        c_phone     = cust[5]
        net_due     = DueModel.get_net_due(c_id)

        self._current_customer_id   = c_id
        self._current_customer_code = str(c_code)

        self._set_customer_fields(True)
        for e in (self._e_code, self._e_name, self._e_phone, self._e_net_due):
            e.delete(0, END)
        self._e_code.insert(0, c_code)
        self._e_name.insert(0, c_name)
        self._e_phone.insert(0, c_phone)
        self._e_net_due.insert(0, net_due)
        self._set_customer_fields(False)

        if float(net_due) <= 0:
            self._btn_pay.config(state="disabled")
        else:
            self._btn_pay.config(state="normal")

    def _pay_due(self):
        try:
            pay_amount = float(self._e_amount.get())
            net_due    = float(self._e_net_due.get())
        except ValueError:
            messagebox.showerror("Pay Due Error", "Please enter a valid payment amount.")
            return

        if pay_amount > net_due:
            self._e_amount.delete(0, END)
            messagebox.showerror("Pay Due Error", "You cannot pay more than the due amount.")
            return

        if not messagebox.askyesno("Confirm Pay Due",
                                   "Are you sure to save this due payment? "
                                   "This cannot be changed after saving."):
            return

        DueModel.add(self._current_customer_id, pay_amount)
        self._last_payment_amount = pay_amount

        messagebox.showinfo("Pay Due Success", "Due payment saved successfully.")
        self._btn_pay.config(state="disabled")
        self._btn_invoice.config(state="normal")
        self._ctrl.on_due_paid()
        self.refresh()

    def _gen_invoice(self):
        code    = self._e_code.get()
        name    = self._e_name.get()
        phone   = self._e_phone.get()
        net_due = float(self._e_net_due.get())
        paid    = self._last_payment_amount
        current = f"{net_due - paid:.2f}"

        rows = CustomerModel.get_by_code(int(code))
        address  = rows[0][4] if rows else ""
        due_date = DueModel.get_last_payment_date() or ""

        create_due_invoice(due_date, code, name, phone, address, net_due, paid, current)

        self._btn_invoice.config(state="disabled")
        self._clear_customer_fields()
        self._code_search.delete(0, END)

    # ── List search ───────────────────────────────────────────────────────────

    def _on_search(self):
        self._populate_list(DueModel.search(self._search_entry.get()))

    def _on_reset(self):
        self._populate_list(DueModel.get_all())
