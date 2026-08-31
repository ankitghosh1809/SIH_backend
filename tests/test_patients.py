"""
Self-test for the patient registry & longitudinal history (Round 3, Agent N).

Follows the conventions in tests/test_review.py: TestClient against the real
app (from app.main import app), init_db() called directly at module level
(idempotent, so harmless even though main.py's lifespan also calls it), and
fixture scan rows inserted straight via the ORM rather than through
POST /api/v1/scans when a test needs specific created_at / risk_level /
probability values on rows tied to a known patient_id — the multipart upload
contract isn't relevant to those tests. The tests that specifically exercise
POST /api/v1/scans's patient_id handling (backward-compat + 404 + linking) do
go through the real endpoint, since that IS the behavior being tested there.
"""
import base64
import uuid
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.db.database import SessionLocal, init_db
from app.db.models import Base, Scan
from app.main import app

init_db()

client = TestClient(app)

# Same minimal-but-valid 1x1 PNG used in tests/test_scans_api.py, so it survives
# the route's image-signature check.
_DUMMY_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _dummy_png_bytes() -> bytes:
    return base64.b64decode(_DUMMY_PNG_BASE64)


def _create_patient(full_name: str = "Test Patient") -> str:
    resp = client.post("/api/v1/patients", json={"full_name": full_name})
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _create_scan_for_patient(patient_id: str, *, risk_level, dr_probability,
                              cataract_probability, created_at) -> str:
    """Direct ORM insert for a scan tied to `patient_id` — same reasoning as
    test_review.py's _create_scan(): no need to depend on the full POST /scans
    multipart contract when a fixture can build the row directly, and this
    needs specific created_at values to test ordering, which POST /scans
    (timestamped by the DB itself) doesn't let a caller set."""
    db = SessionLocal()
    scan = Scan(
        id=str(uuid.uuid4()),
        patient_id=patient_id,
        image_path="test-fixture.jpg",
        dr_probability=dr_probability,
        dr_positive=dr_probability > 0.5,
        cataract_probability=cataract_probability,
        cataract_positive=cataract_probability > 0.5,
        risk_level=risk_level,
        model_version="test",
        inference_ms=1,
        created_at=created_at,
    )
    db.add(scan)
    db.commit()
    scan_id = scan.id
    db.close()
    return scan_id


def test_patients_table_is_registered():
    assert "patients" in Base.metadata.tables.keys()


def test_create_and_get_patient():
    resp = client.post(
        "/api/v1/patients",
        json={
            "full_name": "Asha Kulkarni",
            "age": 54,
            "gender": "female",
            "phone": "9999999999",
            "diabetes_type": "type2",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["full_name"] == "Asha Kulkarni"
    assert body["age"] == 54
    assert body["gender"] == "female"
    assert body["diabetes_type"] == "type2"
    assert "id" in body and "created_at" in body

    fetched = client.get(f"/api/v1/patients/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == body


def test_get_patient_missing_returns_404():
    resp = client.get("/api/v1/patients/does-not-exist")
    assert resp.status_code == 404


def test_search_patients_case_insensitive():
    # Unique substring so this assertion can't collide with a patient created
    # by another test function sharing the same dev.db across this file's run.
    unique = uuid.uuid4().hex[:8]
    full_name = f"Ramesh Zzyxq{unique} Patil"
    _create_patient(full_name)

    resp = client.get(f"/api/v1/patients?search=zzyxq{unique}")  # deliberately lowercase
    assert resp.status_code == 200
    assert full_name in [p["full_name"] for p in resp.json()]


def test_patient_scans_and_trend_ordering():
    patient_id = _create_patient("Trend Test Patient")
    base = datetime(2026, 1, 1, 9, 0, 0)

    oldest = _create_scan_for_patient(
        patient_id, risk_level="low", dr_probability=0.10,
        cataract_probability=0.05, created_at=base,
    )
    middle = _create_scan_for_patient(
        patient_id, risk_level="medium", dr_probability=0.45,
        cataract_probability=0.30, created_at=base + timedelta(days=30),
    )
    newest = _create_scan_for_patient(
        patient_id, risk_level="high", dr_probability=0.80,
        cataract_probability=0.75, created_at=base + timedelta(days=60),
    )

    scans_resp = client.get(f"/api/v1/patients/{patient_id}/scans")
    assert scans_resp.status_code == 200
    scan_body = scans_resp.json()
    assert [s["scan_id"] for s in scan_body] == [newest, middle, oldest]  # newest first
    assert scan_body[0]["risk_level"] == "high"

    trend_resp = client.get(f"/api/v1/patients/{patient_id}/trend")
    assert trend_resp.status_code == 200
    trend_body = trend_resp.json()
    assert trend_body["patient_id"] == patient_id
    points = trend_body["points"]
    assert len(points) == 3
    assert [p["risk_level"] for p in points] == ["low", "medium", "high"]  # oldest first
    assert points[0]["dr_probability"] == 0.10
    assert points[-1]["dr_probability"] == 0.80


def test_patient_scans_and_trend_404_for_missing_patient():
    assert client.get("/api/v1/patients/does-not-exist/scans").status_code == 404
    assert client.get("/api/v1/patients/does-not-exist/trend").status_code == 404


def test_create_scan_without_patient_id_still_works():
    """The single most important test in this file: patient_id must be fully
    optional, so every existing caller that never heard of /patients keeps
    working exactly as before (backward compatibility check)."""
    files = {"file": ("fundus.png", _dummy_png_bytes(), "image/png")}
    resp = client.post(
        "/api/v1/scans", files=files, data={"patient_name": "Backward Compat Patient"}
    )
    assert resp.status_code == 201, resp.text
    assert "scan_id" in resp.json()


def test_create_scan_with_invalid_patient_id_returns_404():
    files = {"file": ("fundus.png", _dummy_png_bytes(), "image/png")}
    resp = client.post("/api/v1/scans", files=files, data={"patient_id": "does-not-exist"})
    assert resp.status_code == 404

    db = SessionLocal()
    created = db.query(Scan).filter(Scan.patient_id == "does-not-exist").count()
    db.close()
    assert created == 0


def test_create_scan_with_valid_patient_id_links_it():
    patient_id = _create_patient("Linked Scan Patient")
    files = {"file": ("fundus.png", _dummy_png_bytes(), "image/png")}
    resp = client.post("/api/v1/scans", files=files, data={"patient_id": patient_id})
    assert resp.status_code == 201, resp.text
    scan_id = resp.json()["scan_id"]

    scans_resp = client.get(f"/api/v1/patients/{patient_id}/scans")
    assert any(s["scan_id"] == scan_id for s in scans_resp.json())
