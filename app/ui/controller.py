class AppController:
    """
    Mediates cross-view refresh calls so that individual views do not need to
    hold direct references to one another.

    Each view registers itself by name on startup. Controller methods then call
    the matching view's ``refresh()`` method when data shared across views changes.
    """

    def __init__(self):
        self._views: dict = {}

    def register(self, name: str, view) -> None:
        self._views[name] = view

    # ── Granular refresh helpers ──────────────────────────────────────────────

    def refresh_sales(self):
        self._call("sale", "refresh")

    def refresh_dues(self):
        self._call("due", "refresh")

    def refresh_stats(self):
        self._call("stats", "refresh")

    def refresh_product_info(self):
        self._call("product_info", "refresh")

    def refresh_stock_info(self):
        self._call("stock_info", "refresh")

    def refresh_home(self):
        self._call("home", "refresh")

    def refresh_products(self):
        self._call("product", "refresh")

    def refresh_stocks(self):
        self._call("stock", "refresh")

    def refresh_customers(self):
        self._call("customer", "refresh")

    # ── Domain-event helpers (group the common refresh combinations) ──────────

    def on_product_changed(self):
        """Call after adding, editing, or deleting a product."""
        self.refresh_products()
        self.refresh_home()
        self.refresh_stocks()
        self.refresh_product_info()

    def on_stock_changed(self):
        """Call after adding, editing, or deleting stock."""
        self.refresh_stocks()
        self.refresh_home()
        self.refresh_product_info()
        self.refresh_stats()

    def on_sale_made(self):
        """Call after a sale is saved."""
        self.refresh_sales()
        self.refresh_dues()
        self.refresh_product_info()
        self.refresh_stats()
        self.refresh_stock_info()
        self.refresh_home()

    def on_due_paid(self):
        """Call after a due payment is saved."""
        self.refresh_dues()
        self.refresh_stats()

    def on_customer_changed(self):
        """Call after adding, editing, or deleting a customer."""
        self.refresh_customers()
        self.refresh_sales()
        self.refresh_dues()

    # ── Internal ─────────────────────────────────────────────────────────────

    def _call(self, name: str, method: str):
        view = self._views.get(name)
        if view and hasattr(view, method):
            getattr(view, method)()
