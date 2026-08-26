"""Everything a shop changes to make the app its own."""

import os
import shutil

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QLineEdit,
                               QPlainTextEdit, QTabWidget, QTableWidgetItem,
                               QWidget)

from app import config
from app.core import db, settings
from app.services import backup, demo
from app.ui import theme
from app.ui.pages.base import Page
from app.ui.widgets.common import (Card, PageHeader, button, divider, hbox,
                                   label, table, vbox)

CURRENCIES = [
    ("USD", "$", 2), ("EUR", "€", 2), ("GBP", "£", 2), ("BDT", "৳", 2),
    ("INR", "₹", 2), ("PKR", "₨", 2), ("NGN", "₦", 2), ("KES", "KSh", 2),
    ("PHP", "₱", 2), ("IDR", "Rp", 0), ("JPY", "¥", 0), ("AED", "د.إ", 2),
    ("ZAR", "R", 2), ("BRL", "R$", 2), ("MXN", "$", 2), ("CAD", "$", 2),
    ("AUD", "$", 2), ("MYR", "RM", 2), ("LKR", "Rs", 2), ("NPR", "Rs", 2),
]


class SettingsPage(Page):
    def build(self) -> None:
        header = PageHeader("Settings", "Shop details, money, receipts and data.")
        self._save_button = header.add_action(
            button("Save changes", "primary", "check", self._save, "Ctrl+S"))
        self.layout.addWidget(header)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._shop_tab(), "Shop")
        self.tabs.addTab(self._money_tab(), "Money and tax")
        self.tabs.addTab(self._selling_tab(), "Selling")
        self.tabs.addTab(self._receipt_tab(), "Receipts")
        self.tabs.addTab(self._appearance_tab(), "Appearance")
        self.tabs.addTab(self._data_tab(), "Data and backups")
        self.layout.addWidget(self.tabs, 1)

    # ── Tab builders ──────────────────────────────────────────────────────────

    def _scroll(self, card: Card) -> QWidget:
        holder = QWidget()
        column = vbox(holder, (0, 14, 0, 0), 14)
        column.addWidget(card)
        column.addStretch(1)
        return holder

    def _field(self, caption: str, widget: QWidget, hint: str = "") -> QWidget:
        holder = QWidget()
        column = vbox(holder, spacing=5)
        column.addWidget(label(caption, "SectionTitle"))
        column.addWidget(widget)
        if hint:
            note = label(hint, "Faint")
            note.setWordWrap(True)
            column.addWidget(note)
        return holder

    def _pair(self, left: QWidget, right: QWidget) -> QWidget:
        holder = QWidget()
        row = hbox(holder, spacing=14)
        row.addWidget(left, 1)
        row.addWidget(right, 1)
        return holder

    def _shop_tab(self) -> QWidget:
        card = Card()
        card.body.addWidget(label("These details print on every receipt and invoice.",
                                  "Muted"))

        self.shop_name = QLineEdit(settings.get("shop.name"))
        self.shop_address = QLineEdit(settings.get("shop.address"))
        self.shop_phone = QLineEdit(settings.get("shop.phone"))
        self.shop_email = QLineEdit(settings.get("shop.email"))
        self.shop_website = QLineEdit(settings.get("shop.website"))
        self.shop_tax_id = QLineEdit(settings.get("shop.tax_id"))
        self.shop_footer = QPlainTextEdit(settings.get("shop.receipt_footer"))
        self.shop_footer.setFixedHeight(60)

        card.body.addWidget(self._field("Shop name", self.shop_name))
        card.body.addWidget(self._field("Address", self.shop_address))
        card.body.addWidget(self._pair(
            self._field("Phone", self.shop_phone),
            self._field("Email", self.shop_email)))
        card.body.addWidget(self._pair(
            self._field("Website", self.shop_website),
            self._field("Tax registration number", self.shop_tax_id)))
        card.body.addWidget(self._field("Receipt footer", self.shop_footer,
                                        "The thank-you line at the bottom."))

        logo_row = hbox(spacing=10)
        self.logo_path = QLineEdit(settings.get("shop.logo"))
        self.logo_path.setReadOnly(True)
        self.logo_path.setPlaceholderText("No logo chosen")
        logo_row.addWidget(self.logo_path, 1)
        logo_row.addWidget(button("Choose…", "", "", self._pick_logo))
        logo_row.addWidget(button("Remove", "ghost", "", self._clear_logo))
        logo_holder = QWidget()
        logo_holder.setLayout(logo_row)
        card.body.addWidget(self._field("Logo", logo_holder,
                                        "Shown on PDF invoices. PNG or JPG."))
        return self._scroll(card)

    def _money_tab(self) -> QWidget:
        card = Card()
        self.currency = QComboBox()
        for code, symbol, decimals in CURRENCIES:
            self.currency.addItem(f"{code}  ({symbol})", (code, symbol, decimals))
        index = next((i for i, (code, _s, _d) in enumerate(CURRENCIES)
                      if code == settings.get("currency.code")), 0)
        self.currency.setCurrentIndex(index)
        self.currency.currentIndexChanged.connect(self._currency_changed)

        self.symbol = QLineEdit(settings.get("currency.symbol"))
        self.symbol.setFixedWidth(90)
        self.decimals = QComboBox()
        self.decimals.addItems(["0", "1", "2", "3"])
        self.decimals.setCurrentText(str(settings.decimals()))

        card.body.addWidget(self._pair(
            self._field("Currency", self.currency),
            self._field("Symbol", self.symbol,
                        "What prints in front of amounts.")))
        card.body.addWidget(self._field(
            "Decimal places", self.decimals,
            "Set 0 for currencies with no small change. Changing this does not "
            "convert amounts already stored."))
        card.body.addWidget(divider())

        self.tax_enabled = QCheckBox("Charge tax on sales")
        self.tax_enabled.setChecked(settings.tax_enabled())
        self.tax_label_field = QLineEdit(settings.get("tax.label"))
        self.tax_rate = QLineEdit(settings.get("tax.rate"))
        self.tax_inclusive = QCheckBox("Prices already include tax")
        self.tax_inclusive.setChecked(settings.tax_inclusive())

        card.body.addWidget(self.tax_enabled)
        card.body.addWidget(self._pair(
            self._field("What it is called", self.tax_label_field,
                        "VAT, GST, Sales tax…"),
            self._field("Default rate (%)", self.tax_rate,
                        "Applied to new products.")))
        card.body.addWidget(self.tax_inclusive)

        self.rounding = QComboBox()
        self.rounding.addItem("No rounding", 0)
        for step, caption in ((1, "Nearest 0.01"), (5, "Nearest 0.05"),
                              (10, "Nearest 0.10"), (50, "Nearest 0.50"),
                              (100, "Nearest 1"), (500, "Nearest 5")):
            self.rounding.addItem(caption, step)
        current = settings.get_int("pos.round_total_to", 0)
        position = self.rounding.findData(current)
        self.rounding.setCurrentIndex(max(0, position))
        card.body.addWidget(self._field(
            "Round sale totals", self.rounding,
            "For shops where the smallest coin is bigger than the smallest unit."))
        return self._scroll(card)

    def _selling_tab(self) -> QWidget:
        card = Card()
        self.allow_negative = QCheckBox("Allow selling items that are out of stock")
        self.allow_negative.setChecked(settings.get_bool("pos.allow_negative_stock"))
        self.low_warning = QCheckBox("Warn when a sale takes stock below zero")
        self.low_warning.setChecked(settings.get_bool("pos.low_stock_warning"))
        self.confirm_sale = QCheckBox("Ask for confirmation before saving a sale")
        self.confirm_sale.setChecked(settings.get_bool("pos.confirm_before_save"))
        self.print_after = QCheckBox("Print a receipt automatically after each sale")
        self.print_after.setChecked(settings.get_bool("pos.print_after_sale"))

        self.methods = QLineEdit(", ".join(settings.get_list("pos.payment_methods")))
        self.default_method = QComboBox()
        for method in settings.get_list("pos.payment_methods"):
            self.default_method.addItem(method.title(), method)
        position = self.default_method.findData(settings.get("pos.default_payment"))
        self.default_method.setCurrentIndex(max(0, position))

        self.invoice_prefix = QLineEdit(settings.get("invoice.prefix"))
        self.invoice_pad = QComboBox()
        self.invoice_pad.addItems(["3", "4", "5", "6"])
        self.invoice_pad.setCurrentText(settings.get("invoice.pad"))

        for widget in (self.allow_negative, self.low_warning, self.confirm_sale,
                       self.print_after):
            card.body.addWidget(widget)
        card.body.addWidget(divider())
        card.body.addWidget(self._pair(
            self._field("Payment methods", self.methods,
                        "Comma separated. They appear as buttons on the till."),
            self._field("Default method", self.default_method)))
        card.body.addWidget(self._pair(
            self._field("Invoice prefix", self.invoice_prefix),
            self._field("Invoice number length", self.invoice_pad)))
        card.body.addWidget(label(
            f"Next invoice will look like "
            f"{settings.get('invoice.prefix')}"
            f"{'1'.zfill(settings.get_int('invoice.pad', 5))}", "Faint"))
        return self._scroll(card)

    def _receipt_tab(self) -> QWidget:
        card = Card()
        self.receipt_format = QComboBox()
        self.receipt_format.addItem("80mm roll (most thermal printers)", "80mm")
        self.receipt_format.addItem("58mm roll (small thermal printers)", "58mm")
        position = self.receipt_format.findData(settings.get("receipt.format"))
        self.receipt_format.setCurrentIndex(max(0, position))

        self.receipt_cashier = QCheckBox("Show who served the customer")
        self.receipt_cashier.setChecked(settings.get_bool("receipt.show_cashier"))

        card.body.addWidget(self._field("Receipt size", self.receipt_format))
        card.body.addWidget(self.receipt_cashier)
        card.body.addWidget(divider())
        card.body.addWidget(label(
            "Receipts print through whichever printer you choose in the print "
            "dialog, so any thermal printer installed on this computer works. "
            "A4 PDF invoices are produced separately from the sale screen.",
            "Muted"))
        card.body.addWidget(button("Print a test receipt", "", "print",
                                   self._test_receipt))
        return self._scroll(card)

    def _appearance_tab(self) -> QWidget:
        card = Card()
        self.theme_choice = QComboBox()
        self.theme_choice.addItem("Light", "light")
        self.theme_choice.addItem("Dark", "dark")
        position = self.theme_choice.findData(settings.get("app.theme"))
        self.theme_choice.setCurrentIndex(max(0, position))

        self.accent_choice = QComboBox()
        for name in theme.ACCENTS:
            self.accent_choice.addItem(name.title(), name)
        position = self.accent_choice.findData(settings.get("app.accent"))
        self.accent_choice.setCurrentIndex(max(0, position))

        card.body.addWidget(self._pair(
            self._field("Theme", self.theme_choice),
            self._field("Accent colour", self.accent_choice)))
        card.body.addWidget(label("Ctrl+Shift+T switches theme at any time.", "Faint"))
        return self._scroll(card)

    def _data_tab(self) -> QWidget:
        card = Card()
        card.body.addWidget(label("Where your data lives", "SectionTitle"))
        path_field = QLineEdit(db.path())
        path_field.setReadOnly(True)
        card.body.addWidget(path_field)
        card.body.addWidget(label(
            "Everything is stored in this single file on this computer. "
            "Nothing is sent anywhere.", "Faint"))

        actions = hbox(spacing=8)
        actions.addWidget(button("Back up now", "primary", "download", self._backup))
        actions.addWidget(button("Save a copy…", "", "download", self._export_backup))
        actions.addWidget(button("Restore…", "", "refresh", self._restore))
        actions.addStretch(1)
        holder = QWidget()
        holder.setLayout(actions)
        card.body.addWidget(holder)

        self.backups = table(["Backup", "Taken", "Size"], 0, 32)
        self.backups.setMaximumHeight(190)
        card.body.addWidget(self.backups)
        card.body.addWidget(divider())

        card.body.addWidget(label("Sample data", "SectionTitle"))
        card.body.addWidget(label(
            "Fills the shop with a month of example trading so you can try every "
            "screen. Use it on a fresh install, not on real data.", "Faint"))
        sample = hbox(spacing=8)
        sample.addWidget(button("Load sample data", "", "grid", self._load_sample))
        sample.addWidget(button("Erase all trading data", "danger", "trash",
                                self._wipe))
        sample.addStretch(1)
        sample_holder = QWidget()
        sample_holder.setLayout(sample)
        card.body.addWidget(sample_holder)
        return self._scroll(card)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _currency_changed(self) -> None:
        _code, symbol, decimals = self.currency.currentData()
        self.symbol.setText(symbol)
        self.decimals.setCurrentText(str(decimals))

    def _pick_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose a logo", os.path.expanduser("~"),
            "Images (*.png *.jpg *.jpeg)")
        if not path:
            return
        target = os.path.join(config.data_dir(), "logo" + os.path.splitext(path)[1])
        shutil.copy2(path, target)
        self.logo_path.setText(target)

    def _clear_logo(self) -> None:
        self.logo_path.clear()

    def _test_receipt(self) -> None:
        from app.repo import sales as sale_repo
        from app.printing import receipt
        sale = sale_repo.last_sale()
        if sale is None:
            self.notify("Make a sale first — the test prints a real receipt.",
                        "warning")
            return
        try:
            receipt.print_receipt(self, sale["id"], copy_label="TEST PRINT")
        except Exception as error:
            self.notify(f"Could not print: {error}", "error")

    def _save(self) -> None:
        try:
            tax_rate = float(self.tax_rate.text().strip() or 0)
        except ValueError:
            self.notify("The tax rate must be a number.", "error")
            return

        methods = [part.strip().lower() for part in self.methods.text().split(",")
                   if part.strip()] or ["cash"]

        settings.set_many({
            "shop.name": self.shop_name.text().strip() or "My Shop",
            "shop.address": self.shop_address.text(),
            "shop.phone": self.shop_phone.text(),
            "shop.email": self.shop_email.text(),
            "shop.website": self.shop_website.text(),
            "shop.tax_id": self.shop_tax_id.text(),
            "shop.receipt_footer": self.shop_footer.toPlainText(),
            "shop.logo": self.logo_path.text(),
            "currency.code": self.currency.currentData()[0],
            "currency.symbol": self.symbol.text().strip(),
            "currency.decimals": self.decimals.currentText(),
            "tax.enabled": int(self.tax_enabled.isChecked()),
            "tax.label": self.tax_label_field.text().strip() or "Tax",
            "tax.rate": tax_rate,
            "tax.inclusive": int(self.tax_inclusive.isChecked()),
            "pos.round_total_to": self.rounding.currentData(),
            "pos.allow_negative_stock": int(self.allow_negative.isChecked()),
            "pos.low_stock_warning": int(self.low_warning.isChecked()),
            "pos.confirm_before_save": int(self.confirm_sale.isChecked()),
            "pos.print_after_sale": int(self.print_after.isChecked()),
            "pos.payment_methods": ",".join(methods),
            "pos.default_payment": self.default_method.currentData() or methods[0],
            "invoice.prefix": self.invoice_prefix.text(),
            "invoice.pad": self.invoice_pad.currentText(),
            "receipt.format": self.receipt_format.currentData(),
            "receipt.show_cashier": int(self.receipt_cashier.isChecked()),
            "app.theme": self.theme_choice.currentData(),
            "app.accent": self.accent_choice.currentData(),
        })
        self.notify("Settings saved.", "success")
        self.window.restyle()

    def _backup(self) -> None:
        path = backup.create("manual")
        backup.prune(20)
        self._reload_backups()
        self.notify(f"Backup saved to {os.path.basename(path)}.", "success")

    def _export_backup(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save a copy of your data",
            os.path.join(os.path.expanduser("~"), "shopdesk-backup.db"),
            "ShopDesk backup (*.db)")
        if not path:
            return
        backup.export_copy(path)
        self.notify("Copy saved.", "success")

    def _restore(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose a backup", backup.folder(),
            "ShopDesk backup (*.db)")
        if not path:
            return
        if not self.window.confirm(
                "Restore this backup?",
                "Everything currently in the app is replaced by the backup. "
                "A copy of the current data is saved first.", "Restore", True):
            return
        try:
            backup.restore(path)
        except Exception as error:
            self.notify(f"Could not restore: {error}", "error")
            return
        settings.invalidate()
        self.window.refresh_all()
        self.window.restyle()
        self.notify("Backup restored.", "success")

    def _load_sample(self) -> None:
        if demo.is_loaded():
            if not self.window.confirm(
                    "Load sample data on top of your products?",
                    "Sample products, customers and sales will be added alongside "
                    "what is already here.", "Load anyway", True):
                return
        counts = demo.load(user_id=self.session.user_id)
        self.window.refresh_all()
        self.notify(
            f"Loaded {counts['products']} products and {counts['sales']} sales.",
            "success")

    def _wipe(self) -> None:
        if not self.window.confirm(
                "Erase all trading data?",
                "Products, customers, sales, stock and payments are deleted. "
                "Staff accounts and settings are kept. A backup is taken first.",
                "Erase everything", True):
            return
        backup.create("before-erase")
        demo.wipe()
        self.window.refresh_all()
        self._reload_backups()
        self.notify("All trading data erased.", "success")

    def _reload_backups(self) -> None:
        entries = backup.list_backups()
        self.backups.setRowCount(len(entries))
        for index, entry in enumerate(entries):
            cells = [entry["name"],
                     entry["created_at"].strftime("%d %b %Y, %I:%M %p"),
                     f"{entry['size'] / 1024:.0f} KB"]
            for column, text in enumerate(cells):
                cell = QTableWidgetItem(text)
                if column:
                    cell.setForeground(theme.color("text_muted"))
                if column == 2:
                    cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.backups.setItem(index, column, cell)

    def refresh(self) -> None:
        self._reload_backups()
