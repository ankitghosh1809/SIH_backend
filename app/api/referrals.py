"""
app/api/referrals.py — Agent O (Round 3): referral & clinical escalation
workflow.

Turns a scan's `risk_level` from a value sitting in the DB into an actual
clinical follow-up loop: a static facility directory, referral CRUD with
status tracking, and a referral-letter PDF.

Two assumptions made without access to the real repo (full list in
ASSUMPTIONS_AND_TODO.md):
  1. The DB-session dependency is `get_db` in `app.db.database`.
  2. Routers in this codebase carry their own `/api/v1` prefix, so
     `app.include_router(referrals.router)` in main.py (as shown in the
     work order, with no prefix argument) is enough on its own.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db import crud
from app.db.referral_models import Referral
from app.data.facilities import FACILITIES
from app.reports.referral_letter import build_referral_letter_pdf
from app.schemas_referral import (
    FacilityResponse,
    ReferralCreate,
    ReferralResponse,
    ReferralSuggestion,
    ReferralUpdate,
)

# ASSUMPTION — see ASSUMPTIONS_AND_TODO.md item 1.
from app.db.database import get_session as get_db

router = APIRouter(prefix="/api/v1", tags=["referrals"])


@router.get("/facilities", response_model=list[FacilityResponse])
def list_facilities():
    return FACILITIES


@router.get(
    "/scans/{scan_id}/referral-suggestion", response_model=ReferralSuggestion
)
def get_referral_suggestion(scan_id: str, db: Session = Depends(get_db)):
    scan = crud.get_scan(db, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    if scan.risk_level == "high":
        return ReferralSuggestion(
            suggested=True,
            reason=(
                "High-risk screening result — referral to a clinical "
                "facility is recommended."
            ),
        )
    return ReferralSuggestion(suggested=False, reason=None)


@router.post(
    "/scans/{scan_id}/referral", response_model=ReferralResponse, status_code=201
)
def create_referral(
    scan_id: str, payload: ReferralCreate, db: Session = Depends(get_db)
):
    scan = crud.get_scan(db, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    # Referrals can be created regardless of risk level — the suggestion
    # endpoint above is advisory, not a hard gate.
    referral = Referral(
        id=str(uuid.uuid4()),
        scan_id=scan_id,
        facility_name=payload.facility_name,
        facility_contact=payload.facility_contact,
        notes=payload.notes,
        status="pending",
    )
    db.add(referral)
    db.commit()
    db.refresh(referral)
    return referral


@router.get("/referrals", response_model=list[ReferralResponse])
def list_referrals(status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Referral)
    if status is not None:
        query = query.filter(Referral.status == status)
    return query.order_by(Referral.created_at.desc()).all()


@router.get("/referrals/{referral_id}", response_model=ReferralResponse)
def get_referral(referral_id: str, db: Session = Depends(get_db)):
    referral = db.query(Referral).filter(Referral.id == referral_id).first()
    if referral is None:
        raise HTTPException(status_code=404, detail="Referral not found")
    return referral


@router.patch("/referrals/{referral_id}", response_model=ReferralResponse)
def update_referral(
    referral_id: str, payload: ReferralUpdate, db: Session = Depends(get_db)
):
    referral = db.query(Referral).filter(Referral.id == referral_id).first()
    if referral is None:
        raise HTTPException(status_code=404, detail="Referral not found")

    if payload.status is not None:
        referral.status = payload.status
    if payload.notes is not None:
        referral.notes = payload.notes
    referral.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(referral)
    return referral


@router.get("/referrals/{referral_id}/letter")
def get_referral_letter(referral_id: str, db: Session = Depends(get_db)):
    referral = db.query(Referral).filter(Referral.id == referral_id).first()
    if referral is None:
        raise HTTPException(status_code=404, detail="Referral not found")

    scan = crud.get_scan(db, referral.scan_id)
    pdf_bytes = build_referral_letter_pdf(scan, referral)
    return Response(content=pdf_bytes, media_type="application/pdf")
