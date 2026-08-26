"""End-to-end checks that every screen and dialog can be built and driven.

These do not open a window -- Qt's offscreen platform renders into memory --
but they construct the real widgets against a real database, which is what
catches a page that crashes on an empty table or a dialog that references a
field it no longer has.
"""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication  # noqa: E402

from app.core.money import parse_amount  # noqa: E402
from app.core.quantity import ONE, parse_qty  # noqa: E402
from app.core.security import Session  # noqa: E402
from app.repo import customers as customer_repo, products as product_repo  # noqa: E402
from app.repo import users as user_repo  # noqa: E402
from app.services import checkout, demo  # noqa: E402
from app.services.cart import Cart  # noqa: E402

PAGES = ["sell", "products", "stock", "customers", "sales", "dues", "reports",
         "settings", "users"]


@pytest.fixture(scope="session")
def qt_app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def shop_with_data(shop, qt_app):
    """A signed-in admin looking at a small but complete shop."""
    from app.ui import theme
    user_id = user_repo.create("owner", "secret123", full_name="Owner", role="admin")
    demo.load(user_id=user_id, days=3, seed=99)
    theme.apply(qt_app)
    return Session(user_id=user_id, username="owner", full_name="Owner", role="admin")


@pytest.fixture
def window(shop_with_data):
    from app.ui.main_window import MainWindow
    main = MainWindow(shop_with_data)
    yield main
    # Closing with items in the cart asks for confirmation, and there is nobody
    # here to answer it.
    main.sign_out_requested = True
    main.close()


def test_every_page_builds_and_refreshes(window):
    for name in PAGES:
        window.go(name)
        assert window.stack.currentWidget() is window._pages[name]
        window._pages[name].refresh()


def test_pages_survive_an_empty_shop(shop, qt_app):
    """A brand new shop has no products, no sales and no customers."""
    from app.ui import theme
    from app.ui.main_window import MainWindow
    user_id = user_repo.create("owner", "secret123", role="admin")
    theme.apply(qt_app)
    main = MainWindow(Session(user_id, "owner", "", "admin"))
    for name in PAGES:
        main.go(name)
        main._pages[name].refresh()
    main.sign_out_requested = True
    main.close()


def test_a_cashier_does_not_see_the_admin_screens(shop_with_data, qt_app):
    from app.ui.main_window import MainWindow
    cashier = Session(user_id=shop_with_data.user_id, username="mina",
                      full_name="Mina", role="cashier")
    main = MainWindow(cashier)
    assert "products" not in main._buttons
    assert "reports" not in main._buttons
    assert "settings" not in main._buttons
    assert "sell" in main._buttons
    assert "dues" in main._buttons
    main.sign_out_requested = True
    main.close()


def test_selling_from_the_till_screen(window, shop_with_data):
    window.go("sell")
    page = window._pages["sell"]

    product = product_repo.list_all(active_only=True)[0]
    page._add_product(product, parse_qty(2))
    assert len(page.cart) == 1

    page.search.setText("a")
    page._on_search("a")

    page.cart.set_discount_percent(10)
    page._render()
    assert page.charge_button.isEnabled()

    page.tendered.set_value(parse_amount("500.00"))
    before = product_repo.stock_of(product["id"])

    # Charge through the service the page uses, so no dialog has to be shown.
    result = checkout.commit(page.cart, tendered=parse_amount("500.00"),
                             user_id=shop_with_data.user_id)
    assert result.change > 0
    assert product_repo.stock_of(product["id"]) == before - parse_qty(2)


def test_quantity_prefix_in_the_search_box(window):
    window.go("sell")
    page = window._pages["sell"]
    assert page._split_quantity("3*cola") == (parse_qty(3), "cola")
    assert page._split_quantity("2x rice") == (parse_qty(2), "rice")
    assert page._split_quantity("cola") == (ONE, "cola")


def test_product_editor_saves_and_validates(window):
    from app.ui.dialogs.product_editor import ProductEditor
    window.go("products")
    page = window._pages["products"]

    editor = ProductEditor(page)
    editor._save()
    assert "name" in editor._error.text().lower()

    editor._name.setText("Smoke test item")
    editor._sell.set_value(parse_amount("4.50"))
    editor._opening.set_value(parse_qty(7))
    editor._save()
    created = product_repo.get(editor.product_id)
    assert created["name"] == "Smoke test item"
    assert created["stock"] == parse_qty(7)

    duplicate = ProductEditor(page)
    duplicate._name.setText("Smoke test item")
    duplicate._sell.set_value(parse_amount("1.00"))
    duplicate._save()
    assert "already a product" in duplicate._error.text()


