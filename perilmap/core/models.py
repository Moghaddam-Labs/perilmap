"""What a result can say. These rules make sure it says it honestly and helpfully."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

DISCLAIMER = (
    "Guidance only. This is not an insurance quote, survey or financial advice. "
    "It describes the area around a home, not the home itself."
)
NOT_AVAILABLE_HERE = "Not available here yet"


class ResultError(ValueError):
    """A result breaks a rule, which is a bug in the plug-in that made it."""


class ResultStatus(Enum):
    AVAILABLE = "available"
    INCOMPLETE = "incomplete"
    GENERAL_INFORMATION = "general_information"
    NO_DATA = "no_data"
    NOT_AVAILABLE_HERE = "not_available_here"
    TEMPORARILY_UNAVAILABLE = "temporarily_unavailable"


@dataclass(frozen=True, repr=False)
class Location:
    """A point on the map. It's kept out of logs and error messages, because it may be a home."""

    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not (math.isfinite(self.latitude) and math.isfinite(self.longitude)):
            raise ValueError("Latitude and longitude must be real numbers.")
        if not -90 <= self.latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90.")
        if not -180 <= self.longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180.")

    def __repr__(self) -> str:
        return "Location(hidden)"


@dataclass(frozen=True)
class DataSource:
    """Where a result comes from, so people can judge and check it."""

    name: str
    publisher: str
    licence: str
    url: str
    attribution: str
    last_updated: str
    resolution: str

    def __post_init__(self) -> None:
        for name, value in vars(self).items():
            if not value.strip():
                raise ResultError(f"A data source needs a {name}.")


@dataclass(frozen=True)
class Link:
    """A page where someone can read more or take the next step."""

    label: str
    url: str

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise ResultError("A link needs a label.")
        if not self.url.startswith("https://"):
            raise ResultError("A link must use https.")


@dataclass(frozen=True)
class ZoneDistance:
    """How far away a risk zone is. Zero means on the zone, and None means none was found."""

    band: str
    metres: float | None
    label: str

    def __post_init__(self) -> None:
        if not self.band.strip() or not self.label.strip():
            raise ResultError("A zone distance needs a band and a label.")
        if self.metres is not None and self.metres < 0:
            raise ResultError("A distance can't be negative.")


@dataclass(frozen=True)
class NearestZones:
    """The nearest zone in each band, within a stated search distance."""

    zones: tuple[ZoneDistance, ...]
    search_radius_metres: float

    def __post_init__(self) -> None:
        if not self.zones:
            raise ResultError("Nearest zones must list every band, even when none is found.")
        if self.search_radius_metres <= 0:
            raise ResultError("The search radius must be above zero.")


# A polygon is a list of rings of (longitude, latitude) points. The first ring is its outside edge
# and any others are holes, as in GeoJSON. Each ring ends on the point it starts from.
Ring = tuple[tuple[float, float], ...]
Polygon = tuple[Ring, ...]


def _check_polygons(polygons: tuple[Polygon, ...], name: str) -> None:
    for polygon in polygons:
        if not polygon:
            raise ResultError(f"Each {name} polygon needs an outside edge.")
        for ring in polygon:
            if len(ring) < 4 or ring[0] != ring[-1]:
                raise ResultError(f"Each {name} ring needs 4 or more points and must be closed.")


@dataclass(frozen=True)
class ZoneShape:
    """Where one band's zones lie inside the search area."""

    band: str
    polygons: tuple[Polygon, ...]

    def __post_init__(self) -> None:
        if not self.band.strip():
            raise ResultError("A zone shape needs a band.")
        if not self.polygons:
            raise ResultError("A zone shape needs at least one polygon.")
        _check_polygons(self.polygons, "zone")


@dataclass(frozen=True)
class ZoneMap:
    """A peril's zones around a location, for drawing on a map.

    It must come from the same data and search area as the peril's nearest zones, so the map and
    the distances agree. Areas with no data are included, so a blank part of the map can't be
    mistaken for an area with no zones.
    """

    search_radius_metres: float
    shapes: tuple[ZoneShape, ...]
    no_data_areas: tuple[Polygon, ...] = ()

    def __post_init__(self) -> None:
        if self.search_radius_metres <= 0:
            raise ResultError("The search radius must be above zero.")
        bands = [shape.band for shape in self.shapes]
        if len(set(bands)) != len(bands):
            raise ResultError("Each band can only have one shape.")
        _check_polygons(self.no_data_areas, "no data")


@dataclass(frozen=True)
class AreaComparison:
    """How an area compares with the wider region, not a risk rating."""

    value: float
    unit: str
    group: str
    range_low: float
    range_high: float
    calculation_note: str

    def __post_init__(self) -> None:
        if not self.unit.strip() or not self.group.strip():
            raise ResultError("A comparison needs a unit and a group.")
        if not self.calculation_note.strip():
            raise ResultError("A comparison must say which parts are our own calculation.")
        if not self.range_low <= self.value <= self.range_high:
            raise ResultError("A compared value must sit inside its range.")


Measurement = NearestZones | AreaComparison


@dataclass(frozen=True)
class PerilResult:
    """One peril's answer. It always says what it means, how sure it is and what to do next."""

    peril_id: str
    title: str
    status: ResultStatus
    summary: str
    what_this_means: str
    how_sure: str
    what_you_can_do: tuple[str, ...]
    sources: tuple[DataSource, ...] = ()
    measurement: Measurement | None = None
    caveats: tuple[str, ...] = ()
    links: tuple[Link, ...] = ()

    def __post_init__(self) -> None:
        for name in ("peril_id", "title", "summary", "what_this_means", "how_sure"):
            if not getattr(self, name).strip():
                raise ResultError(f"A result needs {name}.")
        if not self.what_you_can_do or not all(step.strip() for step in self.what_you_can_do):
            raise ResultError("A result must say what someone can do next.")

        has_measurement = self.measurement is not None
        if self.status in (ResultStatus.AVAILABLE, ResultStatus.INCOMPLETE):
            if not has_measurement:
                raise ResultError(f"A {self.status.value} result needs a measurement.")
        elif has_measurement:
            # A gap in the data must never be able to carry a number that looks like a finding.
            raise ResultError(f"A {self.status.value} result can't carry a measurement.")
        if self.status is ResultStatus.INCOMPLETE and not self.caveats:
            raise ResultError("An incomplete result must say why it's incomplete.")
        if self.status is not ResultStatus.TEMPORARILY_UNAVAILABLE and not self.sources:
            raise ResultError(f"A {self.status.value} result must credit its sources.")


@dataclass(frozen=True)
class Assessment:
    """Everything shown for one location."""

    region_id: str | None
    region_name: str | None
    results: tuple[PerilResult, ...]
    not_covered: tuple[str, ...] = ()
    message: str | None = None
    disclaimer: str = DISCLAIMER

    @property
    def available_here(self) -> bool:
        return self.region_id is not None
