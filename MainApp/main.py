from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import os
import sqlite3
from random import randint

root = Tk()
root.title("Business Management")
right = 1380
down = 840
# root.geometry(f"{right}x{down}")
root.geometry(f"{right}x{down}")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "practice.db")
icon_path = os.path.join(BASE_DIR, "icon.ico")

root.iconbitmap(icon_path)

conn = sqlite3.connect(db_path)

cursor = conn.cursor()


#------------------------ Default Frame Function ----------------------------------------#


def defaultFrame(parent, caption, row, column, **options):
    frame = LabelFrame(parent, text=caption, padx=20,
                       pady=20, font="Courier 18 bold")
    frame.grid(row=row, column=column, padx=20, pady=20, **options)
    return frame

#------------------------ Default Entry Function ----------------------------------------#


def defaultEntry(parent, caption, row, column, width, **options):
    Label(parent, text=caption + ": ",
          font="Courier 15 bold").grid(row=row, column=column, sticky=E)
    entry = ttk.Entry(parent, width=width, justify=RIGHT,
                      font="Courier 14 bold", **options)
    entry.grid(row=row, column=column + 1, pady=5)
    return entry


#------------------------ Default Button Function ----------------------------------------#


def defaultButton(parent, caption, row, column, sticky, **options):
    ttk.Style().configure("TButton", font="Courier 13 bold")
    button = ttk.Button(parent, text=caption,
                        **options)
    button.grid(row=row, column=column, pady=10, sticky=sticky)


#------------------------ Creating notebook --------------------------------#
COLOR_1 = 'black'
COLOR_2 = 'white'
COLOR_3 = 'red'
COLOR_4 = '#2E2E2E'
COLOR_5 = '#8A4B08'
COLOR_6 = '#DF7401'

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
noteStyler.configure("TNotebook", background="#2e2d2d")
noteStyler.configure("TNotebook.Tab", background="#424242", foreground="white", relief="flat", font=(
    "courier", 15, "bold"), padding=5)


notebook = ttk.Notebook(root, padding=2)
notebook.pack()

homeFrame = Frame(notebook, width=right, height=down, pady=2, padx=6)
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

notebook.add(homeFrame, text="Home")
notebook.add(customerFrame, text="Customers")
notebook.add(productFrame, text="Products")
notebook.add(stockFrame, text="Stocks")
notebook.add(saleFrame, text="Sales")
notebook.add(dueFrame, text="Dues")

#------------------------ Product adding Frame --------------------------------#

productAddFrame_Home = defaultFrame(homeFrame, "Add Product to Invoice", 0, 0)


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

    productNameEntry_home.delete(0, END)
    productWeightEntry_home.delete(0, END)
    productPriceEntry_home.delete(0, END)

    product = productCombo_home.get()

    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()

    cursor.execute(
        f"select product, weight, price from products where product='{product}'")
    product_details = cursor.fetchall()
    product_name = product_details[0][0]
    product_weight = product_details[0][1]
    product_price = product_details[0][2]

    productNameEntry_home.insert(0, product_name)
    productWeightEntry_home.insert(0, product_weight)
    productPriceEntry_home.insert(0, product_price)

    productNameEntry_home.config(state="disabled")
    productWeightEntry_home.config(state="disabled")
    productPriceEntry_home.config(state="disabled", foreground="green")

    conn.commit()

    conn.close()


allProducts = getAllProducts()
choose_product_label = Label(productAddFrame_Home, text="Product:",
                             font="Courier 15 bold").grid(row=0, column=0, sticky=E, padx=10)
productCombo_home = ttk.Combobox(productAddFrame_Home, value=allProducts, width=17,
                                 font="Courier 15")
productCombo_home.set("Choose one...")
productCombo_home.bind("<<ComboboxSelected>>", productCombo)
productCombo_home.grid(row=0, column=1, pady=5)

productNameEntry_home = defaultEntry(
    productAddFrame_Home, "Name", 1, 0, 20, state="disabled")
productWeightEntry_home = defaultEntry(
    productAddFrame_Home, "Weight (g)", 2, 0, 20, state="disabled")
productPriceEntry_home = defaultEntry(
    productAddFrame_Home, "Price (BDT)", 3, 0, 20, state="disabled")
productQuantityEntry_home = defaultEntry(
    productAddFrame_Home, "Quantity", 4, 0, 20)


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


