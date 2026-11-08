"""Work out how much of each London borough is in a rivers and sea flood zone, for the website.

Needs two files that aren't in the repo:
- the rivers and sea grid, built by `python -m data_test build` (grids/rivers_and_sea_5m.tif)
- London_Borough_Excluding_MHW.shp from the London Datastore's Statistical GIS Boundary Files,
  https://data.london.gov.uk/dataset/statistical-gis-boundary-files-london (unzip the ESRI folder)

Run from the repo root:
    python scripts/export_borough_flood.py path/to/London_Borough_Excluding_MHW.shp

Needs the data extras: pip install -e ".[data]"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
import shapely
from pyogrio.raw import read
from rasterio.features import geometry_mask
from rasterio.windows import from_bounds

from perilmap.regions.london.settings import BAND_BITS

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GRID = ROOT / "grids" / "rivers_and_sea_5m.tif"
TARGET = ROOT / "web" / "src" / "lib" / "borough-flood.json"

LOW_OR_HIGHER = BAND_BITS["Low"] | BAND_BITS["Medium"] | BAND_BITS["High"]
VERY_LOW = BAND_BITS["Very Low"]


def borough_shares(boundaries: Path, grid: Path) -> list[dict]:
    meta, _, geometries, fields = read(boundaries)
    columns = list(meta["fields"])
    names = fields[columns.index("NAME")]
    codes = fields[columns.index("GSS_CODE")]
    boroughs = []
    with rasterio.open(grid) as source:
        for name, code, wkb in zip(names, codes, geometries, strict=True):
            borough = shapely.from_wkb(wkb)
            window = from_bounds(*borough.bounds, transform=source.transform)
            window = window.round_offsets().round_lengths()
            cells = source.read(1, window=window)
            # A cell belongs to a borough when its centre is inside, so no edge is counted twice.
            inside = ~geometry_mask(
                [borough], cells.shape, source.window_transform(window), all_touched=False
            )
            land = cells[inside]
            low_or_higher = np.count_nonzero(land & LOW_OR_HIGHER)
            # Very Low only, so the two shares never overlap.
            very_low = np.count_nonzero((land & VERY_LOW) & ((land & LOW_OR_HIGHER) == 0))
            boroughs.append(
                {
                    "name": str(name),
                    "code": str(code),
                    "low_or_higher_percent": round(100 * low_or_higher / land.size, 1),
                    "very_low_percent": round(100 * very_low / land.size, 1),
                }
            )
    return sorted(boroughs, key=lambda item: (-item["low_or_higher_percent"], item["name"]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("boundaries", type=Path, help="London_Borough_Excluding_MHW.shp")
    parser.add_argument("--grid", type=Path, default=DEFAULT_GRID)
    args = parser.parse_args()
    boroughs = borough_shares(args.boundaries, args.grid)
    if len(boroughs) != 33:
        print(f"Expected London's 33 boroughs, found {len(boroughs)}.", file=sys.stderr)
        return 1
    data = {
        "note": "Made by scripts/export_borough_flood.py. Don't edit by hand.",
        "boroughs": boroughs,
    }
    TARGET.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {TARGET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
