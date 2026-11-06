"""Find a postcode's position through postcodes.io.

The request comes from our server, so postcodes.io sees the postcode but not who's searching.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from urllib.parse import quote

import httpx

# These libraries log each request's address, which here would include the postcode.
for _library in ("httpx", "httpcore"):
    logging.getLogger(_library).setLevel(logging.WARNING)

POSTCODES_IO = "https://api.postcodes.io"
ATTRIBUTION = "Postcode lookup by postcodes.io"
POSTCODE_PATTERN = re.compile(r"^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$")


class InvalidPostcode(ValueError):
    """The text isn't shaped like a UK postcode."""


class PostcodeNotFound(LookupError):
    """It's shaped like a postcode, but none exists or it has no position."""


class PostcodeServiceError(RuntimeError):
    """The lookup service couldn't answer."""


@dataclass(frozen=True, repr=False)
class PostcodePosition:
    postcode: str
    latitude: float
    longitude: float

    def __repr__(self) -> str:
        return "PostcodePosition(hidden)"


def normalise_postcode(text: str) -> str:
    """Tidy a postcode, refusing anything else before it can reach another service."""
    cleaned = " ".join(text.upper().split())
    if not POSTCODE_PATTERN.fullmatch(cleaned):
        raise InvalidPostcode("That doesn't look like a UK postcode.")
    return cleaned


class PostcodeClient:
    def __init__(self, timeout: float = 3.0, transport: httpx.BaseTransport | None = None) -> None:
        self._client = httpx.Client(
            base_url=POSTCODES_IO,
            timeout=timeout,
            transport=transport,
            follow_redirects=False,
            headers={"User-Agent": "PerilMap"},
        )

    def close(self) -> None:
        self._client.close()

    def lookup(self, text: str) -> PostcodePosition:
        postcode = normalise_postcode(text)
        try:
            response = self._client.get(f"/postcodes/{quote(postcode, safe='')}")
        except httpx.HTTPError:
            raise PostcodeServiceError("The postcode service couldn't be reached.") from None
        if response.status_code == httpx.codes.NOT_FOUND:
            raise PostcodeNotFound("We couldn't find that postcode.")
        if response.status_code != httpx.codes.OK:
            raise PostcodeServiceError("The postcode service returned an error.")
        try:
            result = response.json()["result"]
            latitude, longitude = result["latitude"], result["longitude"]
            found = result["postcode"]
        except (ValueError, KeyError, TypeError):
            raise PostcodeServiceError("The postcode service sent an unexpected reply.") from None
        if latitude is None or longitude is None:
            raise PostcodeNotFound("We couldn't find a position for that postcode.")
        return PostcodePosition(str(found), float(latitude), float(longitude))
