"""Settings for the flood data test."""

from __future__ import annotations

from perilmap.regions.london.settings import (
    BAND_BITS,
    BAND_ORDER,
    BNG_CRS,
    COVERAGE_SQUARE_METRES,
    DEFAULT_RADIUS_METRES,
    FLOOD_SOURCES,
    GRID_RESOLUTION_METRES,
    LONDON_BBOX_BNG,
    FloodSource,
)

__all__ = [
    "ACCURACY_SAMPLE_POINTS",
    "ACCURACY_SAMPLE_SEED",
    "BAND_BITS",
    "BAND_ORDER",
    "BNG_CRS",
    "COVERAGE_BLOCK_METRES",
    "COVERAGE_SQUARE_METRES",
    "DEFAULT_RADIUS_METRES",
    "FLOOD_SOURCES",
    "GRID_RESOLUTION_METRES",
    "LONDON_BBOX_BNG",
    "READ_BATCH_SIZE",
    "TARGET_DISTANCE_ERROR_METRES",
    "TARGET_GRID_MB",
    "TARGET_HEAT_FILE_MB",
    "TARGET_LOOKUP_MS",
    "FloodSource",
]

READ_BATCH_SIZE = 500
COVERAGE_BLOCK_METRES = 5_000

# Targets the test reports against.
TARGET_GRID_MB = 50
TARGET_HEAT_FILE_MB = 10
TARGET_LOOKUP_MS = 100
TARGET_DISTANCE_ERROR_METRES = 10

# Random points used to check the grid against the original shapes.
ACCURACY_SAMPLE_POINTS = 250
ACCURACY_SAMPLE_SEED = 7
