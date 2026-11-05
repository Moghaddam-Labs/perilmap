"""Look up an area's modelled summer temperature in the small heat file."""

from __future__ import annotations

import bisect
import json
from dataclasses import dataclass
from pathlib import Path

import shapely
from pyogrio.raw import read

OUTPUT_LAYER = "heat"
OUTPUT_FIELDS = ("borough", "air_temp_c")
HEAT_FILENAME = "heat_air_temperature.gpkg"

GROUPS = ("coolest fifth", "cooler fifth", "middle fifth", "warmer fifth", "warmest fifth")


class HeatFileError(ValueError):
    """A heat file doesn't match what's expected."""


@dataclass
class HeatBuild:
    """Facts about the built file, saved beside it."""

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


def group_for(temperature: float, breaks: list[float]) -> str:
    return GROUPS[bisect.bisect_right(breaks, temperature)]


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
