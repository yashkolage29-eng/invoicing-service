import pytest

from invoicing.money import format_cents, line_total_cents, tax_cents


def test_line_total():
    assert line_total_cents(3, 250) == 750


@pytest.mark.parametrize("qty,price", [(0, 100), (-1, 100), (1, -5)])
def test_line_total_rejects_bad_input(qty, price):
    with pytest.raises(ValueError):
        line_total_cents(qty, price)


def test_tax_rounds_half_up():
    assert tax_cents(1005, 1000) == 101  # 100.5 -> 101
    assert tax_cents(1004, 1000) == 100


def test_tax_zero_rate():
    assert tax_cents(99999, 0) == 0


def test_tax_rejects_negative_rate():
    with pytest.raises(ValueError):
        tax_cents(100, -1)


def test_format_cents():
    assert format_cents(1234567, "EUR") == "12,345.67 EUR"
    assert format_cents(-5) == "-0.05 USD"
