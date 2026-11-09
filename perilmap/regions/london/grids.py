"""Read the flood grid around a point, then measure the distance to its zones and trace them."""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import rasterio
import shapely
from rasterio.errors import NotGeoreferencedWarning
from rasterio.features import shapes
from rasterio.transform import Affine
from rasterio.windows import Window

from perilmap.regions.london.settings import (
    BAND_BITS,
    BAND_ORDER,
    DEFAULT_RADIUS_METRES,
    SMOOTHING_METRES,
)

# Tracing uses a temporary in-memory grid. On worker threads GDAL warns that it has no map position,
# even though the position is passed in separately and used correctly, which a test checks.
warnings.filterwarnings("ignore", category=NotGeoreferencedWarning, module="rasterio.features")


@dataclass(frozen=True)
class Patch:
    """The grid squares around a point, and how far each one is from it."""

    cells: np.ndarray
    distances: np.ndarray
    transform: Affine
    radius: float


def read_patch(
    dataset: rasterio.DatasetReader, x: float, y: float, radius: float = DEFAULT_RADIUS_METRES
) -> Patch | None:
    """Read the squares within reach of a point, or None if the point is off the grid."""
    resolution = dataset.transform.a
    left, top = dataset.bounds.left, dataset.bounds.top
    reach = int(radius // resolution) + 1
    column, row = int((x - left) // resolution), int((top - y) // resolution)
    window = Window(column - reach, row - reach, 2 * reach + 1, 2 * reach + 1)
    try:
        window = window.intersection(Window(0, 0, dataset.width, dataset.height))
    except rasterio.errors.WindowError:
        return None
    cells = dataset.read(1, window=window)
    rows, columns = np.indices(cells.shape)
    centre_x = left + (columns + window.col_off + 0.5) * resolution
    centre_y = top - (rows + window.row_off + 0.5) * resolution
    # Distance to each cell's edge, so a point inside a cell is exactly 0 from it.
    gap_x = np.maximum(np.abs(centre_x - x) - resolution / 2, 0)
    gap_y = np.maximum(np.abs(centre_y - y) - resolution / 2, 0)
    corner_x, corner_y = left + window.col_off * resolution, top - window.row_off * resolution
    transform = Affine(resolution, 0, corner_x, 0, -resolution, corner_y)
    return Patch(cells, np.hypot(gap_x, gap_y), transform, radius)


def nearest_in_patch(patch: Patch | None) -> dict[str, float]:
    """Find the distance to the nearest cell of each band within the radius."""
    if patch is None:
        return {}
    nearest = {}
    for band in BAND_ORDER:
        matches = patch.distances[(patch.cells & BAND_BITS[band]) > 0]
        if matches.size and matches.min() <= patch.radius:
            nearest[band] = float(matches.min())
    return nearest


def nearest_by_band(
    dataset: rasterio.DatasetReader,
    x: float,
    y: float,
    radius: float = DEFAULT_RADIUS_METRES,
) -> dict[str, float]:
    """Find the distance from a point to the nearest cell of each band within the radius."""
    return nearest_in_patch(read_patch(dataset, x, y, radius))


def zone_outlines(
    patch: Patch | None, bands: tuple[str, ...], smoothing: float = SMOOTHING_METRES
) -> dict[str, shapely.Geometry]:
    """Trace each band's zones within the radius, in grid metres.

    Exactly the squares counted for the distances are traced, so the map and the distances agree.
    Corners are smoothed by up to half a square, so the edges don't look like steps.
    """
    if patch is None:
        return {}
    inside = patch.distances <= patch.radius
    outlines = {}
    for band in bands:
        mask = ((patch.cells & BAND_BITS[band]) > 0) & inside
        if not mask.any():
            continue
        polygons = [
            shapely.Polygon(geometry["coordinates"][0], geometry["coordinates"][1:])
            for geometry, _ in shapes(mask.astype(np.uint8), mask=mask, transform=patch.transform)
        ]
        smoothed = shapely.simplify(np.array(polygons), smoothing, preserve_topology=True)
        outlines[band] = shapely.multipolygons(smoothed)
    return outlines
