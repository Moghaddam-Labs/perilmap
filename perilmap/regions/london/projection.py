"""Turn grid metres into longitude and latitude for shapes on the map."""

from __future__ import annotations

import numpy as np
import shapely
import shapely.geometry
from rasterio.warp import transform as reproject

from perilmap.core.models import Polygon
from perilmap.regions.london.settings import BNG_CRS

# Five decimal places is about 1 m, finer than the 5 m grid and much smaller to send than more.
DECIMAL_PLACES = 5


def _terms(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones_like(u), u, v, u * u, u * v, v * v])


class LocalProjection:
    """A fast stand-in for the full conversion, fitted to the few kilometres around one point.

    Converting tens of thousands of corner points one by one is slow on a small server. Over this
    distance the full conversion is a smooth curve, so a fitted curve matches it to within a
    millimetre, which a test checks.
    """

    def __init__(self, x: float, y: float, reach: float) -> None:
        self._x, self._y = x, y
        steps = np.linspace(-reach, reach, 5)
        grid_x, grid_y = np.meshgrid(x + steps, y + steps)
        xs, ys = grid_x.ravel(), grid_y.ravel()
        longitudes, latitudes = reproject(BNG_CRS, "EPSG:4326", xs.tolist(), ys.tolist())
        terms = _terms(*self._scaled(xs, ys))
        self._longitude = np.linalg.lstsq(terms, np.array(longitudes), rcond=None)[0]
        self._latitude = np.linalg.lstsq(terms, np.array(latitudes), rcond=None)[0]

    def _scaled(self, xs: np.ndarray, ys: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        # Kilometres from the centre, which keeps the fit well conditioned.
        return (xs - self._x) / 1_000, (ys - self._y) / 1_000

    def to_lon_lat(self, points: np.ndarray) -> np.ndarray:
        terms = _terms(*self._scaled(points[:, 0], points[:, 1]))
        return np.column_stack([terms @ self._longitude, terms @ self._latitude])

    def polygons(self, geometry: shapely.Geometry) -> tuple[Polygon, ...]:
        """Convert a shape in grid metres into GeoJSON style polygons, outer edges anticlockwise."""
        converted = shapely.transform(
            shapely.orient_polygons(shapely.multipolygons(shapely.get_parts(geometry))),
            lambda points: np.round(self.to_lon_lat(points), DECIMAL_PLACES),
        )
        return tuple(
            tuple(tuple((float(lon), float(lat)) for lon, lat in ring) for ring in polygon)
            for polygon in shapely.geometry.mapping(converted)["coordinates"]
        )
