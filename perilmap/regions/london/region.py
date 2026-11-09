"""The London plug-in: its area, perils and data files."""

from __future__ import annotations

import threading
from collections.abc import Sequence
from pathlib import Path

import rasterio
import shapely
from rasterio.warp import transform as reproject

from perilmap.core.models import (
    AreaComparison,
    Location,
    NearestZones,
    PerilResult,
    Polygon,
    ResultStatus,
    ZoneDistance,
    ZoneMap,
    ZoneShape,
)
from perilmap.core.plugins import PerilPlugin, RegionPlugin
from perilmap.regions.london import wording
from perilmap.regions.london.coverage import Coverage, CoverageStatus, square_box
from perilmap.regions.london.grids import nearest_in_patch, read_patch, zone_outlines
from perilmap.regions.london.heat import HEAT_FILENAME, HeatLookup
from perilmap.regions.london.projection import LocalProjection
from perilmap.regions.london.settings import (
    BNG_CRS,
    DEFAULT_RADIUS_METRES,
    FLOOD_SOURCES,
    FloodSource,
    grid_filename,
)

# The fitted conversion covers a little more than the search area, so every corner is inside it.
PROJECTION_MARGIN_METRES = 50


class LondonDataError(FileNotFoundError):
    """A required data file is missing, which should stop the app from starting."""


def to_bng(location: Location) -> tuple[float, float]:
    xs, ys = reproject("EPSG:4326", BNG_CRS, [location.longitude], [location.latitude])
    return xs[0], ys[0]


def zone_distance(band: str, metres: float | None, radius: float) -> ZoneDistance:
    """Round a distance and describe it, so it doesn't claim more accuracy than it has."""
    if metres is None:
        return ZoneDistance(band, None, f"None within {radius:,.0f} m")
    if metres == 0:
        return ZoneDistance(band, 0.0, "On the zone, or within about 5 m")
    if metres < 10:
        return ZoneDistance(band, 10.0, "Under 10 m")
    rounded = float(round(metres, -1))
    return ZoneDistance(band, rounded, f"About {rounded:,.0f} m")


def flood_summary(label: str, zones: Sequence[ZoneDistance], radius: float) -> str:
    """Lead with the highest band the spot is on, otherwise the closest zone."""
    on_zone = [zone for zone in zones if zone.metres == 0]
    if on_zone:
        return f"This spot is on, or within about 5 m of, a {on_zone[0].band} {label} zone."
    found = [zone for zone in zones if zone.metres is not None]
    if not found:
        return f"There's no mapped {label} zone within {radius:,.0f} m of this spot."
    nearest = min(found, key=lambda zone: zone.metres)
    return f"The nearest mapped {label} zone is {nearest.band}, {nearest.label.lower()} away."


class FloodPeril(PerilPlugin):
    """Distance to the nearest flood zone in each band, for one Environment Agency product."""

    def __init__(
        self,
        source: FloodSource,
        path: Path,
        coverage: Coverage,
        radius: float = DEFAULT_RADIUS_METRES,
    ) -> None:
        self._source = source
        self._coverage = coverage
        self._radius = radius
        self._dataset = rasterio.open(path)
        # One open file can't safely be read by several requests at the same moment.
        self._lock = threading.Lock()
        self._label = source.label.lower()
        self._data_source = (
            wording.RIVERS_AND_SEA_SOURCE
            if source.key == "rivers_and_sea"
            else wording.SURFACE_WATER_SOURCE
        )
        self._meaning = (
            wording.RIVERS_MEANING if source.key == "rivers_and_sea" else wording.SURFACE_MEANING
        )

    @property
    def peril_id(self) -> str:
        return f"flood_{self._source.key}"

    def assess(self, location: Location) -> PerilResult:
        x, y = to_bng(location)
        status = self._coverage.status(self._source, x, y, self._radius)
        title = f"Flooding from {self._label}"
        if status is CoverageStatus.OUTSIDE:
            return self._gap(title, ResultStatus.NOT_AVAILABLE_HERE, "Not available here yet.")
        if status is CoverageStatus.NO_DATA:
            return self._gap(title, ResultStatus.NO_DATA, wording.NO_SURFACE_DATA_SUMMARY)
        with self._lock:
            patch = read_patch(self._dataset, x, y, self._radius)
        nearest = nearest_in_patch(patch)
        zones = tuple(
            zone_distance(band, nearest.get(band), self._radius) for band in self._source.bands
        )
        incomplete = status is CoverageStatus.NEAR_GAP
        return PerilResult(
            peril_id=self.peril_id,
            title=title,
            status=ResultStatus.INCOMPLETE if incomplete else ResultStatus.AVAILABLE,
            summary=flood_summary(self._label, zones, self._radius),
            what_this_means=self._meaning,
            how_sure=wording.FLOOD_HOW_SURE,
            what_you_can_do=wording.FLOOD_ACTIONS,
            sources=(self._data_source,),
            measurement=NearestZones(zones, self._radius),
            caveats=(wording.INCOMPLETE_CAVEAT,) if incomplete else (),
            links=wording.FLOOD_LINKS,
        )

    def zone_map(self, location: Location) -> ZoneMap | None:
        """Trace the same squares the distances are measured from, plus any areas with no data."""
        x, y = to_bng(location)
        status = self._coverage.status(self._source, x, y, self._radius)
        if status is CoverageStatus.OUTSIDE:
            return None
        with self._lock:
            patch = read_patch(self._dataset, x, y, self._radius)
        projection = LocalProjection(x, y, self._radius + PROJECTION_MARGIN_METRES)
        outlines = zone_outlines(patch, self._source.bands)
        shapes = tuple(
            ZoneShape(band, projection.polygons(outlines[band]))
            for band in self._source.bands
            if band in outlines
        )
        gaps = () if status is CoverageStatus.COVERED else self._no_data_areas(x, y, projection)
        return ZoneMap(self._radius, shapes, gaps)

    def _no_data_areas(
        self, x: float, y: float, projection: LocalProjection
    ) -> tuple[Polygon, ...]:
        """The parts of the search area known to have no data for this product."""
        squares = self._coverage.gap_squares(self._source.key)
        if not squares:
            return ()
        search_area = shapely.Point(x, y).buffer(self._radius, quad_segs=16)
        blank = shapely.union_all([square_box(s.easting, s.northing) for s in squares])
        inside = shapely.intersection(blank, search_area)
        return () if inside.is_empty else projection.polygons(inside)

    def _gap(self, title: str, status: ResultStatus, summary: str) -> PerilResult:
        return PerilResult(
            peril_id=self.peril_id,
            title=title,
            status=status,
            summary=summary,
            what_this_means=wording.NO_SURFACE_DATA_MEANING,
            how_sure=wording.NO_DATA_HOW_SURE,
            what_you_can_do=wording.FLOOD_ACTIONS,
            sources=(self._data_source,),
            links=wording.FLOOD_LINKS,
        )


