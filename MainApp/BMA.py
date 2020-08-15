from tkinter import *
from tkinter import ttk
from tkinter import messagebox, filedialog
import os
import sqlite3
import pytz
from datetime import datetime
import webbrowser

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont

import xlsxwriter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "main.db")
icon_path = os.path.join(BASE_DIR, "b.ico")


def mainApp(state):
    root = Tk()
    root.title("Business Management")
    right = root.winfo_screenwidth()  # 1280  #
    down = root.winfo_screenheight()  # 720  #
    # root.geometry(f"{right}x{down}")
    # root.geometry(f"{right}x{down}")

    #------------------------ Default width and height --------------------------------#

    entryWidth = int(0.01442*float(right))
    fontSize = int(0.00829*float(right))

    # width = root.winfo_width()
    # height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (right // 2)
    y = (root.winfo_screenheight() // 2) - (down // 2)
    root.geometry(f"{right}x{down}+{x}+{y}")
    root.iconbitmap(icon_path)

    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()

    #------------------------ Default Frame Function ----------------------------------------#

    def defaultFrame(parent, caption, row, column, **options):
        frame = LabelFrame(parent, text=caption, padx=20,
                           pady=20, font=f"Courier {fontSize} bold")
        frame.grid(row=row, column=column, padx=20,
                   pady=20, **options, sticky="nswe")
        return frame

    #------------------------ Default Entry Function ----------------------------------------#

    def defaultEntry(parent, caption, row, column, width, **options):
        def make_menu(w):
            global the_menu
            the_menu = Menu(w, tearoff=0)
            the_menu.add_command(label="Cut")
            the_menu.add_command(label="Copy")
            the_menu.add_command(label="Paste")

        def show_menu(e):
            try:
                w = e.widget
                the_menu.entryconfigure("Cut",
                                        command=lambda: w.event_generate("<<Cut>>"))
                the_menu.entryconfigure("Copy",
                                        command=lambda: w.event_generate("<<Copy>>"))
                the_menu.entryconfigure("Paste",
                                        command=lambda: w.event_generate("<<Paste>>"))
                the_menu.tk.call("tk_popup", the_menu, e.x_root, e.y_root)
            except Exception as identifier:
                make_menu(parent)

        make_menu(parent)

        Label(parent, text=caption + ": ",
              font=f"Courier {fontSize} bold").grid(row=row, column=column, sticky=E)
        entry = ttk.Entry(parent, width=width, justify=RIGHT,
                          font=f"Courier {fontSize} bold", **options)
        entry.grid(row=row, column=column + 1, pady=5, sticky=W+E)
        entry.bind_class("TEntry", "<Button-3><ButtonRelease-3>", show_menu)

        return entry

    #------------------------ Default Button Function ----------------------------------------#

    def defaultButton(parent, caption, row, column, sticky, **options):
        ttk.Style().configure(
            "TButton", font=f"verdana {fontSize} bold", foreground="#e4324c")
        button = ttk.Button(parent, text=caption, cursor="hand2",
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

    noteStyler.configure("TNotebook.Tab", background="#204051", width=17, foreground="white", relief=GROOVE, font=(
        "verdana", int(0.00629*float(right))),  padding=[5, 10, 10, 10])

    noteStyler.map("TNotebook.Tab", background=[
        ("selected", "#e4324c")], foreground=[("selected", "white")])

    #
    notebook = ttk.Notebook(root, padding=0, width=right, height=down)
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

    saleFrame = Frame(notebook, width=right, height=down,
                      pady=10, padx=(right * 0.040))
    saleFrame.pack(fill="both", expand=1)

    dueFrame = Frame(notebook, width=right, height=down, pady=10)
    dueFrame.pack(fill="both", expand=1)

    daily_stock_Frame = Frame(notebook, width=right, height=down, pady=10)
    daily_stock_Frame.pack(fill="both", expand=1)

    statsFrame = Frame(notebook, width=right, height=down, pady=50, padx=50)
    statsFrame.pack(fill="both", expand=1)

    productDetailsFrame = Frame(notebook, width=right,
                                height=down, pady=50, padx=(right * 0.105))
    productDetailsFrame.pack(fill="both", expand=1)

    aboutFrame = Frame(notebook, width=right, height=down, pady=30, padx=30)
    aboutFrame.pack(fill="both", expand=1)

    notebook.add(homeFrame, text="Billings")
    notebook.add(customerFrame, text="Customers")
    notebook.add(dueFrame, text="Pay Dues")
    notebook.add(saleFrame, text="Sales")
    notebook.add(productFrame, text="Add Products",
                 state=state)
    notebook.add(stockFrame, text="Add Stocks",
                 state=state)
    notebook.add(productDetailsFrame, text="Product Details",
                 state=state)
    notebook.add(daily_stock_Frame, text="Stock Management",
                 state=state)
    notebook.add(statsFrame, text="Statistics",
                 state=state)
    notebook.add(aboutFrame, text="About")

    # notebook.place(relx=0, rely=0, relheight=1, relwidth=1)

    # notebook.tab(6, tabposition="ne")

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

    Create Invoice Sales

    """

    def create_invoice(invoice_number, invoice_date, customer_code, customer_name, customer_phone, customer_address, product_tuple_list, total_sales, discount_rate, discount_amount, net_sales, payment_amount, due_amount):

        # convert the font so it is compatible
        pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
        pdfmetrics.registerFont(TTFont('Verdana', 'Verdana.ttf'))

        # Page information
        page_width = 595
        page_height = 842
        margin = 13

        i_n = f"{invoice_number}"
        i_d = f"{invoice_date}"
        c_c = f"{customer_code}"
        c_n = f"{customer_name}"
        c_p = f"{customer_phone}"
        c_a = f"{customer_address}"

        l = product_tuple_list

        outfiledir = filedialog.askdirectory()
        outfilepath = os.path.join(outfiledir, i_n + '_' + c_n + '.pdf')
        # Creating a pdf file and setting a naming convention
        c = canvas.Canvas(outfilepath)
        c.setPageSize((page_width, page_height))
        from reportlab.lib.colors import HexColor
        from reportlab.lib import colors
        from reportlab.lib.colors import Color
        red50transparent = Color(100, 0, 0, alpha=0.5)
        blue30transparent = Color(0, 0, 100, alpha=0.3)
        goodColor = HexColor("#2b92c5")

        # sets fill color like orange

        # Invoice information
        c.setFont('Verdana', 20)
        text = 'Biocin Bangladesh'
        # text_width = stringWidth(text, 'Arial', 10)
        c.drawString(4*margin, page_height - margin*3, text)

        c.setFont('Verdana', 20)
        text = 'INVOICE'
        # text_width = stringWidth(text, 'Arial', 10)
        c.drawString(4*margin + 280, page_height - margin*3, text)

        y = page_height - margin*6
        x = 4*margin
        # x2 = x + 30

        # Invoice number
        c.setFont('Verdana', 10)
        text = 'Address: '
        c.drawString(x, y, text)
        tw = stringWidth(text, 'Verdana', 10)
        c.drawString(x + tw, y, "RP Gate, Rajendrapur, Gazipur, Dhaka")

        text = 'Invoice No: '
        c.drawString(x + 280, y, text)
        tw = stringWidth(text, 'Verdana', 10)
        c.drawString(x + 280 + tw, y, i_n)
        y -= margin

        text = 'Phone: '
        c.drawString(x, y, text)
        tw = stringWidth(text, 'Verdana', 10)
        c.drawString(x + tw, y, "01716-573618")

        text = 'Invoice Date: '
        c.drawString(x + 280, y, text)
        tw = stringWidth(text, 'Verdana', 10)
        c.drawString(x + 280 + tw, y, i_d)
        y -= margin

        text = 'Email: '
        c.drawString(x, y, text)
        tw = stringWidth(text, 'Verdana', 10)
        c.drawString(x + tw, y, "biocinbangladesh@gmail.com")

        text = 'Customer Code: '
        c.drawString(x + 280, y, text)
        tw = stringWidth(text, 'Verdana', 10)
        c.drawString(x + 280 + tw, y, c_c)
        y -= margin

        text = 'Customer Name: '
        c.drawString(x + 280, y, text)
        tw = stringWidth(text, 'Verdana', 10)
        c.drawString(x + 280 + tw, y, c_n)
        y -= margin

        text = 'Customer Phone: '
        c.drawString(x + 280, y, text)
        tw = stringWidth(text, 'Verdana', 10)
        c.drawString(x + 280 + tw, y, c_p)
        y -= margin

        text = 'Customer Address: '
        c.drawString(x + 280, y, text)
        tw = stringWidth(text, 'Verdana', 10)
        c.drawString(x + 280 + tw, y, c_a)
        y -= margin
        y -= margin

        box_x_left = 45
        box_x_right = 550
        box_y_top = y
        box_y_bottom = 150

        c.setFillColor(HexColor("#EAEAEC"))
        c.rect(box_x_left, box_y_bottom, 505, y - 170, fill=True, stroke=True)

        c.line(box_x_left, box_y_top, box_x_right, box_y_top)
        c.line(box_x_left, box_y_bottom, box_x_right, box_y_bottom)
        c.line(box_x_left, box_y_top, box_x_left, box_y_bottom)
        c.line(box_x_right, box_y_top, box_x_right, box_y_bottom)

        c.setFillColor(goodColor)
        c.rect(box_x_left, box_y_top - 20, 505, 20, fill=True, stroke=True)

        c.line(box_x_left, box_y_top - 20, box_x_right, box_y_top - 20)
        y -= margin

        c.setFillColor(colors.white)
        c.setFont('Verdana', 10)
        p_text = "Product Name"
        p_text_width = stringWidth(p_text, 'Arial', 10)
        c.drawString(box_x_left + (200 - p_text_width)/2, y, p_text)

        p_text = "Weight (g)"
        p_text_width = stringWidth(p_text, 'Arial', 10)
        c.drawString(box_x_left + 100 + (280 - p_text_width)/2, y, p_text)

        pr_text = "Price"
        pr_text_width = stringWidth(pr_text, 'Arial', 10)
        c.drawString(box_x_left + 140 + (340 - pr_text_width)/2, y, pr_text)

        q_text = "Quantity"
        q_text_width = stringWidth(q_text, 'Arial', 10)
        c.drawString(box_x_left + 167 + (400 - q_text_width)/2, y, q_text)

        t_text = "Total Cost"
        t_text_width = stringWidth(t_text, 'Arial', 10)
        c.drawString(box_x_left + 180 + (550 - t_text_width)/2, y, t_text)

        c.line(box_x_left + 200, box_y_top, box_x_left + 200, box_y_bottom)
        c.line(box_x_left + 280, box_y_top, box_x_left + 280, box_y_bottom)
        c.line(box_x_left + 340, box_y_top, box_x_left + 340, box_y_bottom)
        c.line(box_x_left + 400, box_y_top, box_x_left + 400, box_y_bottom)

        p_name_pos = box_x_left + 30
        p_weight_pos = box_x_left + 230
        p_price_pos = box_x_left + 295
        p_quantity_pos = box_x_left + 360
        p_total_pos = box_x_left + 420

        box_top_pos = box_y_top - 35

        c.setFillColor(colors.black)
        for i in l:
            c.drawString(p_name_pos, box_top_pos, str(
                l.index(i) + 1) + ". " + str(i[0]))
            c.drawString(p_weight_pos, box_top_pos, str(i[1]))
            c.drawString(p_price_pos, box_top_pos, str(i[2]))
            c.drawString(p_quantity_pos, box_top_pos, str(i[3]))
            c.drawString(p_total_pos, box_top_pos, str(i[4]))
            box_top_pos -= 15

        box_bottom_pos = box_y_bottom-20

        t_s_text = "Total Sales: "
        t_s_text_width = stringWidth(t_s_text, 'Arial', 10)
        c.drawString(box_x_left + 130 + (380 - t_s_text_width) /
                     2, box_bottom_pos, t_s_text)

        t_text = f"{total_sales}"
        t_text_width = stringWidth(t_text, 'Arial', 10)
        c.drawString(box_x_left + 170 + (555 - t_text_width) /
                     2, box_bottom_pos, t_text)

        box_bottom_pos -= 20

        d_text = f"Discount: ({discount_rate}%)"
        d_text_width = stringWidth(d_text, 'Arial', 10)
        c.drawString(box_x_left + 130 + (380 - d_text_width) /
                     2, box_bottom_pos, d_text)

        t_text = f"({discount_amount})"
        t_text_width = stringWidth(t_text, 'Arial', 10)
        c.drawString(box_x_left + 170 + (555 - t_text_width) /
                     2, box_bottom_pos, t_text)
        box_bottom_pos -= 8

        c.line(box_x_left + 200, box_bottom_pos, 555, box_bottom_pos)

        box_bottom_pos -= 12

        d_text = "Net Sales: "
        d_text_width = stringWidth(d_text, 'Arial', 10)
        c.drawString(box_x_left + 130 + (380 - d_text_width) /
                     2, box_bottom_pos, d_text)

        t_text = f"{net_sales}"
        t_text_width = stringWidth(t_text, 'Arial', 10)
        c.drawString(box_x_left + 170 + (555 - t_text_width) /
                     2, box_bottom_pos, t_text)

        box_bottom_pos -= 20

        d_text = "Paying amount: "
        d_text_width = stringWidth(d_text, 'Arial', 10)
        c.drawString(box_x_left + 130 + (380 - d_text_width) /
                     2, box_bottom_pos, d_text)

        t_text = f"({payment_amount})"
        t_text_width = stringWidth(t_text, 'Arial', 10)
        c.drawString(box_x_left + 170 + (555 - t_text_width) /
                     2, box_bottom_pos, t_text)

        box_bottom_pos -= 8

        c.line(box_x_left + 200, box_bottom_pos, 555, box_bottom_pos)

        box_bottom_pos -= 12

        d_text = "Due amount: "
        d_text_width = stringWidth(d_text, 'Arial', 10)
        c.drawString(box_x_left + 130 + (380 - d_text_width) /
                     2, box_bottom_pos, d_text)
        c.setFillColor(colors.red)
        t_text = f"{due_amount}"
        t_text_width = stringWidth(t_text, 'Arial', 10)
        c.drawString(box_x_left + 170 + (555 - t_text_width) /
                     2, box_bottom_pos, t_text)

        c.setFillColor(colors.black)
        text = "Authorized Signature"
        tw = stringWidth(text, "Verdana", 10)
        c.drawString(box_x_left, box_bottom_pos + 48, text)
        c.line(box_x_left - 5, box_bottom_pos+12+48,
               box_x_left + tw + 5, box_bottom_pos+12+48)

        text = "Customer Signature"
        tw = stringWidth(text, "Verdana", 10)
        c.drawString(box_x_left, box_bottom_pos, text)
        c.line(box_x_left - 5, box_bottom_pos+12,
               box_x_left + tw + 5, box_bottom_pos+12)

        c.save()

    def print_as_excel(tuple_list):
        outfiledir = filedialog.asksaveasfilename(
            initialdir="/", defaultextension=".xlxs", title="Select file", filetypes=(("Excel Files", "*.xlsx"), ("all files", "*.*")))

        with xlsxwriter.Workbook(outfiledir) as workbook:
            worksheet = workbook.add_worksheet()

            for row_num, data in enumerate(tuple_list):
                worksheet.write_row(row_num, 0, data)

    def create_due_invoice(invoice_date, customer_code, customer_name, customer_phone, customer_address, previous_due, new_due_payment_amount, current_due):

        # convert the font so it is compatible
        pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
        pdfmetrics.registerFont(TTFont('Verdana', 'Verdana.ttf'))

        # Page information
        page_width = 595
        page_height = 842
        margin = 13

        i_d = f"{invoice_date}"
        c_c = f"{customer_code}"
        c_n = f"{customer_name}"
        c_p = f"{customer_phone}"
        c_a = f"{customer_address}"

        timeZone = pytz.timezone("asia/dhaka")

        ct = datetime.now(timeZone)
        due_date_code = ct.strftime(
            "%Y%m%d%H%M%S")

        outfiledir = filedialog.askdirectory()
        outfilepath = os.path.join(
            outfiledir, c_c + "_" + due_date_code + "_" + c_n.split()[0] + "_" + c_n.split()[1] + '_due_payment.pdf')
        # Creating a pdf file and setting a naming convention
        c = canvas.Canvas(outfilepath)
        c.setPageSize((page_width, page_height))
        from reportlab.lib.colors import HexColor
        from reportlab.lib import colors
        from reportlab.lib.colors import Color
        red50transparent = Color(100, 0, 0, alpha=0.5)
        blue30transparent = Color(0, 0, 100, alpha=0.3)
        goodColor = HexColor("#2b92c5")

        # sets fill color like orange

        y = page_height - margin*10
        x = 4*margin

        # Invoice information
        c.setFont('Verdana', 20)
        text = 'Biocin Bangladesh'
        # text_width = stringWidth(text, 'Arial', 10)
        c.drawString(4*margin, page_height - margin*6, text)

        c.setFont('Verdana', 20)
        text = 'DUE INVOICE'
        # text_width = stringWidth(text, 'Arial', 10)
        c.drawString(4*margin + 280, page_height - margin*6, text)

        # x2 = x + 30

        # Invoice number
        c.setFont('Verdana', 10)
        text = 'Address: '
        c.drawString(x, y, text)
        tw = stringWidth(text, 'Verdana', 10)
        c.drawString(x + tw, y, "RP Gate, Rajendrapur, Gazipur, Dhaka")

        text = 'Invoice Date: '
        c.drawString(x + 280, y, text)
        tw = stringWidth(text, 'Verdana', 10)
        c.drawString(x + 280 + tw, y, i_d)
        y -= margin

        text = 'Phone: '
        c.drawString(x, y, text)
        tw = stringWidth(text, 'Verdana', 10)
        c.drawString(x + tw, y, "01716-573618")

        text = 'Customer Code: '
        c.drawString(x + 280, y, text)
        tw = stringWidth(text, 'Verdana', 10)
        c.drawString(x + 280 + tw, y, c_c)
        y -= margin

        text = 'Email: '
        c.drawString(x, y, text)
        tw = stringWidth(text, 'Verdana', 10)
        c.drawString(x + tw, y, "biocinbangladesh@gmail.com")

        text = 'Customer Name: '
        c.drawString(x + 280, y, text)
        tw = stringWidth(text, 'Verdana', 10)
        c.drawString(x + 280 + tw, y, c_n)
        y -= margin

        text = 'Customer Phone: '
        c.drawString(x + 280, y, text)
        tw = stringWidth(text, 'Verdana', 10)
        c.drawString(x + 280 + tw, y, c_p)
        y -= margin

        text = 'Customer Address: '
        c.drawString(x + 280, y, text)
        tw = stringWidth(text, 'Verdana', 10)
        c.drawString(x + 280 + tw, y, c_a)
        y -= margin
        y -= margin*2

        box_bottom = y - 400

        c.setFillColor(HexColor("#EAEAEC"))
        c.rect(x, y - 400, 490, 400, fill=True, stroke=True)

        c.setFont('Verdana', 15)
        c.setFillColor(colors.black)

        y -= 80
        t_s_text = "Previous Due: "
        tw = stringWidth(t_s_text, 'Arial', 15)
        c.drawString(x + 100, y-40, t_s_text)

        t_text = f"{previous_due}"
        t_text_width = stringWidth(t_text, 'Arial', 15)
        c.drawString(x + 350, y-40, t_text)

        y -= 25

        t_s_text = "Due Payment Now: "
        tw = stringWidth(t_s_text, 'Arial', 15)
        c.drawString(x + 100, y-40, t_s_text)

        t_text = f"({new_due_payment_amount})"
        t_text_width = stringWidth(t_text, 'Arial', 15)
        c.drawString(x + 350, y-40, t_text)

        y -= 25
        c.line(x + 50, y-27, x + 430, y-27)
        y -= 10

        t_s_text = "Current Due: "
        tw = stringWidth(t_s_text, 'Arial', 15)
        c.drawString(x + 100, y-40, t_s_text)

        c.setFillColor(colors.red)
        t_text = f"{current_due}"
        t_text_width = stringWidth(t_text, 'Arial', 15)
        c.drawString(x + 350, y-40, t_text)

        c.setFillColor(colors.black)
        box_bottom -= 80

        text = "Authorized Signature"
        tw = stringWidth(text, "Verdana", 15)
        c.drawString(x + 10, box_bottom, text)
        c.line(x + 10 - 5, box_bottom+22,
               x + 10 + tw + 5, box_bottom+22)

        text = "Customer Signature"
        tw = stringWidth(text, "Verdana", 15)
        c.drawString(x + 320, box_bottom, text)
        c.line(x + 320 - 5, box_bottom+22,
               x + 320 + tw + 5, box_bottom+22)

        c.save()

    """


    Stock Management Start


    """

    def stockManagement():

        def stockManagement_trv_list(date):

            trv_stock_managementFrame = defaultFrame(
                daily_stock_Frame, f"Daily Stock Management - {date}", 0, 1)

            trv_stock_management = ttk.Treeview(trv_stock_managementFrame, columns=(
                1, 2, 3, 4, 5), show="headings", height=int(0.02300*float(down)), padding=5, style="Custom.Treeview")
            trv_stock_management.grid(row=0, column=0, columnspan=2)

            trv_stock_management.heading(1, text='ID')
            trv_stock_management.heading(2, text='Product')
            trv_stock_management.heading(3, text='Weight')
            trv_stock_management.heading(4, text='Price')
            trv_stock_management.heading(5, text='Stock Sold')

            trv_stock_management.column(1, anchor=CENTER,
                                        width=int(0.0600*float(right)))
            trv_stock_management.column(2, anchor=CENTER,
                                        width=int(0.1000*float(right)))
            trv_stock_management.column(
                3, anchor=CENTER, width=int(0.1000*float(right)))
            trv_stock_management.column(
                4, anchor=CENTER, width=int(0.1000*float(right)))
            trv_stock_management.column(
                5, anchor=CENTER, width=int(0.1000*float(right)))

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute(
                f"select products.ID, products.product, products.weight, products.price, sum(stocks_removed.quantity) from stocks_removed join products on stocks_removed.product_id=products.ID where stocks_removed.created_at like '%{date}%' GROUP by stocks_removed.product_id")
            stock_management_tuple_list = cursor.fetchall()

            conn.commit()
            conn.close()

            for i in stock_management_tuple_list:
                trv_stock_management.insert("", "end", values=i)

            trv_total_entry = defaultEntry(
                trv_stock_managementFrame, "Total items in the list", 1, 0, entryWidth)
            trv_total_entry.insert(0, f"{len(stock_management_tuple_list)}")
            trv_total_entry.config(state="disabled")

            def printDetails():
                print_as_excel(stock_management_tuple_list)

            printDetailsButton = defaultButton(
                trv_stock_managementFrame, "Generate Excel List", 2, 1, W+E, command=printDetails)

        timeZone = pytz.timezone("asia/dhaka")
        x = datetime.now(timeZone)
        date = x.now().date()
        stockManagement_trv_list(date)

        search_stock_management_frame = defaultFrame(
            daily_stock_Frame, "Search By date", 0, 0)

        def searchStock_management_button():
            query = searchEntry_stock_management.get()
            stockManagement_trv_list(query)

        searchEntry_stock_management = defaultEntry(
            search_stock_management_frame, "Search", 0, 0, entryWidth)
        searchButton_stock_management = defaultButton(
            search_stock_management_frame, "Search", 1, 1, W+E, command=searchStock_management_button)

        def resetStock_management_button():
            stockManagement_trv_list(date)

        resetButton_stock_management = defaultButton(
            search_stock_management_frame, "Reset", 1, 0, W+E, command=resetStock_management_button)

    stockManagement()

    """


    Stats Start


    """

    def stats():

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("select sum(sale_amount), sum(paid_amount) from sales")
        sales_stats_info = cursor.fetchall()
        net_sales_sats = 0
        net_paid_sats = 0

        if sales_stats_info[0][0] != None or sales_stats_info[0][1] != None:
            net_sales_sats = sales_stats_info[0][0]
            net_paid_sats = sales_stats_info[0][1]

        cursor.execute("select sum(amount) from duesPaid")
        dusePaid_stats_info = cursor.fetchall()
        net_duesPaid_stats = 0
        if dusePaid_stats_info[0][0] != None:
            net_duesPaid_stats = dusePaid_stats_info[0][0]

        total_payment_get_stats = net_paid_sats + net_duesPaid_stats

        total_due_stats = net_sales_sats - total_payment_get_stats

        stats_label = Label(statsFrame, text="STATISTICS",
                            font="verdana 40 bold underline", foreground="green").grid(row=0, column=0, pady=50, columnspan=2)

        total_sales_stats_entry = defaultEntry(
            statsFrame, "Total Sales", 1, 0, entryWidth)
        total_payment_get_stats_entry = defaultEntry(
            statsFrame, "Total Payment Get", 2, 0, entryWidth)
        total_due_stats_entry = defaultEntry(
            statsFrame, "Total Dues", 3, 0, entryWidth)

        total_sales_stats_entry.insert(0, net_sales_sats)
        total_payment_get_stats_entry.insert(0, total_payment_get_stats)
        total_due_stats_entry.insert(0, total_due_stats)

        total_sales_stats_entry.config(state="disabled")
        total_payment_get_stats_entry.config(state="disabled")
        total_due_stats_entry.config(state="disabled")

        conn.commit()
        conn.close()

    stats()

    """


    Product Detials Start


    """

    def updateProductsDetails():

        def getProductDetails(ID):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute(f"select * from products where ID={ID}")
            initial_product_details = cursor.fetchall()

            product_name = initial_product_details[0][1]
            product_weight = initial_product_details[0][2]
            product_selling_price = initial_product_details[0][3]

            conn.commit()

            cursor.execute(
                f"select sum(quantity), sum(price) from stocks where product_id={ID}")
            product_costing_details = cursor.fetchall()
            product_total_stock_added = 0
            product_total_stock_price = 0

            if product_costing_details[0][0] != None:
                product_total_stock_added = product_costing_details[0][0]
                product_total_stock_price = product_costing_details[0][1]

            if product_total_stock_added == 0:
                product_cost_price = 0.0
            else:
                product_cost_price = float(
                    product_total_stock_price) / float(product_total_stock_added)

            product_cost_price_format = "{:.2f}".format(product_cost_price)

            conn.commit()

            cursor.execute(
                f"select sum(quantity) from stocks_removed where product_id={ID}")
            product_selling_details = cursor.fetchall()
            product_total_stock_sold = 0
            if product_selling_details[0][0] != None:
                product_total_stock_sold = product_selling_details[0][0]

            product_total_stock_remaining = int(
                product_total_stock_added) - int(product_total_stock_sold)

            product_details_tuple = (product_name, product_weight, product_selling_price, product_cost_price_format,
                                     product_total_stock_added, product_total_stock_sold, product_total_stock_remaining)

            conn.commit()
            conn.close()

            return product_details_tuple

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT ID from products")
        products_IDS_List_tuple = cursor.fetchall()

        conn.commit()
        conn.close()

        if products_IDS_List_tuple != None:
            products_ids_list = []
            for p in products_IDS_List_tuple:
                products_ids_list.append(p[0])

            product_details_list = []
            for id in products_ids_list:
                product_details_list.append(getProductDetails(id))
        else:
            product_details_list = []

        trv_product_details = ttk.Treeview(productDetailsFrame, columns=(
            1, 2, 3, 4, 5, 6, 7), show="headings", height=int(0.02500*float(down)), padding=5, style="Custom.Treeview")
        trv_product_details.grid(row=0, column=0, columnspan=2)

        trv_product_details.heading(1, text='Name')
        trv_product_details.heading(2, text='Weight')
        trv_product_details.heading(3, text='Selling Price')
        trv_product_details.heading(4, text='Cost Price')
        trv_product_details.heading(5, text='Total Stock Added')
        trv_product_details.heading(6, text='Total Stock Sold')
        trv_product_details.heading(7, text='Remaining Stock')

        trv_product_details.column(1, anchor=CENTER,
                                   width=int(0.1000*float(right)))
        trv_product_details.column(2, anchor=CENTER,
                                   width=int(0.0700*float(right)))
        trv_product_details.column(
            3, anchor=CENTER, width=int(0.1000*float(right)))
        trv_product_details.column(
            4, anchor=CENTER, width=int(0.1000*float(right)))
        trv_product_details.column(
            5, anchor=CENTER, width=int(0.1000*float(right)))
        trv_product_details.column(
            6, anchor=CENTER, width=int(0.1000*float(right)))
        trv_product_details.column(
            7, anchor=CENTER, width=int(0.1000*float(right)))

        for i in product_details_list:
            trv_product_details.insert("", "end", values=i)

        trv_total_entry = defaultEntry(
            productDetailsFrame, "Total items in the list", 1, 0, entryWidth)
        trv_total_entry.insert(0, f"{len(product_details_list)}")
        trv_total_entry.config(state="disabled")

        def printDetails():
            print_as_excel(product_details_list)

        printDetailsButton = defaultButton(
            productDetailsFrame, "Generate Excel List", 2, 1, W+E, command=printDetails)

    updateProductsDetails()

    """


    Pay Dues Start


    """

    DueList_frame = defaultFrame(dueFrame, "Paying Dues List", 0, 1, rowspan=2)
    main_dues_sql_query = "select customers.customer_code, customers.first_name, customers.phone, duesPaid.amount, duesPaid.created_at from duesPaid INNER JOIN customers on duesPaid.customer_id=customers.ID order by duesPaid.ID desc"
    payDues_frame = defaultFrame(dueFrame, "Pay Dues", 0, 0)

    def updateDueList(sql_query):
        trv_dues = ttk.Treeview(DueList_frame, columns=(
            1, 2, 3, 4, 5), show="headings", height=int(0.02500*float(down)), padding=5, style="Custom.Treeview")
        trv_dues.grid(row=0, column=0, columnspan=2)

        trv_dues.heading(1, text='Code')
        trv_dues.heading(2, text='Name')
        trv_dues.heading(3, text='Phone')
        trv_dues.heading(4, text='Due Amount')
        trv_dues.heading(5, text='Date')

        trv_dues.column(1, anchor=CENTER,
                        width=int(0.0700*float(right)))
        trv_dues.column(2, anchor=CENTER,
                        width=int(0.1000*float(right)))
        trv_dues.column(3, anchor=CENTER,
                        width=int(0.1000*float(right)))
        trv_dues.column(4, anchor=CENTER,
                        width=int(0.0700*float(right)))
        trv_dues.column(5, anchor=CENTER,
                        width=int(0.1300*float(right)))

        conn = sqlite3.connect(db_path)

        cursor = conn.cursor()

        cursor.execute(sql_query)
        dues_tuple_list = cursor.fetchall()

        for i in dues_tuple_list:
            trv_dues.insert("", "end", values=i)

        trv_total_entry = defaultEntry(
            DueList_frame, "Total items in the list", 1, 0, entryWidth)
        trv_total_entry.insert(0, f"{len(dues_tuple_list)}")
        trv_total_entry.config(state="disabled")

        conn.commit()

        conn.close()

    def payDue_dues():

        customer_code_search_dues_entry = defaultEntry(
            payDues_frame, "Customer Code", 0, 0, entryWidth)
        customer_code_entry_dues = defaultEntry(
            payDues_frame, "Code", 2, 0, entryWidth)
        customer_Name_entry_dues = defaultEntry(
            payDues_frame, "Name", 3, 0, entryWidth)
        customer_Phone_entry_dues = defaultEntry(
            payDues_frame, "Phone", 4, 0, entryWidth)
        customer_Net_Dues_entry_dues = defaultEntry(
            payDues_frame, "Net Due", 5, 0, entryWidth)
        customer_Pay_Amount_entry_dues = defaultEntry(
            payDues_frame, "Paying Amount", 6, 0, entryWidth)

        customer_code_entry_dues.config(state="disabled")
        customer_Name_entry_dues.config(state="disabled")
        customer_Phone_entry_dues.config(state="disabled")
        customer_Net_Dues_entry_dues.config(
            state="disabled", foreground="red")

        def searchCustomer_dues():
            try:
                customer_code_entry_dues.config(state="enabled")
                customer_Name_entry_dues.config(state="enabled")
                customer_Phone_entry_dues.config(state="enabled")
                customer_Net_Dues_entry_dues.config(
                    state="enabled", foreground="red")

                customer_code_entry_dues.delete(0, END)
                customer_Name_entry_dues.delete(0, END)
                customer_Phone_entry_dues.delete(0, END)
                customer_Net_Dues_entry_dues.delete(0, END)

                code = customer_code_search_dues_entry.get()

                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute(
                    f"select * from customers where customer_code = {int(code)}")
                customer_info_dues = cursor.fetchall()
                c_ID = customer_info_dues[0][0]
                c_code = customer_info_dues[0][1]
                c_name = f"{customer_info_dues[0][2]} {customer_info_dues[0][3]}"

                c_phone = customer_info_dues[0][5]

                cursor.execute(
                    f"select sum(due_amount) from sales where customer_id={int(c_ID)}")
                customer_sales_info_dues = cursor.fetchall()

                customer_total_due_dues = 0

                if customer_sales_info_dues[0][0] != None:
                    customer_total_due_dues = customer_sales_info_dues[0][0]

                cursor.execute(
                    f"select sum(amount) from duesPaid where customer_id={int(c_ID)}")
                customer_due_paid_info_dues = cursor.fetchall()

                customer_total_due_paid_dues = 0
                if customer_due_paid_info_dues[0][0] != None:
                    customer_total_due_paid_dues = customer_due_paid_info_dues[
                        0][0]

                customer_total_additional_due = customer_total_due_dues - \
                    customer_total_due_paid_dues

                customer_code_entry_dues.insert(0, c_code)
                customer_Name_entry_dues.insert(0, c_name)
                customer_Phone_entry_dues.insert(0, c_phone)
                customer_Net_Dues_entry_dues.insert(
                    0, customer_total_additional_due)

                customer_code_entry_dues.config(state="disabled")
                customer_Name_entry_dues.config(state="disabled")
                customer_Phone_entry_dues.config(state="disabled")
                customer_Net_Dues_entry_dues.config(
                    state="disabled", foreground="red")

                conn.commit()
                conn.close()

                def payDue_save_dues():
                    try:
                        pay_due_amount = customer_Pay_Amount_entry_dues.get()
                        code = customer_code_search_dues_entry.get()

                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()

                        cursor.execute(
                            f"select ID from customers where customer_code={int(code)}")
                        c_ID = cursor.fetchone()[0]

                        conn.commit()

                        cursor.execute("insert into duesPaid(customer_id, amount) values (?,?)",
                                       (c_ID, float(pay_due_amount)))

                        resposne = messagebox.askyesno(
                            title="Confirm Pay Due", message="Are You Sure to Pay this due amount? This will be saved in database. After saving this information you cannot change.")
                        if resposne == True:
                            conn.commit()
                            conn.close()
                            customer_due_pay_amount_save_button = defaultButton(
                                payDues_frame, "Pay Due", 7, 1, W+E, state="disabled")
                            messagebox.showinfo(
                                title="Pay Due Success", message="The due payment has been saved successfully.")

                            def generate_due_invoice():

                                c_code_due = customer_code_entry_dues.get()
                                c_name_due = customer_Name_entry_dues.get()
                                c_phone_due = customer_Phone_entry_dues.get()
                                c_additional_due = customer_Net_Dues_entry_dues.get()
                                pay_due_amount = customer_Pay_Amount_entry_dues.get()
                                current_due = "{:.2f}".format(
                                    float(c_additional_due) - float(pay_due_amount))

                                conn = sqlite3.connect(db_path)
                                cursor = conn.cursor()

                                cursor.execute(
                                    f"select address from customers where customer_code={int(c_code_due)}")
                                c_address_due = cursor.fetchone()[0]

                                conn.commit()

                                cursor.execute(
                                    "select created_at from duesPaid order by ID desc limit 1 ")
                                due_Date = cursor.fetchone()[0]

                                conn.commit()

                                conn.close()

                                create_due_invoice(due_Date, c_code_due, c_name_due, c_phone_due,
                                                   c_address_due, c_additional_due, pay_due_amount, current_due)

                                payDue_dues()
                                generate_due_invoice_button = defaultButton(
                                    payDues_frame, "Generate Due Invoice", 8, 1, W+E, state="disabled")

                            generate_due_invoice_button = defaultButton(
                                payDues_frame, "Generate Due Invoice", 8, 1, W+E, command=generate_due_invoice)
                            updateDueList(main_dues_sql_query)
                            stats()

                        else:
                            return
                    except Exception as identifier:
                        messagebox.showerror(title="Customer Error",
                                             message="Please enter valid Information.")

                customer_due_pay_amount_save_button = defaultButton(
                    payDues_frame, "Pay Due", 7, 1, W+E, command=payDue_save_dues)

            except Exception as identifier:
                customer_code_entry_dues.config(state="disabled")
                customer_Name_entry_dues.config(state="disabled")
                customer_Phone_entry_dues.config(state="disabled")
                customer_Net_Dues_entry_dues.config(
                    state="disabled", foreground="red")
                customer_code_search_dues_entry.delete(0, END)
                messagebox.showerror(title="Customer Error",
                                     message="Please enter valid customer code.")

        customer_code_search_dues_button = defaultButton(
            payDues_frame, "Search", 1, 1, W+E, command=searchCustomer_dues)

    customer_due_pay_amount_save_button = defaultButton(
        payDues_frame, "Pay Due", 7, 1, W+E, state="disabled")

    generate_due_invoice_button = defaultButton(
        payDues_frame, "Generate Due Invoice", 8, 1, W+E, state="disabled")

    DueSearch_frame = defaultFrame(
        dueFrame, "Search by code, name, phone or date", 1, 0)

    searchDues_dues_entry = defaultEntry(
        DueSearch_frame, "Search", 0, 0, entryWidth)

    def SearchDues_frame():
        query = searchDues_dues_entry.get()
        dues_search_sql_query = f"select customers.customer_code, customers.first_name, customers.phone, duesPaid.amount, duesPaid.created_at from duesPaid INNER JOIN customers on duesPaid.customer_id=customers.ID where customers.customer_code like '%{query}%' or customers.first_name like '%{query}%' or customers.phone like '%{query}%' or duesPaid.created_at like '%{query}%' order by duesPaid.ID desc"
        updateDueList(dues_search_sql_query)

    searchDues_dues_button = defaultButton(
        DueSearch_frame, "Search", 1, 1, W+E, command=SearchDues_frame)

    def resetDuesList_dues():
        updateDueList(main_dues_sql_query)

    resetDuesListButton_dues = defaultButton(
        DueSearch_frame, "Reset", 1, 0, W+E, command=resetDuesList_dues)

    payDue_dues()
    updateDueList(main_dues_sql_query)

    """


    Sales Start


    """

    SalesList_Frame_sales = defaultFrame(saleFrame, "Sales List", 0, 0)
    main_sql_sales_list_query = "select sales.sale_code, customers.first_name, customers.phone, sales.sale_amount, sales.paid_amount, sales.due_amount, sales.created_at from sales inner join customers on sales.customer_id = customers.ID order by sales.created_at desc"

    def UpdateSalesList_sales(sql_query):

        trv_sales = ttk.Treeview(SalesList_Frame_sales, columns=(1, 2, 3, 4, 5, 6, 7),
                                 show="headings", height=int(0.02300*float(down)), padding=5, style="Custom.Treeview")
        trv_sales.grid(row=0, column=0, columnspan=4)

        trv_sales.heading(1, text='Invoice Number')
        trv_sales.heading(2, text='Customer Name')
        trv_sales.heading(3, text='Customer Phone')
        trv_sales.heading(4, text='Net Amount')
        trv_sales.heading(5, text='Paid Amount')
        trv_sales.heading(6, text='Due Amount')
        trv_sales.heading(7, text='Date Added')

        trv_sales.column(1, anchor=CENTER,
                         width=int(0.1000*float(right)))
        trv_sales.column(2, anchor=CENTER,
                         width=int(0.1000*float(right)))
        trv_sales.column(3, anchor=CENTER,
                         width=int(0.1300*float(right)))
        trv_sales.column(4, anchor=CENTER,
                         width=int(0.1000*float(right)))
        trv_sales.column(5, anchor=CENTER,
                         width=int(0.1000*float(right)))
        trv_sales.column(6, anchor=CENTER,
                         width=int(0.1000*float(right)))
        trv_sales.column(7, anchor=CENTER,
                         width=int(0.1300*float(right)))

        conn = sqlite3.connect(db_path)

        cursor = conn.cursor()

        cursor.execute(sql_query)
        sales_tuple_list = cursor.fetchall()

        for i in sales_tuple_list:
            trv_sales.insert("", "end", values=i)

        trv_total_entry = defaultEntry(
            SalesList_Frame_sales, "Total items in the list", 1, 2, entryWidth)
        trv_total_entry.insert(0, f"{len(sales_tuple_list)}")
        trv_total_entry.config(state="disabled")

        def print_sales():
            print_as_excel(sales_tuple_list)

        print_sales_info_button = defaultButton(
            SalesList_Frame_sales, "Generate Excel List", 2, 2, W+E, command=print_sales)

        conn.commit()

        conn.close()

        def getSalesInformationSelected():
            try:
                selectedSalesIID = trv_sales.selection()[0]
                salesCode = trv_sales.item(selectedSalesIID)["values"][0]
                customer_name_selected = trv_sales.item(
                    selectedSalesIID)["values"][1]
                customer_phone_selected = trv_sales.item(selectedSalesIID)[
                    "values"][2]
                net_total_selected = trv_sales.item(
                    selectedSalesIID)["values"][3]
                paid_total_selected = trv_sales.item(
                    selectedSalesIID)["values"][4]
                due_total_selected = trv_sales.item(
                    selectedSalesIID)["values"][5]

                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute(
                    f"select products.product,products.weight, products.price, stocks_removed.quantity, (products.price * stocks_removed.quantity)  from stocks_removed join products on stocks_removed.product_id=products.ID where stocks_removed.sale_code={salesCode}")
                sales_product_information = cursor.fetchall()

                total_sales_without_discounts = 0.0
                for i in sales_product_information:
                    total_sales_without_discounts += float(i[4])

                discount_selected = ((total_sales_without_discounts -
                                      float(net_total_selected)) / total_sales_without_discounts) * 100.0

                conn.commit()
                conn.close()

                salesDetails_window = Tk()
                salesDetails_window.title(f"{salesCode} Information")
                salesDetails_window.iconbitmap(icon_path)

                salesInformationFrame = defaultFrame(
                    salesDetails_window, "Sales Information", 0, 0)

                scEntry = defaultEntry(salesInformationFrame,
                                       "Sales Code", 0, 0, entryWidth)
                cnEntry = defaultEntry(salesInformationFrame,
                                       "Customer Name", 1, 0, entryWidth)
                cpEntry = defaultEntry(salesInformationFrame,
                                       "Customer Phone", 2, 0, entryWidth)
                tsEntry = defaultEntry(salesInformationFrame,
                                       "Total Sales", 4, 0, entryWidth)
                dcEntry = defaultEntry(salesInformationFrame,
                                       "Discount", 5, 0, entryWidth)
                ntEntry = defaultEntry(salesInformationFrame,
                                       "Net Total Sales", 6, 0, entryWidth)
                paEntry = defaultEntry(salesInformationFrame,
                                       "Paid amount", 7, 0, entryWidth)

                duEntry = defaultEntry(salesInformationFrame,
                                       "Due Total", 8, 0, entryWidth)

                trv_sales_selected = ttk.Treeview(salesInformationFrame, columns=(1, 2, 3, 4, 5),
                                                  show="headings", height=int(0.00600*float(down)), padding=5, style="Custom.Treeview")
                trv_sales_selected.grid(row=3, column=0, columnspan=3, pady=10)

                trv_sales_selected.heading(1, text='Product')
                trv_sales_selected.heading(2, text='Weight')
                trv_sales_selected.heading(3, text='Price')
                trv_sales_selected.heading(4, text='Quantity')
                trv_sales_selected.heading(5, text='Total Cost')

                trv_sales_selected.column(1, anchor=CENTER,
                                          width=100)
                trv_sales_selected.column(2, anchor=CENTER,
                                          width=80)
                trv_sales_selected.column(3, anchor=CENTER,
                                          width=90)
                trv_sales_selected.column(4, anchor=CENTER,
                                          width=80)
                trv_sales_selected.column(5, anchor=CENTER,
                                          width=100)

                for i in sales_product_information:
                    trv_sales_selected.insert("", "end", values=i)

                scEntry.insert(0, salesCode)
                cnEntry.insert(0, customer_name_selected)
                cpEntry.insert(0, customer_phone_selected)
                tsEntry.insert(0, total_sales_without_discounts)
                dcEntry.insert(0, str(discount_selected) + "%")
                ntEntry.insert(0, net_total_selected)
                paEntry.insert(0, paid_total_selected)
                duEntry.insert(0, due_total_selected)

                scEntry.config(state="disabled")
                cnEntry.config(state="disabled")
                cpEntry.config(state="disabled")
                tsEntry.config(state="disabled")
                dcEntry.config(state="disabled")
                ntEntry.config(state="disabled")
                paEntry.config(state="disabled")
                duEntry.config(state="disabled")

                salesDetails_window.mainloop()

            except Exception as identifier:
                messagebox.showerror(
                    title="Selection Error", message="You didn't select any sales from the list.")

        salesInformationButton = defaultButton(
            SalesList_Frame_sales, "Details of selected Sales", 2, 3, W+E, command=getSalesInformationSelected)

    searchSales_Entry_sales = ttk.Entry(SalesList_Frame_sales, width=entryWidth, justify=RIGHT,
                                        font=f"Courier {fontSize} bold")
    searchSales_Entry_sales.grid(
        row=1, column=0, pady=5, sticky=W+E, columnspan=2)

    def salesSearch_sales():
        query = searchSales_Entry_sales.get()
        sales_search_sql_query = f"select sales.sale_code, customers.first_name, customers.phone, sales.sale_amount, sales.paid_amount, sales.due_amount, sales.created_at from sales inner join customers on sales.customer_id = customers.ID where sales.sale_code like '%{query}%' or customers.first_name like '%{query}%' or customers.phone like '%{query}%' or sales.created_at like '%{query}%' order by sales.created_at desc"
        UpdateSalesList_sales(sales_search_sql_query)

    searchSales_Button_sales = defaultButton(
        SalesList_Frame_sales, "Search", 2, 1, W+E, command=salesSearch_sales)

    def resetSales_List_sales():
        UpdateSalesList_sales(main_sql_sales_list_query)

    resetSales_Button_sales = defaultButton(
        SalesList_Frame_sales, "Reset", 2, 0, W+E, command=resetSales_List_sales)

    UpdateSalesList_sales(main_sql_sales_list_query)

    """


    Sales END


    """

    """


    Home Start


    """

    #------------------------ Product adding Frame --------------------------------#

    productAddFrame_Home = defaultFrame(
        homeFrame, "Add Product to Invoice", 0, 0)

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

            cursor.execute(
                f"select ID from products where product='{product}'")
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

            product_stock = int(product_stock_updated) - \
                int(product_stock_removed)
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
                        invoice_items_tuple_list = cursor.fetchall()

                        for i in invoice_items_tuple_list:
                            product, weight, price, total_cost = i
                            trv_home.insert("", "end", values=(
                                f"{invoice_items_tuple_list.index(i) + 1}", product, weight, price, total_cost))

                        conn.commit()
                        conn.close()

                    trv_home = ttk.Treeview(productsListFrame_home, columns=(1, 2, 3, 4, 5),
                                            show="headings", height=int(0.01250*float(down)), padding=5, style="Custom.Treeview")
                    trv_home.grid(row=0, column=0, columnspan=2)

                    # trv_home.tag_bind('ttk', '<1>', itemClicked)

                    trv_home.heading(1, text='ID')
                    trv_home.heading(2, text='Product')
                    trv_home.heading(3, text='Price')
                    trv_home.heading(4, text='Quanity')
                    trv_home.heading(5, text='Total Cost')

                    trv_home.column(1, anchor=CENTER,
                                    width=int(0.0600*float(right)))
                    trv_home.column(2, anchor=CENTER,
                                    width=int(0.1250*float(right)))
                    trv_home.column(3, anchor=CENTER,
                                    width=int(0.1000*float(right)))
                    trv_home.column(4, anchor=CENTER,
                                    width=int(0.0800*float(right)))
                    trv_home.column(5, anchor=CENTER,
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
                                    "values"][1]

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
                                totalAmountEntry_home.insert(
                                    0, getTrvTotal_home())
                                totalAmountEntry_home.config(
                                    state="disabled", foreground="green")

                            except Exception as e:
                                messagebox.showerror(
                                    title="Selection error", message="You didn't select any product from the list.")

                                trv_home.delete(*trv_home.get_children())

                                UpdateTreeView()
                                totalAmountEntry_home.config(state="enabled")
                                totalAmountEntry_home.delete(0, END)
                                totalAmountEntry_home.insert(
                                    0, getTrvTotal_home())
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
                                    if float_discount_percentage > 100.0 or float_discount_percentage < 0.0:
                                        discountEntry_home.delete(0, END)
                                        messagebox.showerror(
                                            title="Discount Error", message="The discount ammount cannot be more than 100 or less than 0.")
                                    else:
                                        fraction_discount_percentage = (
                                            float_discount_percentage / 100.0)
                                        net_total = (totalAmount_trv_home - (totalAmount_trv_home *
                                                                             fraction_discount_percentage))
                                        formatted_net_total = "{:.2f}".format(
                                            net_total)

                                        getNetTotal_home(formatted_net_total)

                                        netAmountEntry_home.config(
                                            state="enabled")
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
                                    float_payment_amount = float(
                                        payment_amount)
                                    if float_payment_amount > net_total or float_payment_amount < 0.0:
                                        paymentEntry_home.delete(0, END)
                                        messagebox.showerror(
                                            title="Payment Error", message="The payment cannot be more than net total or less than 0.")
                                    else:
                                        due_amount = (
                                            net_total - float_payment_amount)
                                        formatted_due_amount = "{:.2f}".format(
                                            due_amount)

                                        getDueAmount_home(formatted_due_amount)

                                        def saveInvoice():

                                            try:
                                                def getSaleCode():
                                                    timeZone = pytz.timezone(
                                                        "asia/dhaka")

                                                    ct = datetime.now(timeZone)
                                                    code = ct.strftime(
                                                        "%Y%m%d%H%M%S")
                                                    return code

                                                sale_code = getSaleCode()

                                                customer_id = getCustomerID_home()

                                                totalAmount_trv_home = getTrvTotal_home()

                                                sale_amount = net_total_home

                                                discount_percentage_applied = int((
                                                    float(totalAmount_trv_home) - float(sale_amount))/float((totalAmount_trv_home)) * 100)

                                                paid_amount = float_payment_amount

                                                discount_amount = "{:.2f}".format(float(
                                                    totalAmount_trv_home) - float(sale_amount))

                                                due_amount = due_amount_home

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

                                                conn.commit()

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
                                                    UpdateSalesList_sales(
                                                        main_sql_sales_list_query)
                                                    updateDueList(
                                                        main_dues_sql_query)
                                                    updateProductsDetails()
                                                    stats()
                                                    messagebox.showinfo(
                                                        title="Save Success", message=f"The information is succesfully saved in database. The invoice number is {sale_code}.")
                                                    saveButton_home = defaultButton(
                                                        productsListFrame_home, "Save Invoice", 9, 0, W+E, state="disabled")

                                                    def printInvoice():
                                                        conn = sqlite3.connect(
                                                            db_path)
                                                        cursor = conn.cursor()

                                                        cursor.execute(
                                                            f"select created_at from sales where sale_code={int(sale_code)}")
                                                        sale_date_tuple = cursor.fetchone()
                                                        sale_date = sale_date_tuple[0]

                                                        conn.commit()
                                                        cursor.execute(
                                                            f"select * from customers where ID={int(customer_id)}")
                                                        customer_info_tuple_list = cursor.fetchall()

                                                        conn.commit()
                                                        cursor.execute(
                                                            f"select products.product, products.weight, products.price, stocks_removed.quantity, (products.price * stocks_removed.quantity)  from stocks_removed join products on stocks_removed.product_id=products.ID where stocks_removed.sale_code={int(sale_code)}")
                                                        sales_product_information = cursor.fetchall()

                                                        create_invoice(
                                                            sale_code, sale_date, customer_info_tuple_list[0][1], f"{customer_info_tuple_list[0][2]} {customer_info_tuple_list[0][3]}", customer_info_tuple_list[0][5], customer_info_tuple_list[0][4], sales_product_information, float(totalAmount_trv_home), discount_percentage_applied, discount_amount, float(sale_amount), float(paid_amount), float(due_amount))

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
                                                        stockManagement()

                                                        netAmountEntry_home.config(
                                                            state="enabled")
                                                        netAmountEntry_home.delete(
                                                            0, END)
                                                        netAmountEntry_home.config(
                                                            state="disabled")

                                                        paymentEntry_home.delete(
                                                            0, END)

                                                        discountEntry_home.delete(
                                                            0, END)

                                                        dueEntry_home.config(
                                                            state="enabled")
                                                        dueEntry_home.delete(
                                                            0, END)
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

                                                else:
                                                    return

                                            except Exception as identifier:
                                                messagebox.showerror(
                                                    title="Customer Error", message="Please insert customer Information.")
                                                printButton_home = defaultButton(
                                                    productsListFrame_home, "Generate PDF Invoice", 9, 1, W+E, state="disabled")

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

        trv_home = ttk.Treeview(productsListFrame_home, columns=(1, 2, 3, 4, 5),
                                show="headings", height=int(0.01250*float(down)), padding=5, style="Custom.Treeview")
        trv_home.grid(row=0, column=0, columnspan=2)

        # trv_home.tag_bind('ttk', '<1>', itemClicked)

        trv_home.heading(1, text='ID')
        trv_home.heading(2, text='Product')
        trv_home.heading(3, text='Price')
        trv_home.heading(4, text='Quanity')
        trv_home.heading(5, text='Total Cost')

        trv_home.column(1, anchor=CENTER,
                        width=int(0.0600*float(right)))
        trv_home.column(2, anchor=CENTER,
                        width=int(0.1250*float(right)))
        trv_home.column(3, anchor=CENTER,
                        width=int(0.1000*float(right)))
        trv_home.column(4, anchor=CENTER,
                        width=int(0.0800*float(right)))
        trv_home.column(5, anchor=CENTER,
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

    main_stock_sql_query = "select stocks.ID, products.product, stocks.Quantity, stocks.Price, round(stocks.price_per_product, 2), stocks.created_at from stocks inner join products where stocks.product_id=products.ID order by stocks.created_at desc"

    def updateStockList_stocks(sql_query):

        trv_stocks = ttk.Treeview(stockList_frame_stocks, columns=(1, 2, 3, 4, 5, 6),
                                  show="headings", height=int(0.020*float(down)), padding=5, style="Custom.Treeview")
        trv_stocks.grid(row=0, column=0, columnspan=2)

        trv_stocks.heading(1, text="stock ID")
        trv_stocks.heading(2, text='Product Name')
        trv_stocks.heading(3, text='Quantity')
        trv_stocks.heading(4, text='Price')
        trv_stocks.heading(5, text='Price Per Product')
        trv_stocks.heading(6, text='Added Date')

        trv_stocks.column(1, anchor=CENTER, width=int(0.050*float(right)))
        trv_stocks.column(2, anchor=CENTER, width=int(0.090*float(right)))
        trv_stocks.column(3, anchor=CENTER, width=int(0.050*float(right)))
        trv_stocks.column(4, anchor=CENTER, width=int(0.090*float(right)))
        trv_stocks.column(5, anchor=CENTER, width=int(0.090*float(right)))
        trv_stocks.column(6, anchor=CENTER, width=int(0.120*float(right)))

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(sql_query)
        stocks_tuple_list = cursor.fetchall()

        for i in stocks_tuple_list:
            trv_stocks.insert("", "end", values=i)

        trv_total_entry = defaultEntry(
            stockList_frame_stocks, "Total items in the list", 2, 0, entryWidth)
        trv_total_entry.insert(0, f"{len(stocks_tuple_list)}")
        trv_total_entry.config(state="disabled")
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
                    updateStockList_stocks(main_stock_sql_query)
                    UpdateHomeAddProduct_Frame()
                    updateProductsDetails()
                    stats()
                else:
                    return

            except Exception as identifier:
                messagebox.showerror(
                    title="Selection error", message="You didn't select a customer from the list. Please select one and try to delete.")

                trv_stocks.delete(*trv_stocks.get_children())
                updateStockList_stocks(main_stock_sql_query)
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

                    price_per_product = float(
                        price_edit_stocks.get()) / float(quantity_edit_stocks.get())

                    cursor.execute(
                        f"update stocks set Quantity={int(quantity_edit_stocks.get())} where ID={int(stock_ID)}")
                    cursor.execute(
                        f"update stocks set Price={float(price_edit_stocks.get())} where ID={int(stock_ID)}")

                    cursor.execute(
                        f"update stocks set price_per_product={price_per_product} where ID={int(stock_ID)}")

                    resposne = messagebox.askyesno(
                        title="Confirm Edit", message="Are you sure you want to edit this stock's information?")
                    if resposne == True:
                        conn.commit()
                        conn.close()

                        messagebox.showinfo(
                            title="Edit stock successfully", message="Stock is updated successfully.")
                        trv_stocks.delete(*trv_stocks.get_children())
                        updateStockList_stocks(main_stock_sql_query)
                        UpdateHomeAddProduct_Frame()
                        updateProductsDetails()
                        stats()
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

    updateStockList_stocks(main_stock_sql_query)

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

            cursor.execute(
                f"select ID from products where product='{product}'")
            product_ID = cursor.fetchall()[0][0]

            def addStock():
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()

                    price_per_product = float(
                        productPriceEntry_stocks.get()) / float(productQuantityEntry_stocks.get())

                    cursor.execute("INSERT INTO stocks(product_id, Quantity, Price, price_per_product) VALUES (?, ?, ?, ?)",
                                   (product_ID, int(productQuantityEntry_stocks.get()), float(
                                    productPriceEntry_stocks.get()), price_per_product)
                                   )

                    resposne = messagebox.askyesno(
                        title="Confirm adding stock", message="Are you sure you want to add this stock?")
                    if resposne == True:
                        conn.commit()
                        conn.close()
                        updateStockList_stocks(main_stock_sql_query)
                        updateProductsDetails()
                        stats()
                        productNameEntry_stocks.delete(0, END)
                        productPriceEntry_stocks.delete(0, END)
                        productQuantityEntry_stocks.delete(0, END)

                    else:
                        return

                except Exception as identifier:
                    messagebox.showerror(
                        title="Adding stock error", message="Please insert valid information for the stock.")
                    productNameEntry_stocks.delete(0, END)
                    productPriceEntry_stocks.delete(0, END)
                    productQuantityEntry_stocks.delete(0, END)

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

    stockSearch_frame_stocks = defaultFrame(
        stockFrame, "Search by product name", 1, 0)

    searchStocksEntry_stocks = defaultEntry(
        stockSearch_frame_stocks, "Search Stock", 0, 0, entryWidth)

    def searchStocks_stocks():
        query = searchStocksEntry_stocks.get()
        search_stock_sql_query = f"select stocks.ID, products.product, stocks.Quantity, stocks.price, round(stocks.price_per_product, 2), stocks.created_at from stocks inner join products on stocks.product_id=products.ID where products.product like '%{query}%' or stocks.created_at like '%{query}%' order by stocks.created_at desc"
        updateStockList_stocks(search_stock_sql_query)

    searchStocksButton_stocks = defaultButton(
        stockSearch_frame_stocks, "Search Stock", 1, 1, W+E, command=searchStocks_stocks)

    def resetStocks_stocks():
        updateStockList_stocks(main_stock_sql_query)

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
        customerFrame, "Customer List", 0, 1, rowspan=2)
    main_customer_sql_query = "select customer_code, first_name, last_name, address, phone from customers order by ID desc"

    def updateCustomersList(sql_query):

        trv_customers = ttk.Treeview(customerListFrame_customers, columns=(1, 2, 3, 4, 5),
                                     show="headings", height=int(0.020*float(down)), padding=5, style="Custom.Treeview")
        trv_customers.grid(row=0, column=0, columnspan=3)

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

        cursor.execute(sql_query)
        customers_tuple_list = cursor.fetchall()

        for i in customers_tuple_list:
            trv_customers.insert("", "end", values=i)
        trv_total_entry = defaultEntry(
            customerListFrame_customers, "Total items in the list", 2, 1, entryWidth)
        trv_total_entry.insert(0, f"{len(customers_tuple_list)}")
        trv_total_entry.config(state="disabled")

        def print_customers():
            print_as_excel(customers_tuple_list)

        print_customer_info_button = defaultButton(
            customerListFrame_customers, "Generate Excel List", 2, 0, W+E, command=print_customers)
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
                    updateCustomersList(main_customer_sql_query)
                    UpdateSalesList_sales(main_sql_sales_list_query)
                    updateDueList(main_dues_sql_query)
                else:
                    return

            except Exception as identifier:
                messagebox.showerror(
                    title="Selection error", message="You didn't select a customer from the list. Please select one and try to delete.")

                trv_customers.delete(*trv_customers.get_children())
                updateCustomersList(main_customer_sql_query)

        deleteCustomerFromCustomerListButton = defaultButton(
            customerListFrame_customers, "Delete selected Customer", 1, 0, W+E, command=deleteCustomerFromCustomerList)

        def editCustomerFromCustomerList():
            try:
                selectedCustomerIID = trv_customers.selection()[0]
                code = trv_customers.item(selectedCustomerIID)["values"][0]

                editWindow = Tk()
                editWindow.title("Edit Customer")
                editWindow.iconbitmap(icon_path)

                editCustomerFrame = defaultFrame(
                    editWindow, "Edit Customer", 0, 0)

                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute(
                    f"select first_name, last_name, address, phone from customers WHERE customer_code={int(code)}")
                customer_info_tuple_list = cursor.fetchall()

                f_name_edit = defaultEntry(
                    editCustomerFrame, "First Name", 0, 0, 30)
                l_name_edit = defaultEntry(
                    editCustomerFrame, "Last Name", 1, 0, 30)
                address_edit = defaultEntry(
                    editCustomerFrame, "Address", 2, 0, 30)
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
                        updateCustomersList(main_customer_sql_query)
                        UpdateSalesList_sales(main_sql_sales_list_query)
                        updateDueList(main_dues_sql_query)
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

        def detailsCustomerFromCustomersList():

            try:

                selectedProductIID = trv_customers.selection()[0]
                code = trv_customers.item(selectedProductIID)["values"][0]

                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute(
                    f"select * from customers where customer_code='{code}'")
                customer_info_selected = cursor.fetchall()
                customer_ID_selected = customer_info_selected[0][0]
                customer_name_selected = f"{customer_info_selected[0][2]} {customer_info_selected[0][3]}"
                customer_address_selected = customer_info_selected[0][4]
                customer_phone_selected = customer_info_selected[0][5]

                conn.commit()

                cursor.execute(
                    f"select sum(sale_amount), sum(paid_amount), sum(due_amount) from sales where customer_id={int(customer_ID_selected)}")
                customer_sales_info_selected = cursor.fetchall()

                customer_total_sales_selected = 0
                customer_total_paid_selected = 0
                customer_total_due_selected = 0

                if customer_sales_info_selected[0][0] != None and customer_sales_info_selected[0][1] != None and customer_sales_info_selected[0][1] != None:
                    customer_total_sales_selected = customer_sales_info_selected[0][0]
                    customer_total_paid_selected = customer_sales_info_selected[0][1]
                    customer_total_due_selected = customer_sales_info_selected[0][2]

                conn.commit()

                cursor.execute(
                    f"select sum(amount) from duesPaid where customer_id={int(customer_ID_selected)}")
                customer_due_paid_info_selected = cursor.fetchall()

                customer_total_due_paid_selected = 0
                if customer_due_paid_info_selected[0][0] != None:
                    customer_total_due_paid_selected = customer_due_paid_info_selected[
                        0][0]

                customer_total_additional_due = customer_total_due_selected - \
                    customer_total_due_paid_selected

                conn.commit()
                conn.close()

                details_window = Tk()
                details_window.title(f"{customer_name_selected} Details.")
                details_window.iconbitmap(icon_path)

                details_frame_customer = defaultFrame(
                    details_window, "Customer Details", 0, 0)

                customer_code_selected_entry = defaultEntry(
                    details_frame_customer, "Customer Code", 0, 1, entryWidth)
                customer_name_selected_entry = defaultEntry(
                    details_frame_customer, "Name", 1, 1, entryWidth)
                customer_address_selected_entry = defaultEntry(
                    details_frame_customer, "Address", 2, 1, entryWidth)
                customer_phone_selected_entry = defaultEntry(
                    details_frame_customer, "Phone", 3, 1, entryWidth)
                customer_total_sales_selected_entry = defaultEntry(
                    details_frame_customer, "Total Sales", 4, 1, entryWidth)
                customer_total_paid_selected_entry = defaultEntry(
                    details_frame_customer, "Total paid", 5, 1, entryWidth)
                customer_total_due_occured_selected_entry = defaultEntry(
                    details_frame_customer, "Total due occured", 6, 1, entryWidth)
                customer_total_due_paid_selected_entry = defaultEntry(
                    details_frame_customer, "Total due paid", 7, 1, entryWidth)
                customer_total_additional_due_selected_entry = defaultEntry(
                    details_frame_customer, "Net due", 8, 1, entryWidth)\


                customer_code_selected_entry.insert(0, code)
                customer_name_selected_entry.insert(0, customer_name_selected)
                customer_address_selected_entry.insert(
                    0, customer_address_selected)
                customer_phone_selected_entry.insert(
                    0, customer_phone_selected)
                customer_total_sales_selected_entry.insert(
                    0, customer_total_sales_selected)
                customer_total_paid_selected_entry.insert(
                    0, customer_total_paid_selected)
                customer_total_due_occured_selected_entry.insert(
                    0, customer_total_due_selected)
                customer_total_due_paid_selected_entry.insert(
                    0, customer_total_due_paid_selected)
                customer_total_additional_due_selected_entry.insert(
                    0, customer_total_additional_due)

                customer_code_selected_entry.config(state="disabled")
                customer_name_selected_entry.config(state="disabled")
                customer_address_selected_entry.config(state="disabled")
                customer_phone_selected_entry.config(state="disabled")
                customer_total_sales_selected_entry.config(state="disabled")
                customer_total_paid_selected_entry.config(state="disabled")
                customer_total_due_occured_selected_entry.config(
                    state="disabled")
                customer_total_due_paid_selected_entry.config(state="disabled")
                customer_total_additional_due_selected_entry.config(
                    state="disabled")

                details_window.mainloop()

            except Exception as identifier:
                messagebox.showerror(
                    title="Selection error", message="You didn't select a customer from the list.")

                trv_customers.delete(*trv_customers.get_children())
                updateCustomersList(main_customer_sql_query)

        detailsCustomersFromCustomersList = defaultButton(
            customerListFrame_customers, "Details", 1, 2, W+E, command=detailsCustomerFromCustomersList)

    #------------------------ Create a function to show the list of customers after searching --------------------------------#

    #------------------------ Customer Adding Frame ------------------------#

    customerAddFrame_customers = defaultFrame(
        customerFrame, "Add New Customer", 0, 0)

    customer_first_name_Entry_customers = defaultEntry(
        customerAddFrame_customers, "First Name", 0, 0, entryWidth)
    customer_last_name_Entry_customers = defaultEntry(
        customerAddFrame_customers, "Last Name", 1, 0, entryWidth)
    customer_address_Entry_customers = defaultEntry(
        customerAddFrame_customers, "Address", 2, 0, entryWidth)
    customer_phone_Entry_customers = defaultEntry(
        customerAddFrame_customers, "Phone", 3, 0, entryWidth)

    def addCustomer_customers():
        try:
            def getCustomerCode():

                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                default_code = 1001

                cursor.execute(
                    "select customer_code from customers order by customer_code desc limit 1")
                code_tuple_list = cursor.fetchall()

                if code_tuple_list != []:
                    last_code = code_tuple_list[0][0]

                    new_code = last_code + 1

                    return new_code

                else:
                    return default_code

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

                    updateCustomersList(main_customer_sql_query)
                else:
                    customer_first_name_Entry_customers.delete(0, END)
                    customer_last_name_Entry_customers.delete(0, END)
                    customer_address_Entry_customers.delete(0, END)
                    customer_phone_Entry_customers.delete(0, END)

        except Exception as identifier:
            messagebox.showerror(title="Customer Error",
                                 message="There is an error to add the customer.")

    add_customer_button_customers = defaultButton(
        customerAddFrame_customers, "Add Customer", 4, 1, W+E, command=addCustomer_customers)

    #------------------------ Showing Customer list Frame --------------------------------#

    updateCustomersList(main_customer_sql_query)

    #------------------------ Search Customer Frame --------------------------------#

    searchCustomerFrame_customers = defaultFrame(
        customerFrame, "Search by name, address or phone", 1, 0)

    searchCustomerEntry_customers = defaultEntry(
        searchCustomerFrame_customers, "Search Customer", 0, 0, entryWidth)

    def searchCustomer():
        query = searchCustomerEntry_customers.get()
        search_customer_sql_query = f"select customer_code, first_name, last_name, address, phone from customers where first_name like '%{query}%' or last_name like '%{query}%' or address like '%{query}%' or phone like '%{query}%' order by ID desc"
        updateCustomersList(search_customer_sql_query)

    searchCustomerButton_customers = defaultButton(
        searchCustomerFrame_customers, "Search", 1, 1, W+E, command=searchCustomer)

    def resetCustomerList():
        updateCustomersList(main_customer_sql_query)

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
        productFrame, "Products List", 0, 1, rowspan=2)

    main_product_sql_query = "select product, weight, price from products order by ID desc"

    def updateProductsList(sql_query):

        trv_products = ttk.Treeview(productListFrame_products, columns=(1, 2, 3),
                                    show="headings", height=int(0.020*float(down)), padding=5, style="Custom.Treeview")
        trv_products.grid(row=0, column=0, columnspan=3)

        trv_products.heading(1, text='Name')
        trv_products.heading(2, text='Weight (g)')
        trv_products.heading(3, text='Price (bdt)')

        trv_products.column(1, anchor=CENTER, width=int(0.170*float(right)))
        trv_products.column(2, anchor=CENTER, width=int(0.170*float(right)))
        trv_products.column(3, anchor=CENTER, width=int(0.170*float(right)))

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(sql_query)
        products_tuple_list = cursor.fetchall()

        for i in products_tuple_list:
            trv_products.insert("", "end", values=i)
        trv_total_entry = defaultEntry(
            productListFrame_products, "Total items in the list", 2, 1, entryWidth)
        trv_total_entry.insert(0, f"{len(products_tuple_list)}")
        trv_total_entry.config(state="disabled")

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
                    updateProductsList(main_product_sql_query)
                    UpdateHomeAddProduct_Frame()
                    updateStockAdd()
                    updateProductsDetails()
                else:
                    return

            except Exception as identifier:
                messagebox.showerror(
                    title="Selection error", message="You didn't select a product from the list. Please select one and try to delete.")

                trv_products.delete(*trv_products.get_children())
                updateProductsList(main_product_sql_query)
                updateStockAdd()
                updateStockList_stocks(main_stock_sql_query)
                updateProductsDetails()

        deleteProductFromProductListButton = defaultButton(
            productListFrame_products, "Delete selected product", 1, 0, W+E, command=deleteProductFromProductList)

        def editProductFromProductList():
            try:
                selectedProductIID = trv_products.selection()[0]
                name = trv_products.item(selectedProductIID)["values"][0]

                editWindow = Tk()
                editWindow.title("Edit product")
                editWindow.iconbitmap(icon_path)

                editProductFrame = defaultFrame(
                    editWindow, "Edit Product", 0, 0)

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
                        updateProductsList(main_product_sql_query)
                        UpdateHomeAddProduct_Frame()
                        updateStockAdd()
                        updateStockList_stocks(main_stock_sql_query)
                        updateProductsDetails()

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

        def detailsProductFromProductList():

            try:

                selectedProductIID = trv_products.selection()[0]
                name = trv_products.item(selectedProductIID)["values"][0]

                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute(
                    f"select * from products where product='{name}'")
                product_info_selected = cursor.fetchall()
                product_ID_selected = product_info_selected[0][0]
                product_Weight_selected = product_info_selected[0][2]
                product_Price_selected = product_info_selected[0][3]

                conn.commit()

                cursor.execute(
                    f"select sum(Quantity), sum(Price) from stocks where product_id={product_ID_selected} GROUP by product_id")
                product_stock_info_selected = cursor.fetchall()

                if product_stock_info_selected != []:
                    product_Total_Stock_Added_selected = product_stock_info_selected[0][0]
                    product_Total_Price_Stock_Added_selected = product_stock_info_selected[0][1]
                else:
                    product_Total_Stock_Added_selected = 0
                    product_Total_Price_Stock_Added_selected = 0

                conn.commit()

                cursor.execute(
                    f"select sum(quantity) from stocks_removed where product_id ={int(product_ID_selected)} GROUP by product_id")
                product_Total_Stock_Removed_info_selected = cursor.fetchall()
                if product_Total_Stock_Removed_info_selected != []:
                    product_Total_Stock_Removed_selected = product_Total_Stock_Removed_info_selected[
                        0][0]
                else:
                    product_Total_Stock_Removed_selected = 0

                product_Total_Stock_Available_selected = int(
                    product_Total_Stock_Added_selected) - int(product_Total_Stock_Removed_selected)

                product_Total_Price_Stock_Removed_selected = float(
                    product_Total_Stock_Removed_selected) * float(product_Price_selected)

                conn.commit()
                conn.close()

                details_window = Tk()
                details_window.title(f"{name} Details.")
                details_window.iconbitmap(icon_path)

                details_frame_product = defaultFrame(
                    details_window, "Product Details", 0, 0)

                product_name_selected_entry = defaultEntry(
                    details_frame_product, "Product", 0, 0, entryWidth)
                product_weight_selected_entry = defaultEntry(
                    details_frame_product, "Weight", 1, 0, entryWidth)
                product_price_selected_entry = defaultEntry(
                    details_frame_product, "Price", 2, 0, entryWidth)
                product_Total_Stock_Added_selected_entry = defaultEntry(
                    details_frame_product, "Total Stock addded", 3, 0, entryWidth)
                product_Total_Price_Stock_Addded_selected_entry = defaultEntry(
                    details_frame_product, "Total Price of stock addded", 4, 0, entryWidth)
                product_Total_Stock_Removed_selected_entry = defaultEntry(
                    details_frame_product, "Total stock sold", 5, 0, entryWidth)
                product_Total_Price_Stock_Removed_selected_entry = defaultEntry(
                    details_frame_product, "Total price of stock sold", 6, 0, entryWidth)
                product_Total_Stock_Available_selected_entry = defaultEntry(
                    details_frame_product, "Total stock available", 7, 0, entryWidth)

                product_name_selected_entry.insert(0, name)
                product_weight_selected_entry.insert(
                    0, product_Weight_selected)
                product_price_selected_entry.insert(0, product_Price_selected)
                product_Total_Stock_Added_selected_entry.insert(
                    0, product_Total_Stock_Added_selected)
                product_Total_Price_Stock_Addded_selected_entry.insert(
                    0, product_Total_Price_Stock_Added_selected)
                product_Total_Stock_Removed_selected_entry.insert(
                    0, product_Total_Stock_Removed_selected)
                product_Total_Price_Stock_Removed_selected_entry.insert(
                    0, product_Total_Price_Stock_Removed_selected)
                product_Total_Stock_Available_selected_entry.insert(
                    0, product_Total_Stock_Available_selected)

                product_name_selected_entry.config(state="disabled")
                product_weight_selected_entry.config(state="disabled")
                product_price_selected_entry.config(state="disabled")
                product_Total_Stock_Added_selected_entry.config(
                    state="disabled")
                product_Total_Price_Stock_Addded_selected_entry.config(
                    state="disabled")
                product_Total_Stock_Removed_selected_entry.config(
                    state="disabled")
                product_Total_Price_Stock_Removed_selected_entry.config(
                    state="disabled")
                product_Total_Stock_Available_selected_entry.config(
                    state="disabled")

                details_window.mainloop()

            except Exception as identifier:
                messagebox.showerror(
                    title="Selection error", message="You didn't select a product from the list.")

                trv_products.delete(*trv_products.get_children())
                updateProductsList(main_product_sql_query)

        detailsProductFromProductList = defaultButton(
            productListFrame_products, "Details", 1, 2, W+E, command=detailsProductFromProductList)

    #------------------------ Create a function to show the list of Product after searching --------------------------------#

    #------------------------ Product Adding Frame ------------------------#

    productAddFrame_products = defaultFrame(
        productFrame, "Add New Product", 0, 0)

    product_name_Entry_products = defaultEntry(
        productAddFrame_products, "Product Name", 0, 0, entryWidth)
    product_weight_entry_products = defaultEntry(
        productAddFrame_products, "Weight", 1, 0, entryWidth)
    product_price_Entry_products = defaultEntry(
        productAddFrame_products, "Price", 2, 0, entryWidth)

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
                                int(product_weight), float(product_Price)))

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

                    updateProductsList(main_product_sql_query)
                    UpdateHomeAddProduct_Frame()
                    updateStockAdd()
                    updateStockList_stocks(main_stock_sql_query)
                    updateProductsDetails()

                else:
                    return

        except Exception as identifier:
            messagebox.showerror(title="Products Error",
                                 message="Please insert valid information for the product. If you try to add a product which is already in the list, then please choose a new name.")
            product_name_Entry_products.delete(0, END)
            product_weight_entry_products.delete(0, END)
            product_price_Entry_products.delete(0, END)

    add_product_button_products = defaultButton(
        productAddFrame_products, "Add Product", 4, 1, W+E, command=addProduct_products)

    #------------------------ Showing Customer list Frame --------------------------------#

    updateProductsList(main_product_sql_query)

    #------------------------ Search Customer Frame --------------------------------#

    searchProductFrame_products = defaultFrame(
        productFrame, "Search by name", 1, 0)

    searchProductEntry_products = defaultEntry(
        searchProductFrame_products, "Search Product", 0, 0, entryWidth)

    def searchProduct():
        query = searchProductEntry_products.get()
        serach_product_sql_query = f"select product, weight, price from products where product like '%{query}%' order by ID desc"
        updateProductsList(serach_product_sql_query)

    searchProductButton_products = defaultButton(
        searchProductFrame_products, "Search", 1, 1, W+E, command=searchProduct)

    def resetProductsList():
        updateProductsList(main_product_sql_query)

    resetProductsList_products = defaultButton(
        searchProductFrame_products, "Reset", 1, 0, W+E, command=resetProductsList)
    """


    Product End


    """

    def about():
        about_frame = defaultFrame(aboutFrame, "About this software", 0, 0)

        def callback(url):
            webbrowser.open_new(url)

        detailsLabel = Label(
            about_frame, text="This software is completely built using python. \nAuthor: Hossain KM Shahriar (Shakib)", font="verdana 13")
        detailsLabel.pack()

        github = Label(about_frame, text="Github",
                       fg="#e4324c", cursor="hand2")
        github.pack(side=LEFT)
        github.bind(
            "<Button-1>", lambda e: callback("https://github.com/venomShakib"))

        website = Label(about_frame, text="Portfolio",
                        fg="#e4324c", cursor="hand2")
        website.pack(side=LEFT)
        website.bind(
            "<Button-1>", lambda e: callback("https://venomshakib.github.io/"))

        facebook = Label(about_frame, text="Facebook",
                         fg="#e4324c", cursor="hand2")
        facebook.pack(side=LEFT)
        facebook.bind(
            "<Button-1>", lambda e: callback("https://www.facebook.com/Shakib015"))

    about()

    conn.commit()

    conn.close()

    root.mainloop()


def login():
    loginWindow = Tk()
    loginWindow.title("Login - Business Monitoring App")
    loginWindow.iconbitmap(icon_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("select * from account")
    account_details_list = cursor.fetchall()

    account = [
        {
            "username": account_details_list[0][0],
            "password": account_details_list[0][1]
        },
    ]

    conn.commit()
    conn.close()

    def checkAccount(username, password):

        if username != account[len(account) - 1]["username"] and password != account[len(account) - 1]["password"]:
            messagebox.showerror(title="Login Error",
                                 message="Username and password do not match.")

        elif username != account[len(account) - 1]["username"]:
            messagebox.showerror(
                title="Login Error", message="Username is not correct. Please try again.")

        elif password != account[len(account) - 1]["password"]:
            messagebox.showerror(
                title="Login Error", message="Password is not correct. Please try again.")

        else:
            loginWindow.destroy()
            mainApp("normal")

    loginFrame = LabelFrame(
        loginWindow, text="Login as an Admin", padx=20, pady=20)
    loginFrame.grid(row=1, column=0, padx=40, pady=15, columnspan=3)

    userLabel = Label(loginFrame, text="Username : ", font="verdana 10").grid(
        row=1, column=0, padx=10, sticky=E)
    userEntry = ttk.Entry(loginFrame, width=30, justify=RIGHT)
    userEntry.grid(row=1, column=1)

    passwordLabel = Label(loginFrame, text="Password : ", font="verdana 10").grid(
        row=2, column=0, padx=10, pady=10, sticky=E)
    passwordEntry = ttk.Entry(loginFrame, show='*', width=30, justify=RIGHT)
    passwordEntry.grid(row=2, column=1)

    def getAccount():
        username = userEntry.get()
        password = passwordEntry.get()
        checkAccount(username, password)

    loginButton = Button(loginFrame, text="Login as Admin", padx=10, pady=5, bg="#e4324c", fg="white", border=0,
                         activebackground="#e4324c", activeforeground="#fffff0", font="verdana 10", command=getAccount).grid(row=3, column=1, sticky=W+E, pady=10)
    employeeFrame = LabelFrame(
        loginWindow, text="Login as an Employee", padx=20, pady=20)
    employeeFrame.grid(row=0, column=0, padx=40,
                       pady=50, sticky=W+E, columnspan=3)

    def employeeLogin():
        loginWindow.destroy()
        mainApp("hidden")

    Label(employeeFrame, text="Just click here to login.",
          font="verdana 10").pack(padx=10)

    normalUserButton = Button(employeeFrame, text="Login", padx=10, pady=5, bg="#e4324c", fg="white", border=0,
                              activebackground="#e4324c", activeforeground="#fffff0", font="verdana 10", command=employeeLogin).pack(pady=5, padx=10, anchor="center", fill="x")

    def callback(url):
        webbrowser.open_new(url)

    timeZone = pytz.timezone("asia/dhaka")
    x = datetime.now(timeZone)
    detailsLabel = Label(
        loginWindow, text=f"Copyright @ Shakib, {x.year}", font="verdana 8")
    detailsLabel.grid(row=2, column=0, columnspan=3, pady=10)

    loginWindow.mainloop()


login()
