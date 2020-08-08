from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import os
import sqlite3
from random import randint

from reportlab.pdfgen import canvas

root = Tk()
root.title("Business Management")
right = root.winfo_screenwidth()  # 1280  #
down = root.winfo_screenheight()  # 720  #
# root.geometry(f"{right}x{down}")
# root.geometry(f"{right}x{down}")


#------------------------ Default width and height --------------------------------#

entryWidth = int(0.01342*float(right))


fontSize = int(0.00829*float(right))


# width = root.winfo_width()
# height = root.winfo_height()
x = (root.winfo_screenwidth() // 2) - (right // 2)
y = (root.winfo_screenheight() // 2) - (down // 2)
root.geometry(f"{right}x{down}+{x}+{y}")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "main.db")
icon_path = os.path.join(BASE_DIR, "b.ico")

root.iconbitmap(icon_path)

conn = sqlite3.connect(db_path)

cursor = conn.cursor()


#------------------------ Default Frame Function ----------------------------------------#


def defaultFrame(parent, caption, row, column, **options):
    frame = LabelFrame(parent, text=caption, padx=20,
                       pady=20, font=f"Courier {fontSize} bold")
    frame.grid(row=row, column=column, padx=20, pady=20, **options, sticky=W+E)
    return frame

#------------------------ Default Entry Function ----------------------------------------#


def defaultEntry(parent, caption, row, column, width, **options):
    Label(parent, text=caption + ": ",
          font=f"Courier {fontSize} bold").grid(row=row, column=column, sticky=E)
    entry = ttk.Entry(parent, width=width, justify=RIGHT,
                      font=f"Courier {fontSize} bold", **options)
    entry.grid(row=row, column=column + 1, pady=5, sticky=W+E)
    return entry


#------------------------ Default Button Function ----------------------------------------#


def defaultButton(parent, caption, row, column, sticky, **options):
    ttk.Style().configure(
        "TButton", font=f"Courier {fontSize} bold", **options)
    button = ttk.Button(parent, text=caption,
                        **options)
    button.grid(row=row, column=column, pady=10, sticky=sticky)


#------------------------ Creating notebook --------------------------------#

noteStyler = ttk.Style()

# Import the Notebook.tab element from the default theme
noteStyler.element_create('Plain.Notebook.tab', "from", 'default')
# Redefine the TNotebook Tab layout to use the new element
noteStyler.layout("TNotebook.Tab",
                  [('Plain.Notebook.tab', {'children':
                                           [('Notebook.padding', {'side': 'top', 'children':
                                                                  [('Notebook.focus', {'side': 'top', 'children':
                                                                                       [('Notebook.label', {
                                                                                         'side': 'top', 'sticky': ''})],
                                                                                       'sticky': 'nswe'})],
                                                                  'sticky': 'nswe'})],
                                           'sticky': 'nswe'})])

noteStyler.configure("TNotebook", background="#161C22",
                     tabposition='wn', tabmargins=[0, 0, 0, 0])

noteStyler.configure("TNotebook.Tab", background="#204051", width=12, foreground="white", relief=GROOVE, font=(
    "times", int(0.00829*float(right))),  padding=[10, 10, 10, 10])

noteStyler.map("TNotebook.Tab", background=[
               ("selected", "#006a71")], foreground=[("selected", "white")])


notebook = ttk.Notebook(root, padding=0)
notebook.pack(fill="both", expand=1)

homeFrame = Frame(notebook, width=right, height=down,
                  pady=5, padx=10)
homeFrame.pack(fill="both", expand=1)

customerFrame = Frame(notebook, width=right, height=down, pady=10)
customerFrame.pack(fill="both", expand=1)

productFrame = Frame(notebook, width=right, height=down, pady=10)
productFrame.pack(fill="both", expand=1)

stockFrame = Frame(notebook, width=right, height=down, pady=10)
stockFrame.pack(fill="both", expand=1)

saleFrame = Frame(notebook, width=right, height=down, pady=10)
saleFrame.pack(fill="both", expand=1)

dueFrame = Frame(notebook, width=right, height=down, pady=10)
dueFrame.pack(fill="both", expand=1)


#notebook.place(relx=0, rely=0, relheight=1, relwidth=1)

notebook.add(homeFrame, text="Billings")
notebook.add(customerFrame, text="Customers")
notebook.add(productFrame, text="Products")
notebook.add(stockFrame, text="Stocks")
notebook.add(saleFrame, text="Sales")
notebook.add(dueFrame, text="Dues")


style = ttk.Style()
style.element_create("Custom.Treeheading.border", "from", "default")
style.layout("Custom.Treeview.Heading", [
    ("Custom.Treeheading.cell", {'sticky': 'nswe'}),
    ("Custom.Treeheading.border", {'sticky': 'nswe', 'children': [
        ("Custom.Treeheading.padding", {'sticky': 'nswe', 'children': [
            ("Custom.Treeheading.image", {
                'side': 'right', 'sticky': ''}),
            ("Custom.Treeheading.text", {'sticky': 'we'})
        ]})
    ]}),
])

style.configure("Custom.Treeview.Heading",
                background="#006a71", foreground="#fff", relief="flat", font=(
                    "times", fontSize), padding=5)
style.map("Custom.Treeview.Heading",
          relief=[('active', 'groove'), ('pressed', 'sunken')])

style.configure("Custom.Treeview", font=(
    "Verdana", int(0.0067*float(right))), rowheight=int(0.015625*float(right)))


"""


Sales Start


"""

SalesList_Frame_sales = defaultFrame(saleFrame, "Sales List", 0, 0)


def UpdateSalesList_sales():

    trv_sales = ttk.Treeview(SalesList_Frame_sales, columns=(1, 2, 3, 4, 5, 6, 7),
                             show="headings", height=int(0.02000*float(down)), padding=5, style="Custom.Treeview")
    trv_sales.grid(row=0, column=0)

    trv_sales.heading(1, text='Sale Code')
    trv_sales.heading(2, text='Customer Name')
    trv_sales.heading(3, text='Customer Phone')
    trv_sales.heading(4, text='Net Amount')
    trv_sales.heading(5, text='Paid Amount')
    trv_sales.heading(6, text='Due Amount')
    trv_sales.heading(7, text='Date Added')

    trv_sales.column(1, anchor=CENTER,
                     width=int(0.1000*float(right)))
    trv_sales.column(2, anchor=CENTER,
                     width=int(0.1250*float(right)))
    trv_sales.column(3, anchor=CENTER,
                     width=int(0.1500*float(right)))
    trv_sales.column(4, anchor=CENTER,
                     width=int(0.1000*float(right)))
    trv_sales.column(5, anchor=CENTER,
                     width=int(0.1000*float(right)))
    trv_sales.column(6, anchor=CENTER,
                     width=int(0.1000*float(right)))
    trv_sales.column(7, anchor=CENTER,
                     width=int(0.1500*float(right)))

    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()

    cursor.execute("select sales.sale_code, customers.first_name, customers.phone, sales.sale_amount, sales.paid_amount, sales.due_amount, sales.created_at from sales inner join customers on sales.customer_id = customers.ID order by sales.created_at desc")
    sales_tuple_list = cursor.fetchall()

    for i in sales_tuple_list:
        trv_sales.insert("", "end", values=i)

    conn.commit()

    conn.close()


def salesSearch_sales():
    SalesSearch_Frame_sales = defaultFrame(
        saleFrame, "Search by Customer's Name, Phone number, Sale Code or Date", 1, 0)

    Label(SalesSearch_Frame_sales, text="Search Sales: ",
          font=f"Courier {fontSize} bold").grid(row=0, column=0, sticky=E)
    searchSales_Entry_sales = ttk.Entry(SalesSearch_Frame_sales, width=entryWidth*5, justify=RIGHT,
                                        font=f"Courier {fontSize} bold")
    searchSales_Entry_sales.grid(
        row=0, column=1, pady=5, sticky=W+E, columnspan=2)

    def searchSales_List_sales():

        trv_sales = ttk.Treeview(SalesList_Frame_sales, columns=(1, 2, 3, 4, 5, 6, 7),
                                 show="headings", height=int(0.02000*float(down)), padding=5, style="Custom.Treeview")
        trv_sales.grid(row=0, column=0)

        trv_sales.heading(1, text='Sale Code')
        trv_sales.heading(2, text='Customer Name')
        trv_sales.heading(3, text='Customer Phone')
        trv_sales.heading(4, text='Net Amount')
        trv_sales.heading(5, text='Paid Amount')
        trv_sales.heading(6, text='Due Amount')
        trv_sales.heading(7, text='Date Added')

        trv_sales.column(1, anchor=CENTER,
                         width=int(0.1000*float(right)))
        trv_sales.column(2, anchor=CENTER,
                         width=int(0.1250*float(right)))
        trv_sales.column(3, anchor=CENTER,
                         width=int(0.1500*float(right)))
        trv_sales.column(4, anchor=CENTER,
                         width=int(0.1000*float(right)))
        trv_sales.column(5, anchor=CENTER,
                         width=int(0.1000*float(right)))
        trv_sales.column(6, anchor=CENTER,
                         width=int(0.1000*float(right)))
        trv_sales.column(7, anchor=CENTER,
                         width=int(0.1500*float(right)))

        conn = sqlite3.connect(db_path)

        cursor = conn.cursor()

        query = searchSales_Entry_sales.get()

        cursor.execute(
            f"select sales.sale_code, customers.first_name, customers.phone, sales.sale_amount, sales.paid_amount, sales.due_amount, sales.created_at from sales inner join customers on sales.customer_id = customers.ID where sales.sale_code like '%{query}%' or customers.first_name like '%{query}%' or customers.phone like '%{query}%' or sales.created_at like '%{query}%' order by sales.created_at desc")
        sales_tuple_list = cursor.fetchall()

        for i in sales_tuple_list:
            trv_sales.insert("", "end", values=i)

        conn.commit()

        conn.close()

    searchSales_Button_sales = defaultButton(
        SalesSearch_Frame_sales, "Search", 1, 2, W+E, command=searchSales_List_sales)

    def resetSales_List_sales():
        UpdateSalesList_sales()

    resetSales_Button_sales = defaultButton(
        SalesSearch_Frame_sales, "Reset", 1, 1, W+E, command=resetSales_List_sales)


UpdateSalesList_sales()
salesSearch_sales()
"""


Sales END


"""


"""


Home Start


"""


#------------------------ Product adding Frame --------------------------------#

productAddFrame_Home = defaultFrame(homeFrame, "Add Product to Invoice", 0, 0)


def UpdateHomeAddProduct_Frame():

    def getAllProducts():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        PRODUCTS = []
        cursor.execute("select product from products")
        products = cursor.fetchall()
        for product in products:
            PRODUCTS.append(product[0])
        conn.commit()
        conn.close()
        return PRODUCTS

    def productCombo(event):
        productNameEntry_home.config(state="enabled")
        productWeightEntry_home.config(state="enabled")
        productPriceEntry_home.config(state="enabled")
        productStockEntry_home.config(state="enabled")
        productQuantityEntry_home.config(state="enabled")

        productNameEntry_home.delete(0, END)
        productWeightEntry_home.delete(0, END)
        productPriceEntry_home.delete(0, END)
        productStockEntry_home.delete(0, END)
        productQuantityEntry_home.delete(0, END)

        product = productCombo_home.get()

        conn = sqlite3.connect(db_path)

        cursor = conn.cursor()

        cursor.execute(
            f"select product, weight, price from products where product='{product}'")
        product_details = cursor.fetchall()
        product_name = product_details[0][0]
        product_weight = product_details[0][1]
        product_price = product_details[0][2]

        cursor.execute(f"select ID from products where product='{product}'")
        product_ID = cursor.fetchall()[0][0]

        cursor.execute(
            f"select sum(quantity) from stocks_removed where product_ID = {int(product_ID)}")
        product_stock_removed = cursor.fetchall()[0][0]

        if product_stock_removed == None:
            product_stock_removed = 0

        cursor.execute(
            f"select sum(Quantity) from stocks where product_id = {int(product_ID)}")
        product_stock_updated = cursor.fetchall()[0][0]
        if product_stock_updated == None:
            product_stock_updated = 0

        product_stock = int(product_stock_updated) - int(product_stock_removed)
        if product_stock < 0:
            product_stock = 0

        if product_stock == 0:
            productQuantityEntry_home.insert(0, "Stock is empty")
            productQuantityEntry_home.config(state="disabled")

        productNameEntry_home.insert(0, product_name)
        productWeightEntry_home.insert(0, product_weight)
        productPriceEntry_home.insert(0, product_price)
        productStockEntry_home.insert(0, product_stock)

        productNameEntry_home.config(state="disabled")
        productWeightEntry_home.config(state="disabled")
        productPriceEntry_home.config(state="disabled", foreground="green")
        productStockEntry_home.config(state="disabled")

        conn.commit()

        conn.close()

    allProducts = getAllProducts()
    choose_product_label = Label(productAddFrame_Home, text="Product:",
                                 font=f"Courier {fontSize} bold").grid(row=0, column=0, sticky=E, padx=10)
    productCombo_home = ttk.Combobox(productAddFrame_Home, value=allProducts, width=entryWidth,
                                     font=f"Courier {fontSize} bold")
    productCombo_home.set("Choose one...")
    productCombo_home.bind("<<ComboboxSelected>>", productCombo)
    productCombo_home.grid(row=0, column=1, pady=5)

    productNameEntry_home = defaultEntry(
        productAddFrame_Home, "Name", 1, 0, entryWidth, state="disabled")
    productWeightEntry_home = defaultEntry(
        productAddFrame_Home, "Weight (g)", 2, 0, entryWidth, state="disabled")
    productPriceEntry_home = defaultEntry(
        productAddFrame_Home, "Price (BDT)", 3, 0, entryWidth, state="disabled")
    productQuantityEntry_home = defaultEntry(
        productAddFrame_Home, "Quantity", 5, 0, entryWidth)

    productStockEntry_home = defaultEntry(
        productAddFrame_Home, "Stock Available", 4, 0, entryWidth, state="disabled")

    def getTrvTotal_home():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("select total_cost from invoice_items")
        totalPriceForALLItems = 0.0
        TOTAL_PRICE_LIST = cursor.fetchall()
        for i in TOTAL_PRICE_LIST:
            totalPriceForALLItems += float(i[0])

        conn.commit()
        conn.close()
        return totalPriceForALLItems

    def getNetTotal_home(NT):
        global net_total_home
        net_total_home = NT
        return net_total_home

    def getDueAmount_home(DA):
        global due_amount_home
        due_amount_home = DA
        return due_amount_home

    def getCustomerID_home():

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        customer_code = customerCodeEntry_home.get()

        cursor.execute(
            f"select ID from customers where customer_code={customer_code}")
        customer_ID = cursor.fetchall()

        conn.commit()
        conn.close()

        return customer_ID[0][0]

    #------------------------ Customer Add Frame ------------------------#

    customerAddFrame_home = defaultFrame(
        homeFrame, "Add Customer to Invoice", 1, 0)

    def addCustomer_home():
        # lbl = Label(root, text=myCombo.get()).grid(row=row, column=column+2)

        customer_code_home = CustomerSearchCode_home.get()

        if customer_code_home == "":
            messagebox.showerror(title="Error Code.",
                                 message="Please input a valid code")
            CustomerSearchCode_home.delete(0, END)

            customerCodeEntry_home.config(state="disabled")
            customerNameEntry_home.config(state="disabled")
            customerPhoneEntry_home.config(state="disabled")
            customerAddressEntry_home.config(state="disabled")
        else:

            customerCodeEntry_home.config(state="enabled")
            customerNameEntry_home.config(state="enabled")
            customerPhoneEntry_home.config(state="enabled")
            customerAddressEntry_home.config(state="enabled")

            customerCodeEntry_home.delete(0, END)
            customerNameEntry_home.delete(0, END)
            customerPhoneEntry_home.delete(0, END)
            customerAddressEntry_home.delete(0, END)

            try:
                integerCode = int(customer_code_home)
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()

                    cursor.execute(
                        f"select customer_code, first_name, last_name, phone, address from customers where customer_code={integerCode}")
                    customer_details = cursor.fetchall()

                    customer_code = customer_details[0][0]
                    customer_first_name = customer_details[0][1]
                    customer_last_name = customer_details[0][2]
                    customer_name = f"{customer_first_name} {customer_last_name}"
                    customer_phone = customer_details[0][3]
                    customer_address = customer_details[0][4]

                    customerCodeEntry_home.insert(0, customer_code)
                    customerNameEntry_home.insert(0, customer_name)
                    customerPhoneEntry_home.insert(0, customer_phone)
                    customerAddressEntry_home.insert(0, customer_address)

                    customerCodeEntry_home.config(state="disabled")
                    customerNameEntry_home.config(state="disabled")
                    customerPhoneEntry_home.config(state="disabled")
                    customerAddressEntry_home.config(state="disabled")

                    conn.commit()

                    conn.close()

                except Exception as identifier:

                    customerCodeEntry_home.config(state="disabled")
                    customerNameEntry_home.config(state="disabled")
                    customerPhoneEntry_home.config(state="disabled")
                    customerAddressEntry_home.config(state="disabled")
                    messagebox.showerror(
                        title="Index Error", message="The customer with this code is not found. Try again.")

            except ValueError as e:
                CustomerSearchCode_home.delete(0, END)

                customerCodeEntry_home.config(state="disabled")
                customerNameEntry_home.config(state="disabled")
                customerPhoneEntry_home.config(state="disabled")
                customerAddressEntry_home.config(state="disabled")

                messagebox.showerror(
                    title="Code Error", message="Please input a valid customer code with number. Not alphabet.")

    CustomerSearchCode_home = defaultEntry(
        customerAddFrame_home, "Customer code", 0, 0, entryWidth)
    addCustomerButton_home = defaultButton(
        customerAddFrame_home, "Add Customer", 1, 1, W+E, command=addCustomer_home)

    customerCodeEntry_home = defaultEntry(
        customerAddFrame_home, "Code", 2, 0, entryWidth)
    customerNameEntry_home = defaultEntry(
        customerAddFrame_home, "Name", 3, 0, entryWidth)
    customerPhoneEntry_home = defaultEntry(
        customerAddFrame_home, "Phone", 4, 0, entryWidth)
    customerAddressEntry_home = defaultEntry(
        customerAddFrame_home, "Address", 5, 0, entryWidth)

    customerCodeEntry_home.config(state="disabled")
    customerNameEntry_home.config(state="disabled")
    customerPhoneEntry_home.config(state="disabled")
    customerAddressEntry_home.config(state="disabled")

    def showProduct_trv_home():

        name = productNameEntry_home.get()
        price = productPriceEntry_home.get()
        quantity = productQuantityEntry_home.get()
        stock = productStockEntry_home.get()

        if name == "":
            messagebox.showerror(title="Product Error",
                                 message="Please Choose a product.")
        else:
            try:
                def InsertInTreeView():

                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()

                    cursor.execute("insert into invoice_items values(:name, :price, :quantity, :total_cost)",
                                   {
                                       "name": name,
                                       "price": float(price),
                                       "quantity": int(quantity),
                                       "total_cost": amount_home
                                   }
                                   )

                    conn.commit()
                    conn.close()

                def UpdateTreeView():

                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()

                    cursor.execute("select * from invoice_items")
                    PRODUCTS_LIST = cursor.fetchall()
                    for i in PRODUCTS_LIST:
                        trv_home.insert("", "end", values=i)

                    conn.commit()
                    conn.close()

                trv_home = ttk.Treeview(productsListFrame_home, columns=(1, 2, 3, 4),
                                        show="headings", height=int(0.0070*float(right)), padding=5, style="Custom.Treeview")
                trv_home.grid(row=0, column=0, columnspan=2)

                trv_home.heading(1, text='Product')
                trv_home.heading(2, text='Price')
                trv_home.heading(3, text='Quanity')
                trv_home.heading(4, text='Amount')
                trv_home.column(1, anchor=CENTER,
                                width=int(0.1250*float(right)))
                trv_home.column(2, anchor=CENTER,
                                width=int(0.1250*float(right)))
                trv_home.column(3, anchor=CENTER,
                                width=int(0.1250*float(right)))
                trv_home.column(4, anchor=CENTER,
                                width=int(0.1250*float(right)))
                integerQuantity = int(quantity)

                if integerQuantity > int(stock):
                    productQuantityEntry_home.delete(0, END)
                    messagebox.showerror(title="Product Error",
                                         message="Stock is not enough. Please get more stock for this product.")
                else:

                    amount_home = float(price) * integerQuantity
                    InsertInTreeView()
                    UpdateTreeView()

                    productNameEntry_home.config(state="enabled")
                    productWeightEntry_home.config(state="enabled")
                    productPriceEntry_home.config(state="enabled")
                    productStockEntry_home.config(state="enabled")

                    productNameEntry_home.delete(0, END)
                    productWeightEntry_home.delete(0, END)
                    productPriceEntry_home.delete(0, END)
                    productStockEntry_home.delete(0, END)
                    productQuantityEntry_home.delete(0, END)
                    totalAmountEntry_home = defaultEntry(
                        productsListFrame_home, "Total Amount", 2, 0, 30)

                    totalAmountEntry_home.insert(0, getTrvTotal_home())
                    totalAmountEntry_home.config(
                        state="disabled", foreground="green")

                    def deleteProduct():
                        try:
                            selectedProductIID = trv_home.selection()[0]
                            name = trv_home.item(selectedProductIID)[
                                "values"][0]

                            conn = sqlite3.connect(db_path)
                            cursor = conn.cursor()
                            cursor.execute(
                                f"select oid from invoice_items where name='{name}'")
                            rowid = cursor.fetchall()[0][0]

                            conn.commit()

                            cursor.execute(
                                f"DELETE FROM invoice_items WHERE oid={rowid}")

                            conn.commit()

                            conn.close()

                            trv_home.delete(*trv_home.get_children())

                            UpdateTreeView()
                            totalAmountEntry_home.config(state="enabled")
                            totalAmountEntry_home.delete(0, END)
                            totalAmountEntry_home.insert(0, getTrvTotal_home())
                            totalAmountEntry_home.config(
                                state="disabled", foreground="green")

                        except Exception as e:
                            messagebox.showerror(
                                title="Selection error", message="You didn't select any product from the list.")

                            trv_home.delete(*trv_home.get_children())

                            UpdateTreeView()
                            totalAmountEntry_home.config(state="enabled")
                            totalAmountEntry_home.delete(0, END)
                            totalAmountEntry_home.insert(0, getTrvTotal_home())
                            totalAmountEntry_home.config(
                                state="disabled", foreground="green")

                    def deleteAll():

                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()

                        cursor.execute(
                            f"DELETE FROM invoice_items")

                        conn.commit()

                        conn.close()

                        trv_home.delete(*trv_home.get_children())

                        UpdateTreeView()
                        totalAmountEntry_home.config(state="enabled")
                        totalAmountEntry_home.delete(0, END)
                        totalAmountEntry_home.insert(0, getTrvTotal_home())
                        totalAmountEntry_home.config(
                            state="disabled", foreground="green")

                    def applyDiscount():
                        discount_percentage = discountEntry_home.get()
                        try:
                            totalAmount_trv_home = getTrvTotal_home()
                            float_discount_percentage = 0.0

                            if discount_percentage == "":
                                net_total = totalAmount_trv_home

                                netAmountEntry_home.config(state="enabled")
                                netAmountEntry_home.delete(0, END)
                                netAmountEntry_home.insert(0, net_total)
                                netAmountEntry_home.config(
                                    state="disabled", foreground="green")

                                getNetTotal_home(net_total)

                            elif discount_percentage == 0:
                                net_total = totalAmount_trv_home

                                netAmountEntry_home.config(state="enabled")
                                netAmountEntry_home.delete(0, END)
                                netAmountEntry_home.insert(0, net_total)
                                netAmountEntry_home.config(
                                    state="disabled", foreground="green")

                                getNetTotal_home(net_total)

                            else:
                                float_discount_percentage = float(
                                    discount_percentage)
                                if float_discount_percentage > 100.0:
                                    discountEntry_home.delete(0, END)
                                    messagebox.showerror(
                                        title="Discount Error", message="The discount ammount cannot be more than 100.")
                                else:
                                    fraction_discount_percentage = (
                                        float_discount_percentage / 100.0)
                                    net_total = (totalAmount_trv_home - (totalAmount_trv_home *
                                                                         fraction_discount_percentage))
                                    formatted_net_total = "{:.2f}".format(
                                        net_total)

                                    getNetTotal_home(formatted_net_total)

                                    netAmountEntry_home.config(state="enabled")
                                    netAmountEntry_home.delete(0, END)
                                    netAmountEntry_home.insert(
                                        0, formatted_net_total)
                                    netAmountEntry_home.config(
                                        state="disabled", foreground="green")

                        except ValueError as identifier:
                            discountEntry_home.delete(0, END)
                            messagebox.showerror(
                                title="Discount Error", message="Please give a valid discount percentage.")

                    def addPayment():

                        payment_amount = paymentEntry_home.get()
                        try:
                            net_total = float(net_total_home)
                            float_payment_amount = 0.0

                            if payment_amount == "":
                                paymentEntry_home.delete(0, END)
                                messagebox.showerror(
                                    title="Payment Error", message="Please input a valid payment ammount.")

                            else:
                                float_payment_amount = float(payment_amount)
                                if float_payment_amount > net_total:
                                    paymentEntry_home.delete(0, END)
                                    messagebox.showerror(
                                        title="Payment Error", message="The payment cannot be more than net total.")
                                else:
                                    due_amount = (
                                        net_total - float_payment_amount)
                                    formatted_due_amount = "{:.2f}".format(
                                        due_amount)

                                    getDueAmount_home(formatted_due_amount)

                                    def saveInvoice():

                                        try:
                                            def getSaleCode():
                                                conn = sqlite3.connect(db_path)
                                                cursor = conn.cursor()

                                                new_sale_code = randint(
                                                    10_000_000, 99_999_999)
                                                cursor.execute(
                                                    "select sale_code from sales")
                                                sale_codes_list = []
                                                sale_codes_tuple_list = cursor.fetchall()
                                                for sale_code_tuple in sale_codes_tuple_list:
                                                    sale_codes_list.append(
                                                        sale_code_tuple[0])

                                                if new_sale_code not in sale_codes_list:
                                                    return new_sale_code
                                                else:
                                                    getSaleCode()

                                                conn.commit()

                                                conn.close()

                                            sale_code = getSaleCode()

                                            customer_id = getCustomerID_home()

                                            totalAmount_trv_home = getTrvTotal_home()

                                            sale_amount = net_total_home

                                            discount_percentage_applied = ((
                                                float(totalAmount_trv_home) - float(sale_amount))/float((totalAmount_trv_home)) * 100)

                                            paid_amount = float_payment_amount

                                            due_amount = due_amount_home

                                            print(totalAmount_trv_home,
                                                  discount_percentage_applied)

                                            conn = sqlite3.connect(db_path)
                                            cursor = conn.cursor()

                                            cursor.execute("INSERT INTO sales(sale_code, customer_id, sale_amount, paid_amount, due_amount) VALUES (?,?,?,?,?)",
                                                           (int(sale_code), int(customer_id),
                                                            float(sale_amount), float(paid_amount), float(due_amount)))

                                            cursor.execute(
                                                "select name from invoice_items")
                                            invoice_items_name_tuple_list = cursor.fetchall()
                                            invoice_items_name_list = []
                                            for i in invoice_items_name_tuple_list:
                                                invoice_items_name_list.append(
                                                    i[0])

                                            invoice_items_ID_List_list = []
                                            invoice_items_ID_list = []
                                            for item in invoice_items_name_list:
                                                cursor.execute(
                                                    f"select ID from products where product='{item}'")
                                                invoice_items_ID_tuple_list = cursor.fetchall()

                                                for j in invoice_items_ID_tuple_list:
                                                    invoice_items_ID_List_list.append(
                                                        j)

                                            for i in range(len(invoice_items_ID_List_list)):
                                                invoice_items_ID_list.append(
                                                    invoice_items_ID_List_list[i][0])

                                            cursor.execute(
                                                "select quantity from invoice_items")
                                            invoice_items_quantity_tuples_list = cursor.fetchall()
                                            invoice_items_quantity_list = []
                                            for i in invoice_items_quantity_tuples_list:
                                                invoice_items_quantity_list.append(
                                                    i[0])

                                            cursor.execute("")

                                            lT = []
                                            for i in range(len(invoice_items_ID_list)):
                                                lT.append(
                                                    (invoice_items_ID_list[i], invoice_items_quantity_list[i], sale_code))

                                            cursor.executemany(
                                                "insert into stocks_removed(product_ID, quantity, sale_code) values(?,?,?)", lT)

                                            resposnse = messagebox.askyesno(
                                                title="Confirm Sale", message="Are you sure to save this sale information in database? After saving this you cannot change. Make sure you are aware about what you are doing.")

                                            if resposnse == True:
                                                conn.commit()

                                                conn.close()
                                                UpdateSalesList_sales()
                                                messagebox.showinfo(
                                                    title="Save Success", message=f"The information is succesfully saved in database. The sale code is {sale_code}.")
                                                saveButton_home = defaultButton(
                                                    productsListFrame_home, "Save Invoice", 9, 0, W+E, state="disabled")

                                            else:
                                                return

                                        except Exception as identifier:
                                            messagebox.showerror(
                                                title="Customer Error", message="Please insert customer Information.")
                                            print(identifier)

                                        def printInvoice():
                                            """
                                            pdf = canvas.Canvas("Invoice.pdf")
                                            pdf.drawString(
                                                100, 800, f"Sale Code: {sale_code}")
                                            pdf.drawString(
                                                100, 700, f"Total Amount: {totalAmount_trv_home}")
                                            pdf.drawString(
                                                100, 600, f"Discount percentage: {discount_percentage_applied}")
                                            pdf.drawString(
                                                100, 500, f"Net Amount: {sale_amount}")
                                            pdf.save()
                                            """

                                            customerCodeEntry_home.config(
                                                state="enabled")
                                            customerNameEntry_home.config(
                                                state="enabled")
                                            customerPhoneEntry_home.config(
                                                state="enabled")
                                            customerAddressEntry_home.config(
                                                state="enabled")

                                            CustomerSearchCode_home.delete(
                                                0, END)
                                            customerCodeEntry_home.delete(
                                                0, END)
                                            customerNameEntry_home.delete(
                                                0, END)
                                            customerPhoneEntry_home.delete(
                                                0, END)
                                            customerAddressEntry_home.delete(
                                                0, END)

                                            customerCodeEntry_home.config(
                                                state="disabled")
                                            customerNameEntry_home.config(
                                                state="disabled")
                                            customerPhoneEntry_home.config(
                                                state="disabled")
                                            customerAddressEntry_home.config(
                                                state="disabled")

                                            deleteAll()

                                            netAmountEntry_home.config(
                                                state="enabled")
                                            netAmountEntry_home.delete(0, END)
                                            netAmountEntry_home.config(
                                                state="disabled")

                                            paymentEntry_home.delete(0, END)

                                            discountEntry_home.delete(0, END)

                                            dueEntry_home.config(
                                                state="enabled")
                                            dueEntry_home.delete(0, END)
                                            dueEntry_home.config(
                                                state="disabled")

                                            deleteButton_home = defaultButton(
                                                productsListFrame_home, "Delete Product", 1, 0, W+E, state="disabled")

                                            deleteAllButton_home = defaultButton(
                                                productsListFrame_home, "Delete All Products", 1, 1, W+E, state="disabled")

                                            discountButton_home = defaultButton(
                                                productsListFrame_home, "Get Net Amount", 4, 1, W+E, state="disabled")

                                            addPaymentButton_home = defaultButton(
                                                productsListFrame_home, "Add Payment", 7, 1, W+E, state="disabled")

                                            printButton_home = defaultButton(
                                                productsListFrame_home, "Generate PDF Invoice", 9, 1, W+E, state="disabled")

                                        printButton_home = defaultButton(
                                            productsListFrame_home, "Generate PDF Invoice", 9, 1, W+E, command=printInvoice)

                                    saveButton_home = defaultButton(
                                        productsListFrame_home, "Save Invoice", 9, 0, W+E, command=saveInvoice)

                                    dueEntry_home.config(state="enabled")
                                    dueEntry_home.delete(0, END)
                                    dueEntry_home.insert(
                                        0, formatted_due_amount)
                                    dueEntry_home.config(
                                        state="disabled", foreground="red")

                        except ValueError as identifier:
                            paymentEntry_home.delete(0, END)
                            messagebox.showerror(
                                title="Payment Error", message="The payment ammount is invalid.")

                    deleteButton_home = defaultButton(
                        productsListFrame_home, "Delete Product", 1, 0, W+E, command=deleteProduct)

                    deleteAllButton_home = defaultButton(
                        productsListFrame_home, "Delete All Products", 1, 1, W+E, command=deleteAll)

                    discountEntry_home = defaultEntry(
                        productsListFrame_home, "Discount (%)", 3, 0, 30)

                    discountButton_home = defaultButton(
                        productsListFrame_home, "Get Net Amount", 4, 1, W+E, command=applyDiscount)

                    netAmountEntry_home = defaultEntry(
                        productsListFrame_home, "Net Amount", 5, 0, 30, state="disabled")

                    paymentEntry_home = defaultEntry(
                        productsListFrame_home, "Payment Amount", 6, 0, 30)

                    addPaymentButton_home = defaultButton(
                        productsListFrame_home, "Add Payment", 7, 1, W+E, command=addPayment)

                    dueEntry_home = defaultEntry(
                        productsListFrame_home, "Due Amount", 8, 0, 30, state="disabled")

                    saveButton_home = defaultButton(
                        productsListFrame_home, "Save Invoice", 9, 0, W+E, state="disabled")

                    printButton_home = defaultButton(
                        productsListFrame_home, "Generate PDF Invoice", 9, 1, W+E, state="disabled")

            except Exception as e:
                productQuantityEntry_home.delete(0, END)
                messagebox.showerror(title="Quantity Error",
                                     message="Input a valid quantity")

    addProductButton_home = defaultButton(
        productAddFrame_Home, "Add Product", 6, 1, W+E, command=showProduct_trv_home)

    productsListFrame_home = defaultFrame(
        homeFrame, "Invoice Items List", 0, 1, rowspan=2)

    #------------------------ Display showing at the first in Invoice List but these don't work ----------------------------#

    trv_home = ttk.Treeview(productsListFrame_home, columns=(1, 2, 3, 4),
                            show="headings", height=int(0.00700*float(right)), padding=5, style="Custom.Treeview")
    trv_home.grid(row=0, column=0, columnspan=2)

    #trv_home.tag_bind('ttk', '<1>', itemClicked)

    trv_home.heading(1, text='Product')
    trv_home.heading(2, text='Price')
    trv_home.heading(3, text='Quanity')
    trv_home.heading(4, text='Amount')
    trv_home.column(1, anchor=CENTER,
                    width=int(0.1250*float(right)))
    trv_home.column(2, anchor=CENTER,
                    width=int(0.1250*float(right)))
    trv_home.column(3, anchor=CENTER,
                    width=int(0.1250*float(right)))
    trv_home.column(4, anchor=CENTER,
                    width=int(0.1250*float(right)))

    LLLL = []
    for i in LLLL:
        trv_home.insert("", "end", values=i)

    totalAmountEntry_home = defaultEntry(
        productsListFrame_home, "Total Amount", 2, 0, entryWidth, state="disabled")

    deleteButton_home = defaultButton(
        productsListFrame_home, "Delete Product", 1, 0, W+E, state="disabled")

    deleteAllButton_home = defaultButton(
        productsListFrame_home, "Delete All Products", 1, 1, W+E, state="disabled")

    discountEntry_home = defaultEntry(
        productsListFrame_home, "Discount (%)", 3, 0, entryWidth, state="disabled")

    discountButton_home = defaultButton(
        productsListFrame_home, "Get Net Amount", 4, 1, W+E, state="disabled")

    netAmountEntry_home = defaultEntry(
        productsListFrame_home, "Net Amount", 5, 0, entryWidth, state="disabled")

    paymentEntry_home = defaultEntry(
        productsListFrame_home, "Payment Amount", 6, 0, entryWidth, state="disabled")

    addPaymentButton_home = defaultButton(
        productsListFrame_home, "Add Payment", 7, 1, W+E, state="disabled")

    dueEntry_home = defaultEntry(
        productsListFrame_home, "Due Amount", 8, 0, entryWidth, state="disabled")

    saveButton_home = defaultButton(
        productsListFrame_home, "Save Invoice", 9, 0, W+E, state="disabled")

    printButton_home = defaultButton(
        productsListFrame_home, "Generate PDF Invoice", 9, 1, W+E, state="disabled")


UpdateHomeAddProduct_Frame()

#------------------------ Products List Frame ------------------------#


"""


Home End


"""

"""


Stocks Start


"""


stockAdd_frame_stocks = defaultFrame(stockFrame, "Add stocks", 0, 0)
stockList_frame_stocks = defaultFrame(
    stockFrame, "List of stocks", 0, 1, rowspan=2)


def updateStockList_stocks():

    trv_stocks = ttk.Treeview(stockList_frame_stocks, columns=(1, 2, 3, 4, 5),
                              show="headings", height=int(0.0140*float(right)), padding=5, style="Custom.Treeview")
    trv_stocks.grid(row=0, column=0, columnspan=2)

    trv_stocks.heading(1, text="stock ID")
    trv_stocks.heading(2, text='Product Name')
    trv_stocks.heading(3, text='Quantity')
    trv_stocks.heading(4, text='Price')
    trv_stocks.heading(5, text='Added Date')

    trv_stocks.column(1, anchor=CENTER, width=int(0.100*float(right)))
    trv_stocks.column(2, anchor=CENTER, width=int(0.100*float(right)))
    trv_stocks.column(3, anchor=CENTER, width=int(0.100*float(right)))
    trv_stocks.column(4, anchor=CENTER, width=int(0.100*float(right)))
    trv_stocks.column(5, anchor=CENTER, width=int(0.120*float(right)))

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "select stocks.ID, products.product, stocks.Quantity, stocks.price, stocks.created_at from stocks inner join products where stocks.product_id=products.ID order by stocks.created_at desc")
    stocks_tuple_list = cursor.fetchall()

    for i in stocks_tuple_list:
        trv_stocks.insert("", "end", values=i)
    conn.commit()
    conn.close()

    def deleteStockfromstocklist():
        try:
            selectedStockIID = trv_stocks.selection()[0]
            stock_ID = trv_stocks.item(selectedStockIID)["values"][0]

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute(
                f"DELETE FROM stocks WHERE ID={int(stock_ID)}")

            resposne = messagebox.askyesno(
                title="Confirm delete stock", message="Are you sure you want to delete this stock?")
            if resposne == True:
                conn.commit()
                conn.close()
                trv_stocks.delete(*trv_stocks.get_children())
                updateStockList_stocks()
                UpdateHomeAddProduct_Frame()
            else:
                return

        except Exception as identifier:
            messagebox.showerror(
                title="Selection error", message="You didn't select a customer from the list. Please select one and try to delete.")

            trv_stocks.delete(*trv_stocks.get_children())
            updateStockList_stocks()
            UpdateHomeAddProduct_Frame()

    deleteStockfromstocklist = defaultButton(
        stockList_frame_stocks, "Delete selected stock", 1, 0, W+E, command=deleteStockfromstocklist)

    def editstockfromstocklist():
        try:
            selectedStockIID = trv_stocks.selection()[0]
            stock_ID = trv_stocks.item(selectedStockIID)["values"][0]
            stock_name = trv_stocks.item(selectedStockIID)["values"][1]

            editWindow = Tk()
            editWindow.title("Edit Stock")
            editWindow.iconbitmap(icon_path)

            editStockFrame = defaultFrame(
                editWindow, "Edit Stock", 0, 0)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute(
                f"select Quantity, Price from stocks WHERE ID={int(stock_ID)}")
            stock_info_tuple_list = cursor.fetchall()

            name_edit_stocks = defaultEntry(
                editStockFrame, "Name", 0, 0, 30)
            quantity_edit_stocks = defaultEntry(
                editStockFrame, "Quantity", 1, 0, 30)
            price_edit_stocks = defaultEntry(
                editStockFrame, "Price", 2, 0, 30)

            name_edit_stocks.insert(0, stock_name)
            quantity_edit_stocks.insert(0, stock_info_tuple_list[0][0])
            price_edit_stocks.insert(0, stock_info_tuple_list[0][1])

            name_edit_stocks.config(state="disabled")

            def editAndSaveStock():
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute(
                    f"update stocks set Quantity={int(quantity_edit_stocks.get())} where ID={int(stock_ID)}")
                cursor.execute(
                    f"update stocks set Price={float(price_edit_stocks.get())} where ID={int(stock_ID)}")

                resposne = messagebox.askyesno(
                    title="Confirm Edit", message="Are you sure you want to edit this stock's information?")
                if resposne == True:
                    conn.commit()
                    conn.close()

                    messagebox.showinfo(
                        title="Edit stock successfully", message="Stock is updated successfully.")
                    trv_stocks.delete(*trv_stocks.get_children())
                    updateStockList_stocks()
                    UpdateHomeAddProduct_Frame()
                    editWindow.destroy()

                else:
                    return

            save_edit_button = defaultButton(
                editStockFrame, "Save Changes", 4, 1, W+E, command=editAndSaveStock)

            editWindow.mainloop()

        except Exception as identifier:
            messagebox.showerror(
                title="Selection error", message="You did not select a stock from the list.")

    editStockfromStockList = defaultButton(
        stockList_frame_stocks, "Edit selected Stock", 1, 1, W+E, command=editstockfromstocklist)


