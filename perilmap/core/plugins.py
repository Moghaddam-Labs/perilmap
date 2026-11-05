"""The shared interface. Adding a region or peril means adding a plug-in, not changing the core."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from perilmap.core.models import Location, PerilResult


class PerilPlugin(ABC):
    """Answers one question about one peril, such as river flooding."""

    @property
    @abstractmethod
    def peril_id(self) -> str:
        """A stable identifier, unique within its region."""

    @abstractmethod
    def assess(self, location: Location) -> PerilResult:
        """Return this peril's result for a location inside the region."""


class RegionPlugin(ABC):
    """Supplies a region's area, perils and known gaps."""

    @property
    @abstractmethod
    def region_id(self) -> str:
        """A stable identifier, unique across all regions."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The name shown to people."""

    @property
    @abstractmethod
    def perils(self) -> Sequence[PerilPlugin]:
        """The perils checked here, in the order they should be shown."""

    @property
    @abstractmethod
    def not_covered(self) -> Sequence[str]:
        """Risks this region doesn't check, stated plainly so a result isn't read as complete."""

    @abstractmethod
    def covers(self, location: Location) -> bool:
        """Say whether a location is inside this region."""
