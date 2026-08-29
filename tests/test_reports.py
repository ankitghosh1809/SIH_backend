"""
tests/test_reports.py — Agent E

Self-test for GET /api/v1/scans/{scan_id}/report: create a scan through the real
API, fetch its PDF report, and check it's a real, non-trivial PDF; also covers
the 404 case for a scan id that doesn't exist.

Run from anywhere with:  pytest tests/test_reports.py
"""
import base64
import os
import sys

# Make `app` importable regardless of the current working directory pytest is
# invoked from (matches tests/test_agent_d.py).
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient

from app.main import app

# Same minimal-but-valid 1x1 PNG used in tests/test_scans_api.py — small enough to
# inline, valid enough to pass the scans route's image-signature check.
_DUMMY_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _dummy_png_bytes() -> bytes:
    return base64.b64decode(_DUMMY_PNG_BASE64)


def test_get_scan_report_returns_pdf():
    with TestClient(app) as client:
        files = {"file": ("fundus.png", _dummy_png_bytes(), "image/png")}
        created = client.post(
            "/api/v1/scans", files=files, data={"patient_name": "Test Patient"}
        ).json()
        scan_id = created["scan_id"]

        response = client.get(f"/api/v1/scans/{scan_id}/report")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 500
    assert response.content.startswith(b"%PDF")


def test_get_scan_report_missing_returns_404():
    with TestClient(app) as client:
        response = client.get("/api/v1/scans/does-not-exist/report")
    assert response.status_code == 404
