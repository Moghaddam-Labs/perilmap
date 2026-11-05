"""Command line for the flood data test. Run `python -m data_test --help`."""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import pyogrio
import rasterio

from data_test import coverage, grid, heat, measure, sources
from data_test.config import DEFAULT_RADIUS_METRES, FLOOD_SOURCES, GRID_RESOLUTION_METRES

GRID_DIR = Path("grids")
HEAT_PATH = Path("built/heat_air_temperature.gpkg")
MANIFEST_PATH = GRID_DIR / "sources.json"
REPORT_PATH = Path("reports/flood-data-test.md")

# GDAL warns about shapes with many parts, which this data has by design.
warnings.filterwarnings("ignore", message=".*organizePolygons.*", category=RuntimeWarning)
# The heat source stores unused measure values on its shapes, which are dropped anyway.
warnings.filterwarnings("ignore", message=".*Measured.*", category=UserWarning)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m data_test", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    inspect = commands.add_parser("inspect", help="List a file's layers and fields")
    inspect.add_argument("paths", nargs="+", type=Path)

    build = commands.add_parser("build", help="Build a grid file from one or more downloads")
    build.add_argument("source", choices=FLOOD_SOURCES)
    build.add_argument("paths", nargs="+", type=Path)
    build.add_argument("--layer", help="Layer name, if the default isn't found")
    build.add_argument("--resolution-metres", type=int, default=GRID_RESOLUTION_METRES)

    measure_command = commands.add_parser("measure", help="Check the grids and write a report")
    measure_command.add_argument("--radius-metres", type=float, default=DEFAULT_RADIUS_METRES)
    measure_command.add_argument("--resolution-metres", type=int, default=GRID_RESOLUTION_METRES)
    coverage_command = commands.add_parser(
        "coverage", help="List the blank squares inside London that should show No data"
    )
    coverage_command.add_argument("--resolution-metres", type=int, default=GRID_RESOLUTION_METRES)
    heat_command = commands.add_parser("heat", help="Build the small heat file")
    heat_command.add_argument("source", type=Path)
    return parser


def run_inspect(args: argparse.Namespace) -> int:
    for path in args.paths:
        print(path)
        for name, geometry_type in pyogrio.list_layers(path):
            info = pyogrio.read_info(path, layer=str(name))
            fields = ", ".join(str(field) for field in info["fields"])
            print(f"  {name} ({geometry_type}), {info['features']:,} shapes")
            print(f"    Coordinates: {info['crs']}")
            print(f"    Fields: {fields}")
    return 0


def run_build(args: argparse.Namespace) -> int:
    source = FLOOD_SOURCES[args.source]
    output = grid.grid_path(GRID_DIR, source, args.resolution_metres)
    result = grid.build_grid(
        args.paths, source, output, layer=args.layer, resolution=args.resolution_metres
    )
    manifest = measure.load_source_manifest(MANIFEST_PATH)
    manifest[source.key] = args.paths
    MANIFEST_PATH.write_text(
        json.dumps({key: [str(p) for p in paths] for key, paths in manifest.items()}, indent=2),
        encoding="utf-8",
    )
    print(f"{source.label}: {result.grid_mb:,.1f} MB grid from {result.shapes:,} unique shapes")
    print("Coverage, north at the top. Each character is 5 km, and # holds a flood zone.")
    print("\n".join(result.coverage))
    return 0


def run_measure(args: argparse.Namespace) -> int:
    report = measure.run(
        GRID_DIR,
        measure.load_source_manifest(MANIFEST_PATH),
        radius=args.radius_metres,
        resolution=args.resolution_metres,
        heat_path=HEAT_PATH,
    )
    REPORT_PATH.parent.mkdir(exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(report)
    print(f"Saved to {REPORT_PATH}")
    return 0


def run_coverage(args: argparse.Namespace) -> int:
    boundary = coverage.load_boundary()
    squares: list[coverage.NoDataSquare] = []
    for source in FLOOD_SOURCES.values():
        path = grid.grid_path(GRID_DIR, source, args.resolution_metres)
        if source.fully_downloaded or not path.exists():
            continue
        with rasterio.open(path) as dataset:
            found = coverage.find_no_data_squares(dataset, boundary, source.key)
        squares += found
        km2 = sum(square.km2_inside_london for square in found)
        print(f"{source.label}: {len(found)} blank squares, {km2:,.1f} km² inside London")
    coverage.write_no_data_squares(squares)
    print(f"Saved to {coverage.NO_DATA_FILE}")
    return 0


def run_heat(args: argparse.Namespace) -> int:
    build = heat.build_heat_file(args.source, HEAT_PATH)
    print(f"Heat: {build.file_mb:,.1f} MB file with {build.areas:,} areas")
    print(f"London's range: {build.min_c:.1f} to {build.max_c:.1f} °C")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {
        "inspect": run_inspect,
        "build": run_build,
        "measure": run_measure,
        "coverage": run_coverage,
        "heat": run_heat,
    }
    try:
        return handlers[args.command](args)
    except (
        FileNotFoundError,
        sources.SourceFileError,
        heat.HeatFileError,
        pyogrio.errors.DataSourceError,
    ) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
