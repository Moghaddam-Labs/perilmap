"""Write a small copy of London's boundary for the website's map.

The website draws it so people can see the area PerilMap covers, and checks whether a postcode or
pin falls inside it. The original is in British National Grid; the map needs latitude and longitude.
Needs the data extras: pip install -e ".[data]"
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import shapely
from rasterio.warp import transform_geom

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "perilmap" / "regions" / "london" / "reference" / "london_boundary.geojson"
TARGET = ROOT / "web" / "src" / "lib" / "geo" / "london-boundary.json"

# Removes detail smaller than about 15 m, far below what the map shows at the zoom where the line
# matters. The website only uses this to draw the line and give an early warning; the API makes the
# real decision with the full boundary.
SIMPLIFY_METRES = 15
DECIMALS = 5


def boundary() -> dict:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    (feature,) = data["features"]
    simple = shapely.simplify(shapely.geometry.shape(feature["geometry"]), SIMPLIFY_METRES)
    geometry = transform_geom("EPSG:27700", "EPSG:4326", shapely.geometry.mapping(simple))
    rings = [
        [[round(x, DECIMALS), round(y, DECIMALS)] for x, y in ring]
        for ring in geometry["coordinates"]
    ]
    return {"type": "Polygon", "coordinates": rings}


def main() -> int:
    TARGET.write_text(json.dumps(boundary(), separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Wrote {TARGET} ({TARGET.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
