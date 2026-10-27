"""Run one model-written SELECT against the Olist data, safely (MCP tool run_readonly_sql).

Safety does not depend on parsing SQL in Python. Four layers, each enforced by Postgres:
1. the connection logs in as `olist_reader` (migrations/005_readonly_role.sql): SELECT on
   olist.* only, nothing else;
2. the transaction is READ ONLY and is always rolled back;
3. the query runs inside a server-side cursor (DECLARE ... CURSOR FOR <query>). Postgres
   itself then rejects anything that is not exactly one SELECT/VALUES: several statements,
   UPDATE/DELETE/DDL, EXPLAIN ANALYZE, SELECT ... INTO, data-modifying CTEs;
4. statement_timeout cuts the query off, and at most max_rows + 1 rows are fetched, so a
   huge result never reaches Python.
The checks in Python (empty, too long) only give quicker, clearer errors.

A third-party SQL parser was considered and rejected: the exact one (pglast) is GPL, and
an approximate one could disagree with Postgres about what a query does.
"""

import time
from dataclasses import dataclass
from datetime import date, datetime
from datetime import time as dtime
from decimal import Decimal
from typing import Any

import psycopg
from psycopg import errors

# Far longer than any analytics query; stops a pasted dump before it reaches the server.
MAX_QUERY_CHARS = 10_000
# Long text cells (review comments) are cut so one row cannot flood the model's context.
MAX_CELL_CHARS = 500
CURSOR_NAME = "readonly_sql"

JsonValue = str | int | float | bool | None


class SqlError(Exception):
    """The query was rejected or failed. The message is meant for the model: it says what
    went wrong (often Postgres' own error) so the model can fix the query."""


@dataclass(frozen=True)
class SqlResult:
    columns: list[str]
    rows: list[list[JsonValue]]
    row_count: int  # rows returned (after the limit)
    truncated: bool  # True if the query had more rows than the limit
    elapsed_ms: int


def to_json_value(value: Any) -> JsonValue:
    """Make a Postgres value JSON-friendly for the model."""
    if value is None or isinstance(value, bool | int | float):
        return value
    if isinstance(value, Decimal):
        # Money is numeric(10, 2): float is exact enough to read, and the model treats it
        # as a number rather than a string.
        return float(value)
    if isinstance(value, datetime | date | dtime):
        return value.isoformat()
    text = str(value)
    return text if len(text) <= MAX_CELL_CHARS else text[:MAX_CELL_CHARS] + "…"


def check_query(query: str) -> str:
    """Cheap checks before the database sees the query. Not a security boundary."""
    query = query.strip()
    if not query:
        raise SqlError("empty query")
    if len(query) > MAX_QUERY_CHARS:
        raise SqlError(f"query is longer than {MAX_QUERY_CHARS} characters")
    return query


def run_readonly_sql(
    conn: psycopg.Connection, query: str, *, max_rows: int, timeout_ms: int
) -> SqlResult:
    """Execute `query` and return at most `max_rows` rows.

    `conn` must be in autocommit mode (connect_readonly() opens it so), so that the
    transaction below is a real one and not a savepoint inside someone else's."""
    query = check_query(query)
    start = time.perf_counter()
    try:
        # force_rollback: even a read-only transaction is never committed.
        with conn.transaction(force_rollback=True):
            # Must be the first statement of the transaction. The role defaults to read-only
            # already; setting it here keeps the guarantee even with another role.
            conn.execute("SET TRANSACTION READ ONLY")
            # set_config(..., true) = SET LOCAL, but accepts a bind parameter. Checked:
            # a set_config() call inside the model's query cannot lift this timeout for the
            # statement already running, and only one FETCH is issued below.
            conn.execute("SELECT set_config('statement_timeout', %s, true)", (f"{timeout_ms}ms",))
            conn.execute("SELECT set_config('lock_timeout', '1s', true)")
            # A named cursor is a server-side cursor: psycopg sends DECLARE ... CURSOR FOR
            # <query> using the extended protocol, which also forbids several statements.
            with conn.cursor(name=CURSOR_NAME) as cur:
                cur.execute(query)
                rows = cur.fetchmany(max_rows + 1)  # one FETCH; +1 detects truncation
                columns = [column.name for column in cur.description or []]
    except errors.QueryCanceled as exc:
        raise SqlError(f"query cancelled after the {timeout_ms} ms time limit") from exc
    except errors.InsufficientPrivilege as exc:
        raise SqlError(
            f"{exc.diag.message_primary}. Only the tables of schema olist can be read."
        ) from exc
    except psycopg.Error as exc:
        raise SqlError(exc.diag.message_primary or str(exc)) from exc

    truncated = len(rows) > max_rows
    rows = rows[:max_rows]
    return SqlResult(
        columns=columns,
        rows=[[to_json_value(value) for value in row] for row in rows],
        row_count=len(rows),
        truncated=truncated,
        elapsed_ms=round((time.perf_counter() - start) * 1000),
    )
