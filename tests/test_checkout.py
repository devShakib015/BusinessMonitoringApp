import pytest

from app.core import settings
from app.core.quantity import ONE, parse_qty
from app.repo import customers as customer_repo, products as product_repo, sales as sale_repo
from app.services import checkout
from app.services.cart import Cart


def _cart_with(product, qty=ONE, customer_id=None):
    cart = Cart()
    cart.add_product(product, qty)
    cart.customer_id = customer_id
    return cart


def test_a_paid_sale_moves_stock_and_records_the_money(shop, make_product, money):
    product = make_product(price="10.00", stock="20")
    result = checkout.commit(_cart_with(product, parse_qty(3)), tendered=money("30.00"))

    assert result.due == 0
    assert result.change == 0
    assert product_repo.stock_of(product["id"]) == parse_qty(17)
    assert sale_repo.get(result.sale_id)["total"] == money("30.00")
    assert len(sale_repo.payments(result.sale_id)) == 1


def test_change_is_returned_but_never_recorded_as_income(shop, make_product, money):
    product = make_product(price="10.00")
    result = checkout.commit(_cart_with(product), tendered=money("50.00"))

    assert result.change == money("40.00")
    assert result.paid == money("10.00")


def test_a_walk_in_must_pay_in_full(shop, make_product, money):
    product = make_product(price="10.00")
    with pytest.raises(checkout.CheckoutError, match="Attach a customer"):
        checkout.commit(_cart_with(product), tendered=money("4.00"))


def test_a_customer_can_leave_a_balance_on_account(shop, make_product, money):
    product = make_product(price="10.00")
    customer_id = customer_repo.create(name="Rahim")
    result = checkout.commit(_cart_with(product, customer_id=customer_id),
                             tendered=money("4.00"))

    assert result.due == money("6.00")
    assert customer_repo.balance_of(customer_id) == money("6.00")


def test_credit_limit_is_enforced(shop, make_product, money):
    product = make_product(price="100.00")
    customer_id = customer_repo.create(name="Rahim", credit_limit=money("50.00"))
    cart = _cart_with(product, customer_id=customer_id)
    cart.customer_name = "Rahim"

    with pytest.raises(checkout.CheckoutError, match="credit limit"):
        checkout.commit(cart, tendered=0, method="due")


def test_overselling_is_blocked_by_default(shop, make_product, money):
    product = make_product(stock="2")
    with pytest.raises(checkout.CheckoutError, match="Not enough stock"):
        checkout.commit(_cart_with(product, parse_qty(5)), tendered=money("50.00"))


def test_overselling_is_allowed_when_the_shop_opts_in(shop, make_product, money):
    settings.set_value("pos.allow_negative_stock", "1")
    product = make_product(stock="2")
    checkout.commit(_cart_with(product, parse_qty(5)), tendered=money("50.00"))

    assert product_repo.stock_of(product["id"]) == parse_qty(-3)


def test_an_empty_cart_cannot_be_sold(shop):
    with pytest.raises(checkout.CheckoutError):
        checkout.commit(Cart(), tendered=0)


def test_invoice_numbers_run_in_sequence(shop, make_product, money):
    product = make_product(stock="100")
    numbers = [checkout.commit(_cart_with(product), tendered=money("10.00")).invoice_no
               for _ in range(3)]

    assert numbers == ["INV-00001", "INV-00002", "INV-00003"]


def test_a_failed_sale_leaves_no_trace(shop, make_product, money):
    product = make_product(stock="2")
    with pytest.raises(checkout.CheckoutError):
        checkout.commit(_cart_with(product, parse_qty(9)), tendered=money("90.00"))

    assert sale_repo.list_all() == []
    assert product_repo.stock_of(product["id"]) == parse_qty(2)


def test_voiding_a_sale_puts_the_stock_back(shop, make_product, money):
    product = make_product(stock="10")
    result = checkout.commit(_cart_with(product, parse_qty(4)), tendered=money("40.00"))
    checkout.void_sale(result.sale_id, reason="Rang up twice")

    assert product_repo.stock_of(product["id"]) == parse_qty(10)
    assert sale_repo.get(result.sale_id)["status"] == "void"
    assert sale_repo.payments(result.sale_id) == []


def test_a_voided_sale_stops_counting_against_the_customer(shop, make_product, money):
    product = make_product(price="10.00")
    customer_id = customer_repo.create(name="Rahim")
    result = checkout.commit(_cart_with(product, customer_id=customer_id), tendered=0,
                             method="due")
    assert customer_repo.balance_of(customer_id) == money("10.00")

    checkout.void_sale(result.sale_id, reason="Wrong customer")
    assert customer_repo.balance_of(customer_id) == 0


def test_voiding_needs_a_reason(shop, make_product, money):
    product = make_product()
    result = checkout.commit(_cart_with(product), tendered=money("10.00"))
    with pytest.raises(checkout.CheckoutError, match="reason"):
        checkout.void_sale(result.sale_id, reason="  ")
