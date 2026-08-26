import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core import db, settings  # noqa: E402
from app.core.money import parse_amount  # noqa: E402
from app.repo import products as product_repo  # noqa: E402


@pytest.fixture
def shop(tmp_path):
    """A fresh, empty shop database for one test."""
    db.reset_for_tests(str(tmp_path / "test.db"))
    settings.invalidate()
    yield
    db.close()
    settings.invalidate()


@pytest.fixture
def money():
    return lambda text: parse_amount(text, 2)


@pytest.fixture
def make_product(money):
    def _make(name="Widget", price="10.00", cost="6.00", stock="20", **extra):
        from app.core.quantity import parse_qty
        from app.repo import stock as stock_repo
        product_id = product_repo.create(
            name=name, sell_price=money(price), cost_price=money(cost), **extra)
        if stock:
            stock_repo.add_movement(product_id, parse_qty(stock), "opening",
                                    unit_cost=money(cost))
        return product_repo.get(product_id)
    return _make
