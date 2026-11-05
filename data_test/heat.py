"""Build a small heat file for London, keeping only what PerilMap is allowed to show.

The source file also holds social measures, such as income and ethnicity. Only the
temperature, borough name and area shape are read, so the rest never leaves the source.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pyogrio
import shapely
from pyogrio.raw import read, write

from data_test.config import BNG_CRS
from perilmap.regions.london.heat import (
    OUTPUT_FIELDS,
    OUTPUT_LAYER,
    HeatBuild,
    HeatFileError,
    HeatResult,
    stats_path,
)

SOURCE_LAYER = "airsurfacetemp"
SOURCE_TEMPERATURE_FIELD = "AMS_ARUP_UHeatSummers2018_2022_OverallMeans_LSOABFE_Ply_T2"
SOURCE_BOROUGH_FIELD = "VulnMetrics_Project_Neighborhood"


def polygons_only(geometries: np.ndarray) -> np.ndarray:
    """Repair shapes and drop height values, keeping only their polygon parts."""
    repaired = shapely.force_2d(shapely.make_valid(geometries))
    return np.array(
        [
            shapely.union_all(
                [part for part in shapely.get_parts(shape) if shapely.get_type_id(part) in (3, 6)]
            )
            for shape in repaired
        ],
        dtype=object,
    )


def build_heat_file(source: Path, output: Path) -> HeatBuild:
    """Write the small file, refusing a source that isn't laid out as expected."""
    fields = [str(name) for name in pyogrio.read_info(source, layer=SOURCE_LAYER)["fields"]]
    for field in (SOURCE_TEMPERATURE_FIELD, SOURCE_BOROUGH_FIELD):
        if field not in fields:
            raise HeatFileError(f"Field {field} is missing from {source.name}.")
    meta, _, geometries, values = read(
        source, layer=SOURCE_LAYER, columns=[SOURCE_BOROUGH_FIELD, SOURCE_TEMPERATURE_FIELD]
    )
    names = [str(name) for name in meta["fields"]]
    boroughs = values[names.index(SOURCE_BOROUGH_FIELD)]
    temperatures = values[names.index(SOURCE_TEMPERATURE_FIELD)].astype("float64")
    if not np.all(np.isfinite(temperatures)):
        raise HeatFileError("Some areas have no temperature.")

    shapes = polygons_only(shapely.from_wkb(geometries))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    write(
        output,
        np.array(shapely.to_wkb(shapes.tolist()), dtype=object),
        [boroughs, temperatures],
        fields=list(OUTPUT_FIELDS),
        layer=OUTPUT_LAYER,
        driver="GPKG",
        geometry_type="Unknown",
        crs=BNG_CRS,
    )
    build = HeatBuild(
        areas=len(temperatures),
        min_c=float(temperatures.min()),
        max_c=float(temperatures.max()),
        fifth_breaks_c=[float(v) for v in np.quantile(temperatures, [0.2, 0.4, 0.6, 0.8])],
        file_mb=output.stat().st_size / 1_048_576,
        km2=float(shapely.area(shapes.tolist()).sum()) / 1_000_000,
    )
    stats_path(output).write_text(json.dumps(asdict(build), indent=2), encoding="utf-8")
    return build


def format_heat(result: HeatResult | None) -> str:
    if result is None:
        return "No data"
    return f"{result.air_temp_c:.1f} °C, {result.group}"