updateStockList_stocks()


def getAllProducts():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    PRODUCTS = []
    cursor.execute("select product from products")
    products = cursor.fetchall()
    for product in products:
        PRODUCTS.append(product[0])
    conn.commit()
    conn.close()
    return PRODUCTS


def updateStockAdd():
    def productCombo(event):
        product = productCombo_home.get()

        productNameEntry_stocks.config(state="enabled")

        productNameEntry_stocks.delete(0, END)
        productPriceEntry_stocks.delete(0, END)
        productQuantityEntry_stocks.delete(0, END)

        productNameEntry_stocks.insert(0, product)
        productNameEntry_stocks.config(state="disabled")

        conn = sqlite3.connect(db_path)

        cursor = conn.cursor()

        cursor.execute(f"select ID from products where product='{product}'")
        product_ID = cursor.fetchall()[0][0]

        def addStock():
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute("INSERT INTO stocks(product_id, Quantity, Price) VALUES (?, ?, ?)",
                               (product_ID, int(productQuantityEntry_stocks.get()), float(
                                productPriceEntry_stocks.get()))
                               )

                resposne = messagebox.askyesno(
                    title="Confirm adding stock", message="Are you sure you want to add this stock?")
                if resposne == True:
                    conn.commit()
                    conn.close()
                    updateStockList_stocks()
                    productNameEntry_stocks.delete(0, END)
                    productPriceEntry_stocks.delete(0, END)
                    productQuantityEntry_stocks.delete(0, END)

                else:
                    return

            except Exception as identifier:
                messagebox.showerror(
                    title="Adding stock error", message="Please insert valid information for the stock.")

        stockAdd_button = defaultButton(
            stockAdd_frame_stocks, "Add stock", 4, 1, W+E, command=addStock)

        conn.commit()

        conn.close()

    allProducts = getAllProducts()
    choose_product_label = Label(stockAdd_frame_stocks, text="Product:",
                                 font=f"Courier {fontSize} bold").grid(row=0, column=0, sticky=E, padx=10)
    productCombo_home = ttk.Combobox(stockAdd_frame_stocks, value=allProducts, width=entryWidth,
                                     font=f"Courier {fontSize} bold")
    productCombo_home.set("Choose one...")
    productCombo_home.bind("<<ComboboxSelected>>", productCombo)
    productCombo_home.grid(row=0, column=1, pady=5)

    productNameEntry_stocks = defaultEntry(
        stockAdd_frame_stocks, "Name", 1, 0, entryWidth, state="disabled")
    productPriceEntry_stocks = defaultEntry(
        stockAdd_frame_stocks, "Price (BDT)", 3, 0, entryWidth)
    productQuantityEntry_stocks = defaultEntry(
        stockAdd_frame_stocks, "Quantity", 2, 0, entryWidth)

    stockAdd_button = defaultButton(
        stockAdd_frame_stocks, "Add stock", 4, 1, W+E, state="disabled")


