"""Shared test setup. Database tests need TEST_DATABASE_URL and a PostGIS server."""

from __future__ import annotations

import os
from collections.abc import Iterator

import psycopg
import pytest

from data_test import database


@pytest.fixture
def conn() -> Iterator[psycopg.Connection]:
    """A clean database laid out like Supabase, with PostGIS in `extensions`."""
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set")
    with psycopg.connect(url, autocommit=True) as setup:
        setup.execute("CREATE SCHEMA IF NOT EXISTS extensions")
        setup.execute("CREATE EXTENSION IF NOT EXISTS postgis SCHEMA extensions")
    connection = database.connect(url)
    database.reset(connection)
    connection.execute("SET search_path = perilmap, extensions, public")
    yield connection
    connection.rollback()
    database.reset(connection)
    connection.close()
