"""
tests/test_ml_cleanup.py — Round 3 (Agent P)

Self-test for the tech-debt fixes bundled into this work order: a true
single model load via inference.get_model(), and MODEL_VERSION /
RISK_THRESHOLD_MEDIUM / RISK_THRESHOLD_HIGH centralized in app.config and
actually read from there at call time (not captured once at import time) by
scans.py, batch.py, and compute_risk_level().

Risk-band coverage itself (low/medium/high against the real 0.4/0.7 defaults)
is already exercised by the existing
tests/test_inference.py::test_compute_risk_level_covers_all_three_bands,
which still passes unchanged against the new config-backed defaults, so it
isn't duplicated here — this file only adds the config-responsiveness check.
"""
import base64

from fastapi.testclient import TestClient

from app import config
from app.main import app
from app.ml import inference

_DUMMY_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _dummy_png_bytes() -> bytes:
    return base64.b64decode(_DUMMY_PNG_BASE64)


def test_get_model_returns_same_cached_object():
    first = inference.get_model()
    second = inference.get_model()
    assert first is second


def test_scan_response_reflects_patched_model_version(monkeypatch):
    monkeypatch.setattr(config, "MODEL_VERSION", "test-patched-v1")

    with TestClient(app) as client:
        files = {"file": ("fundus.png", _dummy_png_bytes(), "image/png")}
        created = client.post("/api/v1/scans", files=files).json()

    assert created["model_version"] == "test-patched-v1"


def test_batch_response_reflects_patched_model_version(monkeypatch):
    monkeypatch.setattr(config, "MODEL_VERSION", "test-patched-v2")

    with TestClient(app) as client:
        files = [("files", ("fundus.png", _dummy_png_bytes(), "image/png"))]
        batch_result = client.post("/api/v1/batch", files=files).json()
        scan_id = batch_result["results"][0]["scan_id"]
        # BatchItemResult doesn't carry model_version itself, so confirm via
        # the persisted scan row through the regular GET endpoint instead.
        fetched = client.get(f"/api/v1/scans/{scan_id}").json()

    assert fetched["model_version"] == "test-patched-v2"


def test_compute_risk_level_reads_thresholds_from_config(monkeypatch):
    monkeypatch.setattr(config, "RISK_THRESHOLD_MEDIUM", 0.1)
    monkeypatch.setattr(config, "RISK_THRESHOLD_HIGH", 0.3)

    # Under the real 0.4 / 0.7 defaults (see
    # tests/test_inference.py::test_compute_risk_level_covers_all_three_bands),
    # a max probability of 0.5 lands in the "medium" band. With these patched,
    # lower thresholds it should land in "high" instead — confirms
    # compute_risk_level() reads config at call time, not a value captured
    # once at import time.
    assert inference.compute_risk_level(0.5, 0.1) == "high"
