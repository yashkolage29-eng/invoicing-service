import pytest

from invoicing.validation import ValidationError, parse_invoice


def test_parse_normalises_fields(payload):
    parsed = parse_invoice(payload)
    assert parsed["customer_email"] == "billing@acme.example"
    assert len(parsed["line_items"]) == 2


def test_rejects_non_object():
    with pytest.raises(ValidationError) as exc:
        parse_invoice([1, 2])
    assert "body" in exc.value.errors


def test_collects_all_errors(payload):
    payload["customer_name"] = " "
    payload["customer_email"] = "nope"
    payload["due_date"] = "31/01/2026"
    payload["line_items"][0]["quantity"] = 0
    with pytest.raises(ValidationError) as exc:
        parse_invoice(payload)
    assert set(exc.value.errors) >= {
        "customer_name",
        "customer_email",
        "due_date",
        "line_items[0].quantity",
    }


def test_rejects_unknown_currency_and_bool_quantity(payload):
    payload["currency"] = "XXX"
    payload["line_items"][1]["quantity"] = True
    with pytest.raises(ValidationError) as exc:
        parse_invoice(payload)
    assert "currency" in exc.value.errors
    assert "line_items[1].quantity" in exc.value.errors


def test_rejects_empty_line_items(payload):
    payload["line_items"] = []
    with pytest.raises(ValidationError):
        parse_invoice(payload)
