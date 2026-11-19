"""Persistence and business rules for invoices."""

from __future__ import annotations

import sqlite3
from typing import Any

from .money import line_total_cents, tax_cents

TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"sent", "void"}),
    "sent": frozenset({"paid", "void"}),
    "paid": frozenset(),
    "void": frozenset(),
}


class NotFoundError(LookupError):
    pass


class InvalidTransitionError(ValueError):
    pass


def _next_number(conn: sqlite3.Connection) -> str:
    row = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 AS n FROM invoices").fetchone()
    return f"INV-{row['n']:06d}"


def create_invoice(conn: sqlite3.Connection, payload: dict[str, Any]) -> int:
    with conn:
        cur = conn.execute(
            "INSERT INTO invoices (number, customer_name, billing_email, currency, "
            "tax_rate_bps, due_date, internal_memo) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                _next_number(conn),
                payload["customer_name"],
                payload["customer_email"],
                payload["currency"],
                payload["tax_rate_bps"],
                payload["due_date"],
                payload["notes"],
            ),
        )
        invoice_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO line_items (invoice_id, description, quantity, unit_price_cents) "
            "VALUES (?, ?, ?, ?)",
            [
                (invoice_id, i["description"], i["quantity"], i["unit_price_cents"])
                for i in payload["line_items"]
            ],
        )
    return invoice_id


def _totals(items: list[dict[str, Any]], rate_bps: int) -> dict[str, int]:
    subtotal = sum(line_total_cents(i["quantity"], i["unit_price_cents"]) for i in items)
    tax = tax_cents(subtotal, rate_bps)
    return {"subtotal_cents": subtotal, "tax_cents": tax, "total_cents": subtotal + tax}


def _hydrate(conn: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
    items = [
        dict(r)
        for r in conn.execute(
            "SELECT id, description, quantity, unit_price_cents FROM line_items "
            "WHERE invoice_id = ? ORDER BY id",
            (row["id"],),
        )
    ]
    invoice = dict(row)
    invoice["customer_email"] = invoice.pop("billing_email")
    invoice["notes"] = invoice.pop("internal_memo")
    invoice["line_items"] = items
    invoice.update(_totals(items, row["tax_rate_bps"]))
    return invoice


def get_invoice(conn: sqlite3.Connection, invoice_id: int) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
    if row is None:
        raise NotFoundError(invoice_id)
    return _hydrate(conn, row)


def list_invoices(
    conn: sqlite3.Connection, limit: int = 20, offset: int = 0
) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM invoices ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset)
    ).fetchall()
    return [_hydrate(conn, r) for r in rows]


def set_status(conn: sqlite3.Connection, invoice_id: int, new_status: str) -> dict[str, Any]:
    current = get_invoice(conn, invoice_id)["status"]
    if new_status not in TRANSITIONS.get(current, frozenset()):
        raise InvalidTransitionError(f"cannot move invoice from {current} to {new_status}")
    with conn:
        conn.execute("UPDATE invoices SET status = ? WHERE id = ?", (new_status, invoice_id))
    return get_invoice(conn, invoice_id)
