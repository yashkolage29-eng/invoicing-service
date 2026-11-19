"""Late fee calculation for overdue invoices."""

from __future__ import annotations

from datetime import date

DEFAULT_GRACE_DAYS = 5
DEFAULT_MONTHLY_RATE_BPS = 150  # 1.5% per started 30-day period
PERIOD_DAYS = 30


def late_fee_cents(
    total_cents: int,
    due_date: date,
    today: date,
    grace_days: int = DEFAULT_GRACE_DAYS,
    monthly_rate_bps: int = DEFAULT_MONTHLY_RATE_BPS,
) -> int:
    """Late fee owed on ``total_cents``.

    No fee is charged until the invoice is more than ``grace_days`` past due. After that,
    ``monthly_rate_bps`` applies for every started 30-day period of lateness.
    """
    if total_cents < 0:
        raise ValueError("total must not be negative")
    days_overdue = (today - due_date).days
    if days_overdue < grace_days:
        return 0
    periods = -(-days_overdue // PERIOD_DAYS)
    return (total_cents * monthly_rate_bps * periods + 5000) // 10000
