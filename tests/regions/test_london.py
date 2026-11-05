from __future__ import annotations

import ast
import concurrent.futures
from pathlib import Path

import pytest
import shapely
from rasterio.warp import transform as reproject

import perilmap
from data_test.grid import build_grid, grid_path
from data_test.heat import build_heat_file
from perilmap.core.assessment import RegionRegistry, assess
from perilmap.core.models import (
    NOT_AVAILABLE_HERE,
    AreaComparison,
    Location,
    NearestZones,
    PerilResult,
    ResultStatus,
    ZoneDistance,
)
from perilmap.regions.london import wording
from perilmap.regions.london.coverage import Coverage, NoDataSquare, load_boundary
from perilmap.regions.london.region import (
    LondonDataError,
    LondonRegion,
    flood_summary,
    zone_distance,
)
from perilmap.regions.london.settings import FLOOD_SOURCES
from tests.helpers import square, write_flood_file, write_heat_source

BBOX = (525_000, 175_000, 535_000, 185_000)
HIGH_ZONE = (530_000, 180_000)
GAP_SQUARE = (532_000, 182_000)
IN_LONDON = (530_050, 180_050)


def at(easting: float, northing: float) -> Location:
    longitudes, latitudes = reproject("EPSG:27700", "EPSG:4326", [easting], [northing])
    return Location(latitudes[0], longitudes[0])


@pytest.fixture(scope="module")
def data_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("london")
    for key, layer in (("rivers_and_sea", "RoFRS_4band"), ("surface_water", "RoFSW")):
        rows = [
            ("High", square(*HIGH_ZONE)),
            ("Low", square(530_300, 180_000)),
        ]
        download = write_flood_file(root / f"{key}.gpkg", rows, layer=layer)
        source = FLOOD_SOURCES[key]
        build_grid([download], source, grid_path(root, source, 5), bbox=BBOX)
    heat_source = write_heat_source(
        root / "heat_source.gpkg",
        [
            ("Westminster", 18.26, shapely.box(529_000, 179_000, 531_000, 181_000)),
            ("Camden", 17.4, shapely.box(531_000, 179_000, 533_000, 181_000)),
            ("Hackney", 19.2, shapely.box(533_000, 179_000, 534_000, 181_000)),
        ],
    )
    build_heat_file(heat_source, root / "heat_air_temperature.gpkg")
    return root


@pytest.fixture(scope="module")
def region(data_dir: Path) -> LondonRegion:
    coverage = Coverage(load_boundary(), [NoDataSquare("surface_water", *GAP_SQUARE, 1.0)])
    return LondonRegion(data_dir, coverage)


def result_for(region: LondonRegion, peril_id: str, location: Location) -> PerilResult:
    return next(
        r for r in assess(location, RegionRegistry([region])).results if r.peril_id == peril_id
    )


def test_covers_london_and_nothing_else(region: LondonRegion) -> None:
    assert region.covers(Location(51.5074, -0.1278))  # Charing Cross
    assert not region.covers(Location(50.8225, -0.1372))  # Brighton
    assert not region.covers(Location(40.7128, -74.0060))  # New York


def test_outside_london_says_not_available(region: LondonRegion) -> None:
    assessment = assess(Location(50.8225, -0.1372), RegionRegistry([region]))
    assert not assessment.available_here
    assert assessment.message == NOT_AVAILABLE_HERE


def test_every_peril_answers_in_a_set_order(region: LondonRegion) -> None:
    assessment = assess(at(*IN_LONDON), RegionRegistry([region]))
    assert [r.peril_id for r in assessment.results] == [
        "flood_rivers_and_sea",
        "flood_surface_water",
        "heat",
        "subsidence",
    ]
    assert assessment.region_name == "Greater London"


def test_results_state_what_is_not_covered(region: LondonRegion) -> None:
    assessment = assess(at(*IN_LONDON), RegionRegistry([region]))
    assert "Groundwater flooding" in assessment.not_covered
    assert "Reservoir flooding" in assessment.not_covered


