"""Measure database size and query speed, then check results against known places."""

from __future__ import annotations

import csv
import json
import statistics
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import psycopg

from data_test.config import (
    BAND_ORDER,
    BNG_SRID,
    DEFAULT_RADIUS_METRES,
    FLOOD_SOURCES,
    LONDON_BBOX_BNG,
    SUPABASE_FREE_LIMIT_MB,
    TARGET_DB_MB,
    TARGET_QUERY_MS,
)
from data_test.database import TABLE, SetupError

LOCATIONS_FILE = Path(__file__).with_name("locations.csv")

# The bounded search keeps every lookup cheap, and a zone over the radius away
# isn't useful to someone checking one home anyway.
NEAREST_BY_BAND = f"""
    WITH pin AS (
        SELECT ST_Transform(ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326), {BNG_SRID}) AS g
    )
    SELECT z.source, z.band, MIN(ST_Distance(z.geom, pin.g)) AS metres
    FROM {TABLE} z, pin
    WHERE ST_DWithin(z.geom, pin.g, %(radius)s)
    GROUP BY z.source, z.band
"""

IN_TEST_AREA = f"""
    SELECT ST_Intersects(
        ST_Transform(ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326), {BNG_SRID}),
        ST_MakeEnvelope(%(minx)s, %(miny)s, %(maxx)s, %(maxy)s, {BNG_SRID})
    )
"""


@dataclass(frozen=True)
class Location:
    name: str
    latitude: float
    longitude: float
    expectation: str


@dataclass
class LocationResult:
    location: Location
    in_area: bool
    # {source: {band: metres}}
    nearest: dict[str, dict[str, float]] = field(default_factory=dict)
    round_trip_ms: float = 0.0
    server_ms: float = 0.0

    @property
    def check_passed(self) -> bool:
        return expectation_met(self.location.expectation, self.in_area, self.nearest)


@dataclass
class Sizes:
    database_mb: float
    table_mb: float
    index_mb: float
    pieces_by_source: dict[str, int]


def expectation_met(expectation: str, in_area: bool, nearest: dict[str, dict[str, float]]) -> bool:
    """Compare a result with what we'd expect there. A miss needs a human look."""
    river_bands = set(nearest.get("rivers_and_sea", {}))
    if expectation == "outside_area":
        return not in_area
    if expectation == "near_river":
        return bool(river_bands)
    if expectation == "away_from_river":
        return not river_bands & {"High", "Medium", "Low"}
    raise ValueError(f"Unknown expectation: {expectation}")


def read_locations(path: Path = LOCATIONS_FILE) -> list[Location]:
    with path.open(newline="", encoding="utf-8") as file:
        return [
            Location(
                row["name"], float(row["latitude"]), float(row["longitude"]), row["expectation"]
            )
            for row in csv.DictReader(file)
        ]


def measure_sizes(conn: psycopg.Connection) -> Sizes:
    database, table, index = conn.execute(
        "SELECT pg_database_size(current_database()), "
        "pg_total_relation_size(%(t)s::regclass), pg_indexes_size(%(t)s::regclass)",
        {"t": TABLE},
    ).fetchone()
    pieces = dict(conn.execute(f"SELECT source, count(*) FROM {TABLE} GROUP BY source").fetchall())
    mb = 1_048_576
    return Sizes(database / mb, (table - index) / mb, index / mb, pieces)


def measure_location(conn: psycopg.Connection, location: Location, radius: float) -> LocationResult:
    params = {"lat": location.latitude, "lon": location.longitude, "radius": radius}
    in_area = conn.execute(
        IN_TEST_AREA,
        {
            **params,
            "minx": LONDON_BBOX_BNG[0],
            "miny": LONDON_BBOX_BNG[1],
            "maxx": LONDON_BBOX_BNG[2],
            "maxy": LONDON_BBOX_BNG[3],
        },
    ).fetchone()[0]

    started = perf_counter()
    rows = conn.execute(NEAREST_BY_BAND, params).fetchall()
    round_trip_ms = (perf_counter() - started) * 1_000

    plan = conn.execute(f"EXPLAIN (ANALYZE, FORMAT JSON) {NEAREST_BY_BAND}", params).fetchone()[0]
    plan = json.loads(plan) if isinstance(plan, str) else plan

    nearest: dict[str, dict[str, float]] = {}
    for source, band, metres in rows:
        nearest.setdefault(source, {})[band] = float(metres)
    return LocationResult(
        location, in_area, nearest, round_trip_ms, float(plan[0]["Execution Time"])
    )


