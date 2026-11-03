from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import CORS_ORIGINS_ENV
from app.cors import load_cors_origins
from support import auth_headers

ALLOWED_ORIGIN = "http://localhost:4200"
OTHER_ALLOWED_ORIGIN = "https://app.example.test"
FOREIGN_ORIGIN = "https://evil.example"

ClientFactory = Callable[[str | None], TestClient]


@pytest.fixture
def client_with_origins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ClientFactory:
    from app.main import create_app

    def build(origins: str | None) -> TestClient:
        if origins is None:
            monkeypatch.delenv(CORS_ORIGINS_ENV, raising=False)
        else:
            monkeypatch.setenv(CORS_ORIGINS_ENV, origins)
        return TestClient(create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads")))

    return build


def preflight(client: TestClient, origin: str):
    return client.options(
        "/api/tasks",
        headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
    )


def test_preflight_from_default_origin_is_allowed_with_credentials(client_with_origins: ClientFactory) -> None:
    response = preflight(client_with_origins(None), ALLOWED_ORIGIN)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert response.headers["access-control-allow-credentials"] == "true"


def test_preflight_from_unlisted_origin_is_rejected_without_allow_origin(client_with_origins: ClientFactory) -> None:
    response = preflight(client_with_origins(None), FOREIGN_ORIGIN)
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_configured_origins_replace_defaults(client_with_origins: ClientFactory) -> None:
    client = client_with_origins(f" {ALLOWED_ORIGIN} , {OTHER_ALLOWED_ORIGIN} ")
    assert preflight(client, ALLOWED_ORIGIN).headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert preflight(client, OTHER_ALLOWED_ORIGIN).headers["access-control-allow-origin"] == OTHER_ALLOWED_ORIGIN
    assert "access-control-allow-origin" not in preflight(client, FOREIGN_ORIGIN).headers


def test_configured_origins_exclude_default_origin(client_with_origins: ClientFactory) -> None:
    client = client_with_origins(OTHER_ALLOWED_ORIGIN)
    assert "access-control-allow-origin" not in preflight(client, ALLOWED_ORIGIN).headers


def test_actual_request_from_unlisted_origin_gets_no_cors_headers_and_keeps_contract(
    client_with_origins: ClientFactory,
) -> None:
    client = client_with_origins(None)
    response = client.get("/api/tasks", headers={**auth_headers(), "Origin": FOREIGN_ORIGIN})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert "access-control-allow-origin" not in response.headers


def test_actual_request_from_listed_origin_gets_cors_headers(client_with_origins: ClientFactory) -> None:
    client = client_with_origins(None)
    response = client.get("/api/tasks", headers={**auth_headers(), "Origin": ALLOWED_ORIGIN})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN


def test_unauthenticated_request_still_returns_401(client_with_origins: ClientFactory) -> None:
    response = client_with_origins(None).get("/api/tasks", headers={"Origin": ALLOWED_ORIGIN})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


@pytest.mark.parametrize("value", ["*", f"{ALLOWED_ORIGIN},*", " * "])
def test_wildcard_origin_is_rejected(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv(CORS_ORIGINS_ENV, value)
    with pytest.raises(RuntimeError, match=CORS_ORIGINS_ENV):
        load_cors_origins()


@pytest.mark.parametrize("value", ["", "  ", " , ,"])
def test_blank_value_falls_back_to_default_origins(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv(CORS_ORIGINS_ENV, value)
    assert ALLOWED_ORIGIN in load_cors_origins()
    assert "*" not in load_cors_origins()
