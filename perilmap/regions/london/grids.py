"""Look up the distance to flood zones in a grid file."""

from __future__ import annotations

import numpy as np
import rasterio
from rasterio.windows import Window

from perilmap.regions.london.settings import BAND_BITS, BAND_ORDER, DEFAULT_RADIUS_METRES


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
