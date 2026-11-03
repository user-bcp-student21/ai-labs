import pytest
from fastapi.testclient import TestClient

from support import auth_headers, bearer, jwt_token, legacy_token


def test_legacy_base64_token_is_rejected(client: TestClient) -> None:
    response = client.get("/api/tasks", headers=bearer(legacy_token()))
    assert response.status_code == 401


def test_signed_token_is_accepted(client: TestClient) -> None:
    response = client.get("/api/tasks", headers=bearer(jwt_token()))
    assert response.status_code == 200


@pytest.mark.parametrize(
    "claims",
    [
        {"ttl_seconds": -60},
        {"secret": "another-test-only-secret-value"},
        {"issuer": "someone-else"},
        {"audience": "someone-else"},
    ],
)
def test_forged_or_expired_signed_token_is_rejected(client: TestClient, claims: dict) -> None:
    response = client.get("/api/tasks", headers=bearer(jwt_token(**claims)))
    assert response.status_code == 401


def test_invalid_token_detail_starts_with_invalid_token(client: TestClient) -> None:
    response = client.get("/api/tasks", headers=bearer("not-a-token"))
    assert response.status_code == 401
    assert response.json()["detail"].startswith("Invalid token")


def test_invalid_token_detail_is_generic(client: TestClient) -> None:
    response = client.get("/api/tasks", headers=bearer("not-a-token"))
    assert response.json() == {"detail": "Invalid token"}


def test_owner_mismatch_is_forbidden_on_list(client: TestClient) -> None:
    response = client.get("/api/tasks", params={"owner": "trainer"}, headers=auth_headers())
    assert response.status_code == 403


def test_owner_mismatch_is_forbidden_on_summary(client: TestClient) -> None:
    response = client.get("/api/summary", params={"owner": "trainer"}, headers=auth_headers())
    assert response.status_code == 403


def test_owner_mismatch_is_forbidden_on_create(client: TestClient) -> None:
    response = client.post(
        "/api/tasks",
        headers=auth_headers(),
        json={"title": "x", "description": "y", "owner": "trainer"},
    )
    assert response.status_code == 403


def test_owner_equal_to_identity_is_allowed(client: TestClient) -> None:
    listed = client.get("/api/tasks", params={"owner": "student"}, headers=auth_headers())
    created = client.post("/api/tasks", headers=auth_headers(), json={"title": "x", "owner": "student"})
    assert listed.status_code == 200
    assert created.status_code == 201
    assert created.json()["owner"] == "student"
