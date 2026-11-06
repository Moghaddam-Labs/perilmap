from __future__ import annotations

from collections.abc import Callable, Iterator

import httpx
import pytest
from fastapi.testclient import TestClient

from perilmap.api.app import create_app
from perilmap.api.postcodes import PostcodeClient
from perilmap.api.settings import Settings
from perilmap.core.assessment import RegionRegistry
from tests.core.fake_region import FakeRegion

INSIDE = {"latitude": 15.123456, "longitude": 30.654321}
OUTSIDE = {"latitude": -40.0, "longitude": 30.0}


def postcode_reply(request: httpx.Request) -> httpx.Response:
    if "SW1A" in str(request.url):
        return httpx.Response(
            200,
            json={
                "status": 200,
                "result": {"postcode": "SW1A 2AA", "latitude": 51.5, "longitude": -0.12},
            },
        )
    if "ZZ99" in str(request.url):
        return httpx.Response(
            200,
            json={
                "status": 200,
                "result": {"postcode": "ZZ99 9ZZ", "latitude": None, "longitude": None},
            },
        )
    if "EC1A" in str(request.url):
        return httpx.Response(500)
    if "E1" in str(request.url):
        raise httpx.ConnectError("Failed")
    if "N1" in str(request.url):
        return httpx.Response(200, text="not json")
    return httpx.Response(404, json={"status": 404, "error": "Postcode not found"})


MakeClient = Callable[..., TestClient]


@pytest.fixture
def make_client() -> Iterator[MakeClient]:
    clients: list[TestClient] = []

    def build(settings: Settings | None = None, regions: tuple = ()) -> TestClient:
        registry = RegionRegistry(regions or [FakeRegion()])
        postcode_client = PostcodeClient(transport=httpx.MockTransport(postcode_reply))
        app = create_app(registry, settings or Settings(), postcode_client)
        client = TestClient(app, raise_server_exceptions=False)
        client.__enter__()
        clients.append(client)
        return client

    yield build
    for client in clients:
        client.__exit__(None, None, None)


@pytest.fixture
def client(make_client: MakeClient) -> TestClient:
    return make_client()
