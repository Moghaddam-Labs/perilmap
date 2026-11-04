"""Connect to Postgres and manage the test table."""

from __future__ import annotations

import os
from urllib.parse import urlsplit

import psycopg
from dotenv import load_dotenv
from psycopg import sql

from data_test.config import BNG_SRID

SCHEMA = "perilmap"
TABLE = "flood_zones"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


class SetupError(RuntimeError):
    """The database isn't ready for the test."""


def get_database_url() -> str:
    load_dotenv()
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise SetupError(
            "DATABASE_URL is not set. Copy .env.example to .env and add your connection string."
        )
    return url


def clean_error(message: str, url: str) -> str:
    """Remove the password from a driver message before it's shown or logged."""
    password = urlsplit(url).password
    return message.replace(password, "***") if password else message


def connect(url: str) -> psycopg.Connection:
    """Open a connection. Remote connections must be encrypted."""
    kwargs: dict[str, object] = {"prepare_threshold": None}
    if urlsplit(url).hostname not in LOCAL_HOSTS and "sslmode=" not in url:
        kwargs["sslmode"] = "require"
    try:
        conn = psycopg.connect(url, **kwargs)
    except psycopg.OperationalError as error:
        raise SetupError(
            "Couldn't connect to the database. Check the connection string in .env. "
            f"The driver reported: {clean_error(str(error), url)}"
        ) from None
    use_postgis_schema(conn)
    return conn


def use_postgis_schema(conn: psycopg.Connection) -> None:
    """Point the session at wherever PostGIS is installed (`extensions` on Supabase)."""
    row = conn.execute(
        "SELECT n.nspname FROM pg_extension e "
        "JOIN pg_namespace n ON n.oid = e.extnamespace WHERE e.extname = 'postgis'"
    ).fetchone()
    if row is None:
        raise SetupError("PostGIS isn't enabled on this database.")
    conn.execute(
        sql.SQL("SET search_path = {}, {}, public").format(
            sql.Identifier(SCHEMA), sql.Identifier(row[0])
        )
    )
    conn.commit()


def create_table(conn: psycopg.Connection) -> None:
    """Create the table in its own schema, away from Supabase's public Data API."""
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            source text NOT NULL,
            band text NOT NULL,
            geom geometry(Geometry, {BNG_SRID}) NOT NULL
        )
        """
    )
    conn.execute(f"ALTER TABLE {TABLE} ENABLE ROW LEVEL SECURITY")
    conn.commit()


def drop_index(conn: psycopg.Connection) -> None:
    conn.execute(f"DROP INDEX IF EXISTS {SCHEMA}.{TABLE}_geom_idx")
    conn.commit()


def build_index(conn: psycopg.Connection) -> None:
    conn.execute("SET statement_timeout = 0")
    conn.execute(f"CREATE INDEX IF NOT EXISTS {TABLE}_geom_idx ON {TABLE} USING gist (geom)")
    conn.commit()
    conn.autocommit = True
    try:
        conn.execute(f"VACUUM ANALYZE {TABLE}")
    finally:
        conn.autocommit = False


def reset(conn: psycopg.Connection) -> None:
    """Remove the test schema. Dropping it gives the disk space back straight away."""
    conn.execute(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")
    conn.commit()


def database_size_mb(conn: psycopg.Connection) -> float:
    return conn.execute("SELECT pg_database_size(current_database())").fetchone()[0] / 1_048_576
