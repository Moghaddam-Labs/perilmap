"""Turn flood shapes into a compact grid file, and look up distances from it.

A square is marked if a zone touches any part of it. Results can read up to about
one square's diagonal too close, but a zone is never missed, even a very thin one.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import numpy as np
import rasterio
import shapely
from rasterio.features import rasterize
from rasterio.transform import from_origin
from rasterio.windows import Window

from data_test.config import (
    BAND_BITS,
    BAND_ORDER,
    BNG_CRS,
    COVERAGE_BLOCK_METRES,
    DEFAULT_RADIUS_METRES,
    GRID_RESOLUTION_METRES,
    LONDON_BBOX_BNG,
    FloodSource,
)
from data_test.sources import iter_batches

Bbox = tuple[int, int, int, int]
ATTRIBUTION = "© Environment Agency copyright and/or database right 2025. All rights reserved."


@dataclass
class GridBuild:
    """What a build produced, saved beside the grid so the report can use it."""

    source: str
    resolution_metres: int
    grid_mb: float
    build_seconds: float
    shapes: int
    duplicate_shapes: int
    shape_km2: dict[str, float]
    grid_km2: dict[str, float]
    coverage: list[str]
    built_at: str


def grid_path(grid_dir: Path, source: FloodSource, resolution: int) -> Path:
    return grid_dir / f"{source.key}_{resolution}m.tif"


def stats_path(path: Path) -> Path:
    return path.with_suffix(".json")


def clipped_area_m2(geometries: np.ndarray, bbox: Bbox) -> np.ndarray:
    """Measure shape areas inside the box, so edges don't overstate the source."""
    bounds = shapely.bounds(geometries)
    inside = (
        (bounds[:, 0] >= bbox[0])
        & (bounds[:, 1] >= bbox[1])
        & (bounds[:, 2] <= bbox[2])
        & (bounds[:, 3] <= bbox[3])
    )
    areas = shapely.area(geometries)
    if not inside.all():
        areas[~inside] = shapely.area(
            shapely.clip_by_rect(shapely.make_valid(geometries[~inside]), *bbox)
        )
    return areas


def coverage_map(grid: np.ndarray, resolution: int, block_metres: int) -> list[str]:
    """Draw which blocks hold any flood zone. A blank patch may be a missed download."""
    step = block_metres // resolution
    lines = []
    for top in range(0, grid.shape[0], step):
        lines.append(
            "".join(
                "#" if grid[top : top + step, left : left + step].any() else "."
                for left in range(0, grid.shape[1], step)
            )
        )
    return lines


