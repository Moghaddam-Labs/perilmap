from __future__ import annotations

import httpx
import pytest

from perilmap.api.postcodes import (
    InvalidPostcode,
    PostcodeClient,
    PostcodeNotFound,
    PostcodeServiceError,
    normalise_postcode,
)
from tests.api.conftest import postcode_reply


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("sw1a 2aa", "SW1A 2AA"),
        (" SW1A   2AA ", "SW1A 2AA"),
        ("SW1A2AA", "SW1A2AA"),
        ("E1 6AN", "E1 6AN"),
        ("M1 1AE", "M1 1AE"),
        ("B33 8TH", "B33 8TH"),
    ],
)
def test_real_postcode_shapes_are_accepted(text: str, expected: str) -> None:
    assert normalise_postcode(text) == expected


@pytest.mark.parametrize(
    "text",
    ["", "hello", "SW1A", "12345", "../admin", "SW1A 2AA/../x", "SW1A 2AA?x=1", "SW1A%202AA"],
)
def test_anything_else_never_reaches_the_service(text: str) -> None:
    calls = []

    def reply(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200)

    client = PostcodeClient(transport=httpx.MockTransport(reply))
    with pytest.raises(InvalidPostcode):
        client.lookup(text)
    assert calls == []


def test_position_is_returned_and_hidden_when_printed() -> None:
    client = PostcodeClient(transport=httpx.MockTransport(postcode_reply))
    position = client.lookup("sw1a 2aa")
    assert (position.postcode, position.latitude, position.longitude) == ("SW1A 2AA", 51.5, -0.12)
    assert "SW1A" not in repr(position) and "51.5" not in repr(position)


@pytest.mark.parametrize("postcode", ["AB1 2CD", "ZZ99 9ZZ"])
def test_unknown_postcode_or_no_position_is_not_found(postcode: str) -> None:
    client = PostcodeClient(transport=httpx.MockTransport(postcode_reply))
    with pytest.raises(PostcodeNotFound):
        client.lookup(postcode)


@pytest.mark.parametrize("postcode", ["EC1A 1BB", "E1 6AN", "N1 9GU"])
def test_service_failures_are_reported_as_failures(postcode: str) -> None:
    client = PostcodeClient(transport=httpx.MockTransport(postcode_reply))
    with pytest.raises(PostcodeServiceError):
        client.lookup(postcode)
