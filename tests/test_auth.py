"""
Self-test for the JWT-based auth system (Agent M): registration, login,
/me, and the role-based gating that replaces DOCTOR_API_KEY and the
previously fully-open GET /admin/stats.

Same conventions as tests/test_review.py: direct TestClient(app), calling
init_db() directly rather than relying on lifespan, one test function per
behavior. Usernames get a random suffix per call (see _unique_username)
for the same reason tests/test_review.py's _create_scan() doesn't worry
about ID collisions: dev.db is gitignored but persists across repeated
local `pytest` runs, and users.username is UNIQUE.
"""
import uuid

from fastapi.testclient import TestClient

from app.db.database import SessionLocal, init_db
from app.db.models import Base, Scan
from app.main import app

init_db()

client = TestClient(app)


def _unique_username(role: str) -> str:
    return f"test_{role}_{uuid.uuid4().hex[:8]}"


def _register(username: str, password: str, role: str):
    return client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": password, "role": role},
    )


def _login(username: str, password: str):
    return client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )


def _token_for(role: str) -> str:
    username = _unique_username(role)
    password = "testpass123"
    assert _register(username, password, role).status_code == 201
    resp = _login(username, password)
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _create_scan() -> str:
    """Same direct-ORM-insert pattern as tests/test_review.py — only needs a
    valid scan_id to exist, not a real inference run. See that file's
    module docstring for why this doesn't go through POST /api/v1/scans."""
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


def test_users_table_is_registered():
    assert "users" in Base.metadata.tables.keys()


def test_register_login_me_round_trip():
    username = _unique_username("doctor")
    password = "testpass123"

    resp = _register(username, password, "doctor")
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["username"] == username
    assert body["role"] == "doctor"
    assert "hashed_password" not in body
    assert "password" not in body

    resp = _login(username, password)
    assert resp.status_code == 200, resp.text
    token_body = resp.json()
    assert token_body["token_type"] == "bearer"
    token = token_body["access_token"]

    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["username"] == username


def test_register_duplicate_username_returns_409():
    # Regression test for the IntegrityError -> 409 branch in app/api/auth.py
    # (an assumption this session made; the work order doesn't specify a
    # status code for this case).
    username = _unique_username("doctor")
    password = "testpass123"
    assert _register(username, password, "doctor").status_code == 201
    resp = _register(username, "different-password", "doctor")
    assert resp.status_code == 409


def test_login_wrong_password_returns_401():
    username = _unique_username("doctor")
    password = "testpass123"
    assert _register(username, password, "doctor").status_code == 201

    resp = _login(username, "the-wrong-password")
    assert resp.status_code == 401


def test_me_no_token_returns_401():
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_garbage_token_returns_401():
    resp = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert resp.status_code == 401


def test_camp_staff_forbidden_from_review():
    scan_id = _create_scan()
    token = _token_for("camp_staff")
    resp = client.post(
        f"/api/v1/scans/{scan_id}/review",
        json={"note": "not my job"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_doctor_can_review():
    scan_id = _create_scan()
    token = _token_for("doctor")
    resp = client.post(
        f"/api/v1/scans/{scan_id}/review",
        json={"note": "reviewed"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text


def test_admin_stats_no_token_returns_401():
    resp = client.get("/api/v1/admin/stats")
    assert resp.status_code == 401


def test_admin_stats_admin_token_returns_200():
    token = _token_for("admin")
    resp = client.get(
        "/api/v1/admin/stats", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200, resp.text
