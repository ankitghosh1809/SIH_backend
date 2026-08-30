"""
Self-test for the doctor review workflow (Agent G).

Exercises the review endpoints end-to-end through the real app, plus one
direct check that SQLAlchemy actually registered the `reviews` table
(Task 1 warns this is easy to get wrong silently).

NOTE on _create_scan(): the work order says to create the test scan via
POST /api/v1/scans. That endpoint's exact request contract (multipart
field name, whether an image is required) wasn't in the work order and
this session has no way to check the real app/api/scans.py — so this
inserts a scan row directly via the ORM instead, using only the Scan
columns given verbatim in the work order. If your existing scan tests
already have a fixture/helper that creates a scan through the real
endpoint, swap that in here instead — everything below only needs a
valid scan_id to exist.
"""
import os
import uuid

from fastapi.testclient import TestClient

from app.db.database import SessionLocal, init_db
from app.db.models import Base, Scan
from app.main import app

# main.py wires init_db() into the app's lifespan handler, which only runs if
# TestClient is entered via `with TestClient(app) as client:`. Calling
# init_db() directly here is simpler and version-proof; create_all() is
# idempotent, so it's harmless even if lifespan also runs it later.
init_db()

client = TestClient(app)
API_KEY = os.environ.get("DOCTOR_API_KEY", "dev-doctor-key")


def _create_scan() -> str:
    db = SessionLocal()
    scan = Scan(
        id=str(uuid.uuid4()),
        image_path="test-fixture.jpg",
        dr_probability=0.12,
        dr_positive=False,
        cataract_probability=0.08,
        cataract_positive=False,
        risk_level="low",
        model_version="test",
        inference_ms=1,
    )
    db.add(scan)
    db.commit()
    scan_id = scan.id
    db.close()
    return scan_id


def test_reviews_table_is_registered():
    assert "reviews" in Base.metadata.tables.keys()


def test_review_missing_api_key_returns_401():
    scan_id = _create_scan()
    resp = client.post(f"/api/v1/scans/{scan_id}/review", json={"note": "looks fine"})
    assert resp.status_code == 401


def test_review_wrong_api_key_returns_401():
    scan_id = _create_scan()
    resp = client.post(
        f"/api/v1/scans/{scan_id}/review",
        json={"note": "looks fine"},
        headers={"X-API-Key": "totally-wrong-key"},
    )
    assert resp.status_code == 401


def test_review_correct_key_creates_review():
    scan_id = _create_scan()
    resp = client.post(
        f"/api/v1/scans/{scan_id}/review",
        json={"note": "confirmed, needs follow-up"},
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["scan_id"] == scan_id
    assert body["reviewer_note"] == "confirmed, needs follow-up"
    assert body["override_risk_level"] is None
    assert "review_id" in body and "reviewed_at" in body


def test_review_invalid_override_risk_level_returns_422():
    scan_id = _create_scan()
    resp = client.post(
        f"/api/v1/scans/{scan_id}/review",
        json={"note": "hmm", "override_risk_level": "extreme"},
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 422


def test_get_reviews_needs_no_auth():
    scan_id = _create_scan()
    client.post(
        f"/api/v1/scans/{scan_id}/review",
        json={"note": "second opinion needed", "override_risk_level": "high"},
        headers={"X-API-Key": API_KEY},
    )
    resp = client.get(f"/api/v1/scans/{scan_id}/reviews")
    assert resp.status_code == 200
    reviews = resp.json()
    assert len(reviews) >= 1
    assert any(r["override_risk_level"] == "high" for r in reviews)
