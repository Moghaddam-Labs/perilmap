from __future__ import annotations

from pathlib import Path

import pytest
import shapely

from data_test.config import FLOOD_SOURCES
from data_test.coverage import Coverage, CoverageStatus, NoDataCheck, NoDataSquare
from data_test.grid import GridBuild, build_grid, grid_path
from data_test.measure import (
    Location,
    LocationResult,
    build_report,
    compare_with_shapes,
    expectation_met,
    format_nearest,
    format_result,
    load_source_manifest,
    read_locations,
    run,
)
from tests.helpers import square, write_flood_file


def test_location_list_has_twenty_valid_places() -> None:
    locations = read_locations()
    assert len(locations) == 20
    assert len({location.name for location in locations}) == 20
    assert {location.expectation for location in locations} == {
        "near_river",
        "away_from_river",
        "outside_area",
    }


def test_location_converts_to_british_national_grid() -> None:
    x, y = Location("Charing Cross", 51.5074, -0.1278, "near_river").to_bng()
    assert x == pytest.approx(530_000, abs=500)
    assert y == pytest.approx(180_400, abs=500)


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


@pytest.mark.parametrize(
    ("bands", "text"),
    [
        ({"Low": 1234.4, "High": 0.0}, "High on zone, Low 1,230 m"),
        ({"Medium": 6.0}, "Medium under 10 m"),
        ({}, "None within 1,000 m"),
        (None, "None within 1,000 m"),
    ],
)
def test_format_nearest(bands: dict[str, float] | None, text: str) -> None:
    assert format_nearest(bands, 1000) == text


@pytest.mark.parametrize(
    ("status", "text"),
    [
        (CoverageStatus.OUTSIDE, "Not available here yet"),
        (CoverageStatus.NO_DATA, "No data"),
        (CoverageStatus.NEAR_GAP, "Low 50 m (may be incomplete)"),
        (CoverageStatus.COVERED, "Low 50 m"),
    ],
)
def test_format_result_never_lets_a_gap_look_safe(status: CoverageStatus, text: str) -> None:
    assert format_result(status, {"Low": 50.0}, 1000) == text


def test_comparison_collects_errors_and_mismatches() -> None:
    exact = {"A": {"High": 100.0, "Low": 50.0}, "B": {"Medium": 995.0}}
    grid = {"A": {"High": 103.0}, "B": {}}
    errors, mismatches = compare_with_shapes(grid, exact, radius=1000, resolution=5)
    assert errors == [3.0]
    assert mismatches == 1  # Low was missed. B's zone sits right at the search edge.


def make_build(grid_mb: float = 1.0, grid_area: float = 10.0) -> GridBuild:
    return GridBuild(
        source="rivers_and_sea",
        resolution_metres=5,
        grid_mb=grid_mb,
        build_seconds=1.0,
        shapes=10,
        duplicate_shapes=2,
        shape_km2={"Low": 10.0},
        grid_km2={"Low": grid_area},
        coverage=["#."],
        built_at="2026-11-04T00:00:00+00:00",
    )


def make_result(name: str, expectation: str, ms: float = 4.0) -> LocationResult:
    return LocationResult(
        Location(name, 51.5, -0.1, expectation),
        True,
        {"rivers_and_sea": {"Low": 50.0}},
        {"rivers_and_sea": CoverageStatus.COVERED},
        [ms],
    )


def test_report_passes_within_targets() -> None:
    report = build_report(
        {"rivers_and_sea": make_build()},
        [make_result("Thamesmead", "near_river")],
        {"rivers_and_sea": ([2.0], 0)},
        1000,
    )
    assert "| Grid files | 1.0 MB | Up to 50 MB | Pass |" in report
    assert "| Slowest lookup | 4.0 ms | Up to 100 ms | Pass |" in report
    assert "| Largest distance error | 2.0 m | Up to 10 m | Pass |" in report
    assert "| Zones missed or invented | 0 of 1 checked | None | Pass |" in report
    assert "| Thamesmead | Near river | Low 50 m | Not built | OK |" in report
    assert "```text\n#.\n```" in report


def test_report_fails_when_targets_are_missed() -> None:
    report = build_report(
        {"rivers_and_sea": make_build(grid_mb=80.0)},
        [make_result("Highgate", "away_from_river", ms=300.0)],
        {"rivers_and_sea": ([40.0], 1)},
        1000,
    )
    assert "| 80.0 MB | Up to 50 MB | Fail |" in report
    assert "| 300.0 ms | Up to 100 ms | Fail |" in report
    assert "| 40.0 m | Up to 10 m | Fail |" in report
    assert "| 1 of 2 checked | None | Fail |" in report
    assert "| Highgate | Away from river | Low 50 m | Not built | Review |" in report


def test_full_run_from_download_to_report(tmp_path: Path) -> None:
    source = FLOOD_SOURCES["rivers_and_sea"]
    download = write_flood_file(
        tmp_path / "flood.gpkg",
        [("Low", square(530_000, 180_000)), ("High", square(545_000, 180_000))],
    )
    build_grid([download], source, grid_path(tmp_path, source, 5))
    report = run(tmp_path, {"rivers_and_sea": [download]})
    assert "Largest distance error" in report and "| Fail |" not in report
    assert "Rivers and sea" in report
    assert (
        "| Oxford | Outside area | Not available here yet | Not available here yet | OK |" in report
    )
    assert "| Not built |" in report


def test_report_flags_a_stale_no_data_list() -> None:
    check = NoDataCheck(False, 100, 2, 100.0, 1.5, 20.0)
    report = build_report(
        {"surface_water": make_build()},
        [make_result("Thamesmead", "near_river")],
        {"surface_water": ([1.0], 0)},
        1000,
        {"surface_water": check},
    )
    assert "| Surface water No data list matches the grid | No | Yes | Fail |" in report
    assert "2 of 100 squares are blank" in report


def test_stale_no_data_list_fails_a_full_run(tmp_path: Path) -> None:
    source = FLOOD_SOURCES["surface_water"]
    download = write_flood_file(
        tmp_path / "flood.gpkg", [("High", square(530_000, 180_000))], layer="RoFSW"
    )
    build_grid([download], source, grid_path(tmp_path, source, 5))
    london = shapely.box(529_000, 179_000, 532_000, 182_000)
    stale = Coverage(london, [NoDataSquare("surface_water", 530_000, 180_000, 1.0)])
    report = run(tmp_path, {"surface_water": [download]}, coverage=stale)
    assert "No data list matches the grid | No | Yes | Fail" in report


def test_run_without_grids_explains_what_to_do(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="build command"):
        run(tmp_path, {})


def test_missing_manifest_means_no_comparison(tmp_path: Path) -> None:
    assert load_source_manifest(tmp_path / "sources.json") == {}
