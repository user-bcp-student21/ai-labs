from pathlib import Path

from fastapi.testclient import TestClient

from support import auth_headers

ONE_MIB = 1024 * 1024


def test_upload_keeps_name_and_size(client: TestClient) -> None:
    content = b"Login must be accessible"
    response = client.post(
        "/api/requirements",
        headers=auth_headers(),
        files={"file": ("requirements.txt", content, "text/plain")},
    )
    assert response.status_code == 201
    assert response.json()["fileName"] == "requirements.txt"
    assert response.json()["size"] == len(content)


def test_upload_path_traversal_does_not_leave_upload_dir(client: TestClient, tmp_path: Path) -> None:
    client.post(
        "/api/requirements",
        headers=auth_headers(),
        files={"file": ("../escape.txt", b"x", "text/plain")},
    )
    assert not (tmp_path / "escape.txt").exists()


def test_upload_does_not_overwrite_existing_file(client: TestClient, tmp_path: Path) -> None:
    first = client.post(
        "/api/requirements",
        headers=auth_headers(),
        files={"file": ("requirements.txt", b"first", "text/plain")},
    )
    second = client.post(
        "/api/requirements",
        headers=auth_headers(),
        files={"file": ("requirements.txt", b"second", "text/plain")},
    )
    assert first.status_code == 201
    assert second.status_code == 409
    assert (tmp_path / "uploads" / "requirements.txt").read_bytes() == b"first"


def test_upload_rejects_extension_outside_allowlist(client: TestClient) -> None:
    response = client.post(
        "/api/requirements",
        headers=auth_headers(),
        files={"file": ("payload.exe", b"x", "application/octet-stream")},
    )
    assert response.status_code == 422


def test_upload_rejects_file_over_size_limit(client: TestClient) -> None:
    response = client.post(
        "/api/requirements",
        headers=auth_headers(),
        files={"file": ("requirements.txt", b"a" * (ONE_MIB + 1), "text/plain")},
    )
    assert response.status_code == 413
