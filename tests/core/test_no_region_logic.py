"""Guard the core against picking up details of any real place."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

import perilmap.core

CORE_FILES = sorted(Path(perilmap.core.__file__).parent.glob("*.py"))
FORBIDDEN = re.compile(
    r"\b(london|england|britain|british|uk|thames|environment agency|bgs|gla|fema|california|"
    r"florida|us|usa|postcode|zip code|epsg|27700|bng|easting|northing)\b",
    re.IGNORECASE,
)
ALLOWED_INTERNAL_IMPORTS = "perilmap.core"
FRAMEWORKS = {"fastapi", "pydantic", "rasterio", "shapely", "pyogrio", "numpy", "data_test"}


def test_core_files_are_found() -> None:
    assert len(CORE_FILES) >= 3


@pytest.mark.parametrize("path", CORE_FILES, ids=lambda path: path.name)
def test_core_mentions_no_real_place(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    matches = [match.group() for match in FORBIDDEN.finditer(source) if match.group() != "us"]
    assert matches == []


@pytest.mark.parametrize("path", CORE_FILES, ids=lambda path: path.name)
def test_core_stays_free_of_frameworks_and_data_libraries(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
            if node.module.startswith("perilmap"):
                assert node.module.startswith(ALLOWED_INTERNAL_IMPORTS)
    assert not imported & FRAMEWORKS
