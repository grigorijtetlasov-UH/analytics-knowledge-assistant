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
