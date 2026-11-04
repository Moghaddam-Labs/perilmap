"""Settings for the flood data test."""

from __future__ import annotations

from dataclasses import dataclass

# Greater London's bounding box in British National Grid metres (EPSG:27700).
LONDON_BBOX_BNG: tuple[int, int, int, int] = (503_000, 155_000, 562_000, 201_500)
BNG_CRS = "EPSG:27700"

# Each band has its own bit, so one grid square can hold several bands. Thin bands
# between others would otherwise vanish, which put some distances over 700 m out.
BAND_BITS: dict[str, int] = {"Very Low": 1, "Low": 2, "Medium": 4, "High": 8}
BAND_ORDER: tuple[str, ...] = ("High", "Medium", "Low", "Very Low")

GRID_RESOLUTION_METRES = 5
READ_BATCH_SIZE = 500
COVERAGE_BLOCK_METRES = 5_000
DEFAULT_RADIUS_METRES = 1_000

# Targets the test reports against.
TARGET_GRID_MB = 50
TARGET_LOOKUP_MS = 100
TARGET_DISTANCE_ERROR_METRES = 10

# Random points used to check the grid against the original shapes.
ACCURACY_SAMPLE_POINTS = 250
ACCURACY_SAMPLE_SEED = 7


@dataclass(frozen=True)
class FloodSource:
    """One Environment Agency flood product and where to find its bands."""

    key: str
    label: str
    default_layer: str
    band_fields: tuple[str, ...] = ("Risk_band", "Risk_band3")


FLOOD_SOURCES: dict[str, FloodSource] = {
    "rivers_and_sea": FloodSource("rivers_and_sea", "Rivers and sea", "RoFRS_4band"),
    "surface_water": FloodSource("surface_water", "Surface water", "RoFSW"),
}
