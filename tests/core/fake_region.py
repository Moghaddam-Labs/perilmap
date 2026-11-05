"""An invented region. If the core works with this, it isn't tied to any real place."""

from __future__ import annotations

from collections.abc import Sequence

from perilmap.core.models import (
    AreaComparison,
    DataSource,
    Location,
    NearestZones,
    PerilResult,
    ResultStatus,
    ZoneDistance,
)
from perilmap.core.plugins import PerilPlugin, RegionPlugin

FAKE_SOURCE = DataSource(
    name="Invented hazard map",
    publisher="Testland Survey",
    licence="Test licence",
    url="https://example.com/data",
    attribution="Testland Survey",
    last_updated="January 2026",
    resolution="10 m grid",
)


def make_result(peril_id: str = "lava", **overrides: object) -> PerilResult:
    values: dict[str, object] = {
        "peril_id": peril_id,
        "title": "Lava flow",
        "status": ResultStatus.AVAILABLE,
        "summary": "A High zone is 120 m away.",
        "what_this_means": "Lava has reached this distance before.",
        "how_sure": "Mapped at 10 m, for an area of land rather than one home.",
        "what_you_can_do": ("Read the local lava plan.",),
        "sources": (FAKE_SOURCE,),
        "measurement": NearestZones((ZoneDistance("High", 120.0),), 1_000),
    }
    return PerilResult(**{**values, **overrides})


COMPARISON = AreaComparison(
    value=21.0,
    unit="°C",
    group="warmest fifth",
    range_low=20.0,
    range_high=22.0,
    calculation_note="The range and group are our own calculation.",
)


class LavaPeril(PerilPlugin):
    peril_id = "lava"

    def assess(self, location: Location) -> PerilResult:
        return make_result()


class WarmthPeril(PerilPlugin):
    peril_id = "warmth"

    def assess(self, location: Location) -> PerilResult:
        return make_result(
            "warmth", title="Warmth", measurement=COMPARISON, summary="Warmer than most."
        )


class BrokenPeril(PerilPlugin):
    """Fails in the worst way, with the location in its error message."""

    peril_id = "broken"

    def assess(self, location: Location) -> PerilResult:
        raise RuntimeError(f"Failed at {location.latitude}, {location.longitude}")


class WrongIdPeril(PerilPlugin):
    peril_id = "asked_for"

    def assess(self, location: Location) -> PerilResult:
        return make_result("something_else")


class FakeRegion(RegionPlugin):
    """Covers one box of the map."""

    def __init__(
        self,
        perils: Sequence[PerilPlugin] | None = None,
        region_id: str = "testland",
        latitudes: tuple[float, float] = (10.0, 20.0),
    ) -> None:
        self._perils = (LavaPeril(), WarmthPeril()) if perils is None else perils
        self._region_id = region_id
        self._latitudes = latitudes

    @property
    def region_id(self) -> str:
        return self._region_id

    @property
    def name(self) -> str:
        return "Testland"

    @property
    def perils(self) -> Sequence[PerilPlugin]:
        return self._perils

    @property
    def not_covered(self) -> Sequence[str]:
        return ("Meteor strikes",)

    def covers(self, location: Location) -> bool:
        return self._latitudes[0] <= location.latitude <= self._latitudes[1]
