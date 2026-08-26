from app.core import settings
from app.core.quantity import ONE, parse_qty
from app.services.cart import Cart


def test_totals_of_a_simple_basket(shop, make_product, money):
    cart = Cart()
    cart.add_product(make_product(name="Rice", price="11.50"), parse_qty(2))
    cart.add_product(make_product(name="Oil", price="3.25"), ONE)

    totals = cart.totals()
    assert totals.subtotal == money("26.25")
    assert totals.total == money("26.25")
    assert totals.item_count == 2


def test_scanning_the_same_product_twice_merges_the_line(shop, make_product):
    cart = Cart()
    product = make_product()
    cart.add_product(product, ONE)
    cart.add_product(product, ONE)

    assert len(cart) == 1
    assert cart.lines[0].qty == parse_qty(2)


def test_percentage_discount(shop, make_product, money):
    cart = Cart()
    cart.add_product(make_product(price="100.00"), ONE)
    cart.set_discount_percent(10)

    totals = cart.totals()
    assert totals.order_discount == money("10.00")
    assert totals.total == money("90.00")


def test_discount_cannot_exceed_the_basket(shop, make_product, money):
    cart = Cart()
    cart.add_product(make_product(price="10.00"), ONE)
    cart.set_discount_amount(money("999.00"))

    assert cart.totals().total == 0


def test_exclusive_tax_is_added_on_top(shop, make_product, money):
    settings.set_many({"tax.enabled": "1", "tax.rate": "15", "tax.inclusive": "0"})
    cart = Cart()
    cart.add_product(make_product(price="100.00", tax_rate=15.0), ONE)

    totals = cart.totals()
    assert totals.tax == money("15.00")
    assert totals.total == money("115.00")


def test_inclusive_tax_is_carved_out_of_the_price(shop, make_product, money):
    settings.set_many({"tax.enabled": "1", "tax.rate": "15", "tax.inclusive": "1"})
    cart = Cart()
    cart.add_product(make_product(price="115.00", tax_rate=15.0), ONE)

    totals = cart.totals()
    assert totals.tax == money("15.00")
    assert totals.total == money("115.00")


def test_order_discount_reduces_the_tax_it_carries(shop, make_product, money):
    settings.set_many({"tax.enabled": "1", "tax.rate": "10", "tax.inclusive": "0"})
    cart = Cart()
    cart.add_product(make_product(price="100.00", tax_rate=10.0), ONE)
    cart.set_discount_percent(50)

    totals = cart.totals()
    assert totals.tax == money("5.00")
    assert totals.total == money("55.00")


def test_discount_split_across_lines_adds_up(shop, make_product, money):
    cart = Cart()
    for price in ("3.33", "3.33", "3.34"):
        cart.add_product(make_product(name=f"P{price}", price=price), ONE)
    cart.set_discount_amount(money("1.00"))

    assert sum(cart.line_shares()) == money("1.00")
    assert cart.totals().total == money("9.00")


def test_rounding_to_the_nearest_unit(shop, make_product, money):
    settings.set_value("pos.round_total_to", str(money("1.00")))
    cart = Cart()
    cart.add_product(make_product(price="10.40"), ONE)

    totals = cart.totals()
    assert totals.rounding == money("-0.40")
    assert totals.total == money("10.00")


def test_fractional_quantity_of_a_weighed_product(shop, make_product, money):
    cart = Cart()
    cart.add_product(make_product(price="2.40", unit="kg"), parse_qty("1.5"))

    assert cart.totals().total == money("3.60")


def test_stock_problems_are_reported_per_line(shop, make_product):
    cart = Cart()
    cart.add_product(make_product(name="Rice", stock="2"), parse_qty(5))

    problems = cart.stock_problems()
    assert len(problems) == 1
    assert "Rice" in problems[0]


def test_hold_and_resume_round_trips(shop, make_product):
    cart = Cart()
    cart.add_product(make_product(), parse_qty(3))
    cart.set_discount_percent(5)
    cart.customer_name = "Rahim"

    restored = Cart.from_payload(cart.to_payload())
    assert restored.totals().total == cart.totals().total
    assert restored.customer_name == "Rahim"
