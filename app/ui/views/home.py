from tkinter import *
from tkinter import ttk, messagebox
from time import strftime
import pytz
from datetime import datetime

from app.ui.widgets import Widgets
from app.ui.controller import AppController
from app.models.product import ProductModel
from app.models.sale import SaleModel, InvoiceItemModel
from app.utils.invoice import create_invoice


class HomeView:
    """
    Create Invoice tab (home screen).

    Layout
    ──────
    Left column  (col 0, row 0): "Add Product to Invoice" frame
    Left column  (col 0, row 1): "Add Customer to Invoice" frame
    Right column (col 1, rows 0-1): "Invoice Items List" frame
    """

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def __init__(self, parent, widgets: Widgets, right: int, down: int, ctrl: AppController):
        self._parent = parent
        self._w = widgets
        self._right = right
        self._down = down
        self._ctrl = ctrl

        # Persisted invoice state
        self._net_total: float = 0.0
        self._due_amount: float = 0.0
        self._raw_total: float = 0.0
        self._customer_id: int | None = None
        self._sale_code: str | None = None
        self._discount_rate: float = 0.0
        self._discount_amount: str = "0.00"
        self._payment_amount: float = 0.0
        self._previous_due: str = "0.00"
        self._total_payable: str = "0.00"
        self._sale_saved: bool = False

        self._build()

    def refresh(self):
        """Sync product combo values. Called by controller on product/stock change."""
        self._product_combo["values"] = ProductModel.get_all_names()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self):
        w = self._w
        r, d = self._right, self._down

        # ── Right: invoice items list ──────────────────────────────────────────
        inv_frame = w.frame(self._parent, "Invoice Items List", 0, 1, rowspan=2)
        self._inv_frame = inv_frame
        inv_frame.rowconfigure(0, weight=1)
        inv_frame.columnconfigure(0, weight=1)
        inv_frame.columnconfigure(1, weight=1)
        self._build_invoice_section(inv_frame, d, r)

        # ── Left top: product add ──────────────────────────────────────────────
        prod_frame = w.frame(self._parent, "Add Product to Invoice", 0, 0)
        self._build_product_section(prod_frame, w)

        # ── Left bottom: customer add ──────────────────────────────────────────
        cust_frame = w.frame(self._parent, "Add Customer to Invoice", 1, 0)
        self._build_customer_section(cust_frame, w)

        # Load any items leftover in invoice_items from a previous (unsaved) session
        self._refresh_invoice_treeview()

    # ── Product section ───────────────────────────────────────────────────────

    def _build_product_section(self, frame, w):
        products = ProductModel.get_all_names()

        Label(frame, text="Product:",
              font=f"Verdana {w._font_size} bold",
              bg="#F5F7FA", fg="#2D2D2D").grid(row=0, column=0, sticky=E, padx=10)

        self._product_combo = ttk.Combobox(
            frame, values=products,
            width=w._font_size * 2,
            font=f"Verdana {w._font_size - 3}",
        )
        self._product_combo.set("Choose one...")
        self._product_combo.bind("<<ComboboxSelected>>", self._on_product_selected)
        self._product_combo.grid(row=0, column=1, pady=5)

        self._e_prod_name   = w.entry(frame, "Name",            1, 0, w._font_size * 2, state="disabled")
        self._e_prod_weight = w.entry(frame, "Weight (g)",      2, 0, w._font_size * 2, state="disabled")
        self._e_prod_price  = w.entry(frame, "Price (BDT)",     3, 0, w._font_size * 2, state="disabled")
        self._e_prod_stock  = w.entry(frame, "Stock Available", 4, 0, w._font_size * 2, state="disabled")
        self._e_prod_qty    = w.entry(frame, "Quantity",        5, 0, w._font_size * 2)

        self._btn_add_product = w.button(
            frame, "Add Product", 6, 1, W + E,
            state="disabled", command=self._add_product,
        )

    def _on_product_selected(self, _event):
        """Populate read-only fields from the selected product."""
        if self._sale_saved:
            return

        name = self._product_combo.get()
        row  = ProductModel.get_by_name(name)
        if not row:
            return

        product_name, product_weight, product_price = row
        product_id = ProductModel.get_id_by_name(name)
        available  = ProductModel.get_available_stock(product_id)

        for e in (self._e_prod_name, self._e_prod_weight,
                  self._e_prod_price, self._e_prod_stock, self._e_prod_qty):
            e.config(state="normal")
            e.delete(0, END)

        self._e_prod_name.insert(0, product_name)
        self._e_prod_weight.insert(0, product_weight)
        self._e_prod_price.insert(0, product_price)
        self._e_prod_stock.insert(0, available)

        self._e_prod_name.config(state="disabled")
        self._e_prod_weight.config(state="disabled")
        self._e_prod_price.config(state="disabled", foreground="green")
        self._e_prod_stock.config(state="disabled")

        if available == 0:
            self._e_prod_qty.insert(0, "Stock is empty")
            self._e_prod_qty.config(state="disabled")
            self._btn_add_product.config(state="disabled")
        else:
            self._btn_add_product.config(state="normal")

    def _add_product(self):
        name  = self._e_prod_name.get()
        price = self._e_prod_price.get()
        stock = self._e_prod_stock.get()
        qty   = self._e_prod_qty.get()

        if not name:
            messagebox.showerror("Product Error", "Please choose a product.")
            return

        try:
            int_qty   = int(qty)
            float_price = float(price)
        except ValueError:
            self._e_prod_qty.delete(0, END)
            messagebox.showerror("Quantity Error", "Input a valid quantity.")
            return

        try:
            available = int(stock)
        except ValueError:
            available = 0

        if int_qty > available:
            self._e_prod_qty.delete(0, END)
            messagebox.showerror(
                "Product Error",
                "Stock is not enough. Please get more stock for this product.",
            )
            return

        total_cost = float_price * int_qty
        InvoiceItemModel.add(name, float_price, int_qty, total_cost)
        self._refresh_invoice_treeview()

        # Reset product fields
        for e in (self._e_prod_name, self._e_prod_weight,
                  self._e_prod_price, self._e_prod_stock):
            e.config(state="normal")
            e.delete(0, END)
            e.config(state="disabled")
        self._e_prod_qty.delete(0, END)

        # Enable action buttons now that items exist
        self._btn_delete.config(state="normal")
        self._btn_delete_all.config(state="normal")
        self._e_discount.config(state="normal")
        self._btn_get_net.config(state="normal")

    # ── Customer section ──────────────────────────────────────────────────────

    def _build_customer_section(self, frame, w):
        self._e_cust_search = w.entry(frame, "Customer code", 0, 0, w._font_size * 2)
        self._btn_add_cust  = w.button(
            frame, "Add Customer", 1, 1, W + E, command=self._add_customer)

        self._e_cust_code    = w.entry(frame, "Code",    2, 0, w._font_size * 2, state="disabled")
        self._e_cust_name    = w.entry(frame, "Name",    3, 0, w._font_size * 2, state="disabled")
        self._e_cust_phone   = w.entry(frame, "Phone",   4, 0, w._font_size * 2, state="disabled")
        self._e_cust_address = w.entry(frame, "Address", 5, 0, w._font_size * 2, state="disabled")

    def _add_customer(self):
        code_str = self._e_cust_search.get().strip()
        if not code_str:
            messagebox.showerror("Error", "Please input a valid code.")
            return

        try:
            code = int(code_str)
        except ValueError:
            self._e_cust_search.delete(0, END)
            messagebox.showerror(
                "Code Error",
                "Please input a valid customer code (numbers only).",
            )
            return

        from app.models.customer import CustomerModel
        rows = CustomerModel.get_by_code(code)
        if not rows:
            messagebox.showerror(
                "Index Error",
                "No customer found with this code. Please try again.",
            )
            return

        row = rows[0]
        # row: (ID, customer_code, first_name, last_name, address, phone) – adapt to actual schema
        # The DB schema is: ID, customer_code, first_name, last_name, address, phone (from original)
        self._customer_id  = row[0]
        cust_code    = row[1]
        cust_name    = f"{row[2]} {row[3]}"
        cust_phone   = row[5]
        cust_address = row[4]

        for e in (self._e_cust_code, self._e_cust_name,
                  self._e_cust_phone, self._e_cust_address):
            e.config(state="normal")
            e.delete(0, END)

        self._e_cust_code.insert(0, cust_code)
        self._e_cust_name.insert(0, cust_name)
        self._e_cust_phone.insert(0, cust_phone)
        self._e_cust_address.insert(0, cust_address)

        for e in (self._e_cust_code, self._e_cust_name,
                  self._e_cust_phone, self._e_cust_address):
            e.config(state="disabled")

    # ── Invoice list section ──────────────────────────────────────────────────

    def _build_invoice_section(self, frame, d, r):
        w = self._w

        # Treeview
        self._trv = ttk.Treeview(
            frame, columns=(1, 2, 3, 4, 5),
            show="headings",
            height=int(0.01250 * d),
            padding=5,
            style="Custom.Treeview",
        )
        self._trv.grid(row=0, column=0, columnspan=2, sticky=NSEW)

        for col, header, width_frac in (
            (1, "ID",         0.060),
            (2, "Product",    0.125),
            (3, "Price",      0.100),
            (4, "Quantity",   0.080),
            (5, "Total Cost", 0.125),
        ):
            self._trv.heading(col, text=header)
            self._trv.column(col, anchor=CENTER, width=int(width_frac * r))

        # Live clock
        self._clock_label = Label(
            frame, font=("Verdana", w._font_size, "bold"), foreground="#e4324c",
        )
        self._clock_label.grid(row=10, column=1, sticky=E)
        self._tick_clock()

        # Action buttons (initially disabled)
        self._btn_delete = w.button(
            frame, "Delete Product", 1, 0, W + E,
            state="disabled", command=self._delete_product,
        )
        self._btn_delete_all = w.button(
            frame, "Delete All Products", 1, 1, W + E,
            state="disabled", command=self._delete_all,
        )

        # Total amount display
        self._e_total = w.entry(frame, "Total Amount", 2, 0, 30, state="disabled")

        # Discount
        self._e_discount = w.entry(frame, "Discount (%)", 3, 0, 30, state="disabled")
        self._btn_get_net = w.button(
            frame, "Get Net Amount", 4, 1, W + E,
            state="disabled", command=self._apply_discount,
        )

        # Net amount
        self._e_net = w.entry(frame, "Net Amount", 5, 0, 30, state="disabled")

        # Payment
        self._e_payment = w.entry(frame, "Payment Amount", 6, 0, 30, state="disabled")
        self._btn_add_payment = w.button(
            frame, "Add Payment", 7, 1, W + E,
            state="disabled", command=self._add_payment,
        )

        # Due amount
        self._e_due = w.entry(frame, "Due Amount", 8, 0, 30, state="disabled")

        # Save / Print buttons
        self._btn_save = w.button(
            frame, "Save Invoice", 9, 0, W + E,
            state="disabled", command=self._save_invoice,
        )
        self._btn_print = w.button(
            frame, "Generate PDF Invoice", 9, 1, W + E,
            state="disabled", command=self._print_invoice,
        )

    # ── Invoice treeview helpers ──────────────────────────────────────────────

    def _refresh_invoice_treeview(self):
        self._trv.delete(*self._trv.get_children())
        items = InvoiceItemModel.get_all()
        for idx, item in enumerate(items):
            name, price, qty, total = item
            self._trv.insert("", "end", values=(idx + 1, name, price, qty, total))

        raw = InvoiceItemModel.get_total()
        self._raw_total = raw
        self._e_total.config(state="normal")
        self._e_total.delete(0, END)
        self._e_total.insert(0, f"{raw:.2f}")
        self._e_total.config(state="disabled", foreground="green")

    # ── Invoice actions ───────────────────────────────────────────────────────

    def _delete_product(self):
        try:
            iid  = self._trv.selection()[0]
            name = self._trv.item(iid)["values"][1]
        except IndexError:
            messagebox.showerror("Selection Error", "You didn't select any product from the list.")
            return

        InvoiceItemModel.delete_by_name(name)
        self._refresh_invoice_treeview()

    def _delete_all(self):
        InvoiceItemModel.clear()
        self._refresh_invoice_treeview()

    def _apply_discount(self):
        discount_str = self._e_discount.get().strip()
        raw = self._raw_total

        try:
            if not discount_str:
                net = raw
                pct = 0.0
            else:
                pct = float(discount_str)
                if not (0.0 <= pct <= 100.0):
                    self._e_discount.delete(0, END)
                    messagebox.showerror(
                        "Discount Error",
                        "Discount cannot be more than 100 or less than 0.",
                    )
                    return
                net = raw * (1 - pct / 100.0)
        except ValueError:
            self._e_discount.delete(0, END)
            messagebox.showerror("Discount Error", "Please give a valid discount percentage.")
            return

        self._net_total     = net
        self._discount_rate = pct

        self._e_net.config(state="normal")
        self._e_net.delete(0, END)
        self._e_net.insert(0, f"{net:.2f}")
        self._e_net.config(state="disabled", foreground="green")

        # Enable payment step
        self._e_payment.config(state="normal")
        self._btn_add_payment.config(state="normal")

    def _add_payment(self):
        payment_str = self._e_payment.get().strip()

        if not payment_str:
            self._e_payment.delete(0, END)
            messagebox.showerror("Payment Error", "Please input a valid payment amount.")
            return

        try:
            payment = float(payment_str)
        except ValueError:
            self._e_payment.delete(0, END)
            messagebox.showerror("Payment Error", "The payment amount is invalid.")
            return

        if payment < 0.0 or payment > self._net_total:
            self._e_payment.delete(0, END)
            messagebox.showerror(
                "Payment Error",
                "Payment cannot be more than the net total or less than 0.",
            )
            return

        self._payment_amount = payment
        due = self._net_total - payment
        self._due_amount = due

        self._e_due.config(state="normal")
        self._e_due.delete(0, END)
        self._e_due.insert(0, f"{due:.2f}")
        self._e_due.config(state="disabled", foreground="red")

        self._btn_save.config(state="normal")

    def _save_invoice(self):
        if self._customer_id is None:
            messagebox.showerror("Customer Error", "Please insert customer information.")
            return

        items = InvoiceItemModel.get_product_ids_and_quantities()
        if not items:
            messagebox.showerror("Invoice Error", "The invoice has no items.")
            return

        # Build sale code from current time
        tz = pytz.timezone("asia/dhaka")
        sale_code = datetime.now(tz).strftime("%Y%m%d%H%M%S")

        # Discount info for PDF/display
        discount_amount  = f"{self._raw_total - self._net_total:.2f}"
        self._discount_amount = discount_amount
        discount_pct_int = int(
            (self._raw_total - self._net_total) / self._raw_total * 100
            if self._raw_total else 0
        )
        self._discount_rate = discount_pct_int

        # Previous due for this customer
        previous_due  = SaleModel.get_customer_previous_due(self._customer_id)
        total_payable = self._due_amount + previous_due

        self._previous_due    = f"{previous_due:.2f}"
        self._total_payable   = f"{total_payable:.2f}"

        if not messagebox.askyesno(
            "Confirm Sale",
            "Are you sure to save this sale? After saving you cannot change. "
            "Make sure you are aware of what you are doing.",
        ):
            return

        SaleModel.add(
            sale_code,
            self._customer_id,
            float(self._net_total),
            float(self._payment_amount),
            float(self._due_amount),
            items,
        )

        self._sale_code  = sale_code

        messagebox.showinfo(
            "Save Success",
            f"Sale saved successfully. Invoice number: {sale_code}.",
        )

        # Notify other views
        self._ctrl.on_sale_made()

        # Partially reset form: disable add actions, enable print
        self._sale_saved = True
        self._btn_save.config(state="disabled")
        self._btn_print.config(state="normal")
        self._btn_add_product.config(state="disabled")
        self._btn_add_cust.config(state="disabled")
        self._btn_delete.config(state="disabled")
        self._btn_delete_all.config(state="disabled")
        self._btn_get_net.config(state="disabled")
        self._btn_add_payment.config(state="disabled")

    def _print_invoice(self):
        if not self._sale_code:
            return

        sale_date = SaleModel.get_date(self._sale_code)
        product_list = SaleModel.get_products_for_sale(self._sale_code)

        # Fetch customer info directly from customer entries (already loaded)
        cust_code    = self._e_cust_code.get()
        cust_name    = self._e_cust_name.get()
        cust_phone   = self._e_cust_phone.get()
        cust_address = self._e_cust_address.get()

        create_invoice(
            self._sale_code,
            sale_date,
            cust_code,
            cust_name,
            cust_phone,
            cust_address,
            product_list,
            self._raw_total,
            self._discount_rate,
            self._discount_amount,
            self._net_total,
            self._payment_amount,
            self._due_amount,
            self._previous_due,
            self._total_payable,
        )

        # Full reset
        InvoiceItemModel.clear()
        self._reset_all()

    # ── Reset / helpers ───────────────────────────────────────────────────────

    def _reset_all(self):
        """Clear all fields and disable action buttons, ready for next invoice."""
        self._net_total      = 0.0
        self._due_amount     = 0.0
        self._raw_total      = 0.0
        self._customer_id    = None
        self._sale_code      = None
        self._discount_rate  = 0.0
        self._discount_amount = "0.00"
        self._payment_amount = 0.0
        self._previous_due   = "0.00"
        self._total_payable  = "0.00"
        self._sale_saved     = False

        # Clear invoice treeview + total
        self._refresh_invoice_treeview()

        # Reset product fields
        self._product_combo.set("Choose one...")
        for e in (self._e_prod_name, self._e_prod_weight,
                  self._e_prod_price, self._e_prod_stock):
            e.config(state="normal")
            e.delete(0, END)
            e.config(state="disabled")
        self._e_prod_qty.delete(0, END)

        # Reset customer fields
        self._e_cust_search.delete(0, END)
        for e in (self._e_cust_code, self._e_cust_name,
                  self._e_cust_phone, self._e_cust_address):
            e.config(state="normal")
            e.delete(0, END)
            e.config(state="disabled")

        # Reset amount fields
        self._e_discount.delete(0, END)
        self._e_net.config(state="normal")
        self._e_net.delete(0, END)
        self._e_net.config(state="disabled")
        self._e_payment.delete(0, END)
        self._e_due.config(state="normal")
        self._e_due.delete(0, END)
        self._e_due.config(state="disabled")

        # Re-disable all action buttons
        for btn in (
            self._btn_add_product, self._btn_add_cust,
            self._btn_delete, self._btn_delete_all,
            self._btn_get_net, self._btn_add_payment,
            self._btn_save, self._btn_print,
        ):
            btn.config(state="disabled")

        # Re-enable search buttons
        self._btn_add_cust.config(state="normal")

        # Refresh product combo with current products
        self._product_combo["values"] = ProductModel.get_all_names()

    # ── Clock ─────────────────────────────────────────────────────────────────

    def _tick_clock(self):
        self._clock_label.config(text=strftime("%H:%M:%S %p"))
        self._clock_label.after(1000, self._tick_clock)
