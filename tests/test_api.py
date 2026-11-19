def create(client, payload):
    resp = client.post("/invoices", json=payload)
    assert resp.status_code == 201
    return resp.get_json()


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_create_computes_totals(client, payload):
    body = create(client, payload)
    assert body["number"] == "INV-000001"
    assert body["subtotal_cents"] == 152500
    assert body["tax_cents"] == 12581  # 8.25% of 1525.00, rounded half up
    assert body["total_cents"] == 165081
    assert body["status"] == "draft"


def test_create_sets_location_header(client, payload):
    resp = client.post("/invoices", json=payload)
    assert resp.headers["Location"] == "/invoices/1"


def test_create_validation_error(client, payload):
    payload["customer_email"] = "bad"
    resp = client.post("/invoices", json=payload)
    assert resp.status_code == 422
    assert "customer_email" in resp.get_json()["fields"]


def test_create_rejects_non_json(client):
    resp = client.post("/invoices", data="not json", content_type="text/plain")
    assert resp.status_code == 422


def test_get_and_404(client, payload):
    create(client, payload)
    assert client.get("/invoices/1").status_code == 200
    assert client.get("/invoices/99").status_code == 404


def test_list_pagination(client, payload):
    for _ in range(3):
        create(client, payload)
    page = client.get("/invoices?limit=2&offset=1").get_json()
    assert [i["id"] for i in page] == [2, 1]


def test_list_rejects_bad_limit(client):
    assert client.get("/invoices?limit=0").status_code == 422


def test_status_lifecycle(client, payload):
    create(client, payload)
    assert client.post("/invoices/1/status", json={"status": "sent"}).status_code == 200
    resp = client.post("/invoices/1/status", json={"status": "paid"})
    assert resp.get_json()["status"] == "paid"


def test_status_invalid_transition(client, payload):
    create(client, payload)
    resp = client.post("/invoices/1/status", json={"status": "paid"})
    assert resp.status_code == 409


def test_status_requires_value(client, payload):
    create(client, payload)
    assert client.post("/invoices/1/status", json={}).status_code == 422


def test_delete_draft_removes_invoice_and_items(client, app, payload):
    create(client, payload)
    assert client.delete("/invoices/1").status_code == 204
    assert client.get("/invoices/1").status_code == 404
    from invoicing import db

    conn = db.connect(app.config["DATABASE"])
    try:
        assert conn.execute("SELECT COUNT(*) FROM line_items").fetchone()[0] == 0
    finally:
        conn.close()


def test_delete_sent_invoice_is_conflict(client, payload):
    create(client, payload)
    client.post("/invoices/1/status", json={"status": "sent"})
    assert client.delete("/invoices/1").status_code == 409
    assert client.get("/invoices/1").status_code == 200


def test_delete_missing_invoice_is_404(client):
    assert client.delete("/invoices/42").status_code == 404
