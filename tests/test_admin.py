"""Tests for GET /api/v1/admin/stats (Agent H; auth added by Agent M).

Runs against an isolated in-memory SQLite database via a dependency
override — never touches dev.db or a DATABASE_URL-configured database.
The override applies to every nested Depends(get_session) too, including
the one inside app.auth.security.get_current_user, so registering/logging
in through this fixture's test_client lands in the same isolated DB.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import get_session
from app.db.models import Base, Scan


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def _override_get_session():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_session] = _override_get_session

    with TestClient(app) as test_client:
        yield test_client, TestingSessionLocal

    app.dependency_overrides.clear()


def _make_scan(risk_level: str, model_version: str, inference_ms: int) -> Scan:
    return Scan(
        id=str(uuid.uuid4()),
        image_path="fake/path.jpg",
        dr_probability=0.12,
        dr_positive=False,
        cataract_probability=0.08,
        cataract_positive=False,
        risk_level=risk_level,
        model_version=model_version,
        inference_ms=inference_ms,
    )


def _auth_header(test_client, role: str) -> dict:
    username = f"test_{role}_{uuid.uuid4().hex[:8]}"
    password = "testpass123"
    resp = test_client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": password, "role": role},
    )
    assert resp.status_code == 201, resp.text
    resp = test_client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_admin_stats_requires_auth(client):
    test_client, _ = client
    resp = test_client.get("/api/v1/admin/stats")
    assert resp.status_code == 401


def test_admin_stats_zero_scans(client):
    test_client, _ = client
    headers = _auth_header(test_client, "admin")

    response = test_client.get("/api/v1/admin/stats", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total_scans"] == 0
    assert data["avg_inference_ms"] is None
    assert data["by_risk_level"] == {}
    assert data["by_model_version"] == {}


def test_admin_stats_with_scans(client):
    test_client, SessionLocal = client
    db = SessionLocal()
    db.add(_make_scan("low", "stub-v0", 100))
    db.add(_make_scan("low", "stub-v0", 200))
    db.add(_make_scan("high", "stub-v0", 300))
    db.commit()
    db.close()
    headers = _auth_header(test_client, "admin")

    response = test_client.get("/api/v1/admin/stats", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total_scans"] == 3
    assert data["by_risk_level"] == {"low": 2, "high": 1}
    assert data["by_model_version"] == {"stub-v0": 3}
    assert data["avg_inference_ms"] == pytest.approx(200.0)
