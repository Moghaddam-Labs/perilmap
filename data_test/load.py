"""Load flood polygons into PostGIS, stopping before the free plan's limit."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

import psycopg

from data_test.config import BNG_SRID, DEFAULT_MAX_DB_MB, DEFAULT_SUBDIVIDE_VERTICES, FloodSource
from data_test.database import (
    TABLE,
    build_index,
    create_table,
    database_size_mb,
    drop_index,
)
from data_test.sources import iter_batches

# Repair each shape, then cut large ones into small pieces. Small pieces keep
# distance lookups fast, at the cost of a little extra storage.
INSERT_FROM_STAGING = f"""
    WITH parsed AS (
        SELECT band, ST_Force2D(ST_SetSRID(ST_GeomFromWKB(wkb), {BNG_SRID})) AS g
        FROM flood_staging
    ),
    simplified AS (
        SELECT band,
               CASE WHEN %(simplify)s > 0
                    THEN ST_SimplifyPreserveTopology(g, %(simplify)s)
                    ELSE g END AS g
        FROM parsed
    ),
    cleaned AS (
        SELECT band, ST_CollectionExtract(ST_MakeValid(g), 3) AS g
        FROM simplified
    )
    INSERT INTO {TABLE} (source, band, geom)
    SELECT %(source)s, band, ST_Subdivide(g, %(vertices)s)
    FROM cleaned
    WHERE NOT ST_IsEmpty(g)
"""


class SourceAlreadyLoaded(RuntimeError):
    """Loading twice would double count, which would make the size result wrong."""


@dataclass
class LoadResult:
    features: int = 0
    stopped_early: bool = False
    database_mb: float = 0.0


def load_batches(
    conn: psycopg.Connection,
    source: FloodSource,
    batches: Iterable[list[tuple[str, bytes]]],
    *,
    simplify_metres: float = 0.0,
    subdivide_vertices: int = DEFAULT_SUBDIVIDE_VERTICES,
    max_db_mb: float = DEFAULT_MAX_DB_MB,
) -> LoadResult:
    """Write batches one transaction at a time, checking the size after each."""
    create_table(conn)
    already_loaded = conn.execute(
        f"SELECT EXISTS (SELECT 1 FROM {TABLE} WHERE source = %s)", (source.key,)
    ).fetchone()[0]
    if already_loaded:
        raise SourceAlreadyLoaded(f"{source.label} is already loaded. Run the reset command first.")

    drop_index(conn)
    conn.execute("SET statement_timeout = 0")
    conn.execute("CREATE TEMP TABLE IF NOT EXISTS flood_staging (band text, wkb bytea)")
    conn.commit()

    result = LoadResult(database_mb=database_size_mb(conn))
    for batch in batches:
        if result.database_mb >= max_db_mb:
            result.stopped_early = True
            break
        conn.execute("TRUNCATE flood_staging")
        with (
            conn.cursor() as cursor,
            cursor.copy("COPY flood_staging (band, wkb) FROM STDIN") as copy,
        ):
            for row in batch:
                copy.write_row(row)
        conn.execute(
            INSERT_FROM_STAGING,
            {
                "source": source.key,
                "simplify": simplify_metres,
                "vertices": subdivide_vertices,
            },
        )
        conn.commit()
        result.features += len(batch)
        result.database_mb = database_size_mb(conn)
        print(f"  {result.features:,} shapes loaded, database at {result.database_mb:,.0f} MB")

    if not result.stopped_early:
        build_index(conn)
        result.database_mb = database_size_mb(conn)
    return result


def load_files(
    conn: psycopg.Connection,
    source: FloodSource,
    paths: Sequence[Path],
    *,
    layer: str | None = None,
    **options: object,
) -> LoadResult:
    """Load one or more downloaded files as a single flood source."""

    def batches() -> Iterable[list[tuple[str, bytes]]]:
        for path in paths:
            yield from iter_batches(path, source, layer=layer)

    return load_batches(conn, source, batches(), **options)
