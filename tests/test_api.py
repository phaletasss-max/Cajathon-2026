"""Pruebas de la Fase 6: API HTTP."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.server import app


def test_api_health_and_clusters() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    response = client.get("/clusters?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "cluster_id" in data[0]
        assert "risk_score" in data[0]

    response = client.get("/applications?limit=5")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    response = client.get("/metrics")
    assert response.status_code == 200