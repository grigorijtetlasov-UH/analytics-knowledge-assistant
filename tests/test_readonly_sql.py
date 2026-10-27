"""Attempts to misuse run_readonly_sql, run as the real olist_reader role.

The tests log in with READONLY_DB_PASSWORD (as the MCP server will), not via SET ROLE from
the admin connection: with SET ROLE the session user stays a superuser, and a query like
set_config('role', ...) could switch back, which the real role cannot do.
"""

from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal

import psycopg
import pytest

from app.config import Settings
from app.db import connect_readonly
from app.migrate import migrate, set_readonly_password
from app.readonly_sql import (
    MAX_CELL_CHARS,
    MAX_QUERY_CHARS,
    SqlError,
    SqlResult,
    check_query,
    run_readonly_sql,
    to_json_value,
)

MAX_ROWS = 100
TIMEOUT_MS = 1000


@pytest.fixture
def reader_conn(
    temp_db_settings: Settings, db_conn: psycopg.Connection
) -> Iterator[psycopg.Connection]:
    if temp_db_settings.readonly_db_password is None:
        pytest.skip("READONLY_DB_PASSWORD is not set")
    migrate(db_conn)
    # The role is cluster-wide: this sets the same password .env already holds.
    set_readonly_password(
        db_conn,
        temp_db_settings.readonly_db_user,
        temp_db_settings.readonly_db_password.get_secret_value(),
    )
    db_conn.execute(
        "INSERT INTO olist.product_category_translation VALUES ('beleza_saude', 'health_beauty')"
    )
    with connect_readonly(temp_db_settings) as conn:
        yield conn


def run(conn: psycopg.Connection, query: str, max_rows: int = MAX_ROWS) -> SqlResult:
    return run_readonly_sql(conn, query, max_rows=max_rows, timeout_ms=TIMEOUT_MS)


# --- allowed queries ---


@pytest.mark.db
def test_select_returns_columns_and_rows(reader_conn: psycopg.Connection) -> None:
    result = run(reader_conn, "SELECT * FROM olist.product_category_translation")
    assert result.columns == ["product_category_name", "product_category_name_english"]
    assert result.rows == [["beleza_saude", "health_beauty"]]
    assert (result.row_count, result.truncated) == (1, False)


@pytest.mark.db
def test_unqualified_names_resolve_to_olist(reader_conn: psycopg.Connection) -> None:
    assert run(reader_conn, "SELECT count(*) FROM product_category_translation").rows == [[1]]


@pytest.mark.db
def test_percent_signs_are_not_placeholders(reader_conn: psycopg.Connection) -> None:
    result = run(reader_conn, "SELECT 'health%' LIKE '%th%' AS matches")
    assert result.rows == [[True]]


@pytest.mark.db
@pytest.mark.parametrize(("n", "truncated"), [(MAX_ROWS, False), (MAX_ROWS + 50, True)])
def test_row_limit(reader_conn: psycopg.Connection, n: int, truncated: bool) -> None:
    result = run(reader_conn, f"SELECT g FROM generate_series(1, {n}) AS g")
    assert result.row_count == MAX_ROWS
    assert result.truncated is truncated
    assert result.rows[-1] == [MAX_ROWS]


# --- rejected by Postgres: not exactly one SELECT (server-side cursor) ---


@pytest.mark.db
@pytest.mark.parametrize(
    "query",
    [
        "SELECT 1; DROP TABLE olist.orders",
        "SELECT 1; SELECT 2",
        "DELETE FROM olist.product_category_translation",
        "UPDATE olist.product_category_translation SET product_category_name_english = 'x'",
        "INSERT INTO olist.product_category_translation VALUES ('a', 'b')",
        "TRUNCATE olist.product_category_translation",
        "DROP TABLE olist.product_category_translation",
        "CREATE TABLE olist.evil (id int)",
        "CREATE TEMP TABLE evil AS SELECT 1",
        "WITH d AS (DELETE FROM olist.product_category_translation RETURNING *) "
        "SELECT count(*) FROM d",
        "SELECT * INTO olist.copy FROM olist.product_category_translation",
        "EXPLAIN ANALYZE DELETE FROM olist.product_category_translation",
        "COPY olist.product_category_translation TO STDOUT",
        "SET statement_timeout = 0",
        "GRANT SELECT ON ALL TABLES IN SCHEMA rag TO olist_reader",
    ],
)
def test_non_select_is_rejected_and_data_is_intact(
    reader_conn: psycopg.Connection, db_conn: psycopg.Connection, query: str
) -> None:
    with pytest.raises(SqlError):
        run(reader_conn, query)
    [count] = db_conn.execute("SELECT count(*) FROM olist.product_category_translation").fetchone()
    assert count == 1


