"""The website's types are built from the API's contract, so the two must never drift apart."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from perilmap.core.models import DISCLAIMER
from perilmap.regions.london import wording

ROOT = Path(__file__).resolve().parents[2]


def _export_script():
    spec = importlib.util.spec_from_file_location(
        "export_openapi", ROOT / "scripts" / "export_openapi.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_websites_copy_of_the_contract_is_up_to_date():
    script = _export_script()
    message = "Run: python scripts/export_openapi.py, then npm run api:types in web/"
    assert script.CONTRACT_PATH.read_text(encoding="utf-8") == script.contract_text(), message


def test_the_website_footer_uses_the_same_disclaimer_as_results():
    footer = (ROOT / "web" / "src" / "components" / "SiteFooter.tsx").read_text(encoding="utf-8")
    assert DISCLAIMER in footer


def test_the_websites_source_list_matches_the_api():
    web = (ROOT / "web" / "src" / "lib" / "dataSources.ts").read_text(encoding="utf-8")
    sources = [
        wording.RIVERS_AND_SEA_SOURCE,
        wording.SURFACE_WATER_SOURCE,
        wording.HEAT_SOURCE,
        wording.SUBSIDENCE_SOURCE,
    ]
    for source in sources:
        for value in (source.publisher, source.url, source.last_updated, source.resolution):
            assert value in web, f"web/src/lib/dataSources.ts is missing: {value}"