updateStockAdd()


def searchStocks_stocks():

    trv_stocks = ttk.Treeview(stockList_frame_stocks, columns=(1, 2, 3, 4, 5),
                              show="headings", height=int(0.0140*float(right)), padding=5, style="Custom.Treeview")
    trv_stocks.grid(row=0, column=0, columnspan=2)

    trv_stocks.heading(1, text="stock ID")
    trv_stocks.heading(2, text='Product Name')
    trv_stocks.heading(3, text='Quantity')
    trv_stocks.heading(4, text='Price')
    trv_stocks.heading(5, text='Added Date')

    trv_stocks.column(1, anchor=CENTER, width=int(0.100*float(right)))
    trv_stocks.column(2, anchor=CENTER, width=int(0.100*float(right)))
    trv_stocks.column(3, anchor=CENTER, width=int(0.100*float(right)))
    trv_stocks.column(4, anchor=CENTER, width=int(0.100*float(right)))
    trv_stocks.column(5, anchor=CENTER, width=int(0.120*float(right)))

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = searchStocksEntry_stocks.get()

    cursor.execute(
        f"select stocks.ID, products.product, stocks.Quantity, stocks.price, stocks.created_at from stocks inner join products on stocks.product_id=products.ID where products.product like '%{query}%' or stocks.created_at like '%{query}%' order by stocks.created_at desc")
    stocks_tuple_list = cursor.fetchall()

    for i in stocks_tuple_list:
        trv_stocks.insert("", "end", values=i)
    conn.commit()
    conn.close()

    def deleteStockfromstocklist():
        try:
            selectedStockIID = trv_stocks.selection()[0]
            stock_ID = trv_stocks.item(selectedStockIID)["values"][0]

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute(
                f"DELETE FROM stocks WHERE ID={int(stock_ID)}")

            resposne = messagebox.askyesno(
                title="Confirm delete stock", message="Are you sure you want to delete this stock?")
            if resposne == True:
                conn.commit()
                conn.close()
                trv_stocks.delete(*trv_stocks.get_children())
                updateStockList_stocks()
                UpdateHomeAddProduct_Frame()
            else:
                return

        except Exception as identifier:
            messagebox.showerror(
                title="Selection error", message="You didn't select a customer from the list. Please select one and try to delete.")

            trv_stocks.delete(*trv_stocks.get_children())
            updateStockList_stocks()
            UpdateHomeAddProduct_Frame()

    deleteStockfromstocklist = defaultButton(
        stockList_frame_stocks, "Delete selected stock", 1, 0, W+E, command=deleteStockfromstocklist)

    def editstockfromstocklist():
        try:
            selectedStockIID = trv_stocks.selection()[0]
            stock_ID = trv_stocks.item(selectedStockIID)["values"][0]
            stock_name = trv_stocks.item(selectedStockIID)["values"][1]

            editWindow = Tk()
            editWindow.title("Edit Stock")
            editWindow.iconbitmap(icon_path)

            editStockFrame = defaultFrame(
                editWindow, "Edit Stock", 0, 0)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute(
                f"select Quantity, Price from stocks WHERE ID={int(stock_ID)}")
            stock_info_tuple_list = cursor.fetchall()

            name_edit_stocks = defaultEntry(
                editStockFrame, "Name", 0, 0, 30)
            quantity_edit_stocks = defaultEntry(
                editStockFrame, "Quantity", 1, 0, 30)
            price_edit_stocks = defaultEntry(
                editStockFrame, "Price", 2, 0, 30)

            name_edit_stocks.insert(0, stock_name)
            quantity_edit_stocks.insert(0, stock_info_tuple_list[0][0])
            price_edit_stocks.insert(0, stock_info_tuple_list[0][1])

            name_edit_stocks.config(state="disabled")

            def editAndSaveStock():
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute(
                    f"update stocks set Quantity='{int(quantity_edit_stocks.get())}' where product_id={int(stock_ID)}")
                cursor.execute(
                    f"update stocks set Price='{float(price_edit_stocks.get())}' where product_id={int(stock_ID)}")

                resposne = messagebox.askyesno(
                    title="Confirm Edit", message="Are you sure you want to edit this stock's information?")
                if resposne == True:
                    conn.commit()
                    conn.close()

                    messagebox.showinfo(
                        title="Edit stock successfully", message="Stock is updated successfully.")
                    updateStockList_stocks()
                    editWindow.destroy()

                else:
                    return

            save_edit_button = defaultButton(
                editStockFrame, "Save Changes", 4, 1, W+E, command=editAndSaveStock)

            editWindow.mainloop()

        except Exception as identifier:
            messagebox.showerror(
                title="Selection error", message="You did not select a stock from the list.")

    editStockfromStockList = defaultButton(
        stockList_frame_stocks, "Edit selected Customer", 1, 1, W+E, command=editstockfromstocklist)


