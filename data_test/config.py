"""Settings for the flood data test."""

from __future__ import annotations

from dataclasses import dataclass

# Greater London's bounding box in British National Grid metres (EPSG:27700).
# A box is slightly larger than London itself, so size results err on the high side.
LONDON_BBOX_BNG: tuple[int, int, int, int] = (503_000, 155_000, 562_000, 201_500)

BNG_SRID = 27_700
BAND_ORDER: tuple[str, ...] = ("High", "Medium", "Low", "Very Low")

# Supabase's free plan allows 500 MB. We stop early to leave room for indexes
# and to avoid the project being switched to read-only.
DEFAULT_MAX_DB_MB = 400
SUPABASE_FREE_LIMIT_MB = 500

# Targets the test reports against.
TARGET_DB_MB = 400
TARGET_QUERY_MS = 500

DEFAULT_RADIUS_METRES = 1_000
DEFAULT_SUBDIVIDE_VERTICES = 256
DEFAULT_BATCH_SIZE = 5_000


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
