"""Apply plain-SQL migrations from migrations/ in filename order.

Usage: uv run python -m app.migrate

Why a hand-rolled runner instead of Alembic: the project has no ORM, and the whole
mechanism fits in this file:
- each migrations/NNN_name.sql runs once, inside its own transaction, and is recorded in
  public.schema_migrations together with a SHA-256 checksum of its contents;
- re-running is a no-op;
- editing a migration that was already applied is an error. Write a new migration instead,
  so every database (dev, CI, VPS) ends up with exactly the same schema.

Migration files must not contain BEGIN/COMMIT: the runner owns the transaction.
"""

import hashlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import psycopg
from psycopg import sql

from app.config import get_settings
from app.db import connect

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
FILENAME_RE = re.compile(r"^(\d{3})_[a-z0-9_]+\.sql$")
# Any fixed number works: it only has to be the same for every runner. Holding this
# advisory lock means two runners started at once apply migrations one after another.
ADVISORY_LOCK_KEY = 20_261_026


class MigrationError(Exception):
    """The migrations on disk and the migrations recorded in the database disagree."""


@dataclass(frozen=True)
class Migration:
    version: str  # "001"
    name: str  # "001_extensions.sql"
    sql: str
    checksum: str


def discover_migrations(directory: Path = MIGRATIONS_DIR) -> list[Migration]:
    """Read all NNN_name.sql files, sorted by version."""
    migrations: list[Migration] = []
    seen: set[str] = set()
    for path in sorted(directory.glob("*.sql")):
        match = FILENAME_RE.match(path.name)
        if match is None:
            raise MigrationError(f"bad migration filename {path.name!r}, expected NNN_name.sql")
        version = match.group(1)
        if version in seen:
            raise MigrationError(f"duplicate migration version {version}")
        seen.add(version)
        # read_text() turns CRLF into LF, so the checksum is the same on a Windows
        # checkout (git autocrlf) and on Linux CI.
        sql = path.read_text(encoding="utf-8")
        checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
        migrations.append(Migration(version, path.name, sql, checksum))
    return migrations


def pending_migrations(migrations: list[Migration], applied: dict[str, str]) -> list[Migration]:
    """Return migrations not applied yet. `applied` maps version -> checksum.
    Raise MigrationError if the database and the files on disk have diverged."""
    on_disk = {m.version: m for m in migrations}
    for version, checksum in applied.items():
        if version not in on_disk:
            raise MigrationError(f"migration {version} is applied but missing on disk")
        if on_disk[version].checksum != checksum:
            raise MigrationError(
                f"{on_disk[version].name} was edited after it was applied; "
                "add a new migration instead"
            )
    return [m for m in migrations if m.version not in applied]


def ensure_migrations_table(conn: psycopg.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS public.schema_migrations (
            version    text PRIMARY KEY,
            name       text NOT NULL,
            checksum   text NOT NULL,
            applied_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )


def applied_checksums(conn: psycopg.Connection) -> dict[str, str]:
    rows = conn.execute("SELECT version, checksum FROM public.schema_migrations").fetchall()
    return {version: checksum for version, checksum in rows}


def apply_migration(conn: psycopg.Connection, migration: Migration) -> None:
    """Run one migration and record it, atomically: either both happen or neither."""
    with conn.transaction():
        # No parameters -> psycopg uses the simple query protocol, which allows a file
        # with many statements separated by semicolons.
        conn.execute(migration.sql)
        conn.execute(
            "INSERT INTO public.schema_migrations (version, name, checksum) VALUES (%s, %s, %s)",
            (migration.version, migration.name, migration.checksum),
        )


def migrate(conn: psycopg.Connection, directory: Path = MIGRATIONS_DIR) -> list[Migration]:
    """Apply all pending migrations and return them. `conn` must be in autocommit mode,
    so that each conn.transaction() above is a real, separate transaction."""
    migrations = discover_migrations(directory)
    conn.execute("SELECT pg_advisory_lock(%s)", (ADVISORY_LOCK_KEY,))
    try:
        ensure_migrations_table(conn)
        pending = pending_migrations(migrations, applied_checksums(conn))
        for migration in pending:
            apply_migration(conn, migration)
        return pending
    finally:
        conn.execute("SELECT pg_advisory_unlock(%s)", (ADVISORY_LOCK_KEY,))


def set_readonly_password(conn: psycopg.Connection, role: str, password: str) -> None:
    """Enable login for the read-only role (created NOLOGIN by 005_readonly_role.sql).

    The password lives only in .env, never in a migration file (the repository is public).
    ALTER ROLE does not accept bind parameters, so the value is sent as an escaped literal
    (sql.Literal); Postgres stores it as a SCRAM hash, not in plain text."""
    conn.execute(
        sql.SQL("ALTER ROLE {} LOGIN PASSWORD {}").format(
            sql.Identifier(role), sql.Literal(password)
        )
    )


def main() -> int:
    settings = get_settings()
    try:
        with connect(autocommit=True) as conn:
            applied = migrate(conn)
            if settings.readonly_db_password is not None:
                password = settings.readonly_db_password.get_secret_value()
                set_readonly_password(conn, settings.readonly_db_user, password)
    except MigrationError as exc:
        print(f"migration error: {exc}", file=sys.stderr)
        return 1
    for migration in applied:
        print(f"applied {migration.name}")
    if not applied:
        print("database is up to date")
    if settings.readonly_db_password is None:
        print("READONLY_DB_PASSWORD is not set: the read-only SQL tool stays disabled")
    else:
        print(f"login enabled for read-only role {settings.readonly_db_user}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
