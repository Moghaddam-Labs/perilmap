from __future__ import annotations

import ast
import json
import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import perilmap.api
from perilmap.api.app import create_app
from perilmap.api.settings import Settings
from perilmap.core.assessment import RegionRegistry
from perilmap.core.models import DISCLAIMER, NOT_AVAILABLE_HERE
from tests.api.conftest import INSIDE, OUTSIDE, MakeClient
from tests.core.fake_region import BrokenPeril, FakeRegion, LavaPeril, WarmthPeril

ASSESS = "/v1/assessments"
LOOKUP = "/v1/postcodes/lookup"


def post_from(client: TestClient, address: str) -> int:
    response = client.post(ASSESS, json=INSIDE, headers={"x-forwarded-for": address})
    return response.status_code


def test_health_is_light_and_needs_no_location(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_assessment_returns_every_result_with_its_explanation(client: TestClient) -> None:
    body = client.post(ASSESS, json=INSIDE).json()
    assert body["available_here"] is True
    assert body["region_name"] == "Testland"
    assert body["disclaimer"] == DISCLAIMER
    assert body["not_covered"] == ["Meteor strikes"]
    lava, warmth = body["results"]
    for field in ("what_this_means", "how_sure", "what_you_can_do", "sources", "summary"):
        assert lava[field]
    assert lava["status"] == "available"
    assert lava["sources"][0]["last_updated"] == "January 2026"
    assert lava["sources"][0]["resolution"] == "10 m grid"


def test_measurements_say_which_type_they_are(client: TestClient) -> None:
    lava, warmth = client.post(ASSESS, json=INSIDE).json()["results"]
    assert lava["measurement"]["type"] == "nearest_zones"
    assert lava["measurement"]["zones"] == [
        {"band": "High", "metres": 120.0, "label": "About 120 m"}
    ]
    assert warmth["measurement"]["type"] == "area_comparison"
    assert warmth["measurement"]["calculation_note"]


def test_outside_every_region_says_not_available(client: TestClient) -> None:
    body = client.post(ASSESS, json=OUTSIDE).json()
    assert body["available_here"] is False
    assert body["message"] == NOT_AVAILABLE_HERE
    assert body["results"] == []


def test_one_failed_check_still_returns_the_others(make_client: MakeClient) -> None:
    region = FakeRegion(perils=(LavaPeril(), BrokenPeril(), WarmthPeril()))
    results = make_client(regions=(region,)).post(ASSESS, json=INSIDE).json()["results"]
    assert [result["status"] for result in results] == [
        "available",
        "temporarily_unavailable",
        "available",
    ]
    assert results[1]["measurement"] is None


@pytest.mark.parametrize(
    "body",
    [
        {"latitude": 91, "longitude": 0},
        {"latitude": 0, "longitude": 181},
        {"latitude": "51.5", "longitude": 0},
        {"latitude": 51.5},
        {"latitude": 51.5, "longitude": 0, "extra": 1},
        {"latitude": True, "longitude": 0},
    ],
)
def test_bad_locations_are_refused_without_repeating_them(client: TestClient, body: dict) -> None:
    response = client.post(ASSESS, json=body)
    assert response.status_code == 422
    assert list(response.json()) == ["detail"]
    assert "51.5" not in response.text and "input" not in response.text


def test_location_in_the_address_is_not_accepted(client: TestClient) -> None:
    response = client.get(ASSESS, params=INSIDE)
    assert response.status_code == 405
    assert client.post(ASSESS, params=INSIDE).status_code in (413, 422)


def test_location_never_appears_in_logs(
    make_client: MakeClient, caplog: pytest.LogCaptureFixture
) -> None:
    region = FakeRegion(perils=(BrokenPeril(),))
    client = make_client(regions=(region,))
    with caplog.at_level(logging.DEBUG):
        client.post(ASSESS, json=INSIDE)
        client.post(ASSESS, json={"latitude": 95.654321, "longitude": 30.654321})
        client.post(LOOKUP, json={"postcode": "SW1A 2AA"})
        client.post(LOOKUP, json={"postcode": "EC1A 1BB"})
    for secret in ("15.123", "30.654", "95.654", "SW1A", "EC1A"):
        assert secret not in caplog.text


def test_unexpected_errors_reveal_nothing(make_client: MakeClient, monkeypatch) -> None:
    client = make_client()

    def fail(*args: object) -> None:
        raise RuntimeError("Secret at 15.123456, 30.654321")

    monkeypatch.setattr("perilmap.api.app.assess", fail)
    response = client.post(ASSESS, json=INSIDE)
    assert response.status_code == 500
    assert "Secret" not in response.text and "15.123" not in response.text


def test_every_reply_carries_the_security_headers(client: TestClient) -> None:
    for response in (client.get("/health"), client.post(ASSESS, json=INSIDE), client.get("/nope")):
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["referrer-policy"] == "no-referrer"
        assert "default-src 'none'" in response.headers["content-security-policy"]


def test_large_or_unsized_bodies_are_refused(client: TestClient) -> None:
    big = json.dumps({"postcode": "A" * 2_000})
    headers = {"Content-Type": "application/json"}
    assert client.post(LOOKUP, content=big, headers=headers).status_code == 413


def test_clients_are_rate_limited(make_client: MakeClient) -> None:
    client = make_client(Settings(client_requests_per_minute=2))
    assert client.post(ASSESS, json=INSIDE).status_code == 200
    assert client.post(LOOKUP, json={"postcode": "SW1A 2AA"}).status_code == 200
    refused = client.post(ASSESS, json=INSIDE)
    assert refused.status_code == 429
    assert int(refused.headers["retry-after"]) >= 1
    assert refused.headers["cache-control"] == "no-store"
    assert client.get("/health").status_code == 200


def test_total_rate_limit_applies_across_visitors(make_client: MakeClient) -> None:
    client = make_client(Settings(total_requests_per_minute=1, trust_forwarded_for=True))
    assert (
        client.post(ASSESS, json=INSIDE, headers={"x-forwarded-for": "1.1.1.1"}).status_code == 200
    )
    assert (
        client.post(ASSESS, json=INSIDE, headers={"x-forwarded-for": "2.2.2.2"}).status_code == 429
    )


def test_spoofing_the_forwarded_header_cannot_dodge_the_limit(make_client: MakeClient) -> None:
    client = make_client(Settings(client_requests_per_minute=1, trust_forwarded_for=True))
    first = client.post(ASSESS, json=INSIDE, headers={"x-forwarded-for": "9.9.9.9, 2.2.2.2"})
    spoof = client.post(ASSESS, json=INSIDE, headers={"x-forwarded-for": "8.8.8.8, 2.2.2.2"})
    other = client.post(ASSESS, json=INSIDE, headers={"x-forwarded-for": "3.3.3.3"})
    assert (first.status_code, spoof.status_code, other.status_code) == (200, 429, 200)


def test_forwarded_header_is_ignored_unless_trusted(make_client: MakeClient) -> None:
    client = make_client(Settings(client_requests_per_minute=1))
    assert (
        client.post(ASSESS, json=INSIDE, headers={"x-forwarded-for": "1.1.1.1"}).status_code == 200
    )
    assert (
        client.post(ASSESS, json=INSIDE, headers={"x-forwarded-for": "2.2.2.2"}).status_code == 429
    )


def test_postcode_lookup_returns_position_and_credit(client: TestClient) -> None:
    body = client.post(LOOKUP, json={"postcode": "sw1a 2aa"}).json()
    assert body == {
        "postcode": "SW1A 2AA",
        "latitude": 51.5,
        "longitude": -0.12,
        "attribution": "Postcode lookup by postcodes.io",
    }


@pytest.mark.parametrize(
    ("postcode", "status"),
    [
        ("not a postcode", 422),
        ("AB1 2CD", 404),
        ("ZZ99 9ZZ", 404),
        ("EC1A 1BB", 503),
        ("E1 6AN", 503),
    ],
)
def test_postcode_failures_explain_themselves(
    client: TestClient, postcode: str, status: int
) -> None:
    response = client.post(LOOKUP, json={"postcode": postcode})
    assert response.status_code == status
    assert list(response.json()) == ["detail"]
    assert postcode not in response.text


def test_docs_are_off_unless_asked_for(make_client: MakeClient) -> None:
    assert make_client().get("/docs").status_code == 404
    assert make_client().get("/openapi.json").status_code == 404
    assert make_client(Settings(show_docs=True)).get("/docs").status_code == 200


def test_docs_page_is_not_blocked_by_the_security_policy(make_client: MakeClient) -> None:
    client = make_client(Settings(show_docs=True))
    assert "content-security-policy" not in client.get("/docs").headers
    assert "content-security-policy" in client.get("/health").headers


def test_only_listed_websites_can_call_the_api(make_client: MakeClient) -> None:
    client = make_client(Settings(allowed_origins=("https://perilmap.example",)))
    allowed = client.post(ASSESS, json=INSIDE, headers={"origin": "https://perilmap.example"})
    other = client.post(ASSESS, json=INSIDE, headers={"origin": "https://evil.example"})
    assert allowed.headers["access-control-allow-origin"] == "https://perilmap.example"
    assert "access-control-allow-origin" not in other.headers


def test_browser_preflight_is_answered(make_client: MakeClient) -> None:
    client = make_client(Settings(allowed_origins=("https://perilmap.example",)))
    response = client.options(
        ASSESS,
        headers={
            "origin": "https://perilmap.example",
            "access-control-request-method": "POST",
            "access-control-request-headers": "content-type",
        },
    )
    assert response.status_code == 200


def test_rate_limited_replies_are_readable_by_the_website(make_client: MakeClient) -> None:
    client = make_client(
        Settings(allowed_origins=("https://perilmap.example",), client_requests_per_minute=1)
    )
    headers = {"origin": "https://perilmap.example"}
    client.post(ASSESS, json=INSIDE, headers=headers)
    refused = client.post(ASSESS, json=INSIDE, headers=headers)
    assert refused.status_code == 429
    assert refused.headers["access-control-allow-origin"] == "https://perilmap.example"


def test_settings_are_read_from_the_environment() -> None:
    settings = Settings.from_env(
        {
            "PERILMAP_DATA_DIR": "/data",
            "PERILMAP_ALLOWED_ORIGINS": "https://a.example, https://b.example",
            "PERILMAP_TRUST_FORWARDED_FOR": "true",
            "PERILMAP_CLIENT_RATE_LIMIT": "5",
        }
    )
    assert str(settings.data_dir) == "/data"
    assert settings.allowed_origins == ("https://a.example", "https://b.example")
    assert settings.trust_forwarded_for is True
    assert settings.client_requests_per_minute == 5
    assert Settings.from_env({}).allowed_origins == ()


def test_missing_data_stops_the_app_from_starting() -> None:
    def fail() -> RegionRegistry:
        raise FileNotFoundError("Missing data files")

    app = create_app(fail)
    with pytest.raises(FileNotFoundError), TestClient(app):
        pass


def test_api_contains_no_region_details() -> None:
    allowed = {"main.py"}
    for path in Path(perilmap.api.__file__).parent.glob("*.py"):
        if path.name in allowed:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("perilmap.regions"), path
