"""Sample data.

Someone who downloads a point-of-sale app should be able to see what it does
before typing in their own catalogue.  This fills the shop with a plausible
month of trading -- products, customers, sales, credit and returns -- through
the same code paths a real shop uses, so nothing here is a special case the
rest of the app has to know about.
"""

import random
from datetime import datetime, timedelta

from app.core import clock, db, settings
from app.core.money import parse_amount
from app.core.quantity import ONE, parse_qty
from app.repo import (activity, customers as customer_repo,
                      products as product_repo, stock)
from app.services import checkout
from app.services.cart import Cart

# name, category, unit, cost, price, opening stock, barcode tail
CATALOGUE = [
    ("Basmati Rice 5kg",        "Grocery",       "bag",  "8.20",  "11.50",  40),
    ("Sunflower Oil 1L",        "Grocery",       "btl",  "2.10",   "3.25", 120),
    ("Refined Sugar 1kg",       "Grocery",       "kg",   "0.85",   "1.20", 200),
    ("Red Lentils 1kg",         "Grocery",       "kg",   "1.05",   "1.60", 150),
    ("Wheat Flour 2kg",         "Grocery",       "bag",  "1.40",   "2.10",  90),
    ("Table Salt 1kg",          "Grocery",       "kg",   "0.25",   "0.45", 180),
    ("Rock Sea Salt 500g",      "Grocery",       "pkt",  "0.60",   "0.95",  60),
    ("Tomato Ketchup 500g",     "Grocery",       "btl",  "1.30",   "2.00",  70),

    ("Mineral Water 1.5L",      "Beverages",     "btl",  "0.35",   "0.60", 240),
    ("Cola 500ml",              "Beverages",     "can",  "0.45",   "0.80", 300),
    ("Orange Juice 1L",         "Beverages",     "btl",  "1.20",   "1.90",  80),
    ("Green Tea 100 bags",      "Beverages",     "box",  "2.40",   "3.60",  45),
    ("Instant Coffee 200g",     "Beverages",     "jar",  "4.10",   "5.95",  35),
    ("Energy Drink 250ml",      "Beverages",     "can",  "0.90",   "1.50", 110),

    ("Potato Chips 150g",       "Snacks",        "pkt",  "0.70",   "1.20", 160),
    ("Salted Peanuts 200g",     "Snacks",        "pkt",  "0.80",   "1.35", 130),
    ("Chocolate Bar 45g",       "Snacks",        "pc",   "0.40",   "0.75", 320),
    ("Butter Biscuits 300g",    "Snacks",        "pkt",  "1.10",   "1.75",  95),
    ("Mixed Nuts 250g",         "Snacks",        "pkt",  "2.60",   "3.90",  50),

    ("Laundry Powder 1kg",      "Household",     "pkt",  "1.90",   "2.85",  75),
    ("Dish Soap 500ml",         "Household",     "btl",  "0.95",   "1.55",  85),
    ("Floor Cleaner 1L",        "Household",     "btl",  "1.35",   "2.20",  60),
    ("Kitchen Towel 2 rolls",   "Household",     "pack", "0.85",   "1.40", 100),
    ("Bin Bags 30pc",           "Household",     "roll", "1.10",   "1.80",  70),
    ("AA Batteries 4pc",        "Household",     "pack", "1.50",   "2.60",  90),

    ("Bath Soap 125g",          "Personal Care", "pc",   "0.45",   "0.85", 210),
    ("Shampoo 400ml",           "Personal Care", "btl",  "2.30",   "3.60",  65),
    ("Toothpaste 100g",         "Personal Care", "tube", "1.05",   "1.75", 120),
    ("Toothbrush Soft",         "Personal Care", "pc",   "0.55",   "1.10", 140),
    ("Shaving Foam 200ml",      "Personal Care", "can",  "1.80",   "2.95",  40),
    ("Hand Sanitiser 100ml",    "Personal Care", "btl",  "0.70",   "1.30",  95),

    ("Ballpoint Pen Blue",      "Stationery",    "pc",   "0.15",   "0.35", 400),
    ("A4 Notebook 200pg",       "Stationery",    "pc",   "1.20",   "2.10",  85),
    ("Sticky Notes 3x3",        "Stationery",    "pad",  "0.60",   "1.10",  90),
    ("Glue Stick 15g",          "Stationery",    "pc",   "0.40",   "0.80",  75),
]

CUSTOMERS = [
    ("Rahim Traders",      "01711000101", "12 Market Road", "300.00"),
    ("Sultana Grocers",    "01711000102", "5 Station Lane",  "200.00"),
    ("Karim Enterprise",   "01711000103", "88 Mill Street",  "500.00"),
    ("Nasrin Store",       "01711000104", "3 Canal Side",      "0.00"),
    ("Hasan Brothers",     "01711000105", "41 Old Bazaar",   "250.00"),
    ("Farida Mini Mart",   "01711000106", "7 Green Avenue",  "150.00"),
]


def is_loaded() -> bool:
    return not db.table_is_empty("products")


def load(user_id: int | None = None, days: int = 30, seed: int = 20260826) -> dict:
    """Populate an empty shop with a month of trading.  Returns a count summary."""
    rng = random.Random(seed)
    decimals = settings.decimals()

    with activity.muted():
        product_ids = _seed_catalogue(rng, decimals, days, user_id)
        customer_ids = _seed_customers(decimals)
        sale_count, return_count = _seed_sales(rng, decimals, days, product_ids,
                                               customer_ids, user_id)

    return {
        "products": len(product_ids),
        "customers": len(customer_ids),
        "sales": sale_count,
        "returns": return_count,
    }