def test_on_a_zone_leads_with_the_highest_band(region: LondonRegion) -> None:
    result = result_for(region, "flood_rivers_and_sea", at(*IN_LONDON))
    assert result.status is ResultStatus.AVAILABLE
    assert "on, or within about 5 m of, a High rivers and sea zone" in result.summary
    assert isinstance(result.measurement, NearestZones)
    assert result.measurement.zones[0] == ZoneDistance(
        "High", 0.0, "On the zone, or within about 5 m"
    )


def test_near_a_zone_gives_a_rounded_distance(region: LondonRegion) -> None:
    result = result_for(region, "flood_rivers_and_sea", at(530_250, 180_050))
    assert "The nearest mapped rivers and sea zone is" in result.summary
    zones = {zone.band: zone for zone in result.measurement.zones}
    assert zones["High"].metres % 10 == 0 and zones["High"].label.startswith("About")
    assert zones["Very Low"].metres is None
    assert zones["Very Low"].label == "None within 1,000 m"


def test_each_product_lists_only_the_bands_it_maps(region: LondonRegion) -> None:
    rivers = result_for(region, "flood_rivers_and_sea", at(*IN_LONDON)).measurement
    surface = result_for(region, "flood_surface_water", at(*IN_LONDON)).measurement
    assert [zone.band for zone in rivers.zones] == ["High", "Medium", "Low", "Very Low"]
    assert [zone.band for zone in surface.zones] == ["High", "Medium", "Low"]


def test_surface_water_explains_very_low_outside_its_zones(region: LondonRegion) -> None:
    result = result_for(region, "flood_surface_water", at(*IN_LONDON))
    assert "treats anywhere outside these zones as Very Low" in result.what_this_means


def test_blank_square_shows_no_data_never_a_clear_result(region: LondonRegion) -> None:
    location = at(GAP_SQUARE[0] + 500, GAP_SQUARE[1] + 500)
    result = result_for(region, "flood_surface_water", location)
    assert result.status is ResultStatus.NO_DATA
    assert result.measurement is None
    assert "doesn't mean the risk is low" in result.what_this_means


def test_near_a_blank_square_is_marked_incomplete(region: LondonRegion) -> None:
    result = result_for(region, "flood_surface_water", at(531_500, 182_500))
    assert result.status is ResultStatus.INCOMPLETE
    assert result.caveats == (wording.INCOMPLETE_CAVEAT,)


def test_rivers_are_not_affected_by_surface_water_gaps(region: LondonRegion) -> None:
    location = at(GAP_SQUARE[0] + 500, GAP_SQUARE[1] + 500)
    assert result_for(region, "flood_rivers_and_sea", location).status is ResultStatus.AVAILABLE


def test_heat_shows_value_group_and_range_as_a_comparison(region: LondonRegion) -> None:
    result = result_for(region, "heat", at(*IN_LONDON))
    assert result.status is ResultStatus.AVAILABLE
    assert isinstance(result.measurement, AreaComparison)
    assert result.measurement.value == 18.3
    assert result.measurement.range_low == 17.4 and result.measurement.range_high == 19.2
    assert "18.3 °C" in result.summary and "London's range is 17.4 to 19.2 °C" in result.summary


def test_heat_wording_is_honest_about_what_the_number_is(region: LondonRegion) -> None:
    result = result_for(region, "heat", at(*IN_LONDON))
    assert "Modelled average air temperature, June to August" in result.what_this_means
    assert "not a risk rating" in result.what_this_means
    assert "during a heatwave" in result.what_this_means
    assert "PerilMap's own calculation" in result.measurement.calculation_note
    assert "indicative" in result.how_sure


def test_heat_with_no_area_shows_no_data(region: LondonRegion) -> None:
    result = result_for(region, "heat", at(526_000, 176_000))
    assert result.status is ResultStatus.NO_DATA
    assert result.measurement is None
    assert "says nothing about how warm" in result.what_this_means


