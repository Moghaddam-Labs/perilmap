"""Write the API's contract to a file, so the website's types can be built from it."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from perilmap.api.app import create_app
from perilmap.core.assessment import RegionRegistry

CONTRACT_PATH = (
    Path(__file__).resolve().parent.parent / "web" / "src" / "lib" / "api" / "openapi.json"
)


def contract_text() -> str:
    # The contract doesn't depend on any region, so this needs no data files.
    contract = create_app(RegionRegistry([])).openapi()
    # Python versions word some status codes differently, so use the code to keep this file stable.
    for path in contract["paths"].values():
        for operation in path.values():
            for code, response in operation["responses"].items():
                response["description"] = code
    return json.dumps(contract, indent=2, sort_keys=True) + "\n"


def main() -> int:
    CONTRACT_PATH.write_text(contract_text(), encoding="utf-8")
    print(f"Wrote {CONTRACT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
