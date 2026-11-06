"""Settings read from environment variables, so nothing sensitive sits in the code."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


def _flag(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes"}


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path("grids")
    allowed_origins: tuple[str, ...] = ()
    # Only turn this on behind a proxy that adds the client's address to X-Forwarded-For.
    trust_forwarded_for: bool = False
    show_docs: bool = False
    client_requests_per_minute: int = 30
    total_requests_per_minute: int = 300
    postcode_timeout_seconds: float = 3.0

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        values = os.environ if env is None else env
        origins = values.get("PERILMAP_ALLOWED_ORIGINS", "")
        return cls(
            data_dir=Path(values.get("PERILMAP_DATA_DIR", "grids")),
            allowed_origins=tuple(item.strip() for item in origins.split(",") if item.strip()),
            trust_forwarded_for=_flag(values.get("PERILMAP_TRUST_FORWARDED_FOR")),
            show_docs=_flag(values.get("PERILMAP_SHOW_DOCS")),
            client_requests_per_minute=int(values.get("PERILMAP_CLIENT_RATE_LIMIT", "30")),
            total_requests_per_minute=int(values.get("PERILMAP_TOTAL_RATE_LIMIT", "300")),
        )
