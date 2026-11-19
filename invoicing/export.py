"""CSV export for invoices."""

from __future__ import annotations

import csv
import io
from typing import Any

from .money import format_cents

HEADER = ["number", "customer", "email", "status", "due_date", "total"]


def _format_row(invoice: dict[str, Any]) -> list[str]:
    return [
        invoice["number"],
        invoice["customer_name"],
        invoice["customer_email"],
        invoice["status"],
        invoice["due_date"],
        format_cents(invoice["total_cents"], invoice["currency"]),
    ]


def invoices_to_csv(invoices: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(HEADER)
    for invoice in invoices:
        writer.writerow(_format_row(invoice))
    return buf.getvalue()
