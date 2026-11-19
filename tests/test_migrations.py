import pytest

from invoicing import db


def test_migrate_applies_all_in_order(conn):
    applied = db.migrate(conn)
    assert applied == [p.stem for p in db.migration_files()]
    assert db.applied_versions(conn) == applied


def test_migrate_is_idempotent(conn):
    db.migrate(conn)
    assert db.migrate(conn) == []


def test_rollback_refuses_migration_without_down_script(conn):
    db.migrate(conn)
    last = db.applied_versions(conn)[-1]
    with pytest.raises(db.MigrationError, match="no down script"):
        db.rollback(conn)
    assert last in db.applied_versions(conn)


def test_billing_email_column_replaces_customer_email(conn):
    db.migrate(conn)
    columns = {r["name"] for r in conn.execute("PRAGMA table_info(invoices)")}
    assert "billing_email" in columns
    assert "customer_email" not in columns


def test_rollback_without_migrations_fails(conn):
    with pytest.raises(db.MigrationError):
        db.rollback(conn)


def test_schema_enforces_status_check(conn):
    db.migrate(conn)
    with pytest.raises(Exception, match="CHECK"):
        conn.execute(
            "INSERT INTO invoices (number, customer_name, billing_email, status, due_date) "
            "VALUES ('X', 'a', 'a@b.c', 'bogus', '2026-01-01')"
        )


def test_existing_invoices_survive_billing_email_migration(conn):
    for path in db.migration_files()[:2]:
        conn.executescript(path.read_text())
    db._ensure_table(conn)
    conn.executemany(
        "INSERT INTO schema_migrations (version) VALUES (?)",
        [(p.stem,) for p in db.migration_files()[:2]],
    )
    conn.execute(
        "INSERT INTO invoices (number, customer_name, customer_email, due_date) "
        "VALUES ('INV-000001', 'Acme', 'a@acme.example', '2026-01-31')"
    )
    conn.commit()

    assert db.migrate(conn) == [db.migration_files()[2].stem]
    row = conn.execute("SELECT number, billing_email FROM invoices").fetchone()
    assert (row["number"], row["billing_email"]) == ("INV-000001", "a@acme.example")
