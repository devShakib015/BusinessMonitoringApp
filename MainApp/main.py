from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import os
import sqlite3

root = Tk()
root.title("Business Management")
right = 1366
down = 768
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
style = ttk.Style()
style.configure("TNotebook.Tab", relief="flat", font=(
    "courier", 15, "bold"), padding=5)
notebook = ttk.Notebook(root)
notebook.pack()

homeFrame = Frame(notebook, width=right, height=down, pady=10, padx=6)
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

productAddFrame = defaultFrame(homeFrame, "Add Product to Invoice", 0, 0)


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
    nameEntry.config(state="enabled")
    weightEntry.config(state="enabled")
    priceEntry.config(state="enabled")

    nameEntry.delete(0, END)
    weightEntry.delete(0, END)
    priceEntry.delete(0, END)

    product = myCombo.get()

    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()

    cursor.execute(
        f"select product, weight, price from products where product='{product}'")
    product_details = cursor.fetchall()
    product_name = product_details[0][0]
    product_weight = product_details[0][1]
    product_price = product_details[0][2]

    nameEntry.insert(0, product_name)
    weightEntry.insert(0, product_weight)
    priceEntry.insert(0, product_price)

    nameEntry.config(state="disabled")
    weightEntry.config(state="disabled")
    priceEntry.config(state="disabled", foreground="green")

    conn.commit()

    conn.close()


allProducts = getAllProducts()
lbl = Label(productAddFrame, text="Product:",
            font="Courier 15 bold").grid(row=0, column=0, sticky=E, padx=10)
myCombo = ttk.Combobox(productAddFrame, value=allProducts, width=17,
                       font="Courier 15")
myCombo.set("Choose one...")
myCombo.bind("<<ComboboxSelected>>", productCombo)
myCombo.grid(row=0, column=1, pady=5)

nameEntry = defaultEntry(productAddFrame, "Name", 1, 0, 20)
weightEntry = defaultEntry(productAddFrame, "Weight (g)", 2, 0, 20)
priceEntry = defaultEntry(productAddFrame, "Price (BDT)", 3, 0, 20)
quantityEntry = defaultEntry(productAddFrame, "Quantity", 4, 0, 20)


def getTrvTotal():
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


def showProduct():
    name = nameEntry.get()
    price = priceEntry.get()
    quantity = quantityEntry.get()

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
                                   "total_cost": totalCost
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
                    trv.insert("", "end", values=i)

                conn.commit()
                conn.close()

            trv = ttk.Treeview(productsListFrame, columns=(1, 2, 3, 4),
                               show="headings", height=12, padding=5, style="Custom.Treeview")
            trv.grid(row=0, column=0, columnspan=2)

            trv.heading(1, text='Product')
            trv.heading(2, text='Price')
            trv.heading(3, text='Quanity')
            trv.heading(4, text='Amount')
            trv.column(1, anchor=CENTER, width=190)
            trv.column(2, anchor=CENTER, width=190)
            trv.column(3, anchor=CENTER, width=190)
            trv.column(4, anchor=CENTER, width=190)
            integerQuantity = int(quantity)

            totalCost = float(price) * integerQuantity
            InsertInTreeView()
            UpdateTreeView()

            nameEntry.config(state="enabled")
            weightEntry.config(state="enabled")
            priceEntry.config(state="enabled")

            nameEntry.delete(0, END)
            weightEntry.delete(0, END)
            priceEntry.delete(0, END)
            quantityEntry.delete(0, END)
            totalCostEntry = defaultEntry(
                productsListFrame, "Total Amount", 2, 0, 30)

            totalCostEntry.insert(0, getTrvTotal())
            totalCostEntry.config(state="disabled", foreground="green")

            def deleteProduct():
                try:
                    selectedProductIID = trv.selection()[0]
                    name = trv.item(selectedProductIID)["values"][0]

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

                    trv.delete(*trv.get_children())

                    UpdateTreeView()
                    totalCostEntry.config(state="enabled")
                    totalCostEntry.delete(0, END)
                    totalCostEntry.insert(0, getTrvTotal())
                    totalCostEntry.config(state="disabled", foreground="green")

                except Exception as e:
                    messagebox.showerror(
                        title="Selection error", message="You didn't select any product from the list.")

                    trv.delete(*trv.get_children())

                    UpdateTreeView()
                    totalCostEntry.config(state="enabled")
                    totalCostEntry.delete(0, END)
                    totalCostEntry.insert(0, getTrvTotal())
                    totalCostEntry.config(state="disabled", foreground="green")

            def deleteAll():

                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute(
                    f"DELETE FROM invoice_items")

                conn.commit()

                conn.close()

                trv.delete(*trv.get_children())

                UpdateTreeView()
                totalCostEntry.config(state="enabled")
                totalCostEntry.delete(0, END)
                totalCostEntry.insert(0, getTrvTotal())
                totalCostEntry.config(state="disabled", foreground="green")

            deleteButton = defaultButton(
                productsListFrame, "Delete Product", 1, 0, W+E, command=deleteProduct)

            deleteAllButton = defaultButton(
                productsListFrame, "Delete All Products", 1, 1, W+E, command=deleteAll)

        except Exception as e:
            quantityEntry.delete(0, END)
            messagebox.showerror(title="Quantity Error",
                                 message="Input a valid quantity")


