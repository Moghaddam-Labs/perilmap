from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pyogrio
import pytest
import shapely
from pyogrio.raw import write

from data_test.heat import (
    EXPLANATION,
    GROUPS,
    SOURCE_DESCRIPTION,
    HeatFileError,
    HeatLookup,
    HeatResult,
    build_heat_file,
    format_heat,
    group_for,
    read_build,
)
from tests.helpers import write_heat_source

BREAKS = [17.9, 18.0, 18.1, 18.2]


def square_shape(easting: int) -> shapely.Geometry:
    return shapely.box(easting, 180_000, easting + 100, 180_100)


def make_source(tmp_path: Path) -> Path:
    rows = [
        (
            f"Borough {i}",
            17.5 + i * 0.25,
            shapely.box(530_000 + i * 100, 180_000, 530_100 + i * 100, 180_100),
        )
        for i in range(10)
    ]
    return write_heat_source(tmp_path / "source.gpkg", rows)


def test_social_columns_never_reach_the_built_file(tmp_path: Path) -> None:
    output = tmp_path / "heat.gpkg"
    build_heat_file(make_source(tmp_path), output)
    fields = [str(name) for name in pyogrio.read_info(output)["fields"]]
    assert fields == ["borough", "air_temp_c"]
    assert b"BAME" not in output.read_bytes()
    assert b"IncomeDeprivation" not in output.read_bytes()


def test_built_file_holds_no_hidden_tables_of_social_data(tmp_path: Path) -> None:
    output = tmp_path / "heat.gpkg"
    build_heat_file(make_source(tmp_path), output)
    with sqlite3.connect(output) as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info('heat')")]
    assert set(columns) <= {"fid", "geom", "borough", "air_temp_c"}


def test_build_records_the_range_and_fifths(tmp_path: Path) -> None:
    output = tmp_path / "heat.gpkg"
    build = build_heat_file(make_source(tmp_path), output)
    assert build.areas == 10
    assert build.min_c == pytest.approx(17.5)
    assert build.max_c == pytest.approx(19.75)
    assert len(build.fifth_breaks_c) == 4
    assert read_build(output) == build


@pytest.mark.parametrize(
    ("temperature", "group"),
    [
        (17.2, "coolest fifth"),
        (17.95, "cooler fifth"),
        (18.05, "middle fifth"),
        (18.15, "warmer fifth"),
        (19.3, "warmest fifth"),
        (18.2, "warmest fifth"),
    ],
)
def test_groups_divide_at_the_breaks(temperature: float, group: str) -> None:
    assert group_for(temperature, BREAKS) == group


def test_lookup_finds_an_area_and_its_group(tmp_path: Path) -> None:
    output = tmp_path / "heat.gpkg"
    build_heat_file(make_source(tmp_path), output)
    result = HeatLookup(output).find(530_950, 180_050)
    assert result == HeatResult("Borough 9", 19.75, "warmest fifth")


def test_lookup_outside_every_area_finds_nothing(tmp_path: Path) -> None:
    output = tmp_path / "heat.gpkg"
    build_heat_file(make_source(tmp_path), output)
    assert HeatLookup(output).find(400_000, 400_000) is None


def test_no_match_reads_no_data_never_a_cool_result() -> None:
    assert format_heat(None) == "No data"


def test_format_shows_the_temperature_and_group() -> None:
    assert format_heat(HeatResult("Camden", 18.26, "warmest fifth")) == "18.3 °C, warmest fifth"


def test_shape_height_values_are_removed_and_invalid_shapes_repaired(tmp_path: Path) -> None:
    bowtie = shapely.from_wkt(
        "POLYGON((530000 180000, 530100 180100, 530100 180000, 530000 180100, 530000 180000))"
    )
    source = write_heat_source(tmp_path / "source.gpkg", [("A", 18.0, bowtie)])
    output = tmp_path / "heat.gpkg"
    build_heat_file(source, output)
    assert HeatLookup(output).shapes[0].is_valid
    assert not shapely.has_z(HeatLookup(output).shapes[0])


def test_missing_temperature_field_is_refused(tmp_path: Path) -> None:
    source = tmp_path / "wrong.gpkg"
    write(
        source,
        np.array([shapely.to_wkb(shapely.box(0, 0, 1, 1))], dtype=object),
        [np.array(["A"], dtype=object)],
        fields=["other"],
        layer="airsurfacetemp",
        driver="GPKG",
        geometry_type="Polygon",
        crs="EPSG:27700",
    )
    with pytest.raises(HeatFileError, match="missing"):
        build_heat_file(source, tmp_path / "heat.gpkg")


def test_missing_temperature_value_is_refused(tmp_path: Path) -> None:
    source = write_heat_source(
        tmp_path / "source.gpkg", [("A", float("nan"), shapely.box(0, 0, 1, 1))]
    )
    with pytest.raises(HeatFileError, match="no temperature"):
        build_heat_file(source, tmp_path / "heat.gpkg")


def test_wording_matches_the_source_and_stays_honest() -> None:
    assert "Modelled" in SOURCE_DESCRIPTION
    assert "June to August, day and night" in SOURCE_DESCRIPTION
    assert "not a risk rating" in EXPLANATION
    assert "during a heatwave" in EXPLANATION
    assert len(GROUPS) == 5
