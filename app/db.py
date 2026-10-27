"""Database connection helper."""

import psycopg

from app.config import Settings, get_settings

# Fail after a few seconds instead of hanging forever when the database is down.
CONNECT_TIMEOUT_S = 5


def connect(settings: Settings | None = None, *, autocommit: bool = False) -> psycopg.Connection:
    """Open a new connection. `settings` defaults to the values from .env;
    tests pass their own to point at a throwaway database."""
    settings = settings or get_settings()
    return psycopg.connect(
        settings.database_url, autocommit=autocommit, connect_timeout=CONNECT_TIMEOUT_S
    )


def connect_readonly(settings: Settings | None = None) -> psycopg.Connection:
    """Connection as the read-only role (migrations/005_readonly_role.sql), for the SQL tool.
    Autocommit, so that run_readonly_sql opens a real transaction with conn.transaction()."""
    settings = settings or get_settings()
    return psycopg.connect(
        settings.readonly_database_url, autocommit=True, connect_timeout=CONNECT_TIMEOUT_S
    )
