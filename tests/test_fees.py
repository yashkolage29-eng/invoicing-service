from datetime import date

import pytest

from invoicing import db, repository
from invoicing.fees import late_fee_cents

DUE = date(2026, 3, 1)


def test_no_fee_before_due_date():
    assert late_fee_cents(100_000, DUE, date(2026, 2, 20)) == 0


def test_no_fee_on_last_day_of_grace_period():
    assert late_fee_cents(100_000, DUE, date(2026, 3, 6)) == 0


def test_fee_after_grace_period_is_one_period():
    assert late_fee_cents(100_000, DUE, date(2026, 3, 7)) == 1500


def test_fee_grows_per_started_period():
    assert late_fee_cents(100_000, DUE, date(2026, 4, 5)) == 3000


def test_negative_total_rejected():
    with pytest.raises(ValueError):
        late_fee_cents(-1, DUE, DUE)


def test_invoice_reports_late_fee_only_when_sent(conn, payload):
    db.migrate(conn)
    payload = {**payload, "customer_email": "a@b.example", "notes": None}
    invoice_id = repository.create_invoice(conn, payload)
    draft = repository.get_invoice(conn, invoice_id, today=date(2027, 1, 1))
    assert draft["late_fee_cents"] == 0
    repository.set_status(conn, invoice_id, "sent")
    sent = repository.get_invoice(conn, invoice_id, today=date(2026, 1, 30))
    assert sent["late_fee_cents"] == 0
    overdue = repository.get_invoice(conn, invoice_id, today=date(2026, 2, 20))
    assert overdue["late_fee_cents"] == 2476  # 1.5% of 1650.81
