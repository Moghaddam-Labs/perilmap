"""Tests against a real PostGIS server, laid out like Supabase."""

from __future__ import annotations

from pathlib import Path

import psycopg
import pytest

from data_test import database, measure
from data_test.config import FLOOD_SOURCES
from data_test.load import SourceAlreadyLoaded, load_batches, load_files
from tests.helpers import square, write_flood_file

RIVERS = FLOOD_SOURCES["rivers_and_sea"]
SURFACE = FLOOD_SOURCES["surface_water"]


def pieces(conn: psycopg.Connection) -> int:
    return conn.execute(f"SELECT count(*) FROM {database.TABLE}").fetchone()[0]


def test_postgis_is_found_in_the_extensions_schema(conn: psycopg.Connection) -> None:
    assert conn.execute("SELECT ST_AsText(ST_MakePoint(1, 2))").fetchone()[0] == "POINT(1 2)"


def test_table_lives_outside_public_with_row_level_security(conn: psycopg.Connection) -> None:
    database.create_table(conn)
    row = conn.execute(
        "SELECT n.nspname, c.relrowsecurity FROM pg_class c "
        "JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relname = %s",
        (database.TABLE,),
    ).fetchone()
    assert row == ("perilmap", True)


def test_load_writes_rows_and_builds_the_index(conn: psycopg.Connection, tmp_path: Path) -> None:
    path = write_flood_file(
        tmp_path / "flood.gpkg",
        [("High", square(530_000, 180_000)), ("Low", square(530_500, 180_000))],
    )
    result = load_files(conn, RIVERS, [path])
    assert result.features == 2
    assert result.stopped_early is False
    assert pieces(conn) == 2
    assert (
        conn.execute(
            "SELECT count(*) FROM pg_indexes WHERE indexname = %s",
            (f"{database.TABLE}_geom_idx",),
        ).fetchone()[0]
        == 1
    )


def test_loading_a_source_twice_is_refused(conn: psycopg.Connection) -> None:
    batch = [[("High", square(530_000, 180_000))]]
    load_batches(conn, RIVERS, batch)
    with pytest.raises(SourceAlreadyLoaded):
        load_batches(conn, RIVERS, batch)


def test_two_sources_can_share_the_table(conn: psycopg.Connection) -> None:
    load_batches(conn, RIVERS, [[("High", square(530_000, 180_000))]])
    load_batches(conn, SURFACE, [[("Medium", square(530_000, 180_000))]])
    assert pieces(conn) == 2


def test_size_guard_stops_before_writing_more(conn: psycopg.Connection) -> None:
    result = load_batches(conn, RIVERS, [[("High", square(530_000, 180_000))]], max_db_mb=0)
    assert result.stopped_early is True
    assert result.features == 0
    assert pieces(conn) == 0


def test_large_shapes_are_cut_into_small_pieces(conn: psycopg.Connection) -> None:
    detailed = conn.execute(
        "SELECT ST_AsBinary(ST_Buffer(ST_MakePoint(530000, 180000), 500, 64))"
    ).fetchone()[0]
    load_batches(conn, RIVERS, [[("High", bytes(detailed))]], subdivide_vertices=16)
    assert pieces(conn) > 1
    assert conn.execute(f"SELECT max(ST_NPoints(geom)) FROM {database.TABLE}").fetchone()[0] <= 16


def test_invalid_shapes_are_repaired(conn: psycopg.Connection) -> None:
    bowtie = conn.execute(
        "SELECT ST_AsBinary('POLYGON((530000 180000, 530100 180100, "
        "530100 180000, 530000 180100, 530000 180000))'::geometry)"
    ).fetchone()[0]
    load_batches(conn, RIVERS, [[("High", bytes(bowtie))]])
    assert conn.execute(f"SELECT bool_and(ST_IsValid(geom)) FROM {database.TABLE}").fetchone()[0]


