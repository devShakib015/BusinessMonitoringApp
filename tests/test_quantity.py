import pytest

from app.core.quantity import format_qty, multiply, parse_qty


@pytest.mark.parametrize("text,expected", [
    ("1", 1000), ("1.5", 1500), ("0.25", 250), ("2,5", 2500), (3, 3000),
])
def test_parse(text, expected):
    assert parse_qty(text) == expected


def test_format_trims_noise():
    assert format_qty(2000) == "2"
    assert format_qty(1500) == "1.5"
    assert format_qty(1500, "kg") == "1.5 kg"
    assert format_qty(0) == "0"


def test_multiply_prices_fractional_quantities():
    # 1.5 kg at 2.40 per kg = 3.60
    assert multiply(240, 1500) == 360
