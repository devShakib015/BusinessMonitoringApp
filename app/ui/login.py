from tkinter import *
from tkinter import ttk, messagebox

import pytz
from datetime import datetime

from app.config import ICON_PATH
from app.database.connection import get_db

# ── Light-mode palette (mirrors styles.py) ────────────────────────────────────
_BG       = "#F5F7FA"
_ACCENT   = "#E63946"
_BTN_FG   = "#FFFFFF"
_LABEL_FG = "#2D2D2D"
_CARD_BG  = "#FFFFFF"


class LoginWindow:
    """
    Entry-point window.

    Flow
    ────
    1. If the ``account`` table is empty  →  show **SuperAdminRegisterPage**
       which, on successful registration, transitions to the login page.
    2. Otherwise show the normal **login** page:
       - Employee login  →  app in restricted mode ("hidden").
       - Admin login     →  validates credentials, opens app in full mode ("normal").
    """

    def __init__(self):
        self._window = Tk()
        self._window.title("Business Monitoring App")
        self._window.configure(bg=_BG)
        self._window.resizable(True, True)
        try:
            self._window.iconbitmap(ICON_PATH)
        except Exception:
            pass

        # Center window
        w, h = 480, 520
        sw = self._window.winfo_screenwidth()
        sh = self._window.winfo_screenheight()
        self._window.geometry(f"{w}x{h}+{(sw - w)//2}+{(sh - h)//2}")

        self._setup_styles()

        if self._has_admin():
            self._show_login_page()
        else:
            self._show_register_page()

    # ── Style setup ───────────────────────────────────────────────────────────

    @staticmethod
    def _setup_styles() -> None:
        """Apply clam-based ttk styles for the login window."""
        s = ttk.Style()
        try:
            s.theme_use("clam")
        except Exception:
            pass
        s.configure("TFrame",  background=_BG)
        s.configure("TLabel",  background=_BG, foreground=_LABEL_FG)
        s.configure("TEntry",
                    fieldbackground="#FFFFFF",
                    foreground=_LABEL_FG,
                    borderwidth=1,
                    relief="solid",
                    padding=[4, 2])
        s.map("TEntry",
              fieldbackground=[("disabled", "#F0F0F0")],
              foreground=[("disabled", "#888888")])
        # Red accent button (register / admin login)
        s.configure("Accent.TButton",
                    font=("Verdana", 10, "bold"),
                    background=_ACCENT,
                    foreground=_BTN_FG,
                    borderwidth=0,
                    relief="flat",
                    padding=[8, 8])
        s.map("Accent.TButton",
              background=[("active", "#C0303C"), ("pressed", "#A02030")],
              foreground=[("active", _BTN_FG), ("pressed", _BTN_FG)])
        # Blue button (employee access)
        s.configure("Blue.TButton",
                    font=("Verdana", 10, "bold"),
                    background="#4A90D9",
                    foreground=_BTN_FG,
                    borderwidth=0,
                    relief="flat",
                    padding=[8, 8])
        s.map("Blue.TButton",
              background=[("active", "#3B7DC8"), ("pressed", "#2D6AB0")],
              foreground=[("active", _BTN_FG), ("pressed", _BTN_FG)])

    # ── Admin existence check ─────────────────────────────────────────────────

    @staticmethod
    def _has_admin() -> bool:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM account")
            return cur.fetchone()[0] > 0

    # ── Page management ───────────────────────────────────────────────────────

    def _clear_window(self):
        for widget in self._window.winfo_children():
            widget.destroy()

    # ══════════════════════════════════════════════════════════════════════════
    # REGISTER PAGE
    # ══════════════════════════════════════════════════════════════════════════

    def _show_register_page(self):
        self._clear_window()
        self._window.title("Setup Super Admin — Business Monitoring App")

        outer = Frame(self._window, bg=_BG)
        outer.pack(fill=BOTH, expand=True, padx=40, pady=30)
        outer.columnconfigure(0, weight=1)

        # Heading
        Label(outer, text="Welcome!", font="Verdana 20 bold",
              fg=_ACCENT, bg=_BG).grid(row=0, column=0, pady=(0, 4), sticky=EW)
        Label(outer, text="No admin account found.\nPlease create a Super Admin account to get started.",
              font="Verdana 10", fg=_LABEL_FG, bg=_BG, justify=CENTER).grid(
              row=1, column=0, pady=(0, 20), sticky=EW)

        # Card
        card = Frame(outer, bg=_CARD_BG, relief="solid", bd=1)
        card.grid(row=2, column=0, sticky=EW)
        card.columnconfigure(1, weight=1)

        _title = Label(card, text="Create Super Admin", font="Verdana 13 bold",
                       fg=_LABEL_FG, bg=_CARD_BG, anchor=W)
        _title.grid(row=0, column=0, columnspan=2, padx=20, pady=(18, 12), sticky=EW)

        reg_u = self._field(card, "Username", 1, show="")
        reg_p = self._field(card, "Password", 2, show="*")
        reg_c = self._field(card, "Confirm Password", 3, show="*")

        err_lbl = Label(card, text="", font="Verdana 9", fg=_ACCENT, bg=_CARD_BG)
        err_lbl.grid(row=4, column=0, columnspan=2, padx=20, pady=(0, 4), sticky=W)

        def register():
            u = reg_u.get().strip()
            p = reg_p.get()
            c = reg_c.get()

            if not u:
                err_lbl.config(text="Username cannot be empty.")
                return
            if len(p) < 6:
                err_lbl.config(text="Password must be at least 6 characters.")
                return
            if p != c:
                err_lbl.config(text="Passwords do not match.")
                return

            with get_db() as conn:
                conn.execute("INSERT INTO account(username, password) VALUES (?, ?)", (u, p))

            messagebox.showinfo(
                "Account Created",
                f"Super admin '{u}' created successfully!\nYou can now log in.",
            )
            self._show_login_page()

        btn = ttk.Button(card, text="Create Account",
                         style="Accent.TButton",
                         cursor="hand2", command=register)
        btn.grid(row=5, column=0, columnspan=2, padx=20, pady=(8, 20), sticky=EW)

        self._footer(outer, 3)

    # ══════════════════════════════════════════════════════════════════════════
    # LOGIN PAGE
    # ══════════════════════════════════════════════════════════════════════════

    def _show_login_page(self):
        self._clear_window()
        self._window.title("Login — Business Monitoring App")

        outer = Frame(self._window, bg=_BG)
        outer.pack(fill=BOTH, expand=True, padx=40, pady=30)
        outer.columnconfigure(0, weight=1)

        # Heading
        Label(outer, text="Business Monitoring App", font="Verdana 18 bold",
              fg=_ACCENT, bg=_BG).grid(row=0, column=0, pady=(0, 4), sticky=EW)
        Label(outer, text="Sign in to continue", font="Verdana 10",
              fg=_LABEL_FG, bg=_BG).grid(row=1, column=0, pady=(0, 20), sticky=EW)

        # ── Admin card ────────────────────────────────────────────────────────
        admin_card = Frame(outer, bg=_CARD_BG, relief="solid", bd=1)
        admin_card.grid(row=2, column=0, sticky=EW)
        admin_card.columnconfigure(1, weight=1)

        Label(admin_card, text="Admin Login", font="Verdana 12 bold",
              fg=_LABEL_FG, bg=_CARD_BG, anchor=W).grid(
              row=0, column=0, columnspan=2, padx=20, pady=(16, 10), sticky=EW)

        self._user_entry = self._field(admin_card, "Username", 1, show="")
        self._pass_entry = self._field(admin_card, "Password", 2, show="*")
        # Allow Enter key to submit
        self._pass_entry.bind("<Return>", lambda _: self._admin_login())

        err_lbl = Label(admin_card, text="", font="Verdana 9", fg=_ACCENT, bg=_CARD_BG)
        err_lbl.grid(row=3, column=0, columnspan=2, padx=20, pady=(0, 4), sticky=W)
        self._login_err_lbl = err_lbl

        btn = ttk.Button(admin_card, text="Login as Admin",
                         style="Accent.TButton",
                         cursor="hand2", command=self._admin_login)
        btn.grid(row=4, column=0, columnspan=2, padx=20, pady=(6, 20), sticky=EW)

        # ── Divider ───────────────────────────────────────────────────────────
        sep = Frame(outer, bg="#E0E0E0", height=1)
        sep.grid(row=3, column=0, sticky=EW, pady=12)

        # ── Employee card ─────────────────────────────────────────────────────
        emp_card = Frame(outer, bg=_CARD_BG, relief="solid", bd=1)
        emp_card.grid(row=4, column=0, sticky=EW)
        emp_card.columnconfigure(0, weight=1)

        Label(emp_card, text="Employee Access", font="Verdana 12 bold",
              fg=_LABEL_FG, bg=_CARD_BG, anchor=W).grid(
              row=0, column=0, padx=20, pady=(16, 4), sticky=EW)
        Label(emp_card, text="Click below to continue without an admin account.",
              font="Verdana 9", fg="#666666", bg=_CARD_BG).grid(
              row=1, column=0, padx=20, pady=(0, 8), sticky=EW)

        emp_btn = ttk.Button(emp_card, text="Continue as Employee",
                             style="Blue.TButton",
                             cursor="hand2", command=self._employee_login)
        emp_btn.grid(row=2, column=0, padx=20, pady=(0, 20), sticky=EW)

        self._footer(outer, 5)

    # ── Widget helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _field(parent, label: str, row: int, show: str = "") -> ttk.Entry:
        Label(parent, text=label, font="Verdana 10", fg=_LABEL_FG, bg=_CARD_BG,
              anchor=W).grid(row=row, column=0, padx=20, pady=(4, 0), sticky=EW,
                             columnspan=2)
        entry = ttk.Entry(parent, font="Verdana 10", show=show, justify=LEFT)
        entry.grid(row=row, column=0, padx=20, pady=(0, 8), sticky=EW, columnspan=2,
                   ipady=5)
        return entry

    @staticmethod
    def _footer(parent, row: int):
        tz = pytz.timezone("Asia/Dhaka")
        year = datetime.now(tz).year
        Label(parent, text=f"© {year} LazyProgs · Business Monitoring App",
              font="Verdana 8", fg="#999999", bg=_BG).grid(
              row=row, column=0, pady=(16, 0))

    # ── Login callbacks ───────────────────────────────────────────────────────

    def _admin_login(self) -> None:
        username = self._user_entry.get().strip()
        password = self._pass_entry.get()

        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT username, password FROM account LIMIT 1")
            row = cur.fetchone()

        if row is None:
            self._show_register_page()
            return

        stored_user, stored_pass = row
        if username != stored_user:
            self._login_err_lbl.config(text="Username is incorrect.")
            return
        if password != stored_pass:
            self._login_err_lbl.config(text="Password is incorrect.")
            return

        self._window.destroy()
        from app.ui.app import assets
        assets("normal").run()

    def _employee_login(self) -> None:
        self._window.destroy()
        from app.ui.app import assets
        assets("hidden").run()

    # ── Entry point ───────────────────────────────────────────────────────────

    def run(self) -> None:
        self._window.mainloop()
