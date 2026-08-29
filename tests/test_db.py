"""Self-test for Agent A's database layer (app/db/*).

Exercises the flow from the work order: init_db() against a throwaway
SQLite file, create a scan, fetch it back, list scans, record metrics for
both model types, then confirm get_latest_metrics returns both.

app.db.database builds its engine from DATABASE_URL at import time, and
may already be cached under a different DATABASE_URL by the time this
file runs — e.g. app_agent_d.py imports app.main, which imports
app.db.database, and pytest collects test files alphabetically before
any of them run, so that import can easily happen before this one. The
fixture below swaps in a fresh copy of the module bound to a throwaway
file for the test, then restores whatever was cached before, so this
test is isolated regardless of collection order and can't leak its DB
path into the rest of the suite.
"""
import os
import sys
import tempfile
import uuid

import pytest


@pytest.fixture()
def db(monkeypatch):
    db_path = os.path.join(tempfile.gettempdir(), f"sih_test_{uuid.uuid4().hex}.db")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    previous_module = sys.modules.pop("app.db.database", None)
    from app.db.database import SessionLocal, init_db

    init_db()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        if previous_module is not None:
            sys.modules["app.db.database"] = previous_module
        else:
            sys.modules.pop("app.db.database", None)


def test_db_round_trip(db):
    from app.db import crud

    created = crud.create_scan(
        db,
        scan_id="test-1",
        patient_name="Test Patient",
        image_path="/images/test-1.png",
        heatmap_path=None,
        dr_probability=0.82,
        dr_positive=True,
        cataract_probability=0.10,
        cataract_positive=False,
        risk_level="high",
        model_version="v0.1-classical",
        inference_ms=120,
    )
    assert created.id == "test-1"

    fetched = crud.get_scan(db, "test-1")
    assert fetched is not None
    assert fetched.id == "test-1"
    assert fetched.dr_positive is True

    scans = crud.list_scans(db)
    assert len(scans) == 1
    assert scans[0].id == "test-1"

    crud.record_metrics(
        db,
        model_type="classical",
        accuracy=0.91,
        precision=0.88,
        recall=0.85,
        f1=0.86,
        auc_roc=0.93,
        test_set_size=200,
    )
    crud.record_metrics(
        db,
        model_type="hybrid_quantum",
        accuracy=0.94,
        precision=0.92,
        recall=0.90,
        f1=0.91,
        auc_roc=0.96,
        test_set_size=200,
    )

    latest = crud.get_latest_metrics(db)
    assert latest["classical"] is not None
    assert latest["hybrid_quantum"] is not None
    assert latest["classical"].model_type == "classical"
    assert latest["hybrid_quantum"].model_type == "hybrid_quantum"
