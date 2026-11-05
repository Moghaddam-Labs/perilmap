"""Build small flood files and shapes for tests."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import shapely
from pyogrio.raw import write


def square(x: float, y: float, size: float = 100) -> bytes:
    """A square whose lower-left corner is at (x, y), in British National Grid metres."""
    return shapely.to_wkb(shapely.box(x, y, x + size, y + size))


def write_flood_file(
    path: Path,
    rows: list[tuple[str, bytes]],
    *,
    layer: str = "RoFRS_4band",
    field: str = "Risk_band",
    crs: str = "EPSG:27700",
) -> Path:
    """Write a GeoPackage shaped like the Environment Agency's download."""
    write(
        path,
        np.array([geometry for _, geometry in rows], dtype=object),
        [np.array([band for band, _ in rows], dtype=object)],
        fields=[field],
        layer=layer,
        driver="GPKG",
        geometry_type="Polygon",
        crs=crs,
    )
    return path


def write_heat_source(path: Path, rows: list[tuple[str, float, object]]) -> Path:
    """Write a file shaped like the GLA source, including a social column to be left out."""
    write(
        path,
        np.array([shapely.to_wkb(shape) for _, _, shape in rows], dtype=object),
        [
            np.array([borough for borough, _, _ in rows], dtype=object),
            np.array([temperature for _, temperature, _ in rows], dtype="float64"),
            np.array([12.5 for _ in rows], dtype="float64"),
            np.array([30.0 for _ in rows], dtype="float64"),
        ],
        fields=[
            "VulnMetrics_Project_Neighborhood",
            "AMS_ARUP_UHeatSummers2018_2022_OverallMeans_LSOABFE_Ply_T2",
            "VulnMetrics_Project_IncomeDeprivation",
            "pBAME__csv_pBAME",
        ],
        layer="airsurfacetemp",
        driver="GPKG",
        geometry_type="Polygon",
        crs="EPSG:27700",
    )
    return path