addProductButton = defaultButton(
    productAddFrame, "Add Product", 5, 1, W+E, command=showProduct)


#------------------------ Products List Frame ------------------------#

productsListFrame = defaultFrame(
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

trv = ttk.Treeview(productsListFrame, columns=(1, 2, 3, 4),
                   show="headings", height=12, padding=5, style="Custom.Treeview")
trv.grid(row=0, column=0, columnspan=2)


trv.heading(1, text='Product')
trv.heading(2, text='Price')
trv.heading(3, text='Quanity')
trv.heading(4, text='Amount')
trv.column(1, anchor=CENTER, width=190)
trv.column(2, anchor=CENTER, width=190)
trv.column(3, anchor=CENTER, width=190)
trv.column(4, anchor=CENTER, width=190)

LLLL = []
for i in LLLL:
    trv.insert("", "end", values=i)
totalCostEntry = defaultEntry(
    productsListFrame, "Total Amount", 2, 0, 30)
totalCostEntry.config(state="disabled")

deleteButton = defaultButton(
    productsListFrame, "Delete Product", 1, 0, W+E, state="disabled")

deleteAllButton = defaultButton(
    productsListFrame, "Delete All Products", 1, 1, W+E, state="disabled")


#------------------------ Customer Add Frame ------------------------#

customerAddFrame = defaultFrame(homeFrame, "Add Customer to Invoice", 1, 0)


def addCustomer():
    # lbl = Label(root, text=myCombo.get()).grid(row=row, column=column+2)

    code = searchCode.get()

    if code == "":
        messagebox.showerror(title="Error Code.",
                             message="Please input a valid code")
        searchCode.delete(0, END)

        codeEntry.config(state="disabled")
        customerNameEntry.config(state="disabled")
        phoneEntry.config(state="disabled")
        addressEntry.config(state="disabled")
    else:

        codeEntry.config(state="enabled")
        customerNameEntry.config(state="enabled")
        phoneEntry.config(state="enabled")
        addressEntry.config(state="enabled")

        codeEntry.delete(0, END)
        customerNameEntry.delete(0, END)
        phoneEntry.delete(0, END)
        addressEntry.delete(0, END)

        try:
            integerCode = int(code)
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

                codeEntry.insert(0, customer_code)
                customerNameEntry.insert(0, customer_name)
                phoneEntry.insert(0, customer_phone)
                addressEntry.insert(0, customer_address)

                codeEntry.config(state="disabled")
                customerNameEntry.config(state="disabled")
                phoneEntry.config(state="disabled")
                addressEntry.config(state="disabled")

                conn.commit()

                conn.close()

            except Exception as identifier:

                codeEntry.config(state="disabled")
                customerNameEntry.config(state="disabled")
                phoneEntry.config(state="disabled")
                addressEntry.config(state="disabled")
                messagebox.showerror(
                    title="Index Error", message="Please insert a valid code. Or add a new customer")

        except ValueError as e:
            searchCode.delete(0, END)

            codeEntry.config(state="disabled")
            customerNameEntry.config(state="disabled")
            phoneEntry.config(state="disabled")
            addressEntry.config(state="disabled")

            messagebox.showerror(
                title="Code Error", message="Please input a valid customer code with number. Not alphabet.")


searchCode = defaultEntry(customerAddFrame, "Customer code", 0, 0, 20)
addCustomerButton = defaultButton(
    customerAddFrame, "Add Customer", 1, 1, W+E, command=addCustomer)
codeEntry = defaultEntry(customerAddFrame, "Code", 2, 0, 20)
customerNameEntry = defaultEntry(customerAddFrame, "Name", 3, 0, 20)
phoneEntry = defaultEntry(customerAddFrame, "Phone", 4, 0, 20)
addressEntry = defaultEntry(customerAddFrame, "Address", 5, 0, 20)

codeEntry.config(state="disabled")
customerNameEntry.config(state="disabled")
phoneEntry.config(state="disabled")
addressEntry.config(state="disabled")


conn.commit()

conn.close()

root.mainloop()
