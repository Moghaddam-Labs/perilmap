from __future__ import annotations

import pytest

from data_test.measure import (
    Location,
    LocationResult,
    Sizes,
    build_report,
    expectation_met,
    format_nearest,
    read_locations,
)


def test_location_list_has_twenty_valid_places() -> None:
    locations = read_locations()
    assert len(locations) == 20
    assert len({location.name for location in locations}) == 20
    assert {location.expectation for location in locations} == {
        "near_river",
        "away_from_river",
        "outside_area",
    }
    for location in locations:
        assert 50 < location.latitude < 52
        assert -2 < location.longitude < 1


@pytest.mark.parametrize(
    ("expectation", "in_area", "nearest", "passed"),
    [
        ("near_river", True, {"rivers_and_sea": {"Low": 0.0}}, True),
        ("near_river", True, {}, False),
        ("away_from_river", True, {}, True),
        ("away_from_river", True, {"rivers_and_sea": {"Very Low": 900.0}}, True),
        ("away_from_river", True, {"rivers_and_sea": {"High": 10.0}}, False),
        ("away_from_river", True, {"surface_water": {"High": 0.0}}, True),
        ("outside_area", False, {}, True),
        ("outside_area", True, {}, False),
    ],
)
def test_expectations(
    expectation: str, in_area: bool, nearest: dict[str, dict[str, float]], passed: bool
) -> None:
    assert expectation_met(expectation, in_area, nearest) is passed


def test_unknown_expectation_is_an_error() -> None:
    with pytest.raises(ValueError):
        expectation_met("somewhere", True, {})


def test_format_nearest_orders_bands_and_marks_zone_hits() -> None:
    text = format_nearest({"Low": 1234.4, "High": 0.0}, 1000)
    assert text == "High on zone, Low 1,234 m"


def test_format_nearest_states_the_radius_when_nothing_is_found() -> None:
    assert format_nearest({}, 1000) == "None within 1,000 m"


def make_result(name: str, expectation: str, server_ms: float) -> LocationResult:
    return LocationResult(
        Location(name, 51.5, -0.1, expectation),
        True,
        {"rivers_and_sea": {"Low": 5.0}},
        server_ms + 20,
        server_ms,
    )


def test_report_passes_within_targets() -> None:
    report = build_report(
        Sizes(120.0, 90.0, 20.0, {"rivers_and_sea": 1000}),
        [make_result("Thamesmead", "near_river", 40.0)],
        1000,
    )
    assert "| Database size | 120 MB | Up to 400 MB (free limit 500 MB) | Pass |" in report
    assert "| Slowest lookup on the database | 40 ms | Up to 500 ms | Pass |" in report
    assert "| Thamesmead | Near river | Low 5 m | None within 1,000 m | OK |" in report


def test_report_fails_when_too_big_slow_or_unexpected() -> None:
    report = build_report(
        Sizes(450.0, 400.0, 40.0, {}),
        [make_result("Highgate", "away_from_river", 900.0)],
        1000,
    )
    assert "| 450 MB |" in report and "| Fail |" in report
    assert "| 900 ms | Up to 500 ms | Fail |" in report
    assert "| Highgate | Away from river | Low 5 m | None within 1,000 m | Review |" in report
