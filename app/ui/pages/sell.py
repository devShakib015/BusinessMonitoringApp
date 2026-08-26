"""The till.

Everything a cashier does between one customer and the next happens here:
scan or search, adjust, take money, hand back change.  The design target is
that a sale for a customer paying cash needs a scan and one key.
"""

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (QButtonGroup, QListWidget, QListWidgetItem,
                               QPushButton, QTableWidgetItem, QWidget)

from app.core import settings
from app.core.money import format_plain
from app.core.quantity import ONE, format_qty, parse_qty
from app.printing import receipt
from app.repo import customers as customer_repo, products as product_repo
from app.services import checkout, held
from app.services.cart import Cart
from app.ui import icons, theme
from app.ui.dialogs.customer_picker import CustomerPicker
from app.ui.dialogs.sell_dialogs import (CustomItemDialog, DiscountDialog,
                                         HeldSalesDialog, LineEditorDialog,
                                         SaleCompleteDialog)
from app.ui.pages.base import Page
from app.ui.widgets.common import (Card, EmptyState, MoneyEdit, SearchField, button,
                                   clear_layout, divider, hbox, label, table, vbox)

METHOD_ICONS = {"cash": "cash", "card": "card", "mobile": "mobile", "bank": "bank"}


class SellPage(Page):
    title = "New sale"

    def build(self) -> None:
        self.cart = Cart()
        self.layout.setContentsMargins(20, 18, 20, 18)
        self.layout.setSpacing(0)

        row = hbox(spacing=18)
        row.addWidget(self._build_left(), 1)
        row.addWidget(self._build_right())
        self.layout.addLayout(row, 1)

        self._install_shortcuts()
        self._render()

    # ── Left: search and cart ─────────────────────────────────────────────────

    def _build_left(self) -> QWidget:
        panel = QWidget()
        column = vbox(panel, spacing=12)

        top = hbox(spacing=8)
        self.search = SearchField("Scan a barcode or search by name…", big=True)
        self.search.textChanged.connect(self._on_search)
        self.search.returnPressed.connect(self._on_search_enter)
        self.search.installEventFilter(self)
        top.addWidget(self.search, 1)

        self.hold_button = button("Hold", "ghost", "hold", self._hold, "F4",
                                  "Set this sale aside")
        self.resume_button = button("Held", "ghost", "resume", self._resume, "F5",
                                    "Pick up a held sale")
        top.addWidget(self.hold_button)
        top.addWidget(self.resume_button)
        top.addWidget(button("One-off", "ghost", "plus", self._custom_item, "F6",
                             "Sell something not in the catalogue"))
        column.addLayout(top)

        self.cart_table = table(
            ["#", "Item", "Unit price", "Qty", "Discount", "Amount"], 1, 40)
        self.cart_table.itemDoubleClicked.connect(lambda _: self._edit_line())
        column.addWidget(self.cart_table, 1)

        self.empty = EmptyState(
            "empty_cart", "No items yet",
            "Scan a barcode, or start typing a product name in the search box "
            "above. Press F1 at any time to jump back to search.")
        column.addWidget(self.empty, 1)

        hints = hbox(spacing=14)
        for key, what in (("F1", "Search"), ("F2", "Customer"), ("F3", "Discount"),
                          ("F9", "Charge"), ("Del", "Remove line"),
                          ("Enter", "Add item")):
            hints.addWidget(label(f"{key}  {what}", "Faint"))
        hints.addStretch(1)
        column.addLayout(hints)

        # Search results float over the cart, anchored under the search box.
        self.results = QListWidget(panel)
        self.results.setObjectName("SearchResults")
        self.results.setStyleSheet(
            f"QListWidget {{ background: {theme.hex_of('surface')};"
            f" border: 1px solid {theme.hex_of('border_strong')};"
            f" border-radius: 10px; padding: 4px; }}"
            f"QListWidget::item {{ padding: 8px 10px; border-radius: 7px; }}"
            f"QListWidget::item:selected {{ background: {theme.hex_of('selection')};"
            f" color: {theme.hex_of('text')}; }}")
        self.results.itemActivated.connect(lambda item: self._add_from_result(item))
        self.results.itemClicked.connect(lambda item: self._add_from_result(item))
        self.results.hide()
        return panel

    # ── Right: totals and payment ─────────────────────────────────────────────

    def _build_right(self) -> QWidget:
        panel = Card(padding=18, spacing=14)
        panel.setFixedWidth(372)
        body = panel.body

        customer_row = hbox(spacing=8)
        badge = QWidget()
        badge_layout = vbox(badge, spacing=1)
        self.customer_label = label("Walk-in customer", "SectionTitle")
        self.customer_hint = label("No account attached", "Faint")
        badge_layout.addWidget(self.customer_label)
        badge_layout.addWidget(self.customer_hint)
        customer_row.addWidget(badge, 1)
        customer_row.addWidget(button("Change", "ghost", "customers",
                                      self._choose_customer, "F2"))
        body.addLayout(customer_row)
        body.addWidget(divider())

        self.total_rows = {}
        for key, caption in (("subtotal", "Subtotal"), ("discount", "Discount"),
                             ("tax", settings.tax_label()), ("rounding", "Rounding")):
            line = hbox(spacing=8)
            line.addWidget(label(caption, "TotalRowLabel"))
            line.addStretch(1)
            value = label("—", "TotalRowValue")
            line.addWidget(value)
            holder = QWidget()
            holder.setLayout(line)
            self.total_rows[key] = (holder, value)
            body.addWidget(holder)

        discount_row = hbox(spacing=8)
        discount_row.addWidget(button("Add discount", "ghost", "tag",
                                      self._discount, "F3"))
        discount_row.addStretch(1)
        body.addLayout(discount_row)

        body.addWidget(divider())
        grand = hbox(spacing=8)
        grand.addWidget(label("Total", "GrandTotalLabel"))
        grand.addStretch(1)
        self.grand_total = label(settings.money(0), "GrandTotalValue")
        grand.addWidget(self.grand_total)
        body.addLayout(grand)

        body.addWidget(label("PAYMENT METHOD", "StatLabel"))
        methods = hbox(spacing=6)
        self.method_group = QButtonGroup(self)
        self.method_group.setExclusive(True)
        for method in settings.get_list("pos.payment_methods"):
            chip = QPushButton(method.title())
            chip.setObjectName("PayMethod")
            chip.setCheckable(True)
            chip.setCursor(Qt.PointingHandCursor)
            chip.setIcon(icons.icon(METHOD_ICONS.get(method, "cash"),
                                    theme.hex_of("text_muted"), 15))
            chip.setProperty("method", method)
            chip.clicked.connect(self._render_payment)
            self.method_group.addButton(chip)
            methods.addWidget(chip)
        default = settings.get("pos.default_payment")
        for chip in self.method_group.buttons():
            if chip.property("method") == default:
                chip.setChecked(True)
        if self.method_group.checkedButton() is None and self.method_group.buttons():
            self.method_group.buttons()[0].setChecked(True)
        body.addLayout(methods)

        self.tendered = MoneyEdit(placeholder="Exact amount")
        self.tendered.textChanged.connect(self._render_payment)
        body.addWidget(self.tendered)

        self.quick_cash = hbox(spacing=6)
        body.addLayout(self.quick_cash)

        change_row = hbox(spacing=8)
        change_row.addWidget(label("Change", "TotalRowLabel"))
        change_row.addStretch(1)
        self.change_label = label(settings.money(0), "ChangeValue")
        change_row.addWidget(self.change_label)
        self.change_holder = QWidget()
        self.change_holder.setLayout(change_row)
        body.addWidget(self.change_holder)

        body.addStretch(1)

        self.charge_button = QPushButton("Charge")
        self.charge_button.setObjectName("ChargeButton")
        self.charge_button.setCursor(Qt.PointingHandCursor)
        self.charge_button.clicked.connect(self._charge)
        body.addWidget(self.charge_button)

        clear = button("Clear sale", "ghost", "trash", self._clear_cart)
        body.addWidget(clear)
        return panel

    # ── Shortcuts ─────────────────────────────────────────────────────────────

    def _install_shortcuts(self) -> None:
        pairs = [
            ("F1", lambda: (self.search.setFocus(), self.search.selectAll())),
            ("F9", self._charge),
            ("Ctrl+Return", self._charge),
            ("Delete", self._remove_selected),
            ("Ctrl+D", self._discount),
        ]
        for key, action in pairs:
            QShortcut(QKeySequence(key), self, activated=action)

    # ── Search ────────────────────────────────────────────────────────────────

    def _split_quantity(self, text: str) -> tuple[int, str]:
        """``3*cola`` and ``3x cola`` mean three of them."""
        for separator in ("*", "x", "X"):
            head, found, tail = text.partition(separator)
            if found and head.strip().replace(".", "", 1).isdigit() and tail.strip():
                try:
                    return parse_qty(head.strip()), tail.strip()
                except ValueError:
                    break
        return ONE, text

    def _on_search(self, text: str) -> None:
        term = text.strip()
        if not term:
            self.results.hide()
            return
        _qty, term = self._split_quantity(term)
        matches = product_repo.search_for_sale(term, limit=30)
        self.results.clear()
        for product in matches:
            stock = int(product["stock"])
            detail = (f"{settings.money(int(product['sell_price']))}"
                      f"   ·   {format_qty(stock, product['unit'])} in stock"
                      if product["track_stock"]
                      else settings.money(int(product["sell_price"])))
            if product["sku"]:
                detail += f"   ·   {product['sku']}"
            item = QListWidgetItem(f"{product['name']}\n{detail}")
            item.setData(Qt.UserRole, product["id"])
            if product["track_stock"] and stock <= 0:
                item.setForeground(theme.color("text_faint"))
            self.results.addItem(item)

        if not matches:
            self.results.hide()
            return
        self.results.setCurrentRow(0)
        self._place_results()
        self.results.show()
        self.results.raise_()

    def _place_results(self) -> None:
        panel = self.results.parentWidget()
        origin = self.search.mapTo(panel, self.search.rect().bottomLeft())
        height = min(320, max(60, self.results.count() * 46 + 10))
        self.results.setGeometry(origin.x(), origin.y() + 6,
                                 self.search.width(), height)

    def _on_search_enter(self) -> None:
        raw = self.search.text().strip()
        if not raw:
            return
        qty, term = self._split_quantity(raw)

        exact = product_repo.get_by_barcode(term) or product_repo.get_by_sku(term)
        if exact is not None:
            self._add_product(exact, qty)
            return
        item = self.results.currentItem()
        if item is not None:
            self._add_from_result(item, qty)
            return
        self.notify(f"Nothing matches “{term}”.", "warning")

    def _add_from_result(self, item: QListWidgetItem, qty: int | None = None) -> None:
        product = product_repo.get(item.data(Qt.UserRole))
        if product is None:
            return
        if qty is None:
            qty, _term = self._split_quantity(self.search.text().strip())
        self._add_product(product, qty)

    def _add_product(self, product, qty: int = ONE) -> None:
        if (product["track_stock"] and int(product["stock"]) <= 0
                and not settings.get_bool("pos.allow_negative_stock")):
            self.notify(f"{product['name']} is out of stock.", "warning")
            return

        line = self.cart.add_product(product, qty)
        if (settings.get_bool("pos.low_stock_warning") and product["track_stock"]
                and line.qty > int(product["stock"])):
            self.notify(
                f"Only {format_qty(int(product['stock']), product['unit'])} of "
                f"{product['name']} left in stock.", "warning")

        self.search.clear()
        self.results.hide()
        self._render()
        self.cart_table.selectRow(self.cart.lines.index(line))

    def eventFilter(self, source, event):  # noqa: N802 - Qt naming
        if source is self.search and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Down and self.results.isVisible():
                self.results.setCurrentRow(
                    min(self.results.currentRow() + 1, self.results.count() - 1))
                return True
            if event.key() == Qt.Key_Up and self.results.isVisible():
                self.results.setCurrentRow(max(self.results.currentRow() - 1, 0))
                return True
            if event.key() == Qt.Key_Escape:
                self.results.hide()
                self.search.clear()
                return True
        return super().eventFilter(source, event)

    # ── Cart rendering ────────────────────────────────────────────────────────

    def _render(self) -> None:
        lines = self.cart.lines
        self.cart_table.setVisible(bool(lines))
        self.empty.setVisible(not lines)

        self.cart_table.setRowCount(len(lines))
        for index, line in enumerate(lines):
            cells = [
                (str(index + 1), Qt.AlignCenter),
                (line.name + (f"   ({line.sku})" if line.sku else ""), None),
                (format_plain(line.unit_price, settings.decimals()),
                 Qt.AlignRight | Qt.AlignVCenter),
                (format_qty(line.qty, line.unit), Qt.AlignRight | Qt.AlignVCenter),
                (format_plain(line.discount, settings.decimals()) if line.discount
                 else "—", Qt.AlignRight | Qt.AlignVCenter),
                (format_plain(line.net, settings.decimals()),
                 Qt.AlignRight | Qt.AlignVCenter),
            ]
            for column, (text, alignment) in enumerate(cells):
                cell = QTableWidgetItem(text)
                if alignment:
                    cell.setTextAlignment(alignment)
                if column in (0, 4):
                    cell.setForeground(theme.color("text_muted"))
                if column == 5:
                    font = cell.font()
                    font.setBold(True)
                    cell.setFont(font)
                self.cart_table.setItem(index, column, cell)

        self._render_totals()
        self._render_customer()
        self._render_payment()
        self.resume_button.setText(f"Held ({held.count()})" if held.count() else "Held")

    def _render_totals(self) -> None:
        totals = self.cart.totals()
        values = {
            "subtotal": totals.subtotal,
            "discount": -totals.discount if totals.discount else 0,
            "tax": totals.tax,
            "rounding": totals.rounding,
        }
        for key, (holder, widget) in self.total_rows.items():
            amount = values[key]
            visible = bool(amount) or key == "subtotal"
            holder.setVisible(visible)
            widget.setText(settings.money(amount))
            if key == "discount":
                widget.setStyleSheet(f"color: {theme.hex_of('success')};")
        self.grand_total.setText(settings.money(totals.total))
        self.charge_button.setEnabled(not self.cart.is_empty)

    def _render_customer(self) -> None:
        if self.cart.customer_id is None:
            self.customer_label.setText("Walk-in customer")
            self.customer_hint.setText("No account attached")
            return
        customer = customer_repo.get(self.cart.customer_id)
        if customer is None:
            self.cart.customer_id = None
            self._render_customer()
            return
        balance = int(customer["balance"])
        self.customer_label.setText(customer["name"])
        self.customer_hint.setText(
            f"{customer['phone'] or customer['code']}"
            + (f"  ·  owes {settings.money(balance)}" if balance > 0 else ""))

    def _render_payment(self) -> None:
        totals = self.cart.totals()
        method = self._method()
        tendered = self.tendered.value_or_none()
        if not self.tendered.text().strip():
            tendered = totals.total

        change = max(0, (tendered or 0) - totals.total) if method == "cash" else 0
        shortfall = max(0, totals.total - (tendered or 0))

        self.change_holder.setVisible(method == "cash" and not self.cart.is_empty)
        self.change_label.setText(settings.money(change))

        if shortfall and self.cart.customer_id is not None:
            self.charge_button.setText(
                f"Charge {settings.money(totals.total)}  ·  "
                f"{settings.money(shortfall)} on account")
        elif shortfall and not self.cart.is_empty:
            self.charge_button.setText(f"Charge {settings.money(totals.total)}")
        else:
            self.charge_button.setText(
                f"Charge {settings.money(totals.total)}" if not self.cart.is_empty
                else "Charge")

        self._render_quick_cash(totals.total)

    def _render_quick_cash(self, total: int) -> None:
        clear_layout(self.quick_cash)
        if self.cart.is_empty or self._method() != "cash":
            return

        unit = 10 ** settings.decimals()
        steps, seen = [], {total}
        for note in (unit, 5 * unit, 10 * unit, 50 * unit, 100 * unit):
            rounded = ((total + note - 1) // note) * note
            if rounded not in seen and len(steps) < 3:
                steps.append(rounded)
                seen.add(rounded)

        exact = QPushButton("Exact")
        exact.setObjectName("QuickCash")
        exact.setCursor(Qt.PointingHandCursor)
        exact.clicked.connect(lambda: self.tendered.set_value(total))
        self.quick_cash.addWidget(exact)
        for amount in steps:
            chip = QPushButton(format_plain(amount, settings.decimals(), grouping=False))
            chip.setObjectName("QuickCash")
            chip.setCursor(Qt.PointingHandCursor)
            chip.clicked.connect(lambda _=False, value=amount:
                                 self.tendered.set_value(value))
            self.quick_cash.addWidget(chip)

    def _method(self) -> str:
        chip = self.method_group.checkedButton()
        return chip.property("method") if chip else "cash"

    # ── Line actions ──────────────────────────────────────────────────────────

    def _selected_index(self) -> int | None:
        rows = self.cart_table.selectionModel().selectedRows()
        return rows[0].row() if rows else None

    def _edit_line(self) -> None:
        index = self._selected_index()
        if index is None:
            return
        line = self.cart.lines[index]
        dialog = LineEditorDialog(self, line, allow_price_change=self.session.is_admin)
        if dialog.exec():
            if dialog.removed:
                self.cart.remove(index)
            self._render()

    def _remove_selected(self) -> None:
        index = self._selected_index()
        if index is None:
            return
        self.cart.remove(index)
        self._render()

    def _clear_cart(self) -> None:
        if self.cart.is_empty:
            return
        if not self.window.confirm("Clear this sale?",
                                   "Every line will be removed.", "Clear", True):
            return
        self.cart.clear()
        self.tendered.clear()
        self._render()
        self.search.setFocus()

    def _custom_item(self) -> None:
        dialog = CustomItemDialog(self)
        if dialog.exec():
            self.cart.add_custom(dialog.name, dialog.price, dialog.qty)
            self._render()

    def _discount(self) -> None:
        if self.cart.is_empty:
            self.notify("Add something to the sale first.", "warning")
            return
        if DiscountDialog(self, self.cart).exec():
            self._render()

    def _choose_customer(self) -> None:
        picker = CustomerPicker(self)
        if not picker.exec():
            return
        if picker.selected is None:
            self.cart.customer_id = None
            self.cart.customer_name = ""
        else:
            self.cart.customer_id = picker.selected["id"]
            self.cart.customer_name = picker.selected["name"]
        self._render()

    # ── Hold and resume ───────────────────────────────────────────────────────

    def _hold(self) -> None:
        if self.cart.is_empty:
            self.notify("There is nothing to hold.", "warning")
            return
        held.hold(self.cart, user_id=self.session.user_id)
        self.cart = Cart()
        self.tendered.clear()
        self._render()
        self.search.setFocus()
        self.notify("Sale held. Press F5 to bring it back.", "success")

    def _resume(self) -> None:
        if not self.cart.is_empty:
            if not self.window.confirm(
                    "Replace the current sale?",
                    "Hold or clear the sale in progress first, or it will be lost.",
                    "Replace", True):
                return
        dialog = HeldSalesDialog(self)
        if dialog.exec() and dialog.resume_id:
            self.cart = held.resume(dialog.resume_id)
            self._render()
            self.notify("Held sale resumed.", "success")

    # ── Checkout ──────────────────────────────────────────────────────────────

    def _charge(self) -> None:
        if self.cart.is_empty:
            return
        totals = self.cart.totals()
        method = self._method()

        tendered = self.tendered.value_or_none()
        if not self.tendered.text().strip():
            tendered = totals.total
        if tendered is None:
            self.notify("That payment amount is not a number.", "error")
            return

        if settings.get_bool("pos.confirm_before_save"):
            if not self.window.confirm(
                    f"Charge {settings.money(totals.total)}?",
                    f"{totals.item_count} line(s) · {method.title()}", "Charge"):
                return

        try:
            result = checkout.commit(self.cart, tendered=tendered, method=method,
                                     user_id=self.session.user_id)
        except checkout.CheckoutError as error:
            self.window.confirm("Cannot complete this sale", str(error), "OK")
            return

        if settings.get_bool("pos.print_after_sale"):
            try:
                receipt.print_receipt(self, result.sale_id, ask=False)
            except Exception as error:
                self.notify(f"Sale saved, but printing failed: {error}", "warning")

        self.cart = Cart()
        self.tendered.clear()
        self._render()

        SaleCompleteDialog(self, result).exec()
        self.window.refresh_page("sales")
        self.window.refresh_page("dues")
        self.window.refresh_page("reports")
        self.window.refresh_page("products")
        self.search.setFocus()

    # ── Page lifecycle ────────────────────────────────────────────────────────

    def refresh(self) -> None:
        self._render()

    def on_shown(self) -> None:
        self.refresh()
        self.search.setFocus()

    def resizeEvent(self, event):  # noqa: N802 - Qt naming
        super().resizeEvent(event)
        if self.results.isVisible():
            self._place_results()
