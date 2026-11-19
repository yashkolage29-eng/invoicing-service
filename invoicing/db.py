"""SQLite access and the plain-SQL migration runner."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from flask import current_app, g

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
_NAME_RE = re.compile(r"^(\d{4})_[a-z0-9_]+\.sql$")


class MigrationError(RuntimeError):
    """Raised when a migration cannot be applied or rolled back."""


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE"])
    return g.db


def close_db(_exc: BaseException | None = None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def migration_files() -> list[Path]:
    files = [p for p in MIGRATIONS_DIR.glob("*.sql") if _NAME_RE.match(p.name)]
    return sorted(files, key=lambda p: p.name)


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        "version TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.commit()


def applied_versions(conn: sqlite3.Connection) -> list[str]:
    _ensure_table(conn)
    rows = conn.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall()
    return [r["version"] for r in rows]


def migrate(conn: sqlite3.Connection) -> list[str]:
    """Apply every pending migration in order and return the versions applied."""
    done = set(applied_versions(conn))
    applied: list[str] = []
    for path in migration_files():
        version = path.stem
        if version in done:
            continue
        record = f"INSERT INTO schema_migrations (version) VALUES ('{version}');"
        script = f"BEGIN;\n{path.read_text()}\n{record}\nCOMMIT;"
        try:
            conn.executescript(script)
        except sqlite3.Error as exc:
            conn.rollback()
            raise MigrationError(f"migration {version} failed: {exc}") from exc
        applied.append(version)
    return applied


def rollback(conn: sqlite3.Connection) -> str:
    """Undo the most recently applied migration using its .down.sql file."""
    versions = applied_versions(conn)
    if not versions:
        raise MigrationError("no migrations to roll back")
    version = versions[-1]
    down = MIGRATIONS_DIR / f"{version}.down.sql"
    if not down.exists():
        raise MigrationError(f"migration {version} has no down script")
    try:
        forget = f"DELETE FROM schema_migrations WHERE version = '{version}';"
        conn.executescript(f"BEGIN;\n{down.read_text()}\n{forget}\nCOMMIT;")
    except sqlite3.Error as exc:
        conn.rollback()
        raise MigrationError(f"rollback of {version} failed: {exc}") from exc
    return version
