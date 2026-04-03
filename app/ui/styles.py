from tkinter import ttk

# ── Light-mode palette ─────────────────────────────────────────────────────────
BG          = "#F5F7FA"   # window / frame background — exported for other modules
SIDEBAR_BG  = "#FFFFFF"   # notebook sidebar
TAB_BG      = "#F0F2F5"   # unselected tab
TAB_SEL_BG  = "#E63946"   # selected tab (accent red)
TAB_FG      = "#2D2D2D"   # unselected tab text
TAB_SEL_FG  = "#FFFFFF"   # selected tab text
ACCENT      = "#E63946"   # buttons / labels accent
HEADER_BG   = "#4A90D9"   # treeview heading background
HEADER_FG   = "#FFFFFF"   # treeview heading text
ROW_ODD     = "#FFFFFF"
ROW_EVEN    = "#EBF0FB"
FRAME_FG    = "#E63946"   # LabelFrame title colour
BTN_FG      = "#E63946"   # button foreground


def apply_styles(right: int, font_size: int) -> None:
    """Configure all custom ttk styles for the application (light mode)."""
    s = ttk.Style()
    # Use the closest built-in theme as a base for consistent light rendering
    try:
        s.theme_use("clam")
    except Exception:
        pass

    _apply_global_styles(s, right, font_size)
    _apply_notebook_styles(s, right, font_size)
    _apply_treeview_styles(s, right, font_size)
    _apply_button_styles(s, font_size)
    _apply_entry_styles(s, font_size)


def _apply_global_styles(s, right: int, font_size: int) -> None:
    s.configure(".",
                 background=BG,
                 foreground="#2D2D2D",
                 font=("Verdana", font_size - 2))
    s.configure("TFrame",   background=BG)
    s.configure("TLabel",   background=BG, foreground="#2D2D2D")
    s.configure("TLabelframe",
                 background=BG,
                 relief="groove",
                 borderwidth=1)
    s.configure("TLabelframe.Label",
                 background=BG,
                 foreground=FRAME_FG,
                 font=("Verdana", font_size, "bold"))


def _apply_notebook_styles(s, right: int, font_size: int) -> None:
    try:
        s.element_create("Plain.Notebook.tab", "from", "default")
        s.layout("TNotebook.Tab", [
            ("Plain.Notebook.tab", {"children": [
                ("Notebook.padding", {"side": "top", "children": [
                    ("Notebook.focus", {"side": "top", "children": [
                        ("Notebook.label", {"side": "top", "sticky": ""}),
                    ], "sticky": "nswe"}),
                ], "sticky": "nswe"}),
            ], "sticky": "nswe"}),
        ])
    except Exception:
        pass  # Element may already exist on re-style

    tab_font_size = max(8, int(0.00629 * right))
    s.configure(
        "TNotebook",
        background=SIDEBAR_BG,
        tabposition="wn",
        tabmargins=[6, 6, 6, 0],
    )
    s.configure(
        "TNotebook.Tab",
        background=TAB_BG,
        foreground=TAB_FG,
        width=16,
        relief="flat",
        font=("Verdana", tab_font_size, "bold"),
        padding=[12, 10, 12, 10],
    )
    s.map(
        "TNotebook.Tab",
        background=[("selected", TAB_SEL_BG), ("active", "#D6DCE8")],
        foreground=[("selected", TAB_SEL_FG)],
        relief=[("selected", "flat")],
    )


def _apply_treeview_styles(s, right: int, font_size: int) -> None:
    try:
        s.element_create("Custom.Treeheading.border", "from", "default")
        s.layout("Custom.Treeview.Heading", [
            ("Custom.Treeheading.cell", {"sticky": "nswe"}),
            ("Custom.Treeheading.border", {"sticky": "nswe", "children": [
                ("Custom.Treeheading.padding", {"sticky": "nswe", "children": [
                    ("Custom.Treeheading.image", {"side": "right", "sticky": ""}),
                    ("Custom.Treeheading.text",  {"sticky": "we"}),
                ]}),
            ]}),
        ])
    except Exception:
        pass

    s.configure(
        "Custom.Treeview.Heading",
        background=HEADER_BG,
        foreground=HEADER_FG,
        font=("Verdana", font_size, "bold"),
        padding=6,
        relief="flat",
    )
    s.map(
        "Custom.Treeview.Heading",
        relief=[("active", "groove"), ("pressed", "sunken")],
        background=[("active", "#3B7DC8")],
    )
    s.configure(
        "Custom.Treeview",
        background=ROW_ODD,
        fieldbackground=ROW_ODD,
        foreground="#2D2D2D",
        font=("Verdana", max(8, int(0.0060 * right))),
        rowheight=int(0.015625 * right),
        relief="flat",
        borderwidth=0,
    )
    s.map(
        "Custom.Treeview",
        background=[("selected", TAB_SEL_BG)],
        foreground=[("selected", "#FFFFFF")],
    )


def _apply_button_styles(s, font_size: int) -> None:
    s.configure(
        "TButton",
        font=("Verdana", font_size - 1, "bold"),
        foreground=BTN_FG,
        background="#FFFFFF",
        borderwidth=1,
        relief="solid",
        padding=[8, 4],
    )
    s.map(
        "TButton",
        background=[("active", "#FDECEA"), ("pressed", "#F5C6C8")],
        foreground=[("disabled", "#AAAAAA")],
        bordercolor=[("active", ACCENT)],
    )


def _apply_entry_styles(s, font_size: int) -> None:
    s.configure(
        "TEntry",
        fieldbackground="#FFFFFF",
        foreground="#2D2D2D",
        borderwidth=1,
        relief="solid",
        padding=[4, 2],
    )
    s.map(
        "TEntry",
        fieldbackground=[("disabled", "#F0F0F0")],
        foreground=[("disabled", "#888888")],
    )
