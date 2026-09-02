"""
Self-test for the pull-based notification sync (Agent Q).

Runs against the app's real (shared, gitignored) dev.db via a module-level
TestClient, matching tests/test_review.py's pattern. sync_notifications()
runs inside GET /api/v1/notifications using that same request's
Depends(get_session) session, so — unlike the audit middleware — there's no
separate-session visibility concern here (see tests/test_audit.py's
docstring for why that one's different).

_create_scan() is copied from tests/test_review.py's helper of the same
name (same columns, same reasoning: this session can't exercise the real
POST /api/v1/scans endpoint, so a scan row is inserted directly via the
ORM), with a risk_level parameter added since these tests need both "low"
and "high" scans.
"""
import uuid

from fastapi.testclient import TestClient

from app.db.database import SessionLocal, init_db
from app.db.models import Base, Scan
from app.db.review_models import Review
from app.main import app

init_db()

client = TestClient(app)


def _create_scan(risk_level: str = "low") -> str:
    db = SessionLocal()
    scan = Scan(
        id=str(uuid.uuid4()),
        image_path="test-fixture.jpg",
        dr_probability=0.12,
        dr_positive=False,
        cataract_probability=0.08,
        cataract_positive=False,
        risk_level=risk_level,
        model_version="test",
        inference_ms=1,
    )
    db.add(scan)
    db.commit()
    scan_id = scan.id
    db.close()
    return scan_id


def _create_review(scan_id: str) -> None:
    db = SessionLocal()
    review = Review(
        id=str(uuid.uuid4()),
        scan_id=scan_id,
        reviewer_note="test review",
        override_risk_level=None,
    )
    db.add(review)
    db.commit()
    db.close()


def _matches(notifications: list, event_type: str, scan_id: str) -> list:
    return [
        n for n in notifications
        if n["event_type"] == event_type and n["scan_id"] == scan_id
    ]


def test_notifications_table_is_registered():
    assert "notifications" in Base.metadata.tables.keys()


def test_high_risk_scan_produces_a_notification():
    scan_id = _create_scan(risk_level="high")

    resp = client.get("/api/v1/notifications")
    assert resp.status_code == 200

    matches = _matches(resp.json(), "high_risk_detected", scan_id)
    assert len(matches) == 1


def test_sync_is_idempotent_for_the_same_high_risk_scan():
    scan_id = _create_scan(risk_level="high")

    first = client.get("/api/v1/notifications").json()
    second = client.get("/api/v1/notifications").json()  # calling it again...

    assert len(_matches(first, "high_risk_detected", scan_id)) == 1
    assert len(_matches(second, "high_risk_detected", scan_id)) == 1  # ...didn't duplicate it


def test_completed_review_produces_a_notification():
    scan_id = _create_scan(risk_level="low")
    _create_review(scan_id)

    resp = client.get("/api/v1/notifications")
    assert resp.status_code == 200

    matches = _matches(resp.json(), "review_completed", scan_id)
    assert len(matches) == 1


def test_mark_notification_read_persists():
    scan_id = _create_scan(risk_level="high")
    notifications = client.get("/api/v1/notifications").json()
    target = _matches(notifications, "high_risk_detected", scan_id)[0]
    assert target["is_read"] is False

    patch_resp = client.patch(f"/api/v1/notifications/{target['id']}/read")
    assert patch_resp.status_code == 200
    assert patch_resp.json()["is_read"] is True

    # Persisted, not just returned once — a fresh GET still shows it as read.
    refreshed = client.get("/api/v1/notifications").json()
    refreshed_target = next(n for n in refreshed if n["id"] == target["id"])
    assert refreshed_target["is_read"] is True


def test_mark_unknown_notification_read_returns_404():
    resp = client.patch(f"/api/v1/notifications/{uuid.uuid4()}/read")
    assert resp.status_code == 404
