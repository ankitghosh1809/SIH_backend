"""
tests/test_referrals.py — Agent O (Round 3).

Covers the self-test checklist from the Round-3 Agent O work order.

ASSUMPTION — the single biggest unknown in this whole deliverable: I could
not read the real tests/test_review.py in this session, so `_create_scan()`
below is a best-effort guess at the fields a `Scan` row needs, not a copy
of the real helper. Before running this file, reconcile `_create_scan()`
against the actual helper in tests/test_review.py, and confirm the
`init_db` / `SessionLocal` import path below matches app.db.database. See
ASSUMPTIONS_AND_TODO.md item 4.
"""

import uuid

from fastapi.testclient import TestClient

from app.main import app

# ASSUMPTION — see ASSUMPTIONS_AND_TODO.md items 1 and 4.
from app.db.database import SessionLocal, init_db
from app.db.models import Base, Scan

# Imported (even though not directly referenced) so the `referrals` table is
# guaranteed to be registered on Base.metadata for the test below,
# independent of whatever main.py's own import chain does.
from app.db.referral_models import Referral  # noqa: F401

client = TestClient(app)


def setup_module(module):
    init_db()


def teardown_module(module):
    db = SessionLocal()
    try:
        db.query(Referral).delete()
        db.query(Scan).filter(Scan.id.like("test-scan-%")).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _create_scan(risk_level="high", **overrides):
    """
    ASSUMPTION: best-effort fixture, not a copy of the real helper in
    tests/test_review.py — reconcile field names/required fields against
    that file before relying on this.
    """
    db = SessionLocal()
    try:
        scan_kwargs = {
            "id": overrides.pop("id", f"test-scan-{risk_level}-{uuid.uuid4().hex[:12]}"),
            "risk_level": risk_level,
            "image_path": overrides.pop("image_path", f"test-fixtures/{risk_level}.jpg"),
        }
        # Only set these if the real Scan model actually has them, so this
        # doesn't hard-fail with a TypeError if the real field names differ.
        for field, value in {"dr_probability": 0.87, "cataract_probability": 0.12}.items():
            if hasattr(Scan, field):
                scan_kwargs[field] = value
        scan_kwargs.update(overrides)

        scan = Scan(**scan_kwargs)
        db.add(scan)
        db.commit()
        db.refresh(scan)
        return scan
    finally:
        db.close()


def test_referrals_table_registered():
    assert "referrals" in Base.metadata.tables


def test_list_facilities_non_empty():
    response = client.get("/api/v1/facilities")
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_referral_suggestion_true_for_high_risk():
    scan = _create_scan(risk_level="high")
    response = client.get(f"/api/v1/scans/{scan.id}/referral-suggestion")
    assert response.status_code == 200
    body = response.json()
    assert body["suggested"] is True
    assert body["reason"]


def test_referral_suggestion_false_for_low_risk():
    scan = _create_scan(risk_level="low")
    response = client.get(f"/api/v1/scans/{scan.id}/referral-suggestion")
    assert response.status_code == 200
    body = response.json()
    assert body["suggested"] is False
    assert body["reason"] is None


def test_referral_suggestion_404_for_missing_scan():
    response = client.get("/api/v1/scans/does-not-exist/referral-suggestion")
    assert response.status_code == 404


def test_create_referral_success():
    scan = _create_scan(risk_level="high")
    response = client.post(
        f"/api/v1/scans/{scan.id}/referral",
        json={
            "facility_name": "City Eye Care Centre",
            "facility_contact": "+91-22-4550-1010",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["scan_id"] == scan.id


def test_create_referral_404_for_missing_scan():
    response = client.post(
        "/api/v1/scans/does-not-exist/referral",
        json={"facility_name": "City Eye Care Centre"},
    )
    assert response.status_code == 404


def test_get_referral_404_for_missing():
    response = client.get("/api/v1/referrals/does-not-exist")
    assert response.status_code == 404


def test_patch_referral_status_persists():
    scan = _create_scan(risk_level="high")
    created = client.post(
        f"/api/v1/scans/{scan.id}/referral",
        json={"facility_name": "City Eye Care Centre"},
    ).json()

    patched = client.patch(
        f"/api/v1/referrals/{created['id']}", json={"status": "contacted"}
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "contacted"

    refetched = client.get(f"/api/v1/referrals/{created['id']}")
    assert refetched.json()["status"] == "contacted"


def test_patch_referral_invalid_status_422():
    scan = _create_scan(risk_level="high")
    created = client.post(
        f"/api/v1/scans/{scan.id}/referral",
        json={"facility_name": "City Eye Care Centre"},
    ).json()

    response = client.patch(
        f"/api/v1/referrals/{created['id']}", json={"status": "not-a-real-status"}
    )
    assert response.status_code == 422


def test_list_referrals_filtered_by_status():
    scan = _create_scan(risk_level="high")
    created = client.post(
        f"/api/v1/scans/{scan.id}/referral",
        json={"facility_name": "City Eye Care Centre"},
    ).json()
    client.patch(f"/api/v1/referrals/{created['id']}", json={"status": "contacted"})

    pending_only = client.get("/api/v1/referrals", params={"status": "pending"}).json()
    pending_ids = [r["id"] for r in pending_only]
    assert created["id"] not in pending_ids


def test_referral_letter_returns_pdf():
    scan = _create_scan(risk_level="high")
    created = client.post(
        f"/api/v1/scans/{scan.id}/referral",
        json={"facility_name": "City Eye Care Centre"},
    ).json()

    response = client.get(f"/api/v1/referrals/{created['id']}/letter")
    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")
