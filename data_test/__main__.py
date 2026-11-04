"""Command line for the flood data test. Run `python -m data_test --help`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pyogrio

from data_test import database, load, measure, sources
from data_test.config import (
    DEFAULT_MAX_DB_MB,
    DEFAULT_RADIUS_METRES,
    DEFAULT_SUBDIVIDE_VERTICES,
    FLOOD_SOURCES,
)

REPORT_PATH = Path("reports/flood-data-test.md")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m data_test", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    inspect = commands.add_parser("inspect", help="List a file's layers and fields")
    inspect.add_argument("paths", nargs="+", type=Path)

    def add_source_options(command: argparse.ArgumentParser) -> None:
        command.add_argument("source", choices=FLOOD_SOURCES)
        command.add_argument("paths", nargs="+", type=Path)
        command.add_argument("--layer", help="Layer name, if the default isn't found")
        command.add_argument("--simplify-metres", type=float, default=0.0)

    estimate = commands.add_parser("estimate", help="Measure London's data without a database")
    add_source_options(estimate)

    load_command = commands.add_parser("load", help="Load a source into the database")
    add_source_options(load_command)
    load_command.add_argument("--max-db-mb", type=float, default=DEFAULT_MAX_DB_MB)
    load_command.add_argument("--subdivide-vertices", type=int, default=DEFAULT_SUBDIVIDE_VERTICES)

    measure_command = commands.add_parser("measure", help="Measure size and speed, write a report")
    measure_command.add_argument("--radius-metres", type=float, default=DEFAULT_RADIUS_METRES)

    reset = commands.add_parser("reset", help="Delete the test data")
    reset.add_argument("--yes", action="store_true", help="Confirm the deletion")
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


def run_estimate(args: argparse.Namespace) -> int:
    source = FLOOD_SOURCES[args.source]
    result = sources.estimate(
        args.paths, source, layer=args.layer, simplify_metres=args.simplify_metres
    )
    print(f"{source.label}, London test area")
    print(f"  Shapes: {result.features:,}")
    print(f"  Corner points: {result.vertices:,}")
    print(f"  Raw geometry: {result.geometry_mb:,.1f} MB")
    for band, count in sorted(result.bands.items()):
        print(f"  {band}: {count:,} shapes")
    print("  The database will use more than the raw size, because of indexes and overhead.")
    return 0


def run_load(args: argparse.Namespace) -> int:
    source = FLOOD_SOURCES[args.source]
    with database.connect(database.get_database_url()) as conn:
        result = load.load_files(
            conn,
            source,
            args.paths,
            layer=args.layer,
            simplify_metres=args.simplify_metres,
            subdivide_vertices=args.subdivide_vertices,
            max_db_mb=args.max_db_mb,
        )
    if result.stopped_early:
        print(
            f"Stopped at {result.database_mb:,.0f} MB to stay inside the limit, "
            f"after {result.features:,} shapes. Run reset, then try --simplify-metres."
        )
        return 2
    print(f"Loaded {result.features:,} shapes. Database now at {result.database_mb:,.0f} MB.")
    return 0


def run_measure(args: argparse.Namespace) -> int:
    with database.connect(database.get_database_url()) as conn:
        sizes, results = measure.run(conn, args.radius_metres)
    report = measure.build_report(sizes, results, args.radius_metres)
    REPORT_PATH.parent.mkdir(exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(report)
    print(f"Saved to {REPORT_PATH}")
    return 0


def run_reset(args: argparse.Namespace) -> int:
    if not args.yes:
        print("This deletes all the test data. Run it again with --yes to confirm.")
        return 1
    with database.connect(database.get_database_url()) as conn:
        database.reset(conn)
    print("Test data deleted.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {
        "inspect": run_inspect,
        "estimate": run_estimate,
        "load": run_load,
        "measure": run_measure,
        "reset": run_reset,
    }
    try:
        return handlers[args.command](args)
    except (
        database.SetupError,
        sources.SourceFileError,
        load.SourceAlreadyLoaded,
        pyogrio.errors.DataSourceError,
    ) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