stockSearch_frame_stocks = defaultFrame(
    stockFrame, "Search by product name", 1, 0)

searchStocksEntry_stocks = defaultEntry(
    stockSearch_frame_stocks, "Search Stock", 0, 0, entryWidth)

searchStocksButton_stocks = defaultButton(
    stockSearch_frame_stocks, "Search Stock", 1, 1, W+E, command=searchStocks_stocks)


def resetStocks_stocks():
    updateStockList_stocks()


resetStocksButton_stocks = defaultButton(
    stockSearch_frame_stocks, "Reset Stock", 1, 0, W+E, command=resetStocks_stocks)


"""


Stocks End


"""


"""


Customers Start


"""
#------------------------ Create funtion to update and showing customers list ------------------------#

customerListFrame_customers = defaultFrame(
    customerFrame, "Customer List", 0, 1, rowspan=3)


def updateCustomersList():

    trv_customers = ttk.Treeview(customerListFrame_customers, columns=(1, 2, 3, 4, 5),
                                 show="headings", height=int(0.0140*float(right)), padding=5, style="Custom.Treeview")
    trv_customers.grid(row=0, column=0, columnspan=2)

    trv_customers.heading(1, text='Code')
    trv_customers.heading(2, text='First Name')
    trv_customers.heading(3, text='Last Name')
    trv_customers.heading(4, text='Address')
    trv_customers.heading(5, text='Phone')

    trv_customers.column(1, anchor=CENTER, width=int(0.100*float(right)))
    trv_customers.column(2, anchor=CENTER, width=int(0.100*float(right)))
    trv_customers.column(3, anchor=CENTER, width=int(0.100*float(right)))
    trv_customers.column(4, anchor=CENTER, width=int(0.100*float(right)))
    trv_customers.column(5, anchor=CENTER, width=int(0.100*float(right)))

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "select customer_code, first_name, last_name, address, phone from customers order by ID desc")
    customers_tuple_list = cursor.fetchall()

    for i in customers_tuple_list:
        trv_customers.insert("", "end", values=i)
    conn.commit()
    conn.close()

    def deleteCustomerFromCustomerList():
        try:
            selectedCustomerIID = trv_customers.selection()[0]
            code = trv_customers.item(selectedCustomerIID)["values"][0]

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute(
                f"DELETE FROM customers WHERE customer_code={int(code)}")

            resposne = messagebox.askyesno(
                title="Confirm delete customer", message="Are you sure you want to delete this customer?")
            if resposne == True:
                conn.commit()
                conn.close()
                trv_customers.delete(*trv_customers.get_children())
                updateCustomersList()
            else:
                return

        except Exception as identifier:
            messagebox.showerror(
                title="Selection error", message="You didn't select a customer from the list. Please select one and try to delete.")

            trv_customers.delete(*trv_customers.get_children())
            updateCustomersList()

    deleteCustomerFromCustomerListButton = defaultButton(
        customerListFrame_customers, "Delete selected Customer", 1, 0, W+E, command=deleteCustomerFromCustomerList)

    def editCustomerFromCustomerList():
        try:
            selectedCustomerIID = trv_customers.selection()[0]
            code = trv_customers.item(selectedCustomerIID)["values"][0]

            editWindow = Tk()
            editWindow.title("Edit Customer")
            editWindow.iconbitmap(icon_path)

            editCustomerFrame = defaultFrame(editWindow, "Edit Customer", 0, 0)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute(
                f"select first_name, last_name, address, phone from customers WHERE customer_code={int(code)}")
            customer_info_tuple_list = cursor.fetchall()

            f_name_edit = defaultEntry(
                editCustomerFrame, "First Name", 0, 0, 30)
            l_name_edit = defaultEntry(
                editCustomerFrame, "Last Name", 1, 0, 30)
            address_edit = defaultEntry(editCustomerFrame, "Address", 2, 0, 30)
            phone_edit = defaultEntry(editCustomerFrame, "Phone", 3, 0, 30)

            f_name_edit.insert(0, customer_info_tuple_list[0][0])
            l_name_edit.insert(0, customer_info_tuple_list[0][1])
            address_edit.insert(0, customer_info_tuple_list[0][2])
            phone_edit.insert(0, customer_info_tuple_list[0][3])

            def editAndSaveCustomer():
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute(
                    f"update customers set first_name='{f_name_edit.get().capitalize()}' where customer_code={int(code)}")
                cursor.execute(
                    f"update customers set last_name='{l_name_edit.get().capitalize()}' where customer_code={int(code)}")
                cursor.execute(
                    f"update customers set address='{address_edit.get().capitalize()}' where customer_code={int(code)}")
                cursor.execute(
                    f"update customers set phone='{phone_edit.get()}' where customer_code={int(code)}")

                resposne = messagebox.askyesno(
                    title="Confirm Edit", message="Are you sure you want to edit this customer's information?")
                if resposne == True:
                    conn.commit()
                    conn.close()

                    messagebox.showinfo(
                        title="Edit Customer successfully", message="Customer is updated successfully.")
                    updateCustomersList()
                    editWindow.destroy()

                else:
                    return

            save_edit_button = defaultButton(
                editCustomerFrame, "Save Changes", 4, 1, W+E, command=editAndSaveCustomer)

            editWindow.mainloop()

        except Exception as identifier:
            messagebox.showerror(
                title="Selection error", message="You did not select a customer from the list.")

    editCustomerFromCustomerListButton = defaultButton(
        customerListFrame_customers, "Edit selected Customer", 1, 1, W+E, command=editCustomerFromCustomerList)


