"""
tests/test_explainability.py — Round 3 (Agent P)

Self-test for GET /api/v1/scans/{scan_id}/explain: create a scan through the
real API, fetch its explanation, check the shape/bounds of what comes back;
also covers the 404 case and a couple of direct compute_uncertainty() checks
that don't need to go through the API (per the work order's self-test
section).
"""
import base64

from fastapi.testclient import TestClient

from app.main import app
from app.ml.inference import compute_uncertainty

# Same minimal-but-valid 1x1 PNG used in tests/test_scans_api.py and
# tests/test_reports.py — small enough to inline, valid enough to pass the
# scans route's image-signature check.
_DUMMY_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _dummy_png_bytes() -> bytes:
    return base64.b64decode(_DUMMY_PNG_BASE64)


def test_explain_real_scan_returns_bounded_uncertainties_and_text():
    with TestClient(app) as client:
        files = {"file": ("fundus.png", _dummy_png_bytes(), "image/png")}
        created = client.post("/api/v1/scans", files=files).json()
        scan_id = created["scan_id"]

        response = client.get(f"/api/v1/scans/{scan_id}/explain")

    assert response.status_code == 200
    body = response.json()
    assert body["scan_id"] == scan_id
    assert 0.0 <= body["dr_uncertainty"] <= 1.0
    assert 0.0 <= body["cataract_uncertainty"] <= 1.0
    assert isinstance(body["explanation_text"], str)
    assert body["explanation_text"] != ""


def test_explain_missing_scan_returns_404():
    with TestClient(app) as client:
        response = client.get("/api/v1/scans/does-not-exist/explain")
    assert response.status_code == 404


def test_compute_uncertainty_highest_at_half_lowest_at_extremes():
    assert compute_uncertainty(0.5) == 1.0
    assert compute_uncertainty(0.0) == 0.0
    assert compute_uncertainty(1.0) == 0.0
    # Shape check, not just the three exact endpoints above: uncertainty should
    # fall off monotonically as probability moves away from 0.5 either direction.
    assert compute_uncertainty(0.5) > compute_uncertainty(0.2)
    assert compute_uncertainty(0.5) > compute_uncertainty(0.8)
    assert compute_uncertainty(0.1) < compute_uncertainty(0.4)
