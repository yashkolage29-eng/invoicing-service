import pytest

from invoicing import create_app, db


@pytest.fixture
def app(tmp_path):
    return create_app({"DATABASE": str(tmp_path / "test.sqlite3"), "TESTING": True})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def conn(tmp_path):
    connection = db.connect(str(tmp_path / "raw.sqlite3"))
    yield connection
    connection.close()


@pytest.fixture
def payload():
    return {
        "customer_name": "Acme Ltd",
        "customer_email": "Billing@Acme.example",
        "currency": "USD",
        "tax_rate_bps": 825,
        "due_date": "2026-01-31",
        "notes": "Net 30",
        "line_items": [
            {"description": "Consulting", "quantity": 10, "unit_price_cents": 15000},
            {"description": "Hosting", "quantity": 1, "unit_price_cents": 2500},
        ],
    }
