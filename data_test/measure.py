"""Measure the grid files, check them against the shapes, and write a report."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import numpy as np
import rasterio
from rasterio.warp import transform as reproject

from data_test.config import (
    ACCURACY_SAMPLE_POINTS,
    ACCURACY_SAMPLE_SEED,
    BAND_ORDER,
    BNG_CRS,
    DEFAULT_RADIUS_METRES,
    FLOOD_SOURCES,
    GRID_RESOLUTION_METRES,
    TARGET_DISTANCE_ERROR_METRES,
    TARGET_GRID_MB,
    TARGET_HEAT_FILE_MB,
    TARGET_LOOKUP_MS,
)
from data_test.grid import (
    GridBuild,
    exact_nearest_by_band,
    grid_path,
    nearest_by_band,
    read_build,
)
from data_test.heat import format_heat
from perilmap.regions.london.coverage import (
    Coverage,
    CoverageStatus,
    NoDataCheck,
    check_no_data_list,
)
from perilmap.regions.london.heat import OUTPUT_FIELDS, HeatBuild, HeatLookup
from perilmap.regions.london.wording import (
    HEAT_CALCULATION_NOTE,
    HEAT_DESCRIPTION,
    HEAT_EXPLANATION,
)

LOCATIONS_FILE = Path(__file__).with_name("locations.csv")


@dataclass(frozen=True)
class Location:
    name: str
    latitude: float
    longitude: float
    expectation: str

    def to_bng(self) -> tuple[float, float]:
        xs, ys = reproject("EPSG:4326", BNG_CRS, [self.longitude], [self.latitude])
        return xs[0], ys[0]


@dataclass
class LocationResult:
    location: Location
    in_area: bool
    # {source: {band: metres}}
    nearest: dict[str, dict[str, float]] = field(default_factory=dict)
    statuses: dict[str, CoverageStatus] = field(default_factory=dict)
    lookup_ms: list[float] = field(default_factory=list)
    heat: str = "Not built"

    @property
    def check_passed(self) -> bool:
        return expectation_met(self.location.expectation, self.in_area, self.nearest)


def expectation_met(expectation: str, in_area: bool, nearest: dict[str, dict[str, float]]) -> bool:
    """Compare a result with what we'd expect there. A miss needs a human look."""
    river_bands = set(nearest.get("rivers_and_sea", {}))
    if expectation == "outside_area":
        return not in_area
    if expectation == "near_river":
        return bool(river_bands)
    if expectation == "away_from_river":
        return not river_bands & {"High", "Medium", "Low"}
    raise ValueError(f"Unknown expectation: {expectation}")


def read_locations(path: Path = LOCATIONS_FILE) -> list[Location]:
    with path.open(newline="", encoding="utf-8") as file:
        return [
            Location(
                row["name"], float(row["latitude"]), float(row["longitude"]), row["expectation"]
            )
            for row in csv.DictReader(file)
        ]


def compare_with_shapes(
    grid_results: dict[str, dict[str, float]],
    exact_results: dict[str, dict[str, float]],
    radius: float,
    resolution: int,
) -> tuple[list[float], int]:
    """Return the distance errors, and how many zones the grid missed or invented."""
    errors: list[float] = []
    mismatches = 0
    for name, exact in exact_results.items():
        grid = grid_results.get(name, {})
        for band in BAND_ORDER:
            if band in exact and band in grid:
                errors.append(abs(exact[band] - grid[band]))
            elif band in exact or band in grid:
                # A zone right at the search edge can fall either side of it.
                distance = exact.get(band, grid.get(band, 0.0))
                if distance < radius - 2 * resolution:
                    mismatches += 1
    return errors, mismatches


def format_nearest(bands: dict[str, float] | None, radius: float) -> str:
    """Describe one source's result in rounded distances, e.g. 'High 120 m, Low on zone'."""
    if not bands:
        return f"None within {radius:,.0f} m"
    parts = []
    for band in BAND_ORDER:
        if band in bands:
            metres = bands[band]
            if metres == 0:
                parts.append(f"{band} on zone")
            elif metres < 10:
                parts.append(f"{band} under 10 m")
            else:
                parts.append(f"{band} {round(metres, -1):,.0f} m")
    return ", ".join(parts)


def format_result(status: CoverageStatus, bands: dict[str, float] | None, radius: float) -> str:
    """Describe a result, making sure a gap in the data can never read as safe."""
    if status is CoverageStatus.OUTSIDE:
        return "Not available here yet"
    if status is CoverageStatus.NO_DATA:
        return "No data"
    text = format_nearest(bands, radius)
    return f"{text} (may be incomplete)" if status is CoverageStatus.NEAR_GAP else text


def verdict(passed: bool) -> str:
    return "Pass" if passed else "Fail"