#------------------------ Create a function to show the list of customers after searching --------------------------------#


#------------------------ Customer Adding Frame ------------------------#

customerAddFrame_customers = defaultFrame(
    customerFrame, "Add New Customer", 0, 0)


customer_first_name_Entry_customers = defaultEntry(
    customerAddFrame_customers, "First Name", 0, 0, 20)
customer_last_name_Entry_customers = defaultEntry(
    customerAddFrame_customers, "Last Name", 1, 0, 20)
customer_address_Entry_customers = defaultEntry(
    customerAddFrame_customers, "Address", 2, 0, 20)
customer_phone_Entry_customers = defaultEntry(
    customerAddFrame_customers, "Phone", 3, 0, 20)


def addCustomer_customers():
    try:
        def getCustomerCode():

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            new_code = randint(100000, 999999)

            cursor.execute("select customer_code from customers")
            code_tuple_list = cursor.fetchall()
            code_list = []
            for code in code_tuple_list:
                code_list.append(code[0])

            if new_code not in code_list:
                return new_code
            else:
                getCustomerCode()

            conn.commit()
            conn.close()

        customer_f_Name = customer_first_name_Entry_customers.get().capitalize()
        customer_l_name = customer_last_name_Entry_customers.get().capitalize()
        customer_address = customer_address_Entry_customers.get().capitalize()
        customer_phone = customer_phone_Entry_customers.get()
        customer_code = getCustomerCode()

        if customer_f_Name == "" or customer_l_name == "" or customer_address == "" or customer_phone == "":
            messagebox.showerror(
                title="Insert Error",
                message="Pleae insert all the information with valid input.")
        else:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("INSERT INTO customers(customer_code, first_name, last_name, address, phone) VALUES (?,?,?,?,?)",
                           (int(customer_code), customer_f_Name,
                            customer_l_name, customer_address, customer_phone))

            resposne = messagebox.askyesno(
                title="Confirm Save Customer", message="Are you sure you want to save this customer?")

            if resposne == True:
                conn.commit()
                conn.close()

                messagebox.showinfo(
                    title="Save successfull", message=f"The customer has been saved successfully. The new customer code is {customer_code}.")

                customer_first_name_Entry_customers.delete(0, END)
                customer_last_name_Entry_customers.delete(0, END)
                customer_address_Entry_customers.delete(0, END)
                customer_phone_Entry_customers.delete(0, END)

                updateCustomersList()
            else:
                return

    except Exception as identifier:
        messagebox.showerror(title="Customer Error",
                             message="There is an error to add the customer.")


