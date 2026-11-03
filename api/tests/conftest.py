import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("WORKSHOP_JWT_SECRET", "test-only-secret-not-for-production-use")


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    from app.main import create_app

    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as test_client:
        yield test_client
