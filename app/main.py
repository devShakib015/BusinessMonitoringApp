"""Application entry point."""

import os
import sys
import tempfile

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from app import config
from app.core import db, settings
from app.repo import users as user_repo
from app.ui import icons, theme


def run() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    app.setApplicationDisplayName(config.APP_NAME)
    app.setApplicationVersion(config.APP_VERSION)
    app.setOrganizationName(config.PUBLISHER)

    try:
        db.connect()
    except Exception as error:
        QMessageBox.critical(None, config.APP_NAME,
                             f"The shop database could not be opened.\n\n{error}")
        return 1

    theme.apply(app)
    app.setWindowIcon(icons.app_icon())

    from app.ui.login import LoginDialog, SetupWizard
    from app.ui.main_window import MainWindow

    while True:
        if not user_repo.has_any() or not settings.is_setup_complete():
            entry = SetupWizard()
        else:
            entry = LoginDialog()
        if not entry.exec() or entry.session is None:
            break

        theme.apply(app)
        window = MainWindow(entry.session)
        window.show()
        app.exec()
        if not window.sign_out_requested:
            break

    db.close()
    return 0


def selftest() -> int:
    """Prove a built copy works, without opening a window or touching real data.

    Packaging is the step most likely to break silently -- a missing Qt plugin
    or an unbundled module only shows up when someone runs the download.  This
    drives a whole sale through the release build in a throwaway directory.
    """
    from app.core.money import parse_amount
    from app.core.quantity import parse_qty
    from app.printing import invoice_pdf, receipt
    from app.repo import products as product_repo, stock as stock_repo
    from app.services import checkout
    from app.services.cart import Cart

    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    with tempfile.TemporaryDirectory(prefix="shopdesk-selftest-") as workspace:
        os.environ["SHOPDESK_DATA_DIR"] = workspace
        app = QApplication(sys.argv)

        db.connect()
        theme.apply(app)
        icons.app_icon()

        user_id = user_repo.create("selftest", "selftest-password", role="admin")
        product_id = product_repo.create(name="Test item", sell_price=parse_amount("9.50"),
                                         cost_price=parse_amount("5.00"))
        stock_repo.add_movement(product_id, parse_qty(10), "opening")

        cart = Cart()
        cart.add_product(product_repo.get(product_id), parse_qty(2))
        sale = checkout.commit(cart, tendered=parse_amount("20.00"), user_id=user_id)
        assert sale.change == parse_amount("1.00"), "change calculation is wrong"
        assert product_repo.stock_of(product_id) == parse_qty(8), "stock did not move"

        assert "TOTAL" in receipt.build_html(sale.sale_id), "receipt did not render"
        pdf = invoice_pdf.build(sale.sale_id, os.path.join(workspace, "invoice.pdf"))
        assert os.path.getsize(pdf) > 1000, "invoice PDF looks empty"

        from app.ui.login import LoginDialog
        from app.ui.main_window import MainWindow
        from app.core.security import Session
        LoginDialog()
        MainWindow(Session(user_id, "selftest", "Self test", "admin"))

        db.close()

    print(f"{config.APP_NAME} {config.APP_VERSION}: self-test passed "
          f"(sale {sale.invoice_no}, receipt and invoice rendered).")
    return 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else run())