add_customer_button_customers = defaultButton(
    customerAddFrame_customers, "Add Customer", 4, 1, W+E, command=addCustomer_customers)


#------------------------ Showing Customer list Frame --------------------------------#

updateCustomersList()

#------------------------ Search Customer Frame --------------------------------#

searchCustomerFrame_customers = defaultFrame(
    customerFrame, "Search by name, address or phone", 1, 0)

searchCustomerEntry_customers = defaultEntry(
    searchCustomerFrame_customers, "Search Customer", 0, 0, 20)


def searchCustomer():
    query = searchCustomerEntry_customers.get()

    trv_customers = ttk.Treeview(customerListFrame_customers, columns=(1, 2, 3, 4, 5),
                                 show="headings", height=int(0.0140*float(right)), padding=5, style="Custom.Treeview")
    trv_customers.grid(row=0, column=0, columnspan=2)

    trv_customers.heading(1, text='Code')
    trv_customers.heading(2, text='First Name')
    trv_customers.heading(3, text='Last Name')
    trv_customers.heading(4, text='Address')
    trv_customers.heading(5, text='Phone')

    trv_customers.column(1, anchor=CENTER, width=int(0.100*float(right)))
    trv_customers.column(2, anchor=CENTER, width=int(0.100*float(right)))
    trv_customers.column(3, anchor=CENTER, width=int(0.100*float(right)))
    trv_customers.column(4, anchor=CENTER, width=int(0.100*float(right)))
    trv_customers.column(5, anchor=CENTER, width=int(0.100*float(right)))

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        f"select customer_code, first_name, last_name, address, phone from customers where first_name like '%{query}%' or last_name like '%{query}%' or address like '%{query}%' or phone like '%{query}%' order by ID desc")
    customers_tuple_list = cursor.fetchall()

    for i in customers_tuple_list:
        trv_customers.insert("", "end", values=i)
    conn.commit()
    conn.close()

    def deleteCustomerFromCustomerList():
        try:
            selectedCustomerIID = trv_customers.selection()[0]
            code = trv_customers.item(selectedCustomerIID)["values"][0]

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute(
                f"DELETE FROM customers WHERE customer_code={int(code)}")

            resposne = messagebox.askyesno(
                title="Confirm delete customer", message="Are you sure you want to delete this customer?")
            if resposne == True:
                conn.commit()
                conn.close()
                trv_customers.delete(*trv_customers.get_children())
                updateCustomersList()
            else:
                return

        except Exception as identifier:
            messagebox.showerror(
                title="Selection error", message="You didn't select a customer from the list. Please select one and try to delete.")

            trv_customers.delete(*trv_customers.get_children())
            updateCustomersList()

    deleteCustomerFromCustomerListButton = defaultButton(
        customerListFrame_customers, "Delete selected Customer", 1, 0, W+E, command=deleteCustomerFromCustomerList)

    def editCustomerFromCustomerList():
        try:
            selectedCustomerIID = trv_customers.selection()[0]
            code = trv_customers.item(selectedCustomerIID)["values"][0]

            editWindow = Tk()
            editWindow.title("Edit Customer")
            editWindow.iconbitmap(icon_path)

            editCustomerFrame = defaultFrame(editWindow, "Edit Customer", 0, 0)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute(
                f"select first_name, last_name, address, phone from customers WHERE customer_code={int(code)}")
            customer_info_tuple_list = cursor.fetchall()

            f_name_edit = defaultEntry(
                editCustomerFrame, "First Name", 0, 0, 30)
            l_name_edit = defaultEntry(
                editCustomerFrame, "Last Name", 1, 0, 30)
            address_edit = defaultEntry(editCustomerFrame, "Address", 2, 0, 30)
            phone_edit = defaultEntry(editCustomerFrame, "Phone", 3, 0, 30)

            f_name_edit.insert(0, customer_info_tuple_list[0][0])
            l_name_edit.insert(0, customer_info_tuple_list[0][1])
            address_edit.insert(0, customer_info_tuple_list[0][2])
            phone_edit.insert(0, customer_info_tuple_list[0][3])

            def editAndSaveCustomer():
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute(
                    f"update customers set first_name='{f_name_edit.get().capitalize()}' where customer_code={int(code)}")
                cursor.execute(
                    f"update customers set last_name='{l_name_edit.get().capitalize()}' where customer_code={int(code)}")
                cursor.execute(
                    f"update customers set address='{address_edit.get().capitalize()}' where customer_code={int(code)}")
                cursor.execute(
                    f"update customers set phone='{phone_edit.get()}' where customer_code={int(code)}")

                resposne = messagebox.askyesno(
                    title="Confirm Edit", message="Are you sure you want to edit this customer's information?")
                if resposne == True:
                    conn.commit()
                    conn.close()

                    messagebox.showinfo(
                        title="Edit Customer successfully", message="Customer is updated successfully.")
                    updateCustomersList()
                    editWindow.destroy()

                else:
                    return

            save_edit_button = defaultButton(
                editCustomerFrame, "Save Changes", 4, 1, W+E, command=editAndSaveCustomer)

            editWindow.mainloop()

        except Exception as identifier:
            messagebox.showerror(
                title="Selection error", message="You did not select a customer from the list.")

    editCustomerFromCustomerListButton = defaultButton(
        customerListFrame_customers, "Edit selected Customer", 1, 1, W+E, command=editCustomerFromCustomerList)