def showProduct_trv_home():
    name = productNameEntry_home.get()
    price = productPriceEntry_home.get()
    quantity = productQuantityEntry_home.get()

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
                                    show="headings", height=11, padding=5, style="Custom.Treeview")
            trv_home.grid(row=0, column=0, columnspan=2)

            trv_home.heading(1, text='Product')
            trv_home.heading(2, text='Price')
            trv_home.heading(3, text='Quanity')
            trv_home.heading(4, text='Amount')
            trv_home.column(1, anchor=CENTER, width=190)
            trv_home.column(2, anchor=CENTER, width=190)
            trv_home.column(3, anchor=CENTER, width=190)
            trv_home.column(4, anchor=CENTER, width=190)
            integerQuantity = int(quantity)

            amount_home = float(price) * integerQuantity
            InsertInTreeView()
            UpdateTreeView()

            productNameEntry_home.config(state="enabled")
            productWeightEntry_home.config(state="enabled")
            productPriceEntry_home.config(state="enabled")

            productNameEntry_home.delete(0, END)
            productWeightEntry_home.delete(0, END)
            productPriceEntry_home.delete(0, END)
            productQuantityEntry_home.delete(0, END)
            totalAmountEntry_home = defaultEntry(
                productsListFrame_home, "Total Amount", 2, 0, 30)

            totalAmountEntry_home.insert(0, getTrvTotal_home())
            totalAmountEntry_home.config(state="disabled", foreground="green")

            def deleteProduct():
                try:
                    selectedProductIID = trv_home.selection()[0]
                    name = trv_home.item(selectedProductIID)["values"][0]

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
                        float_discount_percentage = float(discount_percentage)
                        if float_discount_percentage > 100.0:
                            discountEntry_home.delete(0, END)
                            messagebox.showerror(
                                title="Discount Error", message="The discount ammount cannot be more than 100.")
                        else:
                            fraction_discount_percentage = (
                                float_discount_percentage / 100.0)
                            net_total = (totalAmount_trv_home - (totalAmount_trv_home *
                                                                 fraction_discount_percentage))
                            formatted_net_total = "{:.2f}".format(net_total)

                            getNetTotal_home(formatted_net_total)

                            netAmountEntry_home.config(state="enabled")
                            netAmountEntry_home.delete(0, END)
                            netAmountEntry_home.insert(0, formatted_net_total)
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
                            due_amount = (net_total - float_payment_amount)
                            formatted_due_amount = "{:.2f}".format(due_amount)

                            getDueAmount_home(formatted_due_amount)

                            def saveInvoice():

                                try:
                                    def getSaleCode():
                                        conn = sqlite3.connect(db_path)
                                        cursor = conn.cursor()

                                        new_sale_code = randint(100000, 999999)
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

                                    sale_amount = net_total_home

                                    paid_amount = float_payment_amount

                                    due_amount = due_amount_home

                                    conn = sqlite3.connect(db_path)
                                    cursor = conn.cursor()

                                    cursor.execute("INSERT INTO sales(sale_code, customer_id, sale_amount, paid_amount, due_amount) VALUES (?,?,?,?,?)",
                                                   (int(sale_code), int(customer_id),
                                                    float(sale_amount), float(paid_amount), float(due_amount)))

                                    resposnse = messagebox.askyesno(
                                        title="Confirm Sale", message="Are you sure to save this sale information in database? After saving this you cannot change. Make sure you are aware about what you are doing.")

                                    if resposnse == True:
                                        conn.commit()

                                        conn.close()
                                        messagebox.showinfo(
                                            title="Save Success", message="The information is succesfully saved in database.")
                                        saveButton_home = defaultButton(
                                            productsListFrame_home, "Save Invoice", 9, 0, W+E, state="disabled")

                                    else:
                                        return

                                except Exception as identifier:
                                    messagebox.showerror(
                                        title="Customer Error", message="Please insert customer Information.")

                                def printInvoice():
                                    customerCodeEntry_home.config(
                                        state="enabled")
                                    customerNameEntry_home.config(
                                        state="enabled")
                                    customerPhoneEntry_home.config(
                                        state="enabled")
                                    customerAddressEntry_home.config(
                                        state="enabled")

                                    CustomerSearchCode_home.delete(0, END)
                                    customerCodeEntry_home.delete(0, END)
                                    customerNameEntry_home.delete(0, END)
                                    customerPhoneEntry_home.delete(0, END)
                                    customerAddressEntry_home.delete(0, END)

                                    customerCodeEntry_home.config(
                                        state="disabled")
                                    customerNameEntry_home.config(
                                        state="disabled")
                                    customerPhoneEntry_home.config(
                                        state="disabled")
                                    customerAddressEntry_home.config(
                                        state="disabled")

                                    deleteAll()

                                    netAmountEntry_home.config(state="enabled")
                                    netAmountEntry_home.delete(0, END)
                                    netAmountEntry_home.config(
                                        state="disabled")

                                    paymentEntry_home.delete(0, END)

                                    discountEntry_home.delete(0, END)

                                    dueEntry_home.config(state="enabled")
                                    dueEntry_home.delete(0, END)
                                    dueEntry_home.config(state="disabled")

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
                            dueEntry_home.insert(0, formatted_due_amount)
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
    productAddFrame_Home, "Add Product", 5, 1, W+E, command=showProduct_trv_home)


