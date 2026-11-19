"""Integer-cents money helpers. Floats are never used for amounts."""

from __future__ import annotations

SUPPORTED_CURRENCIES = frozenset({"USD", "EUR", "GBP", "INR"})


def line_total_cents(quantity: int, unit_price_cents: int) -> int:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    if unit_price_cents < 0:
        raise ValueError("unit price must not be negative")
    return quantity * unit_price_cents


def tax_cents(subtotal_cents: int, rate_bps: int) -> int:
    """Tax on a subtotal, rounded half up. ``rate_bps`` is basis points (1/100 of a percent)."""
    if rate_bps < 0:
        raise ValueError("tax rate must not be negative")
    return (subtotal_cents * rate_bps + 5000) // 10000


def format_cents(cents: int, currency: str = "USD") -> str:
    sign = "-" if cents < 0 else ""
    major, minor = divmod(abs(cents), 100)
    return f"{sign}{major:,}.{minor:02d} {currency}"