searchCustomerButton_customers = defaultButton(
    searchCustomerFrame_customers, "Search", 1, 1, W+E, command=searchCustomer)


def resetCustomerList():
    updateCustomersList()


resetCustomerList_customers = defaultButton(
    searchCustomerFrame_customers, "Reset", 1, 0, W+E, command=resetCustomerList)

"""

Customer End


"""


"""


Products Start


"""
#------------------------ Create funtion to update and showing Products list ------------------------#

productListFrame_products = defaultFrame(
    productFrame, "Products List", 0, 1, rowspan=3)


def updateProductsList():

    trv_products = ttk.Treeview(productListFrame_products, columns=(1, 2, 3),
                                show="headings", height=int(0.0140*float(right)), padding=5, style="Custom.Treeview")
    trv_products.grid(row=0, column=0, columnspan=2)

    trv_products.heading(1, text='Name')
    trv_products.heading(2, text='Weight (g)')
    trv_products.heading(3, text='Price (bdt)')

    trv_products.column(1, anchor=CENTER, width=int(0.170*float(right)))
    trv_products.column(2, anchor=CENTER, width=int(0.170*float(right)))
    trv_products.column(3, anchor=CENTER, width=int(0.170*float(right)))

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "select product, weight, price from products order by ID desc")
    products_tuple_list = cursor.fetchall()

    for i in products_tuple_list:
        trv_products.insert("", "end", values=i)

    conn.commit()
    conn.close()

    def deleteProductFromProductList():
        try:
            selectedProductIID = trv_products.selection()[0]
            name = trv_products.item(selectedProductIID)["values"][0]

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute(
                f"DELETE FROM products WHERE product='{name}'")

            resposne = messagebox.askyesno(
                title="Confirm delete produtc", message="Are you sure you want to delete this product?")
            if resposne == True:
                conn.commit()
                conn.close()
                trv_products.delete(*trv_products.get_children())
                updateProductsList()
                UpdateHomeAddProduct_Frame()
                updateStockAdd()
            else:
                return

        except Exception as identifier:
            messagebox.showerror(
                title="Selection error", message="You didn't select a product from the list. Please select one and try to delete.")

            trv_products.delete(*trv_products.get_children())
            updateProductsList()
            updateStockAdd()

    deleteProductFromProductListButton = defaultButton(
        productListFrame_products, "Delete selected product", 1, 0, W+E, command=deleteProductFromProductList)

    def editProductFromProductList():
        try:
            selectedProductIID = trv_products.selection()[0]
            name = trv_products.item(selectedProductIID)["values"][0]

            editWindow = Tk()
            editWindow.title("Edit product")
            editWindow.iconbitmap(icon_path)

            editProductFrame = defaultFrame(editWindow, "Edit Product", 0, 0)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute(
                f"select product, weight, price from products WHERE product='{name}'")
            product_info_tuple_list = cursor.fetchall()

            product_name_edit = defaultEntry(
                editProductFrame, "Product Name", 0, 0, 30)
            weight_edit = defaultEntry(
                editProductFrame, "Weight (g)", 1, 0, 30)
            price_edit = defaultEntry(
                editProductFrame, "Price (BDT)", 2, 0, 30)

            product_name_edit.insert(0, product_info_tuple_list[0][0])
            weight_edit.insert(0, product_info_tuple_list[0][1])
            price_edit.insert(0, product_info_tuple_list[0][2])

            def editAndSaveProduct():
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute(
                    f"update products set product='{product_name_edit.get().capitalize()}' where product='{name}'")
                cursor.execute(
                    f"update products set weight={weight_edit.get()} where product='{name}'")
                cursor.execute(
                    f"update products set price={price_edit.get()} where product='{name}'")

                resposne = messagebox.askyesno(
                    title="Confirm Edit", message="Are you sure you want to edit this product's information?")
                if resposne == True:
                    conn.commit()
                    conn.close()

                    messagebox.showinfo(
                        title="Edit product successfully", message="Product is updated successfully.")
                    editWindow.destroy()
                    updateProductsList()
                    UpdateHomeAddProduct_Frame()
                    updateStockAdd()

                else:
                    return

            save_edit_button = defaultButton(
                editProductFrame, "Save Changes", 4, 1, W+E, command=editAndSaveProduct)

            editWindow.mainloop()

        except Exception as identifier:
            messagebox.showerror(
                title="Selection error", message="You did not select a product from the list.")

    editProductFromProductListButton = defaultButton(
        productListFrame_products, "Edit selected Product", 1, 1, W+E, command=editProductFromProductList)


