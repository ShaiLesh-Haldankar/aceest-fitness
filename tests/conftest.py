import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402


@pytest.fixture
def app(tmp_path):
    return create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_client(client):
    payload = {"name": "Arjun", "age": 28, "height": 175, "weight": 80, "program": "FL"}
    resp = client.post("/api/clients", json=payload)
    assert resp.status_code == 201
    return resp.get_json()
