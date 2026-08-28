"""
Agent D's self-test — exercises exactly what the work order's Self-test section
asks for: health + metrics endpoints, CORS headers, and the mounted stub scan
routes.

Run from anywhere with:  pytest backend/tests/test_agent_d.py
(needs `pip install pytest httpx` in addition to requirements.txt — httpx backs
FastAPI's TestClient and isn't needed at runtime, only for this test file.)
"""

import os
import sys

# Make `app` importable regardless of the current working directory pytest is
# invoked from.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_metrics_returns_nulls_with_no_data_yet():
    with TestClient(app) as client:
        response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    assert response.json() == {
        "classical": None,
        "hybrid_quantum": None,
        "evaluated_on": None,
    }


def test_cors_headers_present_for_allowed_origin():
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/health", headers={"Origin": "http://localhost:3000"}
        )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_stub_scan_routes_reachable_through_mounted_router():
    with TestClient(app) as client:
        assert client.get("/api/v1/scans").json() == []
        assert client.get("/api/v1/scans/abc123").json() == {
            "stub": True,
            "scan_id": "abc123",
        }
        assert client.get("/api/v1/scans/abc123/heatmap").json() == {"stub": True}
        assert client.post("/api/v1/scans").status_code == 200
