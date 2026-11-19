"""Request payload validation for the invoice API."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from .money import SUPPORTED_CURRENCIES

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_LINE_ITEMS = 200


class ValidationError(ValueError):
    def __init__(self, errors: dict[str, str]):
        super().__init__("invalid payload")
        self.errors = errors


def _int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def parse_invoice(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValidationError({"body": "expected a JSON object"})

    errors: dict[str, str] = {}
    name = data.get("customer_name")
    if not isinstance(name, str) or not name.strip():
        errors["customer_name"] = "required"

    email = data.get("customer_email")
    if not isinstance(email, str) or not _EMAIL_RE.match(email):
        errors["customer_email"] = "must be a valid email address"

    currency = data.get("currency", "USD")
    if currency not in SUPPORTED_CURRENCIES:
        errors["currency"] = f"must be one of {sorted(SUPPORTED_CURRENCIES)}"

    tax = data.get("tax_rate_bps", 0)
    if _int(tax) is None or not 0 <= tax <= 10000:
        errors["tax_rate_bps"] = "must be an integer between 0 and 10000"

    due = data.get("due_date")
    try:
        due_parsed = date.fromisoformat(due) if isinstance(due, str) else None
    except ValueError:
        due_parsed = None
    if due_parsed is None:
        errors["due_date"] = "must be an ISO date (YYYY-MM-DD)"

    items = data.get("line_items")
    clean_items: list[dict[str, Any]] = []
    if not isinstance(items, list) or not items:
        errors["line_items"] = "at least one line item is required"
    elif len(items) > MAX_LINE_ITEMS:
        errors["line_items"] = f"at most {MAX_LINE_ITEMS} line items"
    else:
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                errors[f"line_items[{i}]"] = "expected an object"
                continue
            desc, qty, price = (
                item.get("description"),
                item.get("quantity"),
                item.get("unit_price_cents"),
            )
            if not isinstance(desc, str) or not desc.strip():
                errors[f"line_items[{i}].description"] = "required"
            if _int(qty) is None or qty <= 0:
                errors[f"line_items[{i}].quantity"] = "must be a positive integer"
            if _int(price) is None or price < 0:
                errors[f"line_items[{i}].unit_price_cents"] = "must be a non-negative integer"
            if not any(k.startswith(f"line_items[{i}]") for k in errors):
                clean_items.append(
                    {"description": desc.strip(), "quantity": qty, "unit_price_cents": price}
                )

    notes = data.get("notes")
    if notes is not None and not isinstance(notes, str):
        errors["notes"] = "must be a string"

    if errors:
        raise ValidationError(errors)

    return {
        "customer_name": name.strip(),
        "customer_email": email.strip().lower(),
        "currency": currency,
        "tax_rate_bps": tax,
        "due_date": due_parsed.isoformat(),
        "notes": notes,
        "line_items": clean_items,
    }