#------------------------ Create a function to show the list of Product after searching --------------------------------#


#------------------------ Product Adding Frame ------------------------#

productAddFrame_products = defaultFrame(
    productFrame, "Add New Product", 0, 0)


product_name_Entry_products = defaultEntry(
    productAddFrame_products, "Product Name", 0, 0, 20)
product_weight_entry_products = defaultEntry(
    productAddFrame_products, "Weight", 1, 0, 20)
product_price_Entry_products = defaultEntry(
    productAddFrame_products, "Price", 2, 0, 20)


def addProduct_products():
    try:

        product_Name = product_name_Entry_products.get().capitalize()
        product_weight = product_weight_entry_products.get()
        product_Price = product_price_Entry_products.get()

        if product_Name == "" or product_weight == "" or product_Price == "":
            messagebox.showerror(
                title="Insert Error",
                message="Pleae insert all the information with valid input.")
        else:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("INSERT INTO products(product, weight, price) VALUES (?,?,?)",
                           (product_Name,
                            product_weight, product_Price))

            resposne = messagebox.askyesno(
                title="Confirm Save Product", message="Are you sure you want to save this product?")

            if resposne == True:
                conn.commit()
                conn.close()

                messagebox.showinfo(
                    title="Save successfull", message="The product has been saved successfully.")

                product_name_Entry_products.delete(0, END)
                product_weight_entry_products.delete(0, END)
                product_price_Entry_products.delete(0, END)

                updateProductsList()
                UpdateHomeAddProduct_Frame()
                updateStockAdd()

            else:
                return

    except Exception as identifier:
        messagebox.showerror(title="Products Error",
                             message="There is an error to add the product.")


add_product_button_products = defaultButton(
    productAddFrame_products, "Add Product", 4, 1, W+E, command=addProduct_products)


#------------------------ Showing Customer list Frame --------------------------------#

updateProductsList()

#------------------------ Search Customer Frame --------------------------------#

searchProductFrame_products = defaultFrame(
    productFrame, "Search by name", 1, 0)

searchProductEntry_products = defaultEntry(
    searchProductFrame_products, "Search Product", 0, 0, 20)


def searchProduct():
    query = searchProductEntry_products.get()

    trv_products = ttk.Treeview(productListFrame_products, columns=(1, 2, 3),
                                show="headings", height=int(0.0140*float(right)), padding=5, style="Custom.Treeview")
    trv_products.grid(row=0, column=0, columnspan=2)

    trv_products.heading(1, text='Name')
    trv_products.heading(2, text='Weight (g)')
    trv_products.heading(3, text='Price (bdt)')

    trv_products.column(1, anchor=CENTER, width=int(0.170*float(right)))
    trv_products.column(2, anchor=CENTER, width=int(0.170*float(right)))
    trv_products.column(3, anchor=CENTER, width=int(0.170*float(right)))

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        f"select product, weight, price from products where product like '%{query}%' order by ID desc")
    products_tuple_list = cursor.fetchall()

    for i in products_tuple_list:
        trv_products.insert("", "end", values=i)

    conn.commit()
    conn.close()

    def deleteProductFromProductList():
        try:
            selectedProductIID = trv_products.selection()[0]
            name = trv_products.item(selectedProductIID)["values"][0]

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute(
                f"DELETE FROM products WHERE product='{name}'")

            resposne = messagebox.askyesno(
                title="Confirm delete produtc", message="Are you sure you want to delete this product?")
            if resposne == True:
                conn.commit()
                conn.close()
                trv_products.delete(*trv_products.get_children())
                updateProductsList()
            else:
                return

        except Exception as identifier:
            messagebox.showerror(
                title="Selection error", message="You didn't select a product from the list. Please select one and try to delete.")

            trv_products.delete(*trv_products.get_children())
            updateProductsList()

    deleteProductFromProductListButton = defaultButton(
        productListFrame_products, "Delete selected product", 1, 0, W+E, command=deleteProductFromProductList)

    def editProductFromProductList():
        try:
            selectedProductIID = trv_products.selection()[0]
            name = trv_products.item(selectedProductIID)["values"][0]

            editWindow = Tk()
            editWindow.title("Edit product")
            editWindow.iconbitmap(icon_path)

            editProductFrame = defaultFrame(editWindow, "Edit Product", 0, 0)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute(
                f"select product, weight, price from products WHERE product='{name}'")
            product_info_tuple_list = cursor.fetchall()

            product_name_edit = defaultEntry(
                editProductFrame, "Product Name", 0, 0, 30)
            weight_edit = defaultEntry(
                editProductFrame, "Weight (g)", 1, 0, 30)
            price_edit = defaultEntry(
                editProductFrame, "Price (BDT)", 2, 0, 30)

            product_name_edit.insert(0, product_info_tuple_list[0][0])
            weight_edit.insert(0, product_info_tuple_list[0][1])
            price_edit.insert(0, product_info_tuple_list[0][2])

            def editAndSaveProduct():
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute(
                    f"update products set product='{product_name_edit.get().capitalize()}' where product='{name}'")
                cursor.execute(
                    f"update products set weight={weight_edit.get()} where product='{name}'")
                cursor.execute(
                    f"update products set price={price_edit.get()} where product='{name}'")

                resposne = messagebox.askyesno(
                    title="Confirm Edit", message="Are you sure you want to edit this product's information?")
                if resposne == True:
                    conn.commit()
                    conn.close()

                    messagebox.showinfo(
                        title="Edit product successfully", message="Product is updated successfully.")
                    updateProductsList()
                    editWindow.destroy()

                else:
                    return

            save_edit_button = defaultButton(
                editProductFrame, "Save Changes", 4, 1, W+E, command=editAndSaveProduct)

            editWindow.mainloop()

        except Exception as identifier:
            messagebox.showerror(
                title="Selection error", message="You did not select a product from the list.")

    editProductFromProductListButton = defaultButton(
        productListFrame_products, "Edit selected Product", 1, 1, W+E, command=editProductFromProductList)


searchProductButton_products = defaultButton(
    searchProductFrame_products, "Search", 1, 1, W+E, command=searchProduct)


def resetProductsList():
    updateProductsList()


resetProductsList_products = defaultButton(
    searchProductFrame_products, "Reset", 1, 0, W+E, command=resetProductsList)
"""


Product End


"""

conn.commit()

conn.close()

root.mainloop()
