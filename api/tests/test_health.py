import socket
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest
from fastapi.testclient import TestClient

from support import auth_headers


class _HealthyUpstream(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"UP")

    def log_message(self, format: str, *args: object) -> None:
        return


@pytest.fixture
def healthy_upstream_url() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _HealthyUpstream)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}/q/health"
    server.shutdown()
    server.server_close()


def _closed_port_url() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    return f"http://127.0.0.1:{port}/q/health"


def _client_with_upstream(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, url: str) -> TestClient:
    from app.main import create_app

    monkeypatch.setenv("AUTH_HEALTH_URL", url)
    return TestClient(create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads")))


def test_backend_health_relays_upstream_status_and_body(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, healthy_upstream_url: str
) -> None:
    with _client_with_upstream(tmp_path, monkeypatch, healthy_upstream_url) as client:
        response = client.get("/api/backend-health", headers=auth_headers())
    assert response.status_code == 200
    assert response.json() == {"requestedBy": "student", "status": 200, "body": "UP"}


def test_backend_health_unreachable_returns_bad_gateway_without_details(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with _client_with_upstream(tmp_path, monkeypatch, _closed_port_url()) as client:
        response = client.get("/api/backend-health", headers=auth_headers())
    assert response.status_code == 502
    assert "127.0.0.1" not in response.text
    assert "Max retries" not in response.text