def build_report(
    builds: dict[str, GridBuild],
    results: list[LocationResult],
    comparisons: dict[str, tuple[list[float], int]],
    radius: float,
    no_data_checks: dict[str, NoDataCheck] | None = None,
    heat_build: HeatBuild | None = None,
) -> str:
    """Write the findings as Markdown."""
    timings = [ms for result in results for ms in result.lookup_ms]
    total_mb = sum(build.grid_mb for build in builds.values())
    passed = sum(result.check_passed for result in results)
    errors = [error for pair in comparisons.values() for error in pair[0]]
    mismatches = sum(pair[1] for pair in comparisons.values())
    worst_error = max(errors, default=0.0)
    no_data_checks = no_data_checks or {}

    lines = [
        "# Flood data test",
        "",
        f"Run on {datetime.now(UTC):%d %B %Y at %H:%M} UTC, "
        f"searching {radius:,.0f} m around each pin.",
        "",
        "## Results",
        "",
        "| Check | Result | Target | Verdict |",
        "|---|---|---|---|",
        f"| Grid files | {total_mb:,.1f} MB | Up to {TARGET_GRID_MB} MB "
        f"| {verdict(total_mb <= TARGET_GRID_MB)} |",
        f"| Slowest lookup | {max(timings, default=0):,.1f} ms | Up to {TARGET_LOOKUP_MS} ms "
        f"| {verdict(max(timings, default=0) <= TARGET_LOOKUP_MS)} |",
        f"| Largest distance error | {worst_error:,.1f} m | Up to "
        f"{TARGET_DISTANCE_ERROR_METRES} m "
        f"| {verdict(worst_error <= TARGET_DISTANCE_ERROR_METRES)} |",
        f"| Zones missed or invented | {mismatches} of {len(errors) + mismatches} checked | None "
        f"| {verdict(mismatches == 0)} |",
        f"| Known places as expected | {passed} of {len(results)} | All, or explained "
        f"| {'Pass' if passed == len(results) else 'Review'} |",
    ]
    for key, check in sorted(no_data_checks.items()):
        lines.append(
            f"| {FLOOD_SOURCES[key].label} No data list matches the grid "
            f"| {'Yes' if check.matches else 'No'} | Yes | {verdict(check.matches)} |"
        )
    if heat_build:
        lines.append(
            f"| Heat file | {heat_build.file_mb:,.1f} MB | Up to {TARGET_HEAT_FILE_MB} MB "
            f"| {verdict(heat_build.file_mb <= TARGET_HEAT_FILE_MB)} |"
        )
    for key, build in sorted(builds.items()):
        label = FLOOD_SOURCES[key].label
        lines += [
            "",
            f"## {label}",
            "",
            f"- Grid file: {build.grid_mb:,.1f} MB at {build.resolution_metres} m",
            f"- Unique shapes read: {build.shapes:,}",
            f"- Overlapping shapes skipped: {build.duplicate_shapes:,}",
            "",
            "The grid area is larger by design, because any square a zone touches is marked.",
            "",
            "| Band | Shapes (km²) | Grid (km²) |",
            "|---|---|---|",
        ]
        for band in BAND_ORDER:
            if band in build.shape_km2:
                lines.append(
                    f"| {band} | {build.shape_km2[band]:,.2f} | {build.grid_km2[band]:,.2f} |"
                )
        lines += [
            "",
            "Coverage, north at the top. Each character is 5 km, and `#` holds a flood zone. "
            "A blank patch inside London may be a missed download.",
            "",
            "```text",
            *build.coverage,
            "```",
        ]
        if key in no_data_checks:
            check = no_data_checks[key]
            share = check.no_data_km2 / check.london_km2 * 100
            lines += [
                "",
                f"Inside the official London boundary, {check.blank_squares:,} of "
                f"{check.london_squares:,} squares are blank and show No data. That's "
                f"{check.no_data_km2:,.1f} km² of {check.london_km2:,.0f} km² ({share:.1f}%).",
                "",
                f"Within {radius:,.0f} m of a blank square or the edge of London, results are "
                f"marked may be incomplete. That applies to {check.near_gap_km2:,.0f} km².",
            ]
    if heat_build:
        lines += [
            "",
            "## Heat",
            "",
            f"- What the number is: {HEAT_DESCRIPTION} (Greater London Authority and Arup).",
            f"- Fields kept: {', '.join(OUTPUT_FIELDS)}, plus the area's shape.",
            f"- Areas: {heat_build.areas:,}, covering {heat_build.km2:,.0f} km². The rest of "
            "London is mainly the River Thames, and shows No data.",
            f"- London's range: {heat_build.min_c:.1f} to {heat_build.max_c:.1f} °C. "
            f"{HEAT_CALCULATION_NOTE}",
            "",
            f"Shown beside each result: {HEAT_EXPLANATION}",
        ]
    lines += [
        "",
        "## Known places",
        "",
        "Expectations are rough checks on approximate coordinates, not proof of accuracy. "
        "Distances are rounded to the nearest 10 m, and on zone means on or within about 5 m. "
        "Review means a person should look at that place on the Environment Agency map.",
        "",
        "| Place | Expected | Rivers and sea | Surface water | Heat | Check |",
        "|---|---|---|---|---|---|",
    ]
    for result in results:
        location = result.location
        expected = location.expectation.replace("_", " ").capitalize()
        cells = {}
        for key in FLOOD_SOURCES:
            if key in result.statuses:
                cells[key] = format_result(result.statuses[key], result.nearest.get(key), radius)
            elif not result.in_area:
                cells[key] = "Not available here yet"
            else:
                cells[key] = "Not built"
        check = "OK" if result.check_passed else "Review"
        lines.append(
            f"| {location.name} | {expected} | {cells['rivers_and_sea']} "
            f"| {cells['surface_water']} | {result.heat} | {check} |"
        )
    return "\n".join(lines) + "\n"


