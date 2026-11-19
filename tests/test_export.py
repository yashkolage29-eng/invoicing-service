from invoicing.export import HEADER, invoices_to_csv


def make_invoice(**over):
    base = {
        "number": "INV-000001",
        "customer_name": "Acme Ltd",
        "customer_email": "billing@acme.example",
        "status": "draft",
        "due_date": "2026-01-31",
        "total_cents": 165081,
        "currency": "USD",
    }
    return {**base, **over}


def test_csv_has_header_and_row():
    lines = invoices_to_csv([make_invoice()]).splitlines()
    assert lines[0] == ",".join(HEADER)
    assert lines[1].endswith('"1,650.81 USD"')


def test_csv_quotes_commas_in_names():
    out = invoices_to_csv([make_invoice(customer_name="Acme, Inc.")])
    assert '"Acme, Inc."' in out