def test_simplifying_reduces_stored_points(conn: psycopg.Connection) -> None:
    detailed = bytes(
        conn.execute(
            "SELECT ST_AsBinary(ST_Buffer(ST_MakePoint(530000, 180000), 500, 64))"
        ).fetchone()[0]
    )
    total = f"SELECT sum(ST_NPoints(geom)) FROM {database.TABLE}"
    load_batches(conn, RIVERS, [[("High", detailed)]])
    full = conn.execute(total).fetchone()[0]
    database.reset(conn)
    load_batches(conn, RIVERS, [[("High", detailed)]], simplify_metres=20)
    assert conn.execute(total).fetchone()[0] < full


def test_measure_finds_distance_by_band_and_source(conn: psycopg.Connection) -> None:
    pin = conn.execute(
        "SELECT ST_X(g), ST_Y(g) FROM (SELECT ST_Transform("
        "ST_SetSRID(ST_MakePoint(-0.1, 51.5), 4326), 27700) AS g) p"
    ).fetchone()
    x, y = pin
    load_batches(
        conn,
        RIVERS,
        [
            [
                ("High", square(x + 200, y - 50)),
                ("Low", square(x - 50, y - 50)),
                ("Medium", square(x + 5_000, y)),
            ]
        ],
    )
    load_batches(conn, SURFACE, [[("Medium", square(x, y + 300))]])
    location = measure.Location("Pin", 51.5, -0.1, "near_river")

    result = measure.measure_location(conn, location, radius=1_000)

    assert result.in_area is True
    assert result.nearest["rivers_and_sea"]["Low"] == 0
    assert result.nearest["rivers_and_sea"]["High"] == pytest.approx(200, abs=0.01)
    assert "Medium" not in result.nearest["rivers_and_sea"]
    assert result.nearest["surface_water"]["Medium"] == pytest.approx(300, abs=0.01)
    assert result.check_passed
    assert result.server_ms > 0


def test_places_outside_the_box_are_flagged(conn: psycopg.Connection) -> None:
    load_batches(conn, RIVERS, [[("High", square(530_000, 180_000))]])
    result = measure.measure_location(
        conn, measure.Location("Oxford", 51.752, -1.2577, "outside_area"), 1_000
    )
    assert result.in_area is False
    assert result.check_passed


def test_full_run_produces_a_report(conn: psycopg.Connection) -> None:
    load_batches(conn, RIVERS, [[("Low", square(530_000, 180_000))]])
    sizes, results = measure.run(conn, 1_000)
    report = measure.build_report(sizes, results, 1_000)
    assert len(results) == 20
    assert sizes.pieces_by_source == {"rivers_and_sea": 1}
    assert "Rivers and sea: 1 stored pieces" in report
    assert "Oxford" in report and "Outside test area" in report


def test_measure_refuses_to_run_without_the_index(conn: psycopg.Connection) -> None:
    load_batches(conn, RIVERS, [[("Low", square(530_000, 180_000))]])
    database.drop_index(conn)
    with pytest.raises(database.SetupError, match="index"):
        measure.run(conn, 1_000)


def test_lookup_uses_the_spatial_index(conn: psycopg.Connection) -> None:
    rows = [[("Low", square(530_000 + i * 200, 180_000)) for i in range(2_000)]]
    load_batches(conn, RIVERS, rows)
    plan = conn.execute(
        f"EXPLAIN {measure.NEAREST_BY_BAND}", {"lat": 51.5, "lon": -0.1, "radius": 1_000}
    ).fetchall()
    assert any(f"{database.TABLE}_geom_idx" in row[0] for row in plan)


def test_reset_removes_the_schema(conn: psycopg.Connection) -> None:
    load_batches(conn, RIVERS, [[("High", square(530_000, 180_000))]])
    database.reset(conn)
    assert (
        conn.execute(
            "SELECT count(*) FROM information_schema.schemata WHERE schema_name = 'perilmap'"
        ).fetchone()[0]
        == 0
    )


def test_connection_error_does_not_reveal_the_password() -> None:
    with pytest.raises(database.SetupError) as caught:
        database.connect("postgresql://user:SECRET-VALUE@127.0.0.1:1/none")
    assert "SECRET-VALUE" not in str(caught.value)
    assert "Couldn't connect" in str(caught.value)


def test_error_cleaner_masks_the_password() -> None:
    url = "postgresql://user:SECRET-VALUE@example.com/db"
    assert database.clean_error("failed for SECRET-VALUE", url) == "failed for ***"