def sample_points(
    dataset: rasterio.DatasetReader, radius: float, count: int = ACCURACY_SAMPLE_POINTS
) -> list[tuple[float, float]]:
    """Pick repeatable random points near flood zones, away from the grid's edges."""
    grid = dataset.read(1)
    margin = int(radius / dataset.transform.a) + 1
    rows, columns = np.nonzero(grid[margin:-margin, margin:-margin])
    if rows.size == 0:
        return []
    generator = np.random.default_rng(ACCURACY_SAMPLE_SEED)
    picks = generator.integers(0, rows.size, count)
    resolution = dataset.transform.a
    x = dataset.bounds.left + (columns[picks] + margin + generator.random(count)) * resolution
    y = dataset.bounds.top - (rows[picks] + margin + generator.random(count)) * resolution
    return list(zip(x.tolist(), y.tolist(), strict=True))


def run(
    grid_dir: Path,
    source_paths: dict[str, list[Path]],
    *,
    radius: float = DEFAULT_RADIUS_METRES,
    resolution: int = GRID_RESOLUTION_METRES,
    coverage: Coverage | None = None,
    heat_path: Path | None = None,
) -> str:
    """Look up every known place in every built grid and return the report."""
    coverage = coverage or Coverage.load()
    locations = read_locations()
    builds: dict[str, GridBuild] = {}
    no_data_checks: dict[str, NoDataCheck] = {}
    results = [
        LocationResult(location, coverage.in_london(*location.to_bng())) for location in locations
    ]
    comparisons: dict[str, tuple[list[float], int]] = {}

    for key, source in FLOOD_SOURCES.items():
        path = grid_path(grid_dir, source, resolution)
        if not path.exists():
            continue
        builds[key] = read_build(path)
        grid_results: dict[str, dict[str, float]] = {}
        exact_results: dict[str, dict[str, float]] = {}
        with rasterio.open(path) as dataset:
            if not source.fully_downloaded:
                no_data_checks[key] = check_no_data_list(dataset, coverage, key, radius)
            for result in results:
                x, y = result.location.to_bng()
                result.statuses[key] = coverage.status(source, x, y, radius)
                if result.statuses[key] in (CoverageStatus.OUTSIDE, CoverageStatus.NO_DATA):
                    continue
                started = perf_counter()
                nearest = nearest_by_band(dataset, x, y, radius)
                result.lookup_ms.append((perf_counter() - started) * 1_000)
                result.nearest[key] = nearest
                grid_results[result.location.name] = nearest
                if source_paths.get(key):
                    exact_results[result.location.name] = exact_nearest_by_band(
                        source_paths[key], source, x, y, radius=radius
                    )
            if source_paths.get(key):
                for index, (x, y) in enumerate(sample_points(dataset, radius)):
                    name = f"Random point {index}"
                    grid_results[name] = nearest_by_band(dataset, x, y, radius)
                    exact_results[name] = exact_nearest_by_band(
                        source_paths[key], source, x, y, radius=radius
                    )
        comparisons[key] = compare_with_shapes(grid_results, exact_results, radius, resolution)

    if not builds:
        raise FileNotFoundError("No grid files found. Run the build command first.")
    heat_build = None
    if heat_path and heat_path.exists():
        lookup = HeatLookup(heat_path)
        heat_build = lookup.build
        for result in results:
            if not result.in_area:
                result.heat = "Not available here yet"
                continue
            started = perf_counter()
            result.heat = format_heat(lookup.find(*result.location.to_bng()))
            result.lookup_ms.append((perf_counter() - started) * 1_000)
    return build_report(builds, results, comparisons, radius, no_data_checks, heat_build)


def load_source_manifest(path: Path) -> dict[str, list[Path]]:
    """Read which downloads each grid came from, so measure can check against them."""
    if not path.exists():
        return {}
    return {key: [Path(p) for p in paths] for key, paths in json.loads(path.read_text()).items()}
