from pathlib import Path

import psycopg
import pytest

from app.migrate import (
    MigrationError,
    discover_migrations,
    migrate,
    pending_migrations,
)

OLIST_TABLES = {
    "customers",
    "geolocation",
    "order_items",
    "order_payments",
    "order_reviews",
    "orders",
    "product_category_translation",
    "products",
    "sellers",
}


def write(directory: Path, name: str, sql: str) -> None:
    (directory / name).write_text(sql, encoding="utf-8")


# --- unit tests: no database needed ---


def test_discover_sorts_by_version(tmp_path: Path) -> None:
    write(tmp_path, "002_second.sql", "SELECT 2;")
    write(tmp_path, "001_first.sql", "SELECT 1;")
    assert [m.version for m in discover_migrations(tmp_path)] == ["001", "002"]


def test_discover_rejects_bad_filename(tmp_path: Path) -> None:
    write(tmp_path, "1_first.sql", "SELECT 1;")
    with pytest.raises(MigrationError, match="bad migration filename"):
        discover_migrations(tmp_path)


def test_discover_rejects_duplicate_version(tmp_path: Path) -> None:
    write(tmp_path, "001_a.sql", "SELECT 1;")
    write(tmp_path, "001_b.sql", "SELECT 1;")
    with pytest.raises(MigrationError, match="duplicate"):
        discover_migrations(tmp_path)


def test_checksum_ignores_crlf_line_endings(tmp_path: Path) -> None:
    (tmp_path / "001_lf.sql").write_bytes(b"SELECT 1;\n")
    (tmp_path / "002_crlf.sql").write_bytes(b"SELECT 1;\r\n")
    lf, crlf = discover_migrations(tmp_path)
    assert lf.checksum == crlf.checksum


def test_pending_skips_applied(tmp_path: Path) -> None:
    write(tmp_path, "001_a.sql", "SELECT 1;")
    write(tmp_path, "002_b.sql", "SELECT 2;")
    first, second = discover_migrations(tmp_path)
    assert pending_migrations([first, second], {"001": first.checksum}) == [second]


def test_pending_rejects_edited_migration(tmp_path: Path) -> None:
    write(tmp_path, "001_a.sql", "SELECT 1;")
    migrations = discover_migrations(tmp_path)
    with pytest.raises(MigrationError, match="edited after it was applied"):
        pending_migrations(migrations, {"001": "checksum-of-old-content"})


def test_pending_rejects_applied_migration_missing_on_disk(tmp_path: Path) -> None:
    write(tmp_path, "001_a.sql", "SELECT 1;")
    migrations = discover_migrations(tmp_path)
    with pytest.raises(MigrationError, match="missing on disk"):
        pending_migrations(migrations, {"001": migrations[0].checksum, "002": "x"})


def test_project_migrations_are_well_formed() -> None:
    assert [m.name for m in discover_migrations()][:2] == [
        "001_extensions.sql",
        "002_olist_schema.sql",
    ]


# --- integration tests: run against a throwaway database ---


@pytest.mark.db
def test_migrate_creates_schema_and_is_idempotent(db_conn: psycopg.Connection) -> None:
    applied = migrate(db_conn)
    assert [m.version for m in applied] == [m.version for m in discover_migrations()]

    tables = db_conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'olist'"
    ).fetchall()
    assert {name for (name,) in tables} == OLIST_TABLES
    assert db_conn.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'").fetchone()

    assert migrate(db_conn) == []


@pytest.mark.db
def test_failed_migration_is_rolled_back(db_conn: psycopg.Connection, tmp_path: Path) -> None:
    write(tmp_path, "001_ok.sql", "CREATE TABLE t_ok (id int);")
    write(tmp_path, "002_bad.sql", "CREATE TABLE t_bad (id int); SELECT 1 / 0;")

    with pytest.raises(psycopg.errors.DivisionByZero):
        migrate(db_conn, tmp_path)

    # 001 stays applied; 002 left nothing behind: neither its table nor a record.
    assert db_conn.execute("SELECT to_regclass('t_ok')").fetchone() == ("t_ok",)
    assert db_conn.execute("SELECT to_regclass('t_bad')").fetchone() == (None,)
    versions = db_conn.execute("SELECT version FROM schema_migrations").fetchall()
    assert versions == [("001",)]
