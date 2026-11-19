# invoice-service

A small Flask API for creating invoices, tracking their status and reading totals.
Storage is SQLite, with plain SQL migrations applied at startup.

## Run

```sh
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
flask --app invoicing:create_app run
```

The database path comes from `INVOICE_DB` (default `invoices.sqlite3`).

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | Liveness check |
| POST | `/invoices` | Create an invoice with line items |
| GET | `/invoices` | List invoices (`limit`, `offset`) |
| GET | `/invoices/<id>` | Fetch one invoice with totals |
| POST | `/invoices/<id>/status` | Move an invoice through its lifecycle |

Lifecycle: `draft -> sent -> paid`; `draft` and `sent` may also be `void`.

## Migrations

SQL files live in `invoicing/migrations/` named `NNNN_description.sql`. Where a rollback is
possible there is a matching `NNNN_description.down.sql`.

## Tests

```sh
pytest
```

Coverage must stay at or above the threshold in `pyproject.toml`.
