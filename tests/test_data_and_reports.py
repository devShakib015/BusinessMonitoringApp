import os
from datetime import date, timedelta

import pytest

from app.core import clock, db
from app.repo import customers as customer_repo, products as product_repo, reports
from app.services import backup, demo, held
from app.services.cart import Cart
from app.core.quantity import ONE


def test_sample_data_produces_a_working_shop(shop):
    counts = demo.load(days=10, seed=7)

    assert counts["products"] == len(demo.CATALOGUE)
    assert counts["sales"] > 0
    assert product_repo.count_active() == len(demo.CATALOGUE)

    start, end = clock.range_bounds(date.today() - timedelta(days=10), date.today())
    summary = reports.summary(start, end)
    assert summary["sale_count"] == counts["sales"]
    assert summary["total"] > 0
    assert reports.top_products(start, end)


def test_sample_data_never_leaves_negative_stock(shop):
    demo.load(days=8, seed=11)
    worst = db.scalar(
        "SELECT MIN(s.stock) FROM (SELECT COALESCE(SUM(qty), 0) AS stock "
        "FROM stock_movements GROUP BY product_id) s", default=0)
    assert worst >= 0


def test_wipe_clears_trading_data_but_keeps_the_shop(shop):
    from app.repo import users
    users.create("owner", "secret123", role="admin")
    demo.load(days=3, seed=5)
    demo.wipe()

    assert product_repo.count_active() == 0
    assert reports.today_snapshot()["sale_count"] == 0
    assert users.count() == 1


def test_backup_and_restore_round_trip(shop, make_product):
    make_product(name="Before backup")
    snapshot = backup.create("test")
    assert os.path.exists(snapshot)

    product_repo.create(name="After backup", sell_price=100)
    assert product_repo.count_active() == 2

    backup.restore(snapshot)
    names = [row["name"] for row in product_repo.list_all()]
    assert names == ["Before backup"]


def test_restore_refuses_a_file_that_is_not_a_shop(shop, tmp_path):
    junk = tmp_path / "notes.db"
    junk.write_bytes(b"this is not a database")
    with pytest.raises(Exception):
        backup.restore(str(junk))


def test_holding_a_sale_frees_the_till(shop, make_product):
    cart = Cart()
    cart.add_product(make_product(name="Rice"), ONE)
    held.hold(cart, label="")

    assert held.count() == 1
    resumed = held.resume(held.list_all()[0]["id"])
    assert resumed.lines[0].name == "Rice"
    assert held.count() == 0


def test_customer_ledger_reads_as_a_statement(shop, make_product, money):
    from app.services import checkout, dues
    customer_id = customer_repo.create(name="Rahim")
    cart = Cart()
    cart.add_product(make_product(price="40.00"), ONE)
    cart.customer_id = customer_id
    checkout.commit(cart, tendered=0, method="due")
    dues.collect(customer_id, money("15.00"))

    entries = customer_repo.ledger(customer_id)
    assert len(entries) == 2
    assert sum(entry["amount"] for entry in entries) == money("25.00")


def test_backups_live_beside_the_database(shop, tmp_path, make_product):
    """A test run must never write into the real user's data directory."""
    make_product()
    path = backup.create("isolation")

    assert os.path.dirname(path) == os.path.join(str(tmp_path), "backups")
    assert [entry["name"] for entry in backup.list_backups()] == [os.path.basename(path)]
