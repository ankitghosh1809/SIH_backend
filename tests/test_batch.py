import base64

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import batch

app = FastAPI()
app.include_router(batch.router)

client = TestClient(app)

# A minimal-but-valid 1x1 PNG, same fixture pattern as test_scans_api.py.
_DUMMY_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _dummy_png_bytes() -> bytes:
    return base64.b64decode(_DUMMY_PNG_BASE64)


def test_batch_upload_returns_200_and_matches_schema():
    files = [("files", (f"fundus_{i}.png", _dummy_png_bytes(), "image/png")) for i in range(3)]
    response = client.post("/api/v1/batch", files=files)
    assert response.status_code == 200

    body = response.json()
    assert body["summary"]["total"] == 3
    assert body["summary"]["succeeded"] == 3
    assert body["summary"]["failed"] == 0
    assert len(body["results"]) == 3
    for item in body["results"]:
        assert item["scan_id"]
        assert item["risk_level"] in {"low", "medium", "high"}
        assert item["error"] is None


def test_batch_over_size_limit_returns_422():
    files = [("files", (f"fundus_{i}.png", _dummy_png_bytes(), "image/png")) for i in range(51)]
    response = client.post("/api/v1/batch", files=files)
    assert response.status_code == 422


def test_batch_partial_failure_does_not_abort_rest():
    files = [
        ("files", ("fundus_0.png", _dummy_png_bytes(), "image/png")),
        ("files", ("not_an_image.txt", b"this is not an image", "text/plain")),
        ("files", ("fundus_1.png", _dummy_png_bytes(), "image/png")),
    ]
    response = client.post("/api/v1/batch", files=files)
    assert response.status_code == 200

    body = response.json()
    assert body["summary"]["total"] == 3
    assert body["summary"]["succeeded"] == 2
    assert body["summary"]["failed"] == 1

    by_name = {item["filename"]: item for item in body["results"]}
    assert by_name["not_an_image.txt"]["scan_id"] is None
    assert by_name["not_an_image.txt"]["error"] is not None
    assert by_name["fundus_0.png"]["scan_id"] is not None
    assert by_name["fundus_1.png"]["scan_id"] is not None
