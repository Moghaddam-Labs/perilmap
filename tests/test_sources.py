from __future__ import annotations

from pathlib import Path

import pytest

from data_test.config import FLOOD_SOURCES, LONDON_BBOX_BNG
from data_test.sources import SourceFileError, iter_batches, normalise_band
from tests.helpers import square, write_flood_file

RIVERS = FLOOD_SOURCES["rivers_and_sea"]
IN_LONDON = (530_000, 180_000)
OUTSIDE_LONDON = (300_000, 400_000)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("High", "High"), ("medium", "Medium"), ("VERY LOW", "Very Low"), (" very  low ", "Very Low")],
)
def test_normalise_band_accepts_source_spellings(raw: str, expected: str) -> None:
    assert normalise_band(raw) == expected


@pytest.mark.parametrize("raw", ["Very High", "", None])
def test_normalise_band_refuses_bands_the_source_does_not_have(raw: object) -> None:
    with pytest.raises(SourceFileError):
        normalise_band(raw)


def test_batches_keep_only_shapes_in_the_test_area(tmp_path: Path) -> None:
    path = write_flood_file(
        tmp_path / "flood.gpkg",
        [("High", square(*IN_LONDON)), ("Low", square(*OUTSIDE_LONDON))],
    )
    rows = [row for batch in iter_batches(path, RIVERS) for row in batch]
    assert [band for band, _ in rows] == ["High"]


def test_layer_and_field_names_match_regardless_of_case(tmp_path: Path) -> None:
    path = write_flood_file(
        tmp_path / "flood.gpkg",
        [("High", square(*IN_LONDON))],
        layer="rofrs_4BAND",
        field="RISK_BAND",
    )
    assert sum(len(batch) for batch in iter_batches(path, RIVERS)) == 1


def test_depth_layer_field_name_is_also_accepted(tmp_path: Path) -> None:
    path = write_flood_file(
        tmp_path / "flood.gpkg", [("High", square(*IN_LONDON))], field="Risk_band3"
    )
    assert sum(len(batch) for batch in iter_batches(path, RIVERS)) == 1


def test_missing_layer_error_lists_what_was_found(tmp_path: Path) -> None:
    path = write_flood_file(tmp_path / "flood.gpkg", [("High", square(*IN_LONDON))], layer="Other")
    with pytest.raises(SourceFileError, match="Other"):
        list(iter_batches(path, RIVERS, layer="RoFRS_4band"))


def test_wrong_coordinate_system_is_refused(tmp_path: Path) -> None:
    path = write_flood_file(
        tmp_path / "flood.gpkg",
        [("High", square(-0.1, 51.5, 0.01))],
        crs="EPSG:4326",
    )
    with pytest.raises(SourceFileError, match="27700"):
        list(iter_batches(path, RIVERS, bbox=(-1, 51, 1, 52)))


def test_unknown_band_in_a_file_is_refused(tmp_path: Path) -> None:
    path = write_flood_file(tmp_path / "flood.gpkg", [("Very High", square(*IN_LONDON))])
    with pytest.raises(SourceFileError, match="Very High"):
        list(iter_batches(path, RIVERS))


def test_test_area_covers_central_london() -> None:
    min_x, min_y, max_x, max_y = LONDON_BBOX_BNG
    assert min_x < 530_000 < max_x
    assert min_y < 180_000 < max_y
