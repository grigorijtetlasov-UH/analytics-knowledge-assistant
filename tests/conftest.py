import uuid
from collections.abc import Iterator

import psycopg
import pytest
from psycopg import sql
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.db import connect


@pytest.fixture
def temp_db_settings() -> Iterator[Settings]:
    """Settings pointing at a fresh, empty database that is dropped after the test.

    Tests never touch the dev database; each one gets its own. Skips the test when
    Postgres is not configured or not running, so unit tests still run anywhere.
    """
    try:
        base = get_settings()
        admin = connect(base, autocommit=True)
    except (ValidationError, psycopg.OperationalError) as exc:
        pytest.skip(f"Postgres is not available: {exc}")

    name = f"test_{uuid.uuid4().hex[:12]}"
    with admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        try:
            yield base.model_copy(update={"postgres_db": name})
        finally:
            # FORCE closes connections a failed test may have left open.
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))


@pytest.fixture
def db_conn(temp_db_settings: Settings) -> Iterator[psycopg.Connection]:
    with connect(temp_db_settings, autocommit=True) as conn:
        yield conn
