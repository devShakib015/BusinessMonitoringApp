import webbrowser
from tkinter import *

import pytz
from datetime import datetime

from app.ui.widgets import Widgets
from app.ui.controller import AppController


class AboutView:
    """Static 'About' tab showing software and author information."""

    def __init__(self, parent, widgets: Widgets, right: int, down: int, ctrl: AppController):
        self._parent = parent
        self._w = widgets
        self._font_size = widgets._font_size
        self._build()

    def refresh(self):
        pass  # Static content – no refresh needed.

    def _build(self):
        tz = pytz.timezone("asia/dhaka")
        year = datetime.now(tz).year

        details_frame = self._w.frame(self._parent, "Details about this software", 0, 0)
        details_frame.columnconfigure(0, weight=1)
        details_frame.rowconfigure(0, weight=1)
        text_field = Text(
            details_frame,
            height=13,
            relief=FLAT,
            bg="#FFFFFF",
            fg="#2D2D2D",
            font=f"Verdana {self._font_size}",
        )
        text_field.grid(row=0, column=0, padx=10, pady=10, sticky=NSEW)
        text_field.insert(
            "end",
            f"This software is called Business Monitoring App. Which is built by Shakib.\n"
            f"The software will help small businesses to monitor things including customer \n"
            f"information, product information, stock information and due information. \n"
            f"You can easily use this software to generate invoices for sales and dues paid. \n"
            f"This software will also calculate your gross profit or loss for a particular \n"
            f"month which you can search and compare your monthly profits or loss. \n"
            f"You can also generate excel sheet for customers, products or sales items. \n"
            f"This is really great for a small business. Thank you.\n\n"
            f"Currently this software is owned by Optimusion. \n"
            f"It cannot be used for any other companies or personal use. \n\n"
            f"Copyright © {year} LazyProgs",
        )
        text_field.config(state=DISABLED)

        author_frame = self._w.frame(self._parent, "About author", 1, 0)
        Label(
            author_frame,
            text=(
                "Hossain KM Shahriar (Shakib).\n"
                "Software Engineer. \n"
                "Founder of LazyProgs. \n"
                "From Bangladesh. \n"
                "Student of Yangzhou University, China. \n"
                "Passionate about Python. \n"
                "Contact: +8801710265421"
            ),
            font=f"Verdana {self._font_size}",
            bg="#F5F7FA",
            fg="#2D2D2D",
        ).pack(side=TOP, expand=True)

        def open_url(url):
            webbrowser.open_new(url)

        for text, url, anchor in (
            ("Github",    "https://github.com/venomShakib",          ("ne", LEFT)),
            ("Portfolio", "https://venomshakib.github.io/",          ("n",  LEFT)),
            ("Facebook",  "https://www.facebook.com/Shakib015",       ("nw", LEFT)),
        ):
            lbl = Label(author_frame, text=text, fg="#E63946", bg="#F5F7FA", cursor="hand2")
            lbl.pack(side=anchor[1], expand=(anchor[0] != "n"), anchor=anchor[0])
            lbl.bind("<Button-1>", lambda e, u=url: open_url(u))
