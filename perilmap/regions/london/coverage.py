"""Decide what a result can honestly say, based on where the data is known to exist."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import numpy as np
import rasterio
import shapely
from pyogrio.raw import read

from perilmap.regions.london.settings import COVERAGE_SQUARE_METRES, FloodSource

REFERENCE_DIR = Path(__file__).with_name("reference")
BOUNDARY_FILE = REFERENCE_DIR / "london_boundary.geojson"
NO_DATA_FILE = REFERENCE_DIR / "no_data_squares.csv"


class CoverageStatus(Enum):
    OUTSIDE = "outside"
    NO_DATA = "no_data"
    NEAR_GAP = "near_gap"
    COVERED = "covered"


@dataclass(frozen=True)
class NoDataSquare:
    """A blank square inside London. Its corner is the south-west one, in metres."""

    source: str
    easting: int
    northing: int
    km2_inside_london: float


@dataclass(frozen=True)
class NoDataCheck:
    """How a saved No data list compares with the grid it describes."""

    matches: bool
    london_squares: int
    blank_squares: int
    london_km2: float
    no_data_km2: float
    near_gap_km2: float


def load_boundary(path: Path = BOUNDARY_FILE) -> shapely.Geometry:
    _, _, geometries, _ = read(path)
    return shapely.union_all(shapely.from_wkb(geometries))


def square_box(easting: int, northing: int) -> shapely.Geometry:
    size = COVERAGE_SQUARE_METRES
    return shapely.box(easting, northing, easting + size, northing + size)


def london_squares(boundary: shapely.Geometry) -> list[tuple[int, int, float]]:
    """List every square touching London, with how much of it lies inside."""
    size = COVERAGE_SQUARE_METRES
    min_x, min_y, max_x, max_y = shapely.bounds(boundary)
    squares = []
    for northing in range(int(min_y // size) * size, int(max_y) + 1, size):
        for easting in range(int(min_x // size) * size, int(max_x) + 1, size):
            square = square_box(easting, northing)
            if shapely.intersects(boundary, square):
                inside = float(shapely.area(shapely.intersection(boundary, square)))
                if inside > 0:
                    squares.append((easting, northing, inside / 1_000_000))
    return squares


def find_no_data_squares(
    dataset: rasterio.DatasetReader, boundary: shapely.Geometry, source_key: str
) -> list[NoDataSquare]:
    """Find squares inside London where a grid holds no flood zone at all."""
    size = COVERAGE_SQUARE_METRES
    resolution = int(dataset.transform.a)
    left, top = dataset.bounds.left, dataset.bounds.top
    if left % size or top % size:
        raise ValueError("The grid's corners must sit on whole coverage squares.")
    grid = dataset.read(1)
    cells = size // resolution
    blank = []
    for easting, northing, km2 in london_squares(boundary):
        column = int((easting - left) / resolution)
        row = int((top - northing - size) / resolution)
        if not np.any(grid[row : row + cells, column : column + cells]):
            blank.append(NoDataSquare(source_key, easting, northing, round(km2, 3)))
    return blank


def write_no_data_squares(squares: list[NoDataSquare], path: Path = NO_DATA_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["source", "easting", "northing", "km2_inside_london"])
        for square in sorted(squares, key=lambda s: (s.source, s.northing, s.easting)):
            writer.writerow(
                [square.source, square.easting, square.northing, square.km2_inside_london]
            )


def read_no_data_squares(path: Path = NO_DATA_FILE) -> list[NoDataSquare]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return [
            NoDataSquare(
                row["source"],
                int(row["easting"]),
                int(row["northing"]),
                float(row["km2_inside_london"]),
            )
            for row in csv.DictReader(file)
        ]


@dataclass
class Coverage:
    """The London boundary plus the squares known to have no data."""

    boundary: shapely.Geometry
    no_data: list[NoDataSquare]

    @classmethod
    def load(cls, boundary: Path = BOUNDARY_FILE, no_data: Path = NO_DATA_FILE) -> Coverage:
        shape = load_boundary(boundary)
        shapely.prepare(shape)
        return cls(shape, read_no_data_squares(no_data))

    def in_london(self, x: float, y: float) -> bool:
        return bool(shapely.contains_xy(self.boundary, x, y))

    def gap_squares(self, source_key: str) -> list[NoDataSquare]:
        return [square for square in self.no_data if square.source == source_key]

    def status(self, source: FloodSource, x: float, y: float, radius: float) -> CoverageStatus:
        """Work out what a result at this point can honestly claim."""
        if not self.in_london(x, y):
            return CoverageStatus.OUTSIDE
        if source.fully_downloaded:
            return CoverageStatus.COVERED
        point = shapely.Point(x, y)
        size = COVERAGE_SQUARE_METRES
        easting, northing = int(x // size) * size, int(y // size) * size
        squares = self.gap_squares(source.key)
        if any(s.easting == easting and s.northing == northing for s in squares):
            return CoverageStatus.NO_DATA
        if shapely.dwithin(point, shapely.boundary(self.boundary), radius) or any(
            shapely.dwithin(point, square_box(s.easting, s.northing), radius) for s in squares
        ):
            return CoverageStatus.NEAR_GAP
        return CoverageStatus.COVERED


def check_no_data_list(
    dataset: rasterio.DatasetReader, coverage: Coverage, source_key: str, radius: float
) -> NoDataCheck:
    """Compare the saved list with the grid, so the two can't quietly drift apart."""
    found = find_no_data_squares(dataset, coverage.boundary, source_key)
    saved = coverage.gap_squares(source_key)
    corners = {(square.easting, square.northing) for square in found}
    saved_corners = {(square.easting, square.northing) for square in saved}
    near = shapely.buffer(shapely.boundary(coverage.boundary), radius)
    for square in found:
        near = shapely.union(
            near, shapely.buffer(square_box(square.easting, square.northing), radius)
        )
    return NoDataCheck(
        matches=corners == saved_corners,
        london_squares=len(london_squares(coverage.boundary)),
        blank_squares=len(found),
        london_km2=float(shapely.area(coverage.boundary)) / 1_000_000,
        no_data_km2=sum(square.km2_inside_london for square in found),
        near_gap_km2=float(shapely.area(shapely.intersection(near, coverage.boundary))) / 1_000_000,
    )