def format_nearest(bands: dict[str, float] | None, radius: float) -> str:
    """Describe one source's result, e.g. 'High 120 m, Low on zone'."""
    if not bands:
        return f"None within {radius:,.0f} m"
    parts = []
    for band in BAND_ORDER:
        if band in bands:
            metres = bands[band]
            parts.append(f"{band} on zone" if metres == 0 else f"{band} {metres:,.0f} m")
    return ", ".join(parts)


def build_report(sizes: Sizes, results: list[LocationResult], radius: float) -> str:
    """Write the findings as Markdown. Holds no connection details."""
    server = [result.server_ms for result in results]
    trips = [result.round_trip_ms for result in results]
    size_ok = sizes.database_mb <= TARGET_DB_MB
    speed_ok = max(server) <= TARGET_QUERY_MS
    passed = sum(result.check_passed for result in results)

    lines = [
        "# Flood data test",
        "",
        f"Run on {datetime.now(UTC):%d %B %Y at %H:%M} UTC, "
        f"searching {radius:,.0f} m around each pin.",
        "",
        "## Results",
        "",
        "| Check | Result | Target | Verdict |",
        "|---|---|---|---|",
        f"| Database size | {sizes.database_mb:,.0f} MB | Up to {TARGET_DB_MB} MB "
        f"(free limit {SUPABASE_FREE_LIMIT_MB} MB) | {'Pass' if size_ok else 'Fail'} |",
        f"| Slowest lookup on the database | {max(server):,.0f} ms | Up to {TARGET_QUERY_MS} ms "
        f"| {'Pass' if speed_ok else 'Fail'} |",
        f"| Known places as expected | {passed} of {len(results)} | All, or explained "
        f"| {'Pass' if passed == len(results) else 'Review'} |",
        "",
        "## Size",
        "",
        f"- Flood table: {sizes.table_mb:,.1f} MB",
        f"- Spatial index: {sizes.index_mb:,.1f} MB",
    ]
    for key, pieces in sorted(sizes.pieces_by_source.items()):
        lines.append(f"- {FLOOD_SOURCES[key].label}: {pieces:,} stored pieces")
    lines += [
        "",
        "## Speed",
        "",
        f"- On the database: median {statistics.median(server):,.0f} ms, "
        f"slowest {max(server):,.0f} ms",
        f"- Including the network: median {statistics.median(trips):,.0f} ms, "
        f"slowest {max(trips):,.0f} ms",
        "",
        "## Known places",
        "",
        "Expectations are rough checks on approximate coordinates, not proof of accuracy. "
        "Review means a person should look at that place on the Environment Agency map.",
        "",
        "| Place | Expected | Rivers and sea | Surface water | Check |",
        "|---|---|---|---|---|",
    ]
    for result in results:
        location = result.location
        expected = location.expectation.replace("_", " ").capitalize()
        if not result.in_area:
            rivers = surface = "Outside test area"
        else:
            rivers = format_nearest(result.nearest.get("rivers_and_sea"), radius)
            surface = format_nearest(result.nearest.get("surface_water"), radius)
        check = "OK" if result.check_passed else "Review"
        lines.append(f"| {location.name} | {expected} | {rivers} | {surface} | {check} |")
    return "\n".join(lines) + "\n"


def run(
    conn: psycopg.Connection, radius: float = DEFAULT_RADIUS_METRES
) -> tuple[Sizes, list[LocationResult]]:
    if conn.execute("SELECT to_regclass(%s)", (f"{TABLE}_geom_idx",)).fetchone()[0] is None:
        raise SetupError("The spatial index is missing, so a load didn't finish. Reset and reload.")
    results = [measure_location(conn, location, radius) for location in read_locations()]
    return measure_sizes(conn), results
