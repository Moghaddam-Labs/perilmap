from __future__ import annotations

import math
from dataclasses import replace

import pytest

from perilmap.core.models import (
    DISCLAIMER,
    AreaComparison,
    DataSource,
    Link,
    Location,
    NearestZones,
    ResultError,
    ResultStatus,
    ZoneDistance,
)
from tests.core.fake_region import COMPARISON, FAKE_SOURCE, make_result


@pytest.mark.parametrize(
    ("latitude", "longitude"),
    [(91, 0), (-91, 0), (0, 181), (0, -181), (math.nan, 0), (0, math.inf)],
)
def test_impossible_locations_are_refused(latitude: float, longitude: float) -> None:
    with pytest.raises(ValueError):
        Location(latitude, longitude)


def test_location_never_shows_its_coordinates() -> None:
    location = Location(51.123456, -0.654321)
    for text in (repr(location), str(location), f"{location}"):
        assert "51.123" not in text and "0.654" not in text


def test_a_complete_result_is_accepted() -> None:
    assert make_result().status is ResultStatus.AVAILABLE


@pytest.mark.parametrize("field", ["peril_id", "title", "summary", "what_this_means", "how_sure"])
def test_every_explanation_is_required(field: str) -> None:
    with pytest.raises(ResultError, match=field):
        make_result(**{field: "  "})


@pytest.mark.parametrize("steps", [(), ("",), ("Do this.", " ")])
def test_a_result_must_say_what_to_do_next(steps: tuple[str, ...]) -> None:
    with pytest.raises(ResultError, match="do next"):
        make_result(what_you_can_do=steps)


@pytest.mark.parametrize("status", [ResultStatus.AVAILABLE, ResultStatus.INCOMPLETE])
def test_a_finding_needs_a_measurement(status: ResultStatus) -> None:
    with pytest.raises(ResultError, match="needs a measurement"):
        make_result(status=status, measurement=None, caveats=("Near a gap.",))


@pytest.mark.parametrize(
    "status",
    [
        ResultStatus.NO_DATA,
        ResultStatus.NOT_AVAILABLE_HERE,
        ResultStatus.GENERAL_INFORMATION,
        ResultStatus.TEMPORARILY_UNAVAILABLE,
    ],
)
def test_a_gap_can_never_carry_a_number(status: ResultStatus) -> None:
    with pytest.raises(ResultError, match="can't carry a measurement"):
        make_result(status=status)


def test_an_incomplete_result_must_say_why() -> None:
    with pytest.raises(ResultError, match="why"):
        make_result(status=ResultStatus.INCOMPLETE)
    assert make_result(status=ResultStatus.INCOMPLETE, caveats=("Near a gap.",))


@pytest.mark.parametrize(
    "status",
    [
        ResultStatus.AVAILABLE,
        ResultStatus.NO_DATA,
        ResultStatus.GENERAL_INFORMATION,
    ],
)
def test_results_must_credit_their_sources(status: ResultStatus) -> None:
    measurement = make_result().measurement if status is ResultStatus.AVAILABLE else None
    with pytest.raises(ResultError, match="credit"):
        make_result(status=status, measurement=measurement, sources=())


def test_a_general_information_card_needs_no_measurement() -> None:
    card = make_result(status=ResultStatus.GENERAL_INFORMATION, measurement=None)
    assert card.measurement is None


@pytest.mark.parametrize(
    "field",
    ["name", "publisher", "licence", "url", "attribution", "last_updated", "resolution"],
)
def test_sources_must_state_freshness_resolution_and_credit(field: str) -> None:
    with pytest.raises(ResultError, match=field):
        replace(FAKE_SOURCE, **{field: ""})
    assert isinstance(FAKE_SOURCE, DataSource)


def test_links_must_use_https_and_have_a_label() -> None:
    assert Link("Read more", "https://example.com").url
    with pytest.raises(ResultError, match="https"):
        Link("Read more", "http://example.com")
    with pytest.raises(ResultError, match="label"):
        Link(" ", "https://example.com")


def test_a_distance_cannot_be_negative() -> None:
    with pytest.raises(ResultError, match="negative"):
        ZoneDistance("High", -1, "Label")


def test_none_means_no_zone_found_and_zero_means_on_a_zone() -> None:
    assert ZoneDistance("Low", None, "None within 1,000 m").metres is None
    assert ZoneDistance("Low", 0, "On the zone").metres == 0


def test_nearest_zones_must_list_bands_and_a_radius() -> None:
    with pytest.raises(ResultError, match="every band"):
        NearestZones((), 1_000)
    with pytest.raises(ResultError, match="radius"):
        NearestZones((ZoneDistance("Low", 5, "Label"),), 0)


def test_comparison_value_must_sit_inside_its_range() -> None:
    with pytest.raises(ResultError, match="range"):
        replace(COMPARISON, value=30.0)


def test_comparison_must_label_our_own_calculation() -> None:
    with pytest.raises(ResultError, match="own calculation"):
        replace(COMPARISON, calculation_note="")
    assert isinstance(COMPARISON, AreaComparison)


def test_disclaimer_covers_quote_survey_and_advice() -> None:
    for word in ("insurance quote", "survey", "financial advice"):
        assert word in DISCLAIMER
