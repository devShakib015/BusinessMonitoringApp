from tkinter import *
from tkinter import ttk

from app.config import ICON_PATH
from app.ui.widgets import Widgets
from app.ui.styles import apply_styles, BG as _BG
from app.ui.controller import AppController


class assets:
    """
    Top-level application window.  Builds the notebook, creates all view
    instances, and registers them with the AppController so cross-view
    refresh calls work correctly.

    Parameters
    ----------
    state : str
        ``"normal"``  – all tabs visible (admin mode).
        ``"hidden"``  – product/stock/stats tabs hidden (employee mode).
    """

    def __init__(self, state: str = "normal"):
        self._root = Tk()
        self._root.title("Business Monitoring App")
        self._root.configure(bg=_BG)
        try:
            self._root.iconbitmap(ICON_PATH)
        except Exception:
            pass

        self._right = self._root.winfo_screenwidth()
        self._down  = self._root.winfo_screenheight()
        self._root.geometry(f"{self._right}x{self._down}+0+0")
        self._root.state("zoomed")
        self._root.attributes("-fullscreen", False)
        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(0, weight=1)

        self._font_size   = int(0.00829 * self._right)
        self._entry_width = int(0.01842 * self._right)
        self._widgets     = Widgets(self._font_size)

        self._root.bind("<F11>",  lambda _: self._root.attributes("-fullscreen", True))
        self._root.bind("<Escape>", lambda _: self._root.attributes("-fullscreen", False))

        apply_styles(self._right, self._font_size)

        self._controller = AppController()
        self._build_notebook(state)

    # ── Notebook construction ─────────────────────────────────────────────────

    def _build_notebook(self, state: str) -> None:
        nb = ttk.Notebook(self._root, padding=0)
        nb.grid(row=0, column=0, sticky=NSEW)

        frames = self._make_frames(nb)
        self._add_tabs(nb, frames, state)
        self._build_views(frames)

    def _make_frames(self, notebook) -> dict:
        r, d = self._right, self._down

        def f(**kw):
            fr = Frame(notebook, bg=_BG, **kw)
            fr.pack(fill=BOTH, expand=True)
            # Give both grid columns equal stretch weight so left+right panels resize
            fr.columnconfigure(0, weight=1)
            fr.columnconfigure(1, weight=2)
            fr.rowconfigure(0, weight=1)
            fr.rowconfigure(1, weight=1)
            return fr

        return {
            "home":         f(pady=5,  padx=10),
            "customer":     f(pady=10),
            "product":      f(pady=10),
            "stock":        f(pady=10),
            "sale":         f(pady=10, padx=int(r * 0.030)),
            "due":          f(pady=10),
            "stock_info":   f(pady=10),
            "stats":        f(pady=40, padx=40),
            "product_info": f(pady=40, padx=int(r * 0.080)),
            "about":        f(pady=int(d * 0.06), padx=int(r * 0.02)),
        }

    def _add_tabs(self, nb, frames: dict, state: str) -> None:
        nb.add(frames["home"],         text="Create Invoice")
        nb.add(frames["customer"],     text="Add Customer")
        nb.add(frames["due"],          text="Due Payment")
        nb.add(frames["sale"],         text="Sales")
        nb.add(frames["product"],      text="Add Product",   state=state)
        nb.add(frames["stock"],        text="Add Stock",     state=state)
        nb.add(frames["product_info"], text="Products Info", state=state)
        nb.add(frames["stock_info"],   text="Stock Info",    state=state)
        nb.add(frames["stats"],        text="Statistics",    state=state)
        nb.add(frames["about"],        text="About")

    def _build_views(self, frames: dict) -> None:
        from app.ui.views.home         import HomeView
        from app.ui.views.customer     import CustomerView
        from app.ui.views.product      import ProductView
        from app.ui.views.stock        import StockView
        from app.ui.views.sale         import SaleView
        from app.ui.views.due          import DueView
        from app.ui.views.stock_info   import StockInfoView
        from app.ui.views.stats        import StatsView
        from app.ui.views.product_info import ProductInfoView
        from app.ui.views.about        import AboutView

        w, r, d = self._widgets, self._right, self._down
        ctrl = self._controller

        view_map = {
            "home":         HomeView(frames["home"],         w, r, d, ctrl),
            "customer":     CustomerView(frames["customer"], w, r, d, ctrl),
            "product":      ProductView(frames["product"],   w, r, d, ctrl),
            "stock":        StockView(frames["stock"],       w, r, d, ctrl),
            "sale":         SaleView(frames["sale"],         w, r, d, ctrl),
            "due":          DueView(frames["due"],           w, r, d, ctrl),
            "stock_info":   StockInfoView(frames["stock_info"], w, r, d, ctrl),
            "stats":        StatsView(frames["stats"],       w, r, d, ctrl),
            "product_info": ProductInfoView(frames["product_info"], w, r, d, ctrl),
            "about":        AboutView(frames["about"],       w, r, d, ctrl),
        }

        for name, view in view_map.items():
            ctrl.register(name, view)

    # ── Entry point ───────────────────────────────────────────────────────────

    def run(self) -> None:
        self._root.mainloop()
