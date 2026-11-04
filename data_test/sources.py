"""Read flood polygons from downloaded files. No database needed."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import pyogrio
import shapely

from data_test.config import BAND_ORDER, BNG_SRID, LONDON_BBOX_BNG, FloodSource


class SourceFileError(ValueError):
    """A downloaded file doesn't match what the test expects."""


def normalise_band(raw: object) -> str:
    """Turn a source value such as 'very low' into 'Very Low'. Refuse unknown bands."""
    cleaned = " ".join(str(raw).replace("_", " ").split()).lower()
    for band in BAND_ORDER:
        if cleaned == band.lower():
            return band
    raise SourceFileError(f"Unknown flood band {raw!r}. Expected one of {BAND_ORDER}.")


def resolve_layer(path: Path, source: FloodSource, requested: str | None = None) -> str:
    """Find the layer to read, matching names regardless of case."""
    layers = [str(row[0]) for row in pyogrio.list_layers(path)]
    wanted = requested or source.default_layer
    for layer in layers:
        if layer.lower() == wanted.lower():
            return layer
    if requested is None and len(layers) == 1:
        return layers[0]
    raise SourceFileError(
        f"Layer {wanted!r} is not in {path.name}. Layers found: {', '.join(layers)}. "
        "Run the inspect command, then pass the right one with --layer."
    )


def resolve_band_field(path: Path, layer: str, source: FloodSource) -> str:
    """Find the band column, matching names regardless of case."""
    fields = [str(name) for name in pyogrio.read_info(path, layer=layer)["fields"]]
    by_lower = {name.lower(): name for name in fields}
    for candidate in source.band_fields:
        if candidate.lower() in by_lower:
            return by_lower[candidate.lower()]
    raise SourceFileError(
        f"No band field in {path.name}, layer {layer}. Fields found: {', '.join(fields)}."
    )


def check_crs(path: Path, layer: str) -> None:
    """Refuse files that aren't in British National Grid, so distances stay in metres."""
    crs = str(pyogrio.read_info(path, layer=layer)["crs"] or "")
    if str(BNG_SRID) not in crs and "OSGB" not in crs.upper():
        raise SourceFileError(
            f"{path.name} uses {crs or 'an unknown coordinate system'}, "
            f"but the test needs EPSG:{BNG_SRID}. Download it in British National Grid."
        )


def iter_batches(
    path: Path,
    source: FloodSource,
    *,
    layer: str | None = None,
    bbox: tuple[int, int, int, int] = LONDON_BBOX_BNG,
    batch_size: int = 5_000,
) -> Iterator[list[tuple[str, bytes]]]:
    """Yield lists of (band, WKB geometry) without loading the whole file into memory."""
    layer_name = resolve_layer(path, source, layer)
    band_field = resolve_band_field(path, layer_name, source)
    check_crs(path, layer_name)
    with pyogrio.open_arrow(
        path,
        layer=layer_name,
        columns=[band_field],
        bbox=bbox,
        batch_size=batch_size,
        use_pyarrow=True,
    ) as (meta, reader):
        geometry_column = meta["geometry_name"] or "wkb"
        for batch in reader:
            bands = batch.column(band_field).to_pylist()
            geometries = batch.column(geometry_column).to_pylist()
            yield [
                (normalise_band(band), bytes(geometry))
                for band, geometry in zip(bands, geometries, strict=True)
                if geometry is not None
            ]


@dataclass
class Estimate:
    """How much geometry a source holds inside the test area."""

    features: int = 0
    vertices: int = 0
    geometry_bytes: int = 0
    bands: Counter[str] = field(default_factory=Counter)

    @property
    def geometry_mb(self) -> float:
        return self.geometry_bytes / 1_048_576


def estimate(
    paths: Sequence[Path],
    source: FloodSource,
    *,
    layer: str | None = None,
    simplify_metres: float = 0.0,
) -> Estimate:
    """Measure raw geometry size before anything touches the database."""
    result = Estimate()
    for path in paths:
        for batch in iter_batches(path, source, layer=layer):
            geometries = shapely.from_wkb([geometry for _, geometry in batch])
            if simplify_metres > 0:
                geometries = shapely.simplify(geometries, simplify_metres, preserve_topology=True)
            result.features += len(batch)
            result.vertices += int(shapely.get_num_coordinates(geometries).sum())
            result.geometry_bytes += sum(len(wkb) for wkb in shapely.to_wkb(geometries))
            result.bands.update(band for band, _ in batch)
    return result
