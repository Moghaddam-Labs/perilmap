"""Find the region for a location, then gather a result from each of its perils."""

from __future__ import annotations

import logging
from collections.abc import Iterable

from perilmap.core.models import (
    NOT_AVAILABLE_HERE,
    Assessment,
    Location,
    PerilResult,
    ResultStatus,
)
from perilmap.core.plugins import PerilPlugin, RegionPlugin

logger = logging.getLogger(__name__)


class RegistryError(ValueError):
    """Regions or perils were set up incorrectly."""


class RegionRegistry:
    """Holds the available regions. Where two overlap, the first one added is used."""

    def __init__(self, regions: Iterable[RegionPlugin] = ()) -> None:
        self._regions: list[RegionPlugin] = []
        for region in regions:
            self.add(region)

    def add(self, region: RegionPlugin) -> None:
        if any(existing.region_id == region.region_id for existing in self._regions):
            raise RegistryError(f"Region {region.region_id} is already added.")
        peril_ids = [peril.peril_id for peril in region.perils]
        if not peril_ids:
            raise RegistryError(f"Region {region.region_id} has no perils.")
        if len(set(peril_ids)) != len(peril_ids):
            raise RegistryError(f"Region {region.region_id} repeats a peril.")
        self._regions.append(region)

    def region_for(self, location: Location) -> RegionPlugin | None:
        return next((region for region in self._regions if region.covers(location)), None)


def temporarily_unavailable(peril: PerilPlugin) -> PerilResult:
    """Say plainly that a check failed, so a failure can't look like low risk."""
    return PerilResult(
        peril_id=peril.peril_id,
        title="This check is unavailable",
        status=ResultStatus.TEMPORARILY_UNAVAILABLE,
        summary="We couldn't complete this check.",
        what_this_means="This says nothing about the risk here, either way.",
        how_sure="No result was produced.",
        what_you_can_do=("Try again shortly.",),
    )


def assess_peril(peril: PerilPlugin, location: Location) -> PerilResult:
    """Run one peril, keeping a failure in one check from taking down the others."""
    try:
        result = peril.assess(location)
        if result.peril_id != peril.peril_id:
            raise RegistryError(f"Peril {peril.peril_id} returned another peril's result.")
        return result
    except Exception as error:
        # Only the error's type is logged, because its message or traceback may hold the location.
        logger.error("Peril %s failed with %s", peril.peril_id, type(error).__name__)
        return temporarily_unavailable(peril)


def assess(location: Location, registry: RegionRegistry) -> Assessment:
    """Produce the full assessment for a location."""
    region = registry.region_for(location)
    if region is None:
        return Assessment(
            region_id=None,
            region_name=None,
            results=(),
            message=NOT_AVAILABLE_HERE,
        )
    return Assessment(
        region_id=region.region_id,
        region_name=region.name,
        results=tuple(assess_peril(peril, location) for peril in region.perils),
        not_covered=tuple(region.not_covered),
    )
