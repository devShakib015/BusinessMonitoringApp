"""The application shell: sidebar navigation around a stack of screens."""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (QButtonGroup, QFrame, QMainWindow, QMessageBox,
                               QPushButton, QStackedWidget, QWidget)

from app import config
from app.core import settings
from app.core.security import Session
from app.ui import icons, theme
from app.ui.widgets.common import hbox, label, vbox
from app.ui.widgets.toast import Toast

# name, label, icon, admin only, shortcut
NAV = [
    ("SELL", None, None, False, None),
    ("sell", "New sale", "sell", False, "Ctrl+1"),
    ("MANAGE", None, None, True, None),
    ("products", "Products", "products", True, "Ctrl+2"),
    ("stock", "Stock", "stock", True, "Ctrl+3"),
    ("customers", "Customers", "customers", False, "Ctrl+4"),
    ("RECORDS", None, None, False, None),
    ("sales", "Sales", "sales", False, "Ctrl+5"),
    ("dues", "Credit book", "dues", False, "Ctrl+6"),
    ("reports", "Reports", "reports", True, "Ctrl+7"),
    ("SYSTEM", None, None, False, None),
    ("settings", "Settings", "settings", True, None),
    ("users", "Staff", "users", True, None),
]


class MainWindow(QMainWindow):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self._pages: dict[str, QWidget] = {}
        self._buttons: dict[str, QPushButton] = {}
        self._toast: Toast | None = None
        self.sign_out_requested = False

        self.setWindowTitle(f"{settings.get('shop.name')} — {config.APP_NAME}")
        self.setWindowIcon(icons.app_icon())
        self.resize(1360, 850)
        self.setMinimumSize(1120, 700)

        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        row = hbox(root, spacing=0)
        row.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        row.addWidget(self.stack, 1)

        self._install_shortcuts()
        self.go("sell")

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("Sidebar")
        bar.setFixedWidth(228)
        body = vbox(bar, (0, 16, 0, 10), 0)

        body.addWidget(label(config.APP_NAME, "SidebarBrand"))
        shop = label(settings.get("shop.name"), "SidebarTagline")
        shop.setWordWrap(True)
        body.addWidget(shop)

        group = QButtonGroup(self)
        group.setExclusive(True)

        for name, text, icon_name, admin_only, shortcut in NAV:
            if admin_only and not self.session.is_admin:
                continue
            if text is None:
                if self._section_has_items(name):
                    body.addWidget(label(name, "SidebarSection"))
                continue
            item = QPushButton(f"  {text}")
            item.setObjectName("NavItem")
            item.setCheckable(True)
            item.setCursor(Qt.PointingHandCursor)
            item.setIcon(icons.icon(icon_name, "#98A2B3", 18))
            item.setIconSize(QSize(18, 18))
            item.clicked.connect(lambda _=False, key=name: self.go(key))
            if shortcut:
                item.setToolTip(f"{text}  ({shortcut})")
            group.addButton(item)
            body.addWidget(item)
            self._buttons[name] = item

        body.addStretch(1)
        body.addWidget(self._build_user_chip())
        body.addWidget(label(f"v{config.APP_VERSION}", "SidebarFooter"))
        return bar

    def _section_has_items(self, section: str) -> bool:
        seen = False
        for name, text, _icon, admin_only, _sc in NAV:
            if text is None:
                if seen:
                    return False
                seen = name == section
                continue
            if seen and (not admin_only or self.session.is_admin):
                return True
        return False

    def _build_user_chip(self) -> QWidget:
        chip = QFrame()
        chip.setObjectName("UserChip")
        row = hbox(chip, (0, 0, 0, 0), 10)

        text = vbox(spacing=1)
        text.addWidget(label(self.session.display_name, "UserChipName"))
        text.addWidget(label(
            "Owner / Admin" if self.session.is_admin else "Cashier", "UserChipRole"))
        row.addLayout(text, 1)

        out = QPushButton()
        out.setIcon(icons.icon("logout", "#98A2B3", 16))
        out.setFixedSize(28, 28)
        out.setCursor(Qt.PointingHandCursor)
        out.setToolTip("Sign out")
        out.setStyleSheet("QPushButton { background: transparent; border: none; }"
                          "QPushButton:hover { background: #262C36; border-radius: 6px; }")
        out.clicked.connect(self.sign_out)
        row.addWidget(out)
        return chip

    # ── Navigation ────────────────────────────────────────────────────────────

    def go(self, name: str) -> None:
        page = self._pages.get(name)
        if page is None:
            page = self._create_page(name)
            if page is None:
                return
            self._pages[name] = page
            self.stack.addWidget(page)

        self.stack.setCurrentWidget(page)
        for key, item in self._buttons.items():
            item.setChecked(key == name)
        if hasattr(page, "on_shown"):
            page.on_shown()

    def _create_page(self, name: str):
        from app.ui.pages import (customers, dues, products, reports, sales,
                                  sell, settings_page, stock, users)
        builders = {
            "sell": sell.SellPage,
            "products": products.ProductsPage,
            "stock": stock.StockPage,
            "customers": customers.CustomersPage,
            "sales": sales.SalesPage,
            "dues": dues.DuesPage,
            "reports": reports.ReportsPage,
            "settings": settings_page.SettingsPage,
            "users": users.UsersPage,
        }
        builder = builders.get(name)
        return builder(self.session, self) if builder else None

    def refresh_page(self, name: str) -> None:
        """Ask another screen to reload, if it has been opened."""
        page = self._pages.get(name)
        if page is not None and hasattr(page, "refresh"):
            page.refresh()

    def refresh_all(self) -> None:
        for name in list(self._pages):
            self.refresh_page(name)

    def restyle(self) -> None:
        """Re-apply the theme after a settings change, rebuilding every screen."""
        from PySide6.QtWidgets import QApplication
        theme.apply(QApplication.instance())
        current = self.stack.currentWidget()
        name = next((key for key, page in self._pages.items() if page is current), "sell")
        for page in self._pages.values():
            self.stack.removeWidget(page)
            page.deleteLater()
        self._pages.clear()

        old_bar = self.centralWidget().layout().itemAt(0).widget()
        self.centralWidget().layout().removeWidget(old_bar)
        old_bar.deleteLater()
        self._buttons.clear()
        self.centralWidget().layout().insertWidget(0, self._build_sidebar())
        self.setWindowTitle(f"{settings.get('shop.name')} — {config.APP_NAME}")
        self.go(name)

    # ── Feedback ──────────────────────────────────────────────────────────────

    def notify(self, message: str, tone: str = "info") -> None:
        if self._toast is not None:
            self._toast.deleteLater()
        self._toast = Toast(self, message, tone)
        self._toast.show_for()

    def confirm(self, title: str, message: str, confirm_text: str = "Continue",
                dangerous: bool = False) -> bool:
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(title)
        box.setInformativeText(message)
        box.setIcon(QMessageBox.Warning if dangerous else QMessageBox.Question)
        proceed = box.addButton(confirm_text, QMessageBox.AcceptRole)
        box.addButton("Cancel", QMessageBox.RejectRole)
        box.exec()
        return box.clickedButton() is proceed

    # ── Shortcuts and lifecycle ───────────────────────────────────────────────

    def _install_shortcuts(self) -> None:
        for name, _text, _icon, admin_only, shortcut in NAV:
            if not shortcut or (admin_only and not self.session.is_admin):
                continue
            QShortcut(QKeySequence(shortcut), self,
                      activated=lambda key=name: self.go(key))
        QShortcut(QKeySequence("Ctrl+Shift+T"), self, activated=self._toggle_theme)

    def _toggle_theme(self) -> None:
        settings.set_value("app.theme", "light" if theme.is_dark() else "dark")
        self.restyle()
        self.notify(f"Switched to {settings.get('app.theme')} theme")

    def sign_out(self) -> None:
        if not self.confirm("Sign out?",
                            "Any sale in progress will be lost.", "Sign out"):
            return
        self.sign_out_requested = True
        self.close()

    def resizeEvent(self, event):  # noqa: N802 - Qt naming
        super().resizeEvent(event)
        if self._toast is not None:
            self._toast._place()

    def closeEvent(self, event):  # noqa: N802 - Qt naming
        sell_page = self._pages.get("sell")
        if (sell_page is not None and not self.sign_out_requested
                and getattr(sell_page, "cart", None) and not sell_page.cart.is_empty):
            if not self.confirm("Close ShopDesk?",
                                "There is a sale in progress that has not been saved.",
                                "Close anyway", dangerous=True):
                event.ignore()
                return
        event.accept()
