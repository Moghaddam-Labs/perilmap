from __future__ import annotations

import logging

import pytest

from perilmap.core.assessment import RegionRegistry, RegistryError, assess, assess_peril
from perilmap.core.models import DISCLAIMER, NOT_AVAILABLE_HERE, Location, ResultStatus
from tests.core.fake_region import BrokenPeril, FakeRegion, LavaPeril, WarmthPeril, WrongIdPeril

INSIDE = Location(15.123456, 30.654321)
OUTSIDE = Location(-40.0, 30.0)


def test_inside_a_region_gets_each_peril_in_order() -> None:
    assessment = assess(INSIDE, RegionRegistry([FakeRegion()]))
    assert assessment.available_here
    assert assessment.region_id == "testland"
    assert assessment.region_name == "Testland"
    assert [result.peril_id for result in assessment.results] == ["lava", "warmth"]


def test_assessment_states_what_is_not_covered_and_the_disclaimer() -> None:
    assessment = assess(INSIDE, RegionRegistry([FakeRegion()]))
    assert assessment.not_covered == ("Meteor strikes",)
    assert assessment.disclaimer == DISCLAIMER


def test_outside_every_region_says_not_available() -> None:
    assessment = assess(OUTSIDE, RegionRegistry([FakeRegion()]))
    assert not assessment.available_here
    assert assessment.results == ()
    assert assessment.message == NOT_AVAILABLE_HERE
    assert assessment.disclaimer == DISCLAIMER


def test_with_no_regions_nothing_is_available() -> None:
    assert not assess(INSIDE, RegionRegistry()).available_here


def test_adding_a_region_needs_no_core_change() -> None:
    registry = RegionRegistry([FakeRegion()])
    assert not assess(OUTSIDE, registry).available_here
    registry.add(FakeRegion(region_id="southland", latitudes=(-50.0, -30.0)))
    assert assess(OUTSIDE, registry).region_id == "southland"


def test_first_region_wins_where_two_overlap() -> None:
    registry = RegionRegistry([FakeRegion(region_id="first"), FakeRegion(region_id="second")])
    assert assess(INSIDE, registry).region_id == "first"


def test_duplicate_region_is_refused() -> None:
    with pytest.raises(RegistryError, match="already"):
        RegionRegistry([FakeRegion(), FakeRegion()])


def test_region_without_perils_is_refused() -> None:
    with pytest.raises(RegistryError, match="no perils"):
        RegionRegistry([FakeRegion(perils=())])


def test_repeated_peril_is_refused() -> None:
    with pytest.raises(RegistryError, match="repeats"):
        RegionRegistry([FakeRegion(perils=(LavaPeril(), LavaPeril()))])


def test_one_failed_peril_does_not_take_down_the_others() -> None:
    region = FakeRegion(perils=(LavaPeril(), BrokenPeril(), WarmthPeril()))
    results = assess(INSIDE, RegionRegistry([region])).results
    assert [result.status for result in results] == [
        ResultStatus.AVAILABLE,
        ResultStatus.TEMPORARILY_UNAVAILABLE,
        ResultStatus.AVAILABLE,
    ]


def test_a_failed_check_never_looks_like_low_risk() -> None:
    result = assess_peril(BrokenPeril(), INSIDE)
    assert result.measurement is None
    assert "says nothing about the risk" in result.what_this_means
    assert result.what_you_can_do == ("Try again shortly.",)


def test_failures_never_log_the_location(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG):
        assess_peril(BrokenPeril(), INSIDE)
    assert "broken" in caplog.text and "RuntimeError" in caplog.text
    assert "15.123" not in caplog.text and "30.654" not in caplog.text
    assert all(record.exc_info is None for record in caplog.records)


def test_a_peril_returning_the_wrong_result_is_treated_as_failed() -> None:
    result = assess_peril(WrongIdPeril(), INSIDE)
    assert result.peril_id == "asked_for"
    assert result.status is ResultStatus.TEMPORARILY_UNAVAILABLE