def build_grid(
    paths: Sequence[Path],
    source: FloodSource,
    output: Path,
    *,
    layer: str | None = None,
    resolution: int = GRID_RESOLUTION_METRES,
    bbox: Bbox = LONDON_BBOX_BNG,
) -> GridBuild:
    """Write one grid file from one or more downloads, which may overlap."""
    started = perf_counter()
    min_x, min_y, max_x, max_y = bbox
    width, height = (max_x - min_x) // resolution, (max_y - min_y) // resolution
    transform = from_origin(min_x, max_y, resolution, resolution)
    masks = {band: np.zeros((height, width), "uint8") for band in BAND_BITS}
    shape_m2 = dict.fromkeys(BAND_BITS, 0.0)
    seen: set[int] = set()
    shapes = duplicates = 0

    for path in paths:
        for batch in iter_batches(path, source, layer=layer, bbox=bbox):
            for band in BAND_BITS:
                wkbs = []
                for row_band, wkb in batch:
                    if row_band != band:
                        continue
                    key = hash((band, wkb))
                    if key in seen:
                        duplicates += 1
                        continue
                    seen.add(key)
                    wkbs.append(wkb)
                if not wkbs:
                    continue
                geometries = shapely.from_wkb(wkbs)
                shapes += len(geometries)
                shape_m2[band] += float(clipped_area_m2(geometries, bbox).sum())
                rasterize(
                    geometries.tolist(), out=masks[band], transform=transform, all_touched=True
                )

    grid = np.zeros((height, width), "uint8")
    for band, bit in BAND_BITS.items():
        grid[masks[band] > 0] |= bit
    del masks

    output.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        output,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype="uint8",
        crs=BNG_CRS,
        transform=transform,
        compress="zstd",
        zstd_level=19,
        predictor=2,
        tiled=True,
        blockxsize=256,
        blockysize=256,
    ) as dataset:
        dataset.write(grid, 1)
        dataset.update_tags(
            source=source.label,
            resolution_metres=resolution,
            attribution=ATTRIBUTION,
            licence="Open Government Licence v3.0",
            bands=json.dumps(BAND_BITS),
        )

    cell_km2 = resolution * resolution / 1_000_000
    build = GridBuild(
        source=source.key,
        resolution_metres=resolution,
        grid_mb=output.stat().st_size / 1_048_576,
        build_seconds=perf_counter() - started,
        shapes=shapes,
        duplicate_shapes=duplicates,
        shape_km2={band: area / 1_000_000 for band, area in shape_m2.items() if area > 0},
        grid_km2={
            band: float(((grid & bit) > 0).sum()) * cell_km2
            for band, bit in BAND_BITS.items()
            if shape_m2[band] > 0
        },
        coverage=coverage_map(grid, resolution, COVERAGE_BLOCK_METRES),
        built_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )
    stats_path(output).write_text(json.dumps(asdict(build), indent=2), encoding="utf-8")
    return build


def read_build(output: Path) -> GridBuild:
    return GridBuild(**json.loads(stats_path(output).read_text(encoding="utf-8")))


def nearest_by_band(
    dataset: rasterio.DatasetReader,
    x: float,
    y: float,
    radius: float = DEFAULT_RADIUS_METRES,
) -> dict[str, float]:
    """Find the distance from a point to the nearest cell of each band within the radius."""
    resolution = dataset.transform.a
    left, top = dataset.bounds.left, dataset.bounds.top
    reach = int(radius // resolution) + 1
    column, row = int((x - left) // resolution), int((top - y) // resolution)
    window = Window(column - reach, row - reach, 2 * reach + 1, 2 * reach + 1)
    try:
        window = window.intersection(Window(0, 0, dataset.width, dataset.height))
    except rasterio.errors.WindowError:
        return {}
    cells = dataset.read(1, window=window)
    rows, columns = np.indices(cells.shape)
    centre_x = left + (columns + window.col_off + 0.5) * resolution
    centre_y = top - (rows + window.row_off + 0.5) * resolution
    # Distance to each cell's edge, so a point inside a cell is exactly 0 from it.
    gap_x = np.maximum(np.abs(centre_x - x) - resolution / 2, 0)
    gap_y = np.maximum(np.abs(centre_y - y) - resolution / 2, 0)
    distances = np.hypot(gap_x, gap_y)
    nearest = {}
    for band in BAND_ORDER:
        matches = distances[(cells & BAND_BITS[band]) > 0]
        if matches.size and matches.min() <= radius:
            nearest[band] = float(matches.min())
    return nearest


def exact_nearest_by_band(
    paths: Sequence[Path],
    source: FloodSource,
    x: float,
    y: float,
    *,
    layer: str | None = None,
    radius: float = DEFAULT_RADIUS_METRES,
) -> dict[str, float]:
    """Measure the same distances from the original shapes, to check the grid against."""
    point = shapely.Point(x, y)
    bbox = (int(x - radius), int(y - radius), int(x + radius) + 1, int(y + radius) + 1)
    nearest: dict[str, float] = {}
    for path in paths:
        for batch in iter_batches(path, source, layer=layer, bbox=bbox):
            for band, wkb in batch:
                distance = float(shapely.distance(point, shapely.from_wkb(wkb)))
                if distance <= radius and distance < nearest.get(band, float("inf")):
                    nearest[band] = distance
    return nearest
