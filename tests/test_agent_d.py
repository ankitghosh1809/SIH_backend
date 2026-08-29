"""
Agent D's self-test — health + metrics endpoints, CORS headers.

(The original version of this file also asserted Agent D's own throwaway stub
scan-router responses, which was only valid before stitching. Now that Agent
C's real app/api/scans.py is mounted, that coverage lives in
tests/test_scans_api.py instead — asserting the stub shape here would just be
testing for the wrong behavior.)

Run from anywhere with:  pytest tests/test_agent_d.py
(needs `pip install pytest httpx2` in addition to requirements.txt — httpx2
backs FastAPI's TestClient and isn't needed at runtime, only for this test file.)
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