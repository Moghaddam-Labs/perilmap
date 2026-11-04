from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import rasterio
import shapely

from data_test.config import BAND_BITS, FLOOD_SOURCES
from data_test.grid import (
    build_grid,
    coverage_map,
    exact_nearest_by_band,
    grid_path,
    nearest_by_band,
    read_build,
)
from tests.helpers import square, write_flood_file

RIVERS = FLOOD_SOURCES["rivers_and_sea"]
BBOX = (530_000, 180_000, 532_000, 182_000)


def build(tmp_path: Path, rows: list[tuple[str, bytes]], name: str = "flood.gpkg"):
    source = write_flood_file(tmp_path / name, rows)
    output = grid_path(tmp_path / "grids", RIVERS, 5)
    return source, output, build_grid([source], RIVERS, output, resolution=5, bbox=BBOX)


def read_grid(path: Path) -> np.ndarray:
    with rasterio.open(path) as dataset:
        return dataset.read(1)


def test_build_records_each_band_and_matches_its_area(tmp_path: Path) -> None:
    _, output, result = build(
        tmp_path,
        [("High", square(530_100, 180_100)), ("Low", square(531_000, 181_000, 200))],
    )
    assert result.shapes == 2
    assert result.shape_km2 == pytest.approx({"High": 0.01, "Low": 0.04})
    assert result.grid_km2["High"] == pytest.approx(0.01, rel=0.1)
    assert result.grid_km2["Low"] == pytest.approx(0.04, rel=0.1)
    grid = read_grid(output)
    assert set(np.unique(grid)) == {0, BAND_BITS["High"], BAND_BITS["Low"]}


def test_one_square_can_hold_several_bands(tmp_path: Path) -> None:
    _, output, _ = build(
        tmp_path,
        [("High", square(530_100, 180_100)), ("Low", square(530_100, 180_100))],
    )
    assert BAND_BITS["High"] | BAND_BITS["Low"] in set(np.unique(read_grid(output)))


def test_band_thinner_than_a_square_is_not_lost(tmp_path: Path) -> None:
    sliver = shapely.to_wkb(shapely.box(530_501, 180_000, 530_502, 182_000))
    _, output, _ = build(
        tmp_path,
        [
            ("High", square(530_000, 180_000, 500)),
            ("Medium", sliver),
            ("Low", shapely.to_wkb(shapely.box(530_502, 180_000, 531_000, 182_000))),
        ],
    )
    with rasterio.open(output) as dataset:
        nearest = nearest_by_band(dataset, 530_700, 181_000, 500)
    assert nearest["Medium"] == pytest.approx(198, abs=8)


def test_overlapping_downloads_are_not_counted_twice(tmp_path: Path) -> None:
    shared = ("High", square(530_100, 180_100))
    first = write_flood_file(tmp_path / "a.gpkg", [shared])
    second = write_flood_file(tmp_path / "b.gpkg", [shared, ("Low", square(531_000, 181_000))])
    output = grid_path(tmp_path, RIVERS, 5)
    result = build_grid([first, second], RIVERS, output, resolution=5, bbox=BBOX)
    assert result.shapes == 2
    assert result.duplicate_shapes == 1
    assert result.shape_km2["High"] == pytest.approx(0.01)


def test_holes_in_shapes_stay_empty(tmp_path: Path) -> None:
    ring = shapely.box(530_100, 180_100, 530_400, 180_400).difference(
        shapely.box(530_200, 180_200, 530_300, 180_300)
    )
    _, output, result = build(tmp_path, [("High", shapely.to_wkb(ring))])
    assert result.grid_km2["High"] == pytest.approx(0.08, rel=0.1)
    with rasterio.open(output) as dataset:
        assert nearest_by_band(dataset, 530_250, 180_250, 500)["High"] == pytest.approx(50, abs=8)


def test_shape_area_outside_the_box_is_not_counted(tmp_path: Path) -> None:
    _, _, result = build(tmp_path, [("High", square(529_950, 180_100))])
    assert result.shape_km2["High"] == pytest.approx(0.005)
    assert result.grid_km2["High"] == pytest.approx(0.005, rel=0.1)


def test_stats_are_saved_beside_the_grid(tmp_path: Path) -> None:
    _, output, result = build(tmp_path, [("High", square(530_100, 180_100))])
    assert read_build(output) == result


def test_grid_carries_attribution_and_coordinates(tmp_path: Path) -> None:
    _, output, _ = build(tmp_path, [("High", square(530_100, 180_100))])
    with rasterio.open(output) as dataset:
        assert dataset.crs.to_epsg() == 27_700
        assert "Environment Agency" in dataset.tags()["attribution"]
        assert dataset.tags()["licence"] == "Open Government Licence v3.0"


def test_lookup_measures_distance_for_each_band(tmp_path: Path) -> None:
    _, output, _ = build(
        tmp_path,
        [
            ("High", square(530_500, 180_500)),
            ("Low", square(530_000, 180_500)),
            ("Medium", square(531_900, 181_900)),
        ],
    )
    with rasterio.open(output) as dataset:
        nearest = nearest_by_band(dataset, 530_300, 180_550, 500)
    assert nearest["High"] == pytest.approx(200, abs=8)
    assert nearest["Low"] == pytest.approx(200, abs=8)
    assert "Medium" not in nearest


def test_point_inside_a_zone_is_zero(tmp_path: Path) -> None:
    _, output, _ = build(tmp_path, [("High", square(530_100, 180_100))])
    with rasterio.open(output) as dataset:
        assert nearest_by_band(dataset, 530_150, 180_150, 500)["High"] == 0


def test_lookup_beyond_the_grid_is_empty(tmp_path: Path) -> None:
    _, output, _ = build(tmp_path, [("High", square(530_100, 180_100))])
    with rasterio.open(output) as dataset:
        assert nearest_by_band(dataset, 400_000, 400_000, 500) == {}


def test_lookup_near_the_grid_edge_still_works(tmp_path: Path) -> None:
    _, output, _ = build(tmp_path, [("High", square(530_000, 180_000))])
    with rasterio.open(output) as dataset:
        assert nearest_by_band(dataset, 529_990, 180_050, 500)["High"] == pytest.approx(10, abs=8)


def test_grid_and_exact_distances_agree_within_a_cell(tmp_path: Path) -> None:
    source, output, _ = build(
        tmp_path,
        [("High", square(530_503, 180_507)), ("Low", square(531_111, 180_222))],
    )
    with rasterio.open(output) as dataset:
        grid = nearest_by_band(dataset, 530_800, 180_400, 800)
    exact = exact_nearest_by_band([source], RIVERS, 530_800, 180_400, radius=800)
    assert grid.keys() == exact.keys()
    for band in exact:
        assert grid[band] == pytest.approx(exact[band], abs=8)


def test_coverage_map_marks_blocks_with_zones() -> None:
    grid = np.zeros((4, 4), "uint8")
    grid[0, 3] = 1
    grid[3, 0] = 4
    assert coverage_map(grid, resolution=5, block_metres=10) == [".#", "#."]
