"""
Patient registry & longitudinal history (Round 3, Agent N).

A `scan` previously only carried a free-text `patient_name` — no real patient
entity, no way to list every scan for the same person, and no way to see
whether their risk is rising or falling across visits. This adds a real
`patients` table and the endpoints to see a patient's full scan history and
risk trend, which for a screening program (vs. a one-off scan) is often more
clinically useful than any single scan in isolation.

`patient_id` on Scan stays nullable and optional everywhere on purpose —
old data and any caller that only sends `patient_name` must keep working
unchanged. See app/api/scans.py and app/db/crud.py for the additive-only
changes that support that.
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_session
from app.db.models import Scan
from app.db.patient_models import Patient  # import registers the `patients` table
from app.schemas_patient import (
    PatientCreate,
    PatientResponse,
    PatientScanSummary,
    TrendPoint,
    TrendResponse,
)

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])


def _to_patient_response(row: Patient) -> PatientResponse:
    return PatientResponse(
        id=row.id,
        full_name=row.full_name,
        age=row.age,
        gender=row.gender,
        phone=row.phone,
        diabetes_type=row.diabetes_type,
        created_at=row.created_at,
    )


def _get_patient_or_404(db: Session, patient_id: str) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.post("", response_model=PatientResponse, status_code=201)
def create_patient(payload: PatientCreate, db: Session = Depends(get_session)):
    patient = Patient(
        id=str(uuid.uuid4()),
        full_name=payload.full_name,
        age=payload.age,
        gender=payload.gender,
        phone=payload.phone,
        diabetes_type=payload.diabetes_type,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return _to_patient_response(patient)


@router.get("", response_model=List[PatientResponse])
def list_patients(search: Optional[str] = None, limit: int = 20, db: Session = Depends(get_session)):
    query = db.query(Patient)
    if search:
        # ASSUMPTION: an empty `?search=` is treated the same as omitting the
        # param (falls through to the "most recent" branch below) rather than
        # as a substring that trivially matches every row — the work order
        # doesn't say either way, and "cleared search box shows the default
        # list" matches typical frontend behavior.
        query = query.filter(Patient.full_name.ilike(f"%{search}%"))
    # ASSUMPTION: the work order doesn't specify ordering for the search
    # branch, only for the no-search ("most recent limit patients") branch —
    # applying the same newest-first order to both keeps the endpoint's
    # behavior consistent and predictable either way.
    query = query.order_by(Patient.created_at.desc())
    patients = query.limit(limit).all()
    return [_to_patient_response(p) for p in patients]


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: str, db: Session = Depends(get_session)):
    patient = _get_patient_or_404(db, patient_id)
    return _to_patient_response(patient)


@router.get("/{patient_id}/scans", response_model=List[PatientScanSummary])
def get_patient_scans(patient_id: str, db: Session = Depends(get_session)):
    _get_patient_or_404(db, patient_id)
    scans = (
        db.query(Scan)
        .filter(Scan.patient_id == patient_id)
        .order_by(Scan.created_at.desc())
        .all()
    )
    return [
        PatientScanSummary(
            scan_id=s.id,
            created_at=s.created_at,
            risk_level=s.risk_level,
            dr_probability=s.dr_probability,
            cataract_probability=s.cataract_probability,
        )
        for s in scans
    ]


@router.get("/{patient_id}/trend", response_model=TrendResponse)
def get_patient_trend(patient_id: str, db: Session = Depends(get_session)):
    _get_patient_or_404(db, patient_id)
    scans = (
        db.query(Scan)
        .filter(Scan.patient_id == patient_id)
        .order_by(Scan.created_at.asc())  # oldest first — frontend plots left-to-right
        .all()
    )
    points = [
        TrendPoint(
            created_at=s.created_at,
            dr_probability=s.dr_probability,
            cataract_probability=s.cataract_probability,
            risk_level=s.risk_level,
        )
        for s in scans
    ]
    return TrendResponse(patient_id=patient_id, points=points)
