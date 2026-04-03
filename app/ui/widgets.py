from tkinter import *
from tkinter import ttk, Menu

# Light-mode accent (matches styles.py)
_ACCENT   = "#E63946"
_BG       = "#F5F7FA"
_LABEL_FG = "#2D2D2D"


class Widgets:
    """
    Factory for the three standard widget types used throughout the app.
    Font sizes are computed from screen width and passed in at construction time.
    """

    def __init__(self, font_size: int):
        self._font_size = font_size
        self._context_menu: Menu | None = None

    # ── Public factory methods ────────────────────────────────────────────────

    def frame(self, parent, caption: str, row: int, column: int, **grid_options) -> LabelFrame:
        f = LabelFrame(
            parent,
            text=caption,
            padx=12, pady=12,
            font=f"Verdana {self._font_size} bold",
            fg=_ACCENT,
            bg=_BG,
            relief="groove",
            bd=1,
        )
        f.grid(row=row, column=column, padx=12, pady=12, sticky=NSEW, **grid_options)
        # Make the frame's interior columns/rows stretch
        f.columnconfigure(1, weight=1)
        return f

    def entry(self, parent, caption: str, row: int, column: int, width: int, **entry_options) -> ttk.Entry:
        """Creates a label+entry pair and returns the Entry widget."""
        self._ensure_context_menu(parent)

        def show_menu(event):
            try:
                w = event.widget
                self._context_menu.entryconfigure(
                    "Cut",   command=lambda: w.event_generate("<<Cut>>"))
                self._context_menu.entryconfigure(
                    "Copy",  command=lambda: w.event_generate("<<Copy>>"))
                self._context_menu.entryconfigure(
                    "Paste", command=lambda: w.event_generate("<<Paste>>"))
                self._context_menu.tk.call(
                    "tk_popup", self._context_menu, event.x_root, event.y_root)
            except Exception:
                self._ensure_context_menu(parent)

        Label(
            parent,
            text=caption + ": ",
            font=f"Verdana {self._font_size - 3} bold",
            bg=_BG,
            fg=_LABEL_FG,
        ).grid(row=row, column=column, sticky=E)

        entry = ttk.Entry(
            parent,
            width=width,
            justify=RIGHT,
            font=f"Verdana {self._font_size - 3} bold",
            **entry_options,
        )
        entry.grid(row=row, column=column + 1, pady=4, padx=4, sticky=W + E)
        entry.bind_class("TEntry", "<Button-3><ButtonRelease-3>", show_menu)
        return entry

    def button(self, parent, caption: str, row: int, column: int, sticky: str, **btn_options) -> ttk.Button:
        btn = ttk.Button(parent, text=caption, cursor="hand2", **btn_options)
        btn.grid(row=row, column=column, pady=6, padx=4, sticky=sticky)
        return btn

    @staticmethod
    def make_responsive(widget, cols: int = 2, rows: int | None = None) -> None:
        """
        Give equal stretch weight to all grid columns (and optionally rows) of
        *widget* so that its children expand when the window is resized.
        """
        for c in range(cols):
            widget.columnconfigure(c, weight=1)
        if rows is not None:
            for r in range(rows):
                widget.rowconfigure(r, weight=1)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _ensure_context_menu(self, parent):
        if self._context_menu is None:
            self._context_menu = Menu(parent, tearoff=0)
            self._context_menu.add_command(label="Cut")
            self._context_menu.add_command(label="Copy")
            self._context_menu.add_command(label="Paste")