class HeatPeril(PerilPlugin):
    """How an area's modelled summer temperature compares across London."""

    peril_id = "heat"

    def __init__(self, path: Path) -> None:
        self._lookup = HeatLookup(path)

    def assess(self, location: Location) -> PerilResult:
        title = "Summer temperature"
        result = self._lookup.find(*to_bng(location))
        if result is None:
            return PerilResult(
                peril_id=self.peril_id,
                title=title,
                status=ResultStatus.NO_DATA,
                summary=wording.NO_HEAT_DATA_SUMMARY,
                what_this_means=wording.NO_HEAT_DATA_MEANING,
                how_sure=wording.NO_DATA_HOW_SURE,
                what_you_can_do=wording.HEAT_ACTIONS,
                sources=(wording.HEAT_SOURCE,),
                links=wording.HEAT_LINKS,
            )
        build = self._lookup.build
        low, high = round(build.min_c, 1), round(build.max_c, 1)
        value = round(result.air_temp_c, 1)
        return PerilResult(
            peril_id=self.peril_id,
            title=title,
            status=ResultStatus.AVAILABLE,
            summary=(
                f"{value:.1f} °C, among the {result.group} of London's neighbourhoods. "
                f"London's range is {low:.1f} to {high:.1f} °C."
            ),
            what_this_means=f"{wording.HEAT_DESCRIPTION}. {wording.HEAT_EXPLANATION}",
            how_sure=wording.HEAT_HOW_SURE,
            what_you_can_do=wording.HEAT_ACTIONS,
            sources=(wording.HEAT_SOURCE,),
            measurement=AreaComparison(
                value=value,
                unit="°C",
                group=result.group,
                range_low=low,
                range_high=high,
                calculation_note=wording.HEAT_CALCULATION_NOTE,
            ),
            links=wording.HEAT_LINKS,
        )


class SubsidencePeril(PerilPlugin):
    """A London-wide explainer. The free data isn't suitable for a result at any one location."""

    peril_id = "subsidence"

    def assess(self, location: Location) -> PerilResult:
        return PerilResult(
            peril_id=self.peril_id,
            title="Clay subsidence",
            status=ResultStatus.GENERAL_INFORMATION,
            summary=wording.SUBSIDENCE_SUMMARY,
            what_this_means=wording.SUBSIDENCE_MEANING,
            how_sure=wording.SUBSIDENCE_HOW_SURE,
            what_you_can_do=wording.SUBSIDENCE_ACTIONS,
            sources=(wording.SUBSIDENCE_SOURCE,),
            links=wording.SUBSIDENCE_LINKS,
        )


class LondonRegion(RegionPlugin):
    """Greater London, using the data files built by the data test."""

    region_id = "london"
    name = "Greater London"
    not_covered = wording.NOT_COVERED

    def __init__(self, data_dir: Path, coverage: Coverage | None = None) -> None:
        required = [
            *(data_dir / grid_filename(source) for source in FLOOD_SOURCES.values()),
            data_dir / HEAT_FILENAME,
        ]
        missing = [path.name for path in required if not path.exists()]
        if missing:
            raise LondonDataError(f"Missing data files: {', '.join(missing)}.")
        self._coverage = coverage or Coverage.load()
        self._perils: tuple[PerilPlugin, ...] = (
            *(
                FloodPeril(source, data_dir / grid_filename(source), self._coverage)
                for source in FLOOD_SOURCES.values()
            ),
            HeatPeril(data_dir / HEAT_FILENAME),
            SubsidencePeril(),
        )

    @property
    def perils(self) -> Sequence[PerilPlugin]:
        return self._perils

    def covers(self, location: Location) -> bool:
        return self._coverage.in_london(*to_bng(location))
