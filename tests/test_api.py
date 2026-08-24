"""
test_api.py
Unit and integration tests for Blink FastAPI routes.
"""

import pytest
from fastapi.testclient import TestClient
from server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_index_or_docs(client):
    response = client.get("/docs")
    assert response.status_code == 200


def test_frontend_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Blink" in response.text



def test_monitoring_status(client):
    response = client.get("/api/monitoring/status")
    assert response.status_code == 200
    data = response.json()
    assert "running" in data
    assert "stats" in data


def test_settings_endpoints(client):
    # GET settings
    get_res = client.get("/api/settings")
    assert get_res.status_code == 200
    cfg = get_res.json()
    assert "ear_threshold" in cfg

    # POST settings
    payload = {
        "camera_index": 0,
        "blink_rate_threshold": 14.0,
        "notification_cooldown": 60,
        "ear_threshold": 0.22,
        "twenty_twenty_twenty_enabled": True,
        "twenty_twenty_twenty_interval_sec": 1200,
        "sound_enabled": True,
        "calibrated": True,
    }
    post_res = client.post("/api/settings", json=payload)
    assert post_res.status_code == 200
    assert post_res.json()["settings"]["blink_rate_threshold"] == 14.0


def test_history_endpoints(client):
    res = client.get("/api/history")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    summary_res = client.get("/api/history/summary")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert "total_sessions" in summary


def test_calibration_status(client):
    res = client.get("/api/calibration/status")
    assert res.status_code == 200
    data = res.json()
    assert "calibrating" in data
    assert "ear_threshold" in data
