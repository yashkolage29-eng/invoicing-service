import pytest

from invoicing import db


def test_migrate_applies_all_in_order(conn):
    applied = db.migrate(conn)
    assert applied == [p.stem for p in db.migration_files()]
    assert db.applied_versions(conn) == applied


def test_migrate_is_idempotent(conn):
    db.migrate(conn)
    assert db.migrate(conn) == []


def test_rollback_last_migration(conn):
    db.migrate(conn)
    last = db.applied_versions(conn)[-1]
    assert db.rollback(conn) == last
    assert last not in db.applied_versions(conn)


def test_rollback_without_migrations_fails(conn):
    with pytest.raises(db.MigrationError):
        db.rollback(conn)


def test_schema_enforces_status_check(conn):
    db.migrate(conn)
    with pytest.raises(Exception, match="CHECK"):
        conn.execute(
            "INSERT INTO invoices (number, customer_name, customer_email, status, due_date) "
            "VALUES ('X', 'a', 'a@b.c', 'bogus', '2026-01-01')"
        )
