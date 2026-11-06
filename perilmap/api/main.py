"""The app as it runs in production, with the real regions connected."""

from __future__ import annotations

from perilmap.api.app import create_app
from perilmap.api.settings import Settings
from perilmap.core.assessment import RegionRegistry
from perilmap.regions.london.region import LondonRegion

settings = Settings.from_env()


def build_registry() -> RegionRegistry:
    return RegionRegistry([LondonRegion(settings.data_dir)])


app = create_app(build_registry, settings)
