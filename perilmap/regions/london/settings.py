"""Settings for London's flood and heat data."""

from __future__ import annotations

from dataclasses import dataclass

# Greater London's bounding box in British National Grid metres (EPSG:27700), plus a margin
# wider than the search radius. Corners sit on whole kilometres, so squares line up.
LONDON_BBOX_BNG: tuple[int, int, int, int] = (502_000, 154_000, 563_000, 202_000)
BNG_CRS = "EPSG:27700"

# Each band has its own bit, so one grid square can hold several bands. Thin bands
# between others would otherwise vanish, which put some distances over 700 m out.
BAND_BITS: dict[str, int] = {"Very Low": 1, "Low": 2, "Medium": 4, "High": 8}
BAND_ORDER: tuple[str, ...] = ("High", "Medium", "Low", "Very Low")

GRID_RESOLUTION_METRES = 5
COVERAGE_SQUARE_METRES = 1_000
DEFAULT_RADIUS_METRES = 1_000


@dataclass(frozen=True)
class FloodSource:
    """One Environment Agency flood product and where to find its bands."""

    key: str
    label: str
    default_layer: str
    # The bands this product maps, highest risk first.
    bands: tuple[str, ...] = BAND_ORDER
    # True when one download covered all of London, so a blank area means no flood zone.
    # False when many separate downloads were used, so a blank area could be a gap.
    fully_downloaded: bool = False
    band_fields: tuple[str, ...] = ("Risk_band", "Risk_band3")


FLOOD_SOURCES: dict[str, FloodSource] = {
    "rivers_and_sea": FloodSource(
        "rivers_and_sea", "Rivers and sea", "RoFRS_4band", fully_downloaded=True
    ),
    "surface_water": FloodSource(
        "surface_water", "Surface water", "RoFSW", bands=("High", "Medium", "Low")
    ),
}


def grid_filename(source: FloodSource, resolution: int = GRID_RESOLUTION_METRES) -> str:
    return f"{source.key}_{resolution}m.tif"
