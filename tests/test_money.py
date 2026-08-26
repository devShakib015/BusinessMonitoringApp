import pytest

from app.core.money import (extract_inclusive_tax, format_amount, format_plain,
                            parse_amount, percent_of, split_proportionally)


@pytest.mark.parametrize("text,expected", [
    ("10", 1000), ("10.5", 1050), ("10.55", 1055), ("1,250.50", 125050),
    ("1250,50", 125050), (" 12 ", 1200), (0.1, 10), ("0.005", 1),
])
def test_parse_amount(text, expected):
    assert parse_amount(text, 2) == expected


@pytest.mark.parametrize("bad", ["", None, "abc", "1.2.3"])
def test_parse_amount_rejects_junk(bad):
    with pytest.raises(ValueError):
        parse_amount(bad, 2)


def test_no_float_drift_over_many_lines():
    """0.1 + 0.2 style drift is what integer minor units exist to prevent."""
    assert sum(parse_amount("0.1", 2) for _ in range(10)) == parse_amount("1.00", 2)


def test_formatting():
    assert format_plain(125050, 2) == "1,250.50"
    assert format_amount(125050, "$", 2) == "$1,250.50"
    assert format_amount(-500, "$", 2) == "-$5.00"
    assert format_amount(1250, "", 0) == "1,250"


def test_percent_rounds_half_up():
    assert percent_of(1055, 10) == 106


def test_inclusive_tax_is_the_part_already_in_the_price():
    # A 115.00 shelf price at 15% contains 15.00 of tax.
    assert extract_inclusive_tax(11500, 0.15) == 1500


def test_split_adds_up_exactly():
    parts = split_proportionally(100, [333, 333, 334])
    assert sum(parts) == 100
    assert all(p > 0 for p in parts)


def test_split_handles_awkward_remainders():
    for total in range(0, 97):
        parts = split_proportionally(total, [7, 11, 13])
        assert sum(parts) == total