# --- rejected by privileges: a SELECT, but of something the role may not read ---


@pytest.mark.db
@pytest.mark.parametrize(
    ("query", "message"),
    [
        ("SELECT * FROM rag.chunks", "permission denied for schema rag"),
        ("SELECT * FROM public.schema_migrations", "permission denied for table"),
        ("SELECT pg_read_file('postgresql.conf')", "permission denied for function"),
        ("SELECT lo_import('/etc/passwd')", "permission denied for function"),
        # Stopped by the read-only transaction before the missing UPDATE privilege.
        (
            "SELECT * FROM olist.product_category_translation FOR UPDATE",
            "read-only transaction",
        ),
    ],
)
def test_forbidden_select_is_rejected(
    reader_conn: psycopg.Connection, query: str, message: str
) -> None:
    with pytest.raises(SqlError, match=message):
        run(reader_conn, query)


@pytest.mark.db
def test_cannot_switch_to_the_admin_role(
    reader_conn: psycopg.Connection, temp_db_settings: Settings
) -> None:
    admin = temp_db_settings.postgres_user  # a superuser in the Docker image
    with pytest.raises(SqlError, match="permission denied to set role"):
        run(reader_conn, f"SELECT set_config('role', '{admin}', false)")


# --- limits ---


@pytest.mark.db
@pytest.mark.parametrize(
    "query",
    [
        "SELECT pg_sleep(10)",
        # Lifting the timeout from inside the query must not work.
        "SELECT set_config('statement_timeout', '0', true), pg_sleep(10)",
        "SELECT pg_sleep(10) FROM (SELECT set_config('statement_timeout', '0', true)) AS s",
        # A CPU-heavy query, not only sleeping.
        "SELECT count(*) FROM generate_series(1, 1000000000)",
    ],
)
def test_slow_query_is_cancelled(reader_conn: psycopg.Connection, query: str) -> None:
    with pytest.raises(SqlError, match="time limit"):
        run(reader_conn, query)


@pytest.mark.db
def test_connection_is_usable_after_an_error(reader_conn: psycopg.Connection) -> None:
    with pytest.raises(SqlError):
        run(reader_conn, "SELECT * FROM rag.chunks")
    assert run(reader_conn, "SELECT 1 AS one").rows == [[1]]


@pytest.mark.db
def test_role_has_no_dangerous_attributes(db_conn: psycopg.Connection) -> None:
    migrate(db_conn)
    row = db_conn.execute(
        "SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls, rolconfig"
        " FROM pg_roles WHERE rolname = 'olist_reader'"
    ).fetchone()
    assert row[:5] == (False, False, False, False, False)
    assert "default_transaction_read_only=on" in row[5]
    assert "statement_timeout=5s" in row[5]


# --- unit tests: no database ---


@pytest.mark.parametrize("query", ["", "   \n", "x" * (MAX_QUERY_CHARS + 1)])
def test_check_query_rejects_empty_and_long(query: str) -> None:
    with pytest.raises(SqlError):
        check_query(query)


def test_to_json_value() -> None:
    assert to_json_value(Decimal("129.90")) == 129.9
    assert to_json_value(datetime(2018, 1, 2, 3, 4, 5)) == "2018-01-02T03:04:05"
    assert to_json_value(None) is None
    long_text = to_json_value("a" * (MAX_CELL_CHARS + 10))
    assert isinstance(long_text, str) and len(long_text) == MAX_CELL_CHARS + 1
