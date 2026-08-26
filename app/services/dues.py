"""Collecting money owed on account."""

from app.core import settings
from app.repo import activity, customers as customer_repo, payments as payment_repo


class DueError(Exception):
    """A due collection that must not be saved."""


def collect(customer_id: int, amount: int, *, method: str = "cash",
            note: str = "", user_id: int | None = None,
            allow_overpay: bool = False) -> int:
    """Record a payment against a customer's outstanding balance."""
    customer = customer_repo.get(customer_id)
    if customer is None:
        raise DueError("That customer no longer exists.")
    if amount <= 0:
        raise DueError("Enter an amount greater than zero.")

    balance = int(customer["balance"])
    if balance <= 0:
        raise DueError(f"{customer['name']} has nothing outstanding.")
    if amount > balance and not allow_overpay:
        raise DueError(
            f"{customer['name']} owes {settings.money(balance)}. "
            f"You entered {settings.money(amount)}.")

    payment_id = payment_repo.collect_due(customer_id, amount, method=method,
                                          note=note, user_id=user_id)
    activity.record(user_id, "due.collect",
                    f"{customer['name']} · {settings.money(amount)}")
    return payment_id
