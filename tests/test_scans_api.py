import base64

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import scans

app = FastAPI()
app.include_router(scans.router)

client = TestClient(app)

# A minimal-but-valid 1x1 PNG, so it survives the route's image-signature check.
_DUMMY_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _dummy_png_bytes() -> bytes:
    return base64.b64decode(_DUMMY_PNG_BASE64)


def test_create_scan_returns_201_and_matches_schema():
    files = {"file": ("fundus.png", _dummy_png_bytes(), "image/png")}
    response = client.post("/api/v1/scans", files=files, data={"patient_name": "Test Patient"})
    assert response.status_code == 201
    body = response.json()
    assert set(body.keys()) == {
        "scan_id", "created_at", "prediction", "risk_level", "heatmap_url", "model_version",
    }
    assert set(body["prediction"].keys()) == {"diabetic_retinopathy", "cataract"}
    for field in ("diabetic_retinopathy", "cataract"):
        # Round 3 (Agent P) added `uncertainty` to PredictionField
        # (app/schemas.py) and populates it on every response — required by
        # that work order's "every ScanResponse includes uncertainty for both
        # conditions" — so the expected key set here now includes it too.
        assert set(body["prediction"][field].keys()) == {"positive", "probability", "uncertainty"}
    assert body["risk_level"] in {"low", "medium", "high"}


def test_create_scan_rejects_invalid_image():
    files = {"file": ("not_an_image.txt", b"this is not an image", "text/plain")}
    response = client.post("/api/v1/scans", files=files)
    assert response.status_code == 422


def test_get_scan_by_id_roundtrip():
    files = {"file": ("fundus.png", _dummy_png_bytes(), "image/png")}
    created = client.post("/api/v1/scans", files=files).json()
    scan_id = created["scan_id"]

    response = client.get(f"/api/v1/scans/{scan_id}")
    assert response.status_code == 200
    assert response.json()["scan_id"] == scan_id


def test_get_scan_missing_returns_404():
    response = client.get("/api/v1/scans/does-not-exist")
    assert response.status_code == 404


def test_get_heatmap_bytes_back():
    files = {"file": ("fundus.png", _dummy_png_bytes(), "image/png")}
    created = client.post("/api/v1/scans", files=files).json()
    scan_id = created["scan_id"]

    response = client.get(f"/api/v1/scans/{scan_id}/heatmap")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")


def test_get_heatmap_missing_returns_404():
    response = client.get("/api/v1/scans/does-not-exist/heatmap")
    assert response.status_code == 404


def test_list_scans_contains_created_scan():
    files = {"file": ("fundus.png", _dummy_png_bytes(), "image/png")}
    created = client.post("/api/v1/scans", files=files).json()
    scan_id = created["scan_id"]

    response = client.get("/api/v1/scans")
    assert response.status_code == 200
    scan_ids = [item["scan_id"] for item in response.json()]
    assert scan_id in scan_ids
