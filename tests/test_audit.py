"""
Self-test for the request audit log middleware (Agent Q).

Runs against the app's real (shared, gitignored) dev.db via a module-level
TestClient, matching tests/test_review.py's pattern. This is deliberate, not
an oversight: the audit middleware opens its own SessionLocal() directly
(app/audit/middleware.py) rather than going through FastAPI's
Depends(get_session), so app.dependency_overrides — the trick
tests/test_admin.py uses for an isolated in-memory DB — can't reach it.

"Which row did my request just create" is identified by ID-set difference
(before/after), not by ordering on created_at. SQLite's default timestamp
resolution is coarse enough that two tests running back-to-back can land in
the same second, making "ORDER BY created_at DESC LIMIT 1" return whichever
row SQLite feels like on a tie — not necessarily the one just written. An
earlier version of this file did exactly that and was flaky as a result.
"""
from fastapi.testclient import TestClient

from app.db.audit_models import AuditLog
from app.db.database import SessionLocal, init_db
from app.main import app

init_db()

client = TestClient(app)


def _audit_log_count() -> int:
    db = SessionLocal()
    try:
        return db.query(AuditLog).count()
    finally:
        db.close()


def _existing_audit_log_ids() -> set:
    db = SessionLocal()
    try:
        return {row.id for row in db.query(AuditLog.id).all()}
    finally:
        db.close()


def _the_new_row(before_ids: set) -> AuditLog:
    db = SessionLocal()
    try:
        rows = db.query(AuditLog).filter(~AuditLog.id.in_(before_ids)).all()
        assert len(rows) == 1, f"expected exactly one new audit log row, found {len(rows)}"
        return rows[0]
    finally:
        db.close()


def test_audit_logs_table_is_registered():
    from app.db.models import Base

    assert "audit_logs" in Base.metadata.tables.keys()


def test_hitting_an_endpoint_creates_an_audit_log_row():
    before = _audit_log_count()
    resp = client.get("/api/v1/audit/logs")
    assert resp.status_code == 200
    after = _audit_log_count()
    assert after == before + 1


def test_no_auth_header_logs_anonymous_actor():
    before_ids = _existing_audit_log_ids()
    resp = client.get("/api/v1/audit/logs")
    assert resp.status_code == 200
    new_row = _the_new_row(before_ids)
    assert new_row.actor == "anonymous"


def test_any_authorization_header_logs_authenticated_actor():
    before_ids = _existing_audit_log_ids()
    resp = client.get(
        "/api/v1/audit/logs",
        headers={"Authorization": "Bearer totally-not-a-real-token"},
    )
    assert resp.status_code == 200
    new_row = _the_new_row(before_ids)
    assert new_row.actor == "authenticated"


def test_audit_write_failure_does_not_break_the_request(monkeypatch):
    def _boom():
        raise RuntimeError("simulated audit DB failure")

    monkeypatch.setattr("app.audit.middleware.SessionLocal", _boom)

    before = _audit_log_count()
    resp = client.get("/api/v1/audit/logs")
    assert resp.status_code == 200

    after = _audit_log_count()
    assert after == before