#------------------------ Products List Frame ------------------------#

productsListFrame_home = defaultFrame(
    homeFrame, "Invoice Items List", 0, 1, rowspan=2)


#------------------------ Display showing at the first in Invoice List but these don't work ----------------------------#

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
                background="#67c392", foreground="#fff", relief="flat", font=(
                    "times", 12), padding=5)
style.map("Custom.Treeview.Heading",
          relief=[('active', 'groove'), ('pressed', 'sunken')])

style.configure("Custom.Treeview", font=("Verdana", 10))

trv_home = ttk.Treeview(productsListFrame_home, columns=(1, 2, 3, 4),
                        show="headings", height=11, padding=5, style="Custom.Treeview")
trv_home.grid(row=0, column=0, columnspan=2)


trv_home.heading(1, text='Product')
trv_home.heading(2, text='Price')
trv_home.heading(3, text='Quanity')
trv_home.heading(4, text='Amount')
trv_home.column(1, anchor=CENTER, width=190)
trv_home.column(2, anchor=CENTER, width=190)
trv_home.column(3, anchor=CENTER, width=190)
trv_home.column(4, anchor=CENTER, width=190)

LLLL = []
for i in LLLL:
    trv_home.insert("", "end", values=i)
totalAmountEntry_home = defaultEntry(
    productsListFrame_home, "Total Amount", 2, 0, 30, state="disabled")

deleteButton_home = defaultButton(
    productsListFrame_home, "Delete Product", 1, 0, W+E, state="disabled")

deleteAllButton_home = defaultButton(
    productsListFrame_home, "Delete All Products", 1, 1, W+E, state="disabled")

discountEntry_home = defaultEntry(
    productsListFrame_home, "Discount (%)", 3, 0, 30, state="disabled")

discountButton_home = defaultButton(
    productsListFrame_home, "Get Net Amount", 4, 1, W+E, state="disabled")

netAmountEntry_home = defaultEntry(
    productsListFrame_home, "Net Amount", 5, 0, 30, state="disabled")

paymentEntry_home = defaultEntry(
    productsListFrame_home, "Payment Amount", 6, 0, 30, state="disabled")

addPaymentButton_home = defaultButton(
    productsListFrame_home, "Add Payment", 7, 1, W+E, state="disabled")

dueEntry_home = defaultEntry(
    productsListFrame_home, "Due Amount", 8, 0, 30, state="disabled")

saveButton_home = defaultButton(
    productsListFrame_home, "Save Invoice", 9, 0, W+E, state="disabled")

printButton_home = defaultButton(
    productsListFrame_home, "Generate PDF Invoice", 9, 1, W+E, state="disabled")

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
                    title="Index Error", message="Please insert a valid code. Or add a new customer")

        except ValueError as e:
            CustomerSearchCode_home.delete(0, END)

            customerCodeEntry_home.config(state="disabled")
            customerNameEntry_home.config(state="disabled")
            customerPhoneEntry_home.config(state="disabled")
            customerAddressEntry_home.config(state="disabled")

            messagebox.showerror(
                title="Code Error", message="Please input a valid customer code with number. Not alphabet.")


CustomerSearchCode_home = defaultEntry(
    customerAddFrame_home, "Customer code", 0, 0, 20)
addCustomerButton_home = defaultButton(
    customerAddFrame_home, "Add Customer", 1, 1, W+E, command=addCustomer_home)

customerCodeEntry_home = defaultEntry(customerAddFrame_home, "Code", 2, 0, 20)
customerNameEntry_home = defaultEntry(customerAddFrame_home, "Name", 3, 0, 20)
customerPhoneEntry_home = defaultEntry(
    customerAddFrame_home, "Phone", 4, 0, 20)
customerAddressEntry_home = defaultEntry(
    customerAddFrame_home, "Address", 5, 0, 20)

customerCodeEntry_home.config(state="disabled")
customerNameEntry_home.config(state="disabled")
customerPhoneEntry_home.config(state="disabled")
customerAddressEntry_home.config(state="disabled")


conn.commit()

conn.close()

root.mainloop()
