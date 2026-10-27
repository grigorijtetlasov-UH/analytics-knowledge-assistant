-- Read-only role for the MCP tool run_readonly_sql (Milestone 5).
--
-- This role is the main safety layer of that tool: whatever SQL the model sends, it runs
-- with these privileges only. Defence in depth (all enforced by Postgres, not by our code):
-- * SELECT on the `olist` tables and nothing else: no rag.*, no schema_migrations, no
--   INSERT/UPDATE/DELETE/TRUNCATE, no CREATE in any schema (Postgres 15+ no longer lets
--   PUBLIC create objects in `public`);
-- * every transaction is read-only by default, every statement is cut off after 5 s;
-- * not a superuser and cannot create databases or roles, so no server-file functions
--   (pg_read_file needs superuser or pg_read_server_files) and no privilege escalation.
--
-- No password here: the repository is public. The role is created NOLOGIN; app/migrate.py
-- enables login with READONLY_DB_PASSWORD from .env.
--
-- Roles are cluster-wide (shared by all databases on the server), unlike schemas. Every
-- test database runs this migration too, so the role is created only if it is missing.

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'olist_reader') THEN
        CREATE ROLE olist_reader NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION
            NOBYPASSRLS CONNECTION LIMIT 5;
    END IF;
END
$$;

-- Session defaults applied at login. The tool also sets them per transaction (SET LOCAL),
-- so they hold even if a default is changed here later.
ALTER ROLE olist_reader SET default_transaction_read_only = on;
ALTER ROLE olist_reader SET statement_timeout = '5s';
ALTER ROLE olist_reader SET idle_in_transaction_session_timeout = '10s';
-- Unqualified table names ("orders") resolve to olist.orders.
ALTER ROLE olist_reader SET search_path = olist;

-- CONNECT is granted to PUBLIC by default; granting it explicitly documents the intent.
-- format(%I): the database name is not known in advance (test databases have random names).
DO $$
BEGIN
    EXECUTE format('GRANT CONNECT ON DATABASE %I TO olist_reader', current_database());
END
$$;

GRANT USAGE ON SCHEMA olist TO olist_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA olist TO olist_reader;
-- Tables added to `olist` by later migrations become readable without another GRANT.
ALTER DEFAULT PRIVILEGES IN SCHEMA olist GRANT SELECT ON TABLES TO olist_reader;