def test_subsidence_is_general_information_with_no_rating(region: LondonRegion) -> None:
    result = result_for(region, "subsidence", at(*IN_LONDON))
    assert result.status is ResultStatus.GENERAL_INFORMATION
    assert result.measurement is None
    assert "can't assess this particular home" in result.summary
    assert "not suitable for local or site specific analysis" in result.how_sure
    assert "PerilMap's own calculation" in result.what_this_means


def test_subsidence_card_is_the_same_everywhere(region: LondonRegion) -> None:
    assert result_for(region, "subsidence", at(*IN_LONDON)) == result_for(
        region, "subsidence", at(526_000, 176_000)
    )


def test_subsidence_links_to_bgs_and_a_report(region: LondonRegion) -> None:
    urls = [link.url for link in result_for(region, "subsidence", at(*IN_LONDON)).links]
    assert any("clay-shrink-swell" in url for url in urls)
    assert any("shop.bgs.ac.uk" in url for url in urls)


def test_every_result_has_guidance_links_and_credits(region: LondonRegion) -> None:
    for result in assess(at(*IN_LONDON), RegionRegistry([region])).results:
        assert result.links
        assert result.sources and all(source.attribution for source in result.sources)
        assert result.what_you_can_do


@pytest.mark.parametrize(
    ("metres", "expected"),
    [
        (None, (None, "None within 1,000 m")),
        (0.0, (0.0, "On the zone, or within about 5 m")),
        (6.0, (10.0, "Under 10 m")),
        (124.0, (120.0, "About 120 m")),
        (995.0, (1000.0, "About 1,000 m")),
    ],
)
def test_distances_do_not_claim_false_accuracy(
    metres: float | None, expected: tuple[float | None, str]
) -> None:
    zone = zone_distance("Low", metres, 1_000)
    assert (zone.metres, zone.label) == expected


def test_summary_with_nothing_nearby_avoids_saying_safe() -> None:
    zones = [ZoneDistance("High", None, "None within 1,000 m")]
    summary = flood_summary("rivers and sea", zones, 1_000)
    assert summary == "There's no mapped rivers and sea zone within 1,000 m of this spot."


def test_summary_names_the_closest_zone() -> None:
    zones = [ZoneDistance("High", 300.0, "About 300 m"), ZoneDistance("Low", 40.0, "About 40 m")]
    summary = flood_summary("surface water", zones, 1_000)
    assert summary == "The nearest mapped surface water zone is Low, about 40 m away."


def test_missing_data_files_stop_the_region_starting(tmp_path: Path) -> None:
    with pytest.raises(LondonDataError, match="rivers_and_sea_5m.tif"):
        LondonRegion(tmp_path)


def test_reads_are_safe_when_requests_overlap(region: LondonRegion) -> None:
    registry = RegionRegistry([region])
    expected = assess(at(*IN_LONDON), registry)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: assess(at(*IN_LONDON), registry), range(40)))
    assert all(result == expected for result in results)
    assert all(r.status is not ResultStatus.TEMPORARILY_UNAVAILABLE for r in expected.results)


def test_app_code_never_depends_on_the_data_test() -> None:
    package = Path(perilmap.__file__).parent
    for path in package.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("data_test"), path
            if isinstance(node, ast.Import):
                assert all(not a.name.startswith("data_test") for a in node.names), path


def test_wording_avoids_em_dashes_and_claims_of_safety() -> None:
    text = Path(wording.__file__).read_text(encoding="utf-8").lower()
    assert "—" not in text
    assert "safe" not in text
    assert "no risk." not in text.replace("not as no risk.", "")


def test_all_links_use_https() -> None:
    links = [wording.CHECK_FLOOD_RISK, *wording.FLOOD_LINKS, *wording.HEAT_LINKS]
    assert all(link.url.startswith("https://") for link in [*links, *wording.SUBSIDENCE_LINKS])
