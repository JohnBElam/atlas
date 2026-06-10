from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.api.envelope import envelope, error_envelope, success
from app.main import app

client = TestClient(app)


def test_envelope_shape() -> None:
    result = envelope(data={"ok": True}, error=None, meta={"page": 1})
    assert set(result.keys()) == {"data", "error", "meta"}
    assert result["data"] == {"ok": True}
    assert result["error"] is None
    assert result["meta"] == {"page": 1}


def test_success_helper() -> None:
    result = success({"status": "ok"})
    assert result["data"] == {"status": "ok"}
    assert result["error"] is None
    assert result["meta"] == {}


def test_error_envelope_status_and_body() -> None:
    response = error_envelope("not found", 404)
    assert response.status_code == 404
    body = json.loads(response.body)
    assert body["data"] is None
    assert body["error"] == "not found"
    assert body["meta"] == {}


def test_health_endpoint_envelope() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["data"]["status"] == "ok"
    assert isinstance(body["meta"], dict)


def test_unknown_source_returns_404_with_envelope() -> None:
    response = client.get("/api/v1/sources/00000000-0000-0000-0000-000000000099")
    assert response.status_code == 404
    body = response.json()
    assert body["data"] is None
    assert body["error"] is not None
    assert isinstance(body["meta"], dict)