def test_customer_editor_and_detail(window, shop_with_data):
    from app.ui.dialogs.customer_detail import CustomerDetail, TakePaymentDialog
    from app.ui.dialogs.customer_picker import CustomerEditor
    window.go("customers")
    page = window._pages["customers"]

    editor = CustomerEditor(page)
    editor._name.setText("Smoke Test Trader")
    editor._save()
    customer_id = editor.customer_id
    assert customer_repo.get(customer_id)["name"] == "Smoke Test Trader"

    cart = Cart()
    cart.add_product(product_repo.list_all(active_only=True)[0], ONE)
    cart.customer_id = customer_id
    checkout.commit(cart, tendered=0, method="due", user_id=shop_with_data.user_id)

    detail = CustomerDetail(page, customer_id, shop_with_data.user_id)
    assert detail._ledger.rowCount() == 1

    payment = TakePaymentDialog(page, customer_repo.get(customer_id),
                                shop_with_data.user_id)
    payment._save()
    assert customer_repo.balance_of(customer_id) == 0


def test_sale_detail_and_a_return(window, shop_with_data):
    from app.repo import sales as sale_repo
    from app.ui.dialogs.sale_detail import ReturnDialog, SaleDetail, VoidDialog

    window.go("sales")
    page = window._pages["sales"]
    sale = sale_repo.list_all(limit=1)[0]

    detail = SaleDetail(page, sale["id"], shop_with_data.user_id, is_admin=True)
    assert detail._items.rowCount() > 0

    returning = ReturnDialog(page, sale["id"], shop_with_data.user_id)
    returning._editors[0][0].set_value(ONE)
    returning._recalculate()
    returning._save()
    assert sale_repo.returns_for(sale["id"])

    voiding = VoidDialog(page, sale["id"], shop_with_data.user_id)
    voiding._save()
    assert "returns recorded" in voiding._error.text()


def test_stock_dialogs(window, shop_with_data):
    from app.ui.dialogs.stock_dialogs import AdjustStockDialog, ReceiveStockDialog
    window.go("stock")
    page = window._pages["stock"]
    product = product_repo.list_all(active_only=True)[0]
    before = product_repo.stock_of(product["id"])

    receive = ReceiveStockDialog(page, product["id"])
    receive._qty.set_value(parse_qty(12))
    receive._cost.set_value(parse_amount("3.00"))
    receive._save()
    assert product_repo.stock_of(product["id"]) == before + parse_qty(12)

    counted = AdjustStockDialog(page, product["id"])
    counted._counted.set_value(parse_qty(5))
    counted._save()
    assert product_repo.stock_of(product["id"]) == parse_qty(5)


def test_day_close_compares_the_drawer(window):
    from app.ui.dialogs.day_close import DayCloseDialog
    window.go("reports")
    dialog = DayCloseDialog(window._pages["reports"])
    dialog._counted.set_value(dialog._expected)
    dialog._compare()
    assert "balances exactly" in dialog._difference.text()

    dialog._counted.set_value(dialog._expected + parse_amount("5.00"))
    dialog._compare()
    assert "over" in dialog._difference.text()


def test_settings_save_and_restyle(window):
    window.go("settings")
    page = window._pages["settings"]
    page.shop_name.setText("Renamed Shop")
    page.accent_choice.setCurrentIndex(1)
    page._save()

    from app.core import settings
    assert settings.get("shop.name") == "Renamed Shop"
    assert "Renamed Shop" in window.windowTitle()


def test_backup_and_restore_through_the_settings_screen(window):
    from app.services import backup
    window.go("settings")
    page = window._pages["settings"]
    page._backup()
    assert backup.list_backups()
    page._reload_backups()
    assert page.backups.rowCount() == len(backup.list_backups())


def test_theme_toggle_rebuilds_every_page(window):
    from app.core import settings
    for name in PAGES:
        window.go(name)
    window._toggle_theme()
    assert settings.get("app.theme") == "dark"
    window.go("reports")
    assert window.stack.currentWidget() is window._pages["reports"]
