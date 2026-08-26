import pytest

from app.core.quantity import ONE, parse_qty
from app.repo import customers as customer_repo, products as product_repo
from app.services import checkout, dues, returns
from app.services.cart import Cart


def _sell(product, qty=ONE, tendered=None, customer_id=None, money=None):
    cart = Cart()
    cart.add_product(product, qty)
    cart.customer_id = customer_id
    total = cart.totals().total
    return checkout.commit(cart, tendered=total if tendered is None else tendered,
                           method="cash" if tendered != 0 else "due")


def test_a_return_restocks_and_refunds(shop, make_product, money):
    product = make_product(price="10.00", stock="10")
    sale = _sell(product, parse_qty(3))

    lines = returns.returnable_lines(sale.sale_id)
    lines[0].qty = parse_qty(1)
    _, total = returns.commit(sale.sale_id, lines, method="cash")

    assert total == money("10.00")
    assert product_repo.stock_of(product["id"]) == parse_qty(8)


def test_nothing_can_be_returned_twice(shop, make_product):
    product = make_product(stock="10")
    sale = _sell(product, parse_qty(2))

    lines = returns.returnable_lines(sale.sale_id)
    lines[0].qty = parse_qty(2)
    returns.commit(sale.sale_id, lines, method="cash")

    assert returns.returnable_lines(sale.sale_id) == []


def test_returning_more_than_was_bought_is_refused(shop, make_product):
    product = make_product(stock="10")
    sale = _sell(product, parse_qty(2))

    lines = returns.returnable_lines(sale.sale_id)
    lines[0].qty = parse_qty(5)
    with pytest.raises(returns.ReturnError, match="can still be returned"):
        returns.commit(sale.sale_id, lines, method="cash")


def test_a_return_refunds_the_discounted_price_not_the_shelf_price(shop, make_product, money):
    product = make_product(price="100.00", stock="10")
    cart = Cart()
    cart.add_product(product, ONE)
    cart.set_discount_percent(20)
    sale = checkout.commit(cart, tendered=money("80.00"))

    lines = returns.returnable_lines(sale.sale_id)
    lines[0].qty = ONE
    _, total = returns.commit(sale.sale_id, lines, method="cash")

    assert total == money("80.00")


def test_damaged_goods_can_be_refunded_without_restocking(shop, make_product):
    product = make_product(stock="10")
    sale = _sell(product, parse_qty(2))

    lines = returns.returnable_lines(sale.sale_id)
    lines[0].qty = parse_qty(1)
    lines[0].restock = False
    returns.commit(sale.sale_id, lines, method="cash", reason="Damaged")

    assert product_repo.stock_of(product["id"]) == parse_qty(8)


def test_a_return_can_be_credited_to_the_customers_account(shop, make_product, money):
    product = make_product(price="10.00", stock="10")
    customer_id = customer_repo.create(name="Rahim")
    cart = Cart()
    cart.add_product(product, parse_qty(3))
    cart.customer_id = customer_id
    sale = checkout.commit(cart, tendered=0, method="due")
    assert customer_repo.balance_of(customer_id) == money("30.00")

    lines = returns.returnable_lines(sale.sale_id)
    lines[0].qty = parse_qty(1)
    returns.commit(sale.sale_id, lines, method="due")

    assert customer_repo.balance_of(customer_id) == money("20.00")


def test_a_walk_in_cannot_be_credited_to_an_account(shop, make_product):
    product = make_product(stock="10")
    sale = _sell(product)
    lines = returns.returnable_lines(sale.sale_id)
    lines[0].qty = ONE

    with pytest.raises(returns.ReturnError, match="walk-in"):
        returns.commit(sale.sale_id, lines, method="due")


def test_collecting_a_due_reduces_the_balance(shop, make_product, money):
    product = make_product(price="50.00", stock="10")
    customer_id = customer_repo.create(name="Rahim")
    cart = Cart()
    cart.add_product(product, ONE)
    cart.customer_id = customer_id
    checkout.commit(cart, tendered=0, method="due")

    dues.collect(customer_id, money("20.00"))
    assert customer_repo.balance_of(customer_id) == money("30.00")


def test_overpaying_a_due_is_refused_unless_allowed(shop, make_product, money):
    product = make_product(price="50.00", stock="10")
    customer_id = customer_repo.create(name="Rahim")
    cart = Cart()
    cart.add_product(product, ONE)
    cart.customer_id = customer_id
    checkout.commit(cart, tendered=0, method="due")

    with pytest.raises(dues.DueError, match="owes"):
        dues.collect(customer_id, money("80.00"))


def test_paying_a_customer_with_no_balance_is_refused(shop, money):
    customer_id = customer_repo.create(name="Rahim")
    with pytest.raises(dues.DueError, match="nothing outstanding"):
        dues.collect(customer_id, money("10.00"))
