from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import rasterio
import shapely
from rasterio.transform import from_origin

from data_test.config import DEFAULT_RADIUS_METRES, FLOOD_SOURCES, LONDON_BBOX_BNG
from perilmap.regions.london.coverage import (
    Coverage,
    CoverageStatus,
    NoDataSquare,
    check_no_data_list,
    find_no_data_squares,
    load_boundary,
    read_no_data_squares,
    write_no_data_squares,
)

RIVERS = FLOOD_SOURCES["rivers_and_sea"]
SURFACE = FLOOD_SOURCES["surface_water"]
LONDON = shapely.box(530_000, 180_000, 540_000, 190_000)


def make_coverage(*squares: NoDataSquare) -> Coverage:
    return Coverage(LONDON, list(squares))


def write_grid(path: Path, marked: list[tuple[int, int]]) -> Path:
    """Write a 5 m grid over LONDON, marking a cell in each listed square."""
    left, top, resolution = 530_000, 190_000, 5
    grid = np.zeros((2_000, 2_000), "uint8")
    for easting, northing in marked:
        grid[(top - northing - 500) // resolution, (easting + 500 - left) // resolution] = 8
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=2_000,
        width=2_000,
        count=1,
        dtype="uint8",
        crs="EPSG:27700",
        transform=from_origin(left, top, resolution, resolution),
    ) as dataset:
        dataset.write(grid, 1)
    return path


def test_real_boundary_matches_greater_london() -> None:
    boundary = load_boundary()
    assert shapely.area(boundary) / 1_000_000 == pytest.approx(1_595, abs=5)
    assert shapely.contains_xy(boundary, 530_000, 180_400)  # Charing Cross
    assert not shapely.contains_xy(boundary, 531_000, 104_000)  # Brighton


def test_grid_area_extends_past_london_by_more_than_the_radius() -> None:
    min_x, min_y, max_x, max_y = shapely.bounds(load_boundary())
    assert LONDON_BBOX_BNG[0] <= min_x - DEFAULT_RADIUS_METRES
    assert LONDON_BBOX_BNG[1] <= min_y - DEFAULT_RADIUS_METRES
    assert LONDON_BBOX_BNG[2] >= max_x + DEFAULT_RADIUS_METRES
    assert LONDON_BBOX_BNG[3] >= max_y + DEFAULT_RADIUS_METRES


def test_outside_london_is_not_available() -> None:
    assert make_coverage().status(SURFACE, 500_000, 180_000, 1_000) is CoverageStatus.OUTSIDE
    assert make_coverage().status(RIVERS, 500_000, 180_000, 1_000) is CoverageStatus.OUTSIDE


def test_blank_square_shows_no_data_never_a_clear_result() -> None:
    coverage = make_coverage(NoDataSquare("surface_water", 535_000, 185_000, 1.0))
    assert coverage.status(SURFACE, 535_500, 185_500, 500) is CoverageStatus.NO_DATA


def test_near_a_blank_square_is_marked_incomplete() -> None:
    coverage = make_coverage(NoDataSquare("surface_water", 535_000, 185_000, 1.0))
    assert coverage.status(SURFACE, 536_400, 185_500, 500) is CoverageStatus.NEAR_GAP


def test_near_the_edge_of_london_is_marked_incomplete() -> None:
    assert make_coverage().status(SURFACE, 530_400, 185_000, 500) is CoverageStatus.NEAR_GAP


def test_well_inside_london_is_covered() -> None:
    assert make_coverage().status(SURFACE, 535_000, 185_000, 500) is CoverageStatus.COVERED


def test_a_full_download_ignores_blank_squares_and_edges() -> None:
    coverage = make_coverage(NoDataSquare("rivers_and_sea", 535_000, 185_000, 1.0))
    assert coverage.status(RIVERS, 535_500, 185_500, 500) is CoverageStatus.COVERED
    assert coverage.status(RIVERS, 530_100, 185_000, 500) is CoverageStatus.COVERED


def test_one_sources_squares_do_not_affect_another() -> None:
    coverage = make_coverage(NoDataSquare("other_source", 535_000, 185_000, 1.0))
    assert coverage.status(SURFACE, 535_500, 185_500, 100) is CoverageStatus.COVERED


def test_no_data_squares_round_trip_through_the_file(tmp_path: Path) -> None:
    squares = [NoDataSquare("surface_water", 535_000, 185_000, 0.25)]
    path = tmp_path / "squares.csv"
    write_no_data_squares(squares, path)
    assert read_no_data_squares(path) == squares


def test_finding_blank_squares_in_a_grid(tmp_path: Path) -> None:
    every_other = [
        (e, n) for e in range(530_000, 540_000, 1_000) for n in range(180_000, 190_000, 1_000)
    ]
    every_other.remove((535_000, 185_000))
    with rasterio.open(write_grid(tmp_path / "grid.tif", every_other)) as dataset:
        found = find_no_data_squares(dataset, LONDON, "surface_water")
    assert found == [NoDataSquare("surface_water", 535_000, 185_000, 1.0)]


def test_check_spots_a_list_that_no_longer_matches(tmp_path: Path) -> None:
    all_marked = [
        (e, n) for e in range(530_000, 540_000, 1_000) for n in range(180_000, 190_000, 1_000)
    ]
    stale = make_coverage(NoDataSquare("surface_water", 535_000, 185_000, 1.0))
    with rasterio.open(write_grid(tmp_path / "grid.tif", all_marked)) as dataset:
        assert check_no_data_list(dataset, make_coverage(), "surface_water", 500).matches
        assert not check_no_data_list(dataset, stale, "surface_water", 500).matches


def test_grid_not_on_whole_squares_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "grid.tif"
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=10,
        width=10,
        count=1,
        dtype="uint8",
        crs="EPSG:27700",
        transform=from_origin(530_500, 190_000, 5, 5),
    ) as dataset:
        dataset.write(np.zeros((10, 10), "uint8"), 1)
    with rasterio.open(path) as dataset, pytest.raises(ValueError, match="whole"):
        find_no_data_squares(dataset, LONDON, "surface_water")
