"""Build a small heat file for London, keeping only what PerilMap is allowed to show.

The source file also holds social measures, such as income and ethnicity. Only the
temperature, borough name and area shape are read, so the rest never leaves the source.
"""

from __future__ import annotations

import bisect
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pyogrio
import shapely
from pyogrio.raw import read, write

from data_test.config import BNG_CRS

SOURCE_LAYER = "airsurfacetemp"
SOURCE_TEMPERATURE_FIELD = "AMS_ARUP_UHeatSummers2018_2022_OverallMeans_LSOABFE_Ply_T2"
SOURCE_BOROUGH_FIELD = "VulnMetrics_Project_Neighborhood"
OUTPUT_LAYER = "heat"
OUTPUT_FIELDS = ("borough", "air_temp_c")

GROUPS = ("coolest fifth", "cooler fifth", "middle fifth", "warmer fifth", "warmest fifth")

# The source's own description of the number.
SOURCE_DESCRIPTION = "Modelled average air temperature, June to August, day and night, 2018 to 2022"
SOURCE_CREDIT = "Greater London Authority and Arup"
EXPLANATION = (
    "Temperatures across London only vary by about two degrees, so we show how this area "
    "compares, not a risk rating. This is the average outdoor summer temperature, not how hot "
    "your home gets inside or during a heatwave."
)
# PerilMap's own working, labelled so it can't be mistaken for the source's wording.
OWN_CALCULATION_NOTE = "This range and the fifths are PerilMap's own calculation from this data."


class HeatFileError(ValueError):
    """The heat source file doesn't match what the test expects."""


@dataclass
class HeatBuild:
    """Facts about the built file, saved beside it so the report can use them."""

    areas: int
    min_c: float
    max_c: float
    # The four temperatures that divide the areas into fifths.
    fifth_breaks_c: list[float]
    file_mb: float
    km2: float


@dataclass(frozen=True)
class HeatResult:
    borough: str
    air_temp_c: float
    group: str


def stats_path(path: Path) -> Path:
    return path.with_suffix(".json")


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


def group_for(temperature: float, breaks: list[float]) -> str:
    return GROUPS[bisect.bisect_right(breaks, temperature)]


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


def read_build(path: Path) -> HeatBuild:
    return HeatBuild(**json.loads(stats_path(path).read_text(encoding="utf-8")))


class HeatLookup:
    """Finds the area a point falls in. No match means there's no data for that spot."""

    def __init__(self, path: Path) -> None:
        self.build = read_build(path)
        meta, _, geometries, values = read(path, layer=OUTPUT_LAYER)
        names = [str(name) for name in meta["fields"]]
        if tuple(names) != OUTPUT_FIELDS:
            raise HeatFileError(f"Unexpected fields in {path.name}: {', '.join(names)}.")
        self.shapes = shapely.from_wkb(geometries)
        self.boroughs = values[0]
        self.temperatures = values[1].astype("float64")
        self.tree = shapely.STRtree(self.shapes)

    def find(self, x: float, y: float) -> HeatResult | None:
        matches = self.tree.query(shapely.Point(x, y), predicate="intersects")
        if len(matches) == 0:
            return None
        index = int(matches[0])
        temperature = float(self.temperatures[index])
        return HeatResult(
            str(self.boroughs[index]),
            temperature,
            group_for(temperature, self.build.fifth_breaks_c),
        )


def format_heat(result: HeatResult | None) -> str:
    if result is None:
        return "No data"
    return f"{result.air_temp_c:.1f} °C, {result.group}"