def _seed_catalogue(rng, decimals, days, user_id) -> list[int]:
    ids = []
    opened_at = (datetime.now() - timedelta(days=days + 1)).strftime(clock.STAMP)
    for index, (name, category, unit, cost, price, opening) in enumerate(CATALOGUE):
        product_id = product_repo.create(
            name=name,
            sku=f"SKU{index + 1:04d}",
            barcode=f"860{index + 1:010d}",
            category_id=product_repo.category_id_for(category),
            unit=unit,
            cost_price=parse_amount(cost, decimals),
            sell_price=parse_amount(price, decimals),
            tax_rate=settings.default_tax_rate(),
            low_stock_level=parse_qty(rng.choice([5, 10, 12, 15, 20])),
        )
        db.execute(
            "INSERT INTO stock_movements(product_id, qty, unit_cost, reason, note, "
            "user_id, created_at) VALUES (?,?,?,'opening','Opening stock',?,?)",
            (product_id, parse_qty(opening), parse_amount(cost, decimals),
             user_id, opened_at))
        ids.append(product_id)
    return ids


def _seed_customers(decimals) -> list[int]:
    ids = []
    for name, phone, address, limit in CUSTOMERS:
        ids.append(customer_repo.create(
            name=name, phone=phone, address=address,
            credit_limit=parse_amount(limit, decimals)))
    return ids


def _seed_sales(rng, decimals, days, product_ids, customer_ids, user_id):
    """Trade the shop forward day by day, busier at weekends and in the evening."""
    sale_count = 0
    sale_ids: list[int] = []
    start = datetime.now() - timedelta(days=days)

    for offset in range(days + 1):
        day = start + timedelta(days=offset)
        busy = day.weekday() in (4, 5)          # Friday/Saturday market days
        for _ in range(rng.randint(4, 11) + (3 if busy else 0)):
            moment = day.replace(
                hour=rng.choices(range(9, 21),
                                 weights=[3, 4, 5, 6, 5, 4, 5, 7, 9, 8, 6, 3])[0],
                minute=rng.randint(0, 59), second=rng.randint(0, 59))
            if moment > datetime.now():
                continue

            cart = Cart()
            for product_id in rng.sample(product_ids, rng.randint(1, 6)):
                product = product_repo.get(product_id)
                if product["stock"] <= 0:
                    continue
                wanted = parse_qty(rng.randint(1, 4))
                cart.add_product(product, min(wanted, product["stock"]))
            if cart.is_empty:
                continue

            if rng.random() < 0.18:
                cart.set_discount_percent(rng.choice([2, 5, 10]))

            on_account = rng.random() < 0.16
            if on_account:
                customer_id = rng.choice(customer_ids)
                customer = customer_repo.get(customer_id)
                cart.customer_id = customer_id
                cart.customer_name = customer["name"]

            total = cart.totals().total
            if on_account:
                tendered = rng.choice([0, total // 2, total * 3 // 4])
                method = "cash" if tendered else "due"
            else:
                tendered = total
                method = rng.choices(["cash", "card", "mobile"],
                                     weights=[6, 2, 2])[0]

            try:
                result = checkout.commit(cart, tendered=tendered, method=method,
                                         user_id=user_id,
                                         when=moment.strftime(clock.STAMP))
            except checkout.CheckoutError:
                continue
            sale_ids.append(result.sale_id)
            sale_count += 1

    return_count = _seed_returns(rng, sale_ids, user_id)
    _seed_due_payments(rng, customer_ids, decimals, user_id)
    _seed_restocks(rng, product_ids, user_id)
    return sale_count, return_count


def _seed_returns(rng, sale_ids, user_id) -> int:
    from app.services import returns as returns_service

    count = 0
    for sale_id in rng.sample(sale_ids, min(4, len(sale_ids))):
        lines = returns_service.returnable_lines(sale_id)
        if not lines:
            continue
        line = lines[0]
        line.qty = min(ONE, line.max_qty)
        try:
            returns_service.commit(sale_id, [line], method="cash",
                                   reason="Customer changed their mind",
                                   user_id=user_id)
            count += 1
        except returns_service.ReturnError:
            continue
    return count


def _seed_due_payments(rng, customer_ids, decimals, user_id) -> None:
    from app.services import dues

    for customer_id in customer_ids:
        balance = customer_repo.balance_of(customer_id)
        if balance <= 0 or rng.random() < 0.35:
            continue
        try:
            dues.collect(customer_id, max(1, int(balance * rng.uniform(0.3, 0.8))),
                         method="cash", note="Part payment", user_id=user_id)
        except dues.DueError:
            continue


def _seed_restocks(rng, product_ids, user_id) -> None:
    """Top most lines back up, but leave a few running low.

    A shop where nothing ever needs reordering is not a shop -- the low-stock
    warnings and the reorder report have nothing to show.
    """
    for product_id in product_ids:
        product = product_repo.get(product_id)
        if product["stock"] > product["low_stock_level"] or rng.random() < 0.22:
            continue
        stock.receive(product_id, parse_qty(rng.randint(20, 60)),
                      int(product["cost_price"]), note="Weekly restock",
                      user_id=user_id)


def wipe() -> None:
    """Remove all trading data, keeping users and settings."""
    with db.transaction() as conn:
        for table in ("return_items", "sale_returns", "payments", "sale_items",
                      "sales", "stock_movements", "held_sales", "products",
                      "categories", "customers", "activity_log"):
            conn.execute(f"DELETE FROM {table}")
        conn.execute("DELETE FROM counters")
        conn.execute("DELETE FROM sqlite_sequence")
