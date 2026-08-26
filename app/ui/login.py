"""Signing in, and the first-run setup for a brand new shop."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
                               QLineEdit, QStackedWidget, QWidget)

from app import config
from app.core import settings
from app.core.security import Session, password_problem
from app.repo import users as user_repo
from app.services import demo
from app.ui import icons, theme
from app.ui.pages.settings_page import CURRENCIES
from app.ui.widgets.common import Card, button, hbox, hint, label, vbox


class LoginDialog(QDialog):
    """Username and password, on a centred card."""

    def __init__(self):
        super().__init__()
        self.session: Session | None = None
        self.setWindowTitle(f"Sign in — {config.APP_NAME}")
        self.setWindowIcon(icons.app_icon())
        self.setFixedSize(420, 470)
        self.setStyleSheet(f"QDialog {{ background: {theme.hex_of('bg')}; }}")

        outer = vbox(self, (36, 34, 36, 28), 16)

        brand = QWidget()
        brand_layout = vbox(brand, spacing=4)
        mark = label("")
        mark.setPixmap(icons.app_icon().pixmap(56, 56))
        mark.setAlignment(Qt.AlignCenter)
        brand_layout.addWidget(mark)
        title = label(settings.get("shop.name"), "PageTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        brand_layout.addWidget(title)
        tagline = label(f"{config.APP_NAME} · {config.APP_TAGLINE}", "PageSubtitle")
        tagline.setAlignment(Qt.AlignCenter)
        brand_layout.addWidget(tagline)
        outer.addWidget(brand)

        card = Card(padding=22, spacing=12)
        self._username = QLineEdit()
        self._username.setPlaceholderText("Username")
        self._password = QLineEdit()
        self._password.setPlaceholderText("Password")
        self._password.setEchoMode(QLineEdit.Password)
        self._password.returnPressed.connect(self._sign_in)
        self._username.returnPressed.connect(self._password.setFocus)

        self._remember = QCheckBox("Remember this username")
        self._remember.setChecked(bool(settings.get("app.last_user", "")))
        self._username.setText(settings.get("app.last_user", ""))

        self._error = label("")
        self._error.setWordWrap(True)
        self._error.setStyleSheet(
            f"color: {theme.hex_of('danger')}; background: {theme.hex_of('danger_soft')};"
            f"border-radius: 8px; padding: 8px 10px; font-weight: 600;")
        self._error.hide()

        card.body.addWidget(label("Sign in", "SectionTitle"))
        card.body.addWidget(self._username)
        card.body.addWidget(self._password)
        card.body.addWidget(self._remember)
        card.body.addWidget(self._error)
        card.body.addWidget(button("Sign in", "primary", on_click=self._sign_in))
        outer.addWidget(card)

        outer.addStretch(1)
        footer = label(f"v{config.APP_VERSION}  ·  data stays on this computer",
                       "Faint")
        footer.setAlignment(Qt.AlignCenter)
        outer.addWidget(footer)

        (self._password if self._username.text() else self._username).setFocus()

    def _sign_in(self) -> None:
        username = self._username.text().strip()
        password = self._password.text()
        if not username or not password:
            self._show("Enter your username and password.")
            return

        session = user_repo.authenticate(username, password)
        if session is None:
            self._show("That username and password do not match an account.")
            self._password.clear()
            self._password.setFocus()
            return

        settings.set_value("app.last_user", username if self._remember.isChecked() else "")
        self.session = session
        self.accept()

    def _show(self, message: str) -> None:
        self._error.setText(message)
        self._error.show()


class SetupWizard(QDialog):
    """Three questions, then the shop is open."""

    def __init__(self):
        super().__init__()
        self.session: Session | None = None
        self.setWindowTitle(f"Set up {config.APP_NAME}")
        self.setWindowIcon(icons.app_icon())
        self.setFixedSize(560, 600)
        self.setStyleSheet(f"QDialog {{ background: {theme.hex_of('bg')}; }}")

        outer = vbox(self, (34, 30, 34, 24), 16)

        self._title = label("Welcome", "PageTitle")
        self._subtitle = label("", "PageSubtitle")
        self._subtitle.setWordWrap(True)
        outer.addWidget(self._title)
        outer.addWidget(self._subtitle)

        self._steps = QStackedWidget()
        self._steps.addWidget(self._shop_step())
        self._steps.addWidget(self._money_step())
        self._steps.addWidget(self._account_step())
        outer.addWidget(self._steps, 1)

        self._error = label("")
        self._error.setWordWrap(True)
        self._error.setStyleSheet(
            f"color: {theme.hex_of('danger')}; background: {theme.hex_of('danger_soft')};"
            f"border-radius: 8px; padding: 8px 10px; font-weight: 600;")
        self._error.hide()
        outer.addWidget(self._error)

        controls = hbox(spacing=8)
        self._progress = label("Step 1 of 3", "Faint")
        controls.addWidget(self._progress)
        controls.addStretch(1)
        self._back = button("Back", "ghost", on_click=self._go_back)
        self._next = button("Continue", "primary", on_click=self._go_next)
        controls.addWidget(self._back)
        controls.addWidget(self._next)
        outer.addLayout(controls)

        self._show_step(0)

    # ── Steps ─────────────────────────────────────────────────────────────────

    def _shop_step(self) -> QWidget:
        card = Card(padding=22, spacing=12)
        self._shop_name = QLineEdit()
        self._shop_name.setPlaceholderText("Rahman General Store")
        self._shop_address = QLineEdit()
        self._shop_address.setPlaceholderText("Street, town")
        self._shop_phone = QLineEdit()
        self._shop_phone.setPlaceholderText("Phone customers can call")

        card.body.addWidget(label("Shop name", "SectionTitle"))
        card.body.addWidget(self._shop_name)
        card.body.addWidget(label("Address", "SectionTitle"))
        card.body.addWidget(self._shop_address)
        card.body.addWidget(label("Phone", "SectionTitle"))
        card.body.addWidget(self._shop_phone)
        card.body.addWidget(hint(
            "These print on your receipts and invoices. You can change them "
            "any time in Settings."))
        return _wrap(card)

    def _money_step(self) -> QWidget:
        card = Card(padding=22, spacing=12)
        self._currency = QComboBox()
        for code, symbol, decimals in CURRENCIES:
            self._currency.addItem(f"{code}  —  {symbol}", (code, symbol, decimals))

        self._tax_enabled = QCheckBox("I charge tax on sales")
        self._tax_label = QLineEdit("VAT")
        self._tax_rate = QLineEdit("0")
        self._tax_inclusive = QCheckBox("My shelf prices already include tax")

        card.body.addWidget(label("Currency", "SectionTitle"))
        card.body.addWidget(self._currency)
        card.body.addWidget(self._tax_enabled)
        row = hbox(spacing=12)
        row.addWidget(self._tax_label, 1)
        row.addWidget(self._tax_rate, 1)
        holder = QWidget()
        holder.setLayout(row)
        card.body.addWidget(label("Tax name and default rate (%)", "SectionTitle"))
        card.body.addWidget(holder)
        card.body.addWidget(self._tax_inclusive)
        card.body.addWidget(hint(
            "Leave tax switched off if you do not charge it — nothing about tax "
            "will appear on the till."))
        return _wrap(card)

    def _account_step(self) -> QWidget:
        card = Card(padding=22, spacing=12)
        self._full_name = QLineEdit()
        self._full_name.setPlaceholderText("Your name")
        self._username = QLineEdit()
        self._username.setPlaceholderText("Username you will sign in with")
        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.Password)
        self._password.setPlaceholderText("At least 6 characters")
        self._confirm = QLineEdit()
        self._confirm.setEchoMode(QLineEdit.Password)
        self._confirm.setPlaceholderText("Type it again")
        self._sample = QCheckBox("Fill the shop with sample data so I can try it out")
        self._sample.setChecked(True)

        card.body.addWidget(label("Owner account", "SectionTitle"))
        card.body.addWidget(self._full_name)
        card.body.addWidget(self._username)
        card.body.addWidget(self._password)
        card.body.addWidget(self._confirm)
        card.body.addWidget(self._sample)
        card.body.addWidget(hint(
            "This account can do everything. You can add cashiers later, who can "
            "sell but cannot change prices or see reports."))
        return _wrap(card)

    # ── Navigation ────────────────────────────────────────────────────────────

    HEADINGS = [
        ("Welcome to ShopDesk", "First, tell the app about your shop."),
        ("Money", "How you price and what you charge on top."),
        ("Your account", "One last step — an account to sign in with."),
    ]

    def _show_step(self, index: int) -> None:
        self._steps.setCurrentIndex(index)
        title, subtitle = self.HEADINGS[index]
        self._title.setText(title)
        self._subtitle.setText(subtitle)
        self._progress.setText(f"Step {index + 1} of {self._steps.count()}")
        self._back.setVisible(index > 0)
        self._next.setText("Finish setup" if index == self._steps.count() - 1
                           else "Continue")
        self._error.hide()

    def _go_back(self) -> None:
        self._show_step(max(0, self._steps.currentIndex() - 1))

    def _go_next(self) -> None:
        index = self._steps.currentIndex()
        if index == 0:
            if not self._shop_name.text().strip():
                self._show("Give your shop a name.")
                return
        elif index == 1:
            try:
                float(self._tax_rate.text().strip() or 0)
            except ValueError:
                self._show("The tax rate must be a number, for example 15.")
                return

        if index < self._steps.count() - 1:
            self._show_step(index + 1)
            return
        self._finish()

    def _finish(self) -> None:
        username = self._username.text().strip()
        if not username:
            self._show("Choose a username.")
            return
        problem = password_problem(self._password.text(), self._confirm.text())
        if problem:
            self._show(problem)
            return

        code, symbol, decimals = self._currency.currentData()
        settings.set_many({
            "shop.name": self._shop_name.text().strip(),
            "shop.address": self._shop_address.text().strip(),
            "shop.phone": self._shop_phone.text().strip(),
            "currency.code": code,
            "currency.symbol": symbol,
            "currency.decimals": decimals,
            "tax.enabled": int(self._tax_enabled.isChecked()),
            "tax.label": self._tax_label.text().strip() or "Tax",
            "tax.rate": self._tax_rate.text().strip() or 0,
            "tax.inclusive": int(self._tax_inclusive.isChecked()),
            "app.setup_complete": 1,
        })

        user_id = user_repo.create(username, self._password.text(),
                                   full_name=self._full_name.text().strip(),
                                   role="admin")
        if self._sample.isChecked():
            self._next.setEnabled(False)
            self._next.setText("Preparing sample data…")
            self._next.repaint()
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                demo.load(user_id=user_id, days=21)
            finally:
                QApplication.restoreOverrideCursor()

        self.session = Session(user_id=user_id, username=username,
                               full_name=self._full_name.text().strip(), role="admin")
        self.accept()

    def _show(self, message: str) -> None:
        self._error.setText(message)
        self._error.show()


def _wrap(card: Card) -> QWidget:
    holder = QWidget()
    column = vbox(holder, spacing=0)
    column.addWidget(card)
    column.addStretch(1)
    return holder
