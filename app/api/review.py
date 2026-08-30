"""
Doctor review workflow (Agent G): lets a clinician attach a note to a scan
and, optionally, override its AI-assigned risk level. This is the
human-in-the-loop piece that makes "screening aid, not diagnostic
replacement" a real workflow rather than just a disclaimer.

Auth is a single shared API key (not full user accounts) — deliberately
scoped down for the hackathon build. Swap DOCTOR_API_KEY for real per-user
credentials before this goes anywhere near a real deployment with real
patients.
"""
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.crud import get_scan
from app.db.database import get_session
from app.db.review_models import Review  # import registers the `reviews` table

DOCTOR_API_KEY = os.environ.get("DOCTOR_API_KEY", "dev-doctor-key")  # change in production
VALID_RISK_LEVELS = {"low", "medium", "high"}

router = APIRouter(prefix="/api/v1", tags=["review"])


def require_doctor_key(x_api_key: Optional[str] = Header(None)):
    # Optional[str] = Header(None), NOT str = Header(...):
    # with Header(...) (required), FastAPI raises its own 422 for a *missing*
    # header before this function body ever runs, so a request with no
    # X-API-Key at all would get 422 instead of the 401 the self-test wants.
    # Making it optional and checking manually is what gives 401 either way
    # (missing or wrong).
    if x_api_key != DOCTOR_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")


class ReviewRequest(BaseModel):
    note: Optional[str] = None
    override_risk_level: Optional[str] = None  # must be low | medium | high if provided


class ReviewResponse(BaseModel):
    review_id: str
    scan_id: str
    reviewer_note: Optional[str]
    override_risk_level: Optional[str]
    reviewed_at: str


def _serialize(review: Review) -> ReviewResponse:
    reviewed_at = (
        review.reviewed_at.isoformat() if review.reviewed_at else datetime.utcnow().isoformat()
    )
    return ReviewResponse(
        review_id=review.id,
        scan_id=review.scan_id,
        reviewer_note=review.reviewer_note,
        override_risk_level=review.override_risk_level,
        reviewed_at=reviewed_at,
    )


@router.post(
    "/scans/{scan_id}/review",
    response_model=ReviewResponse,
    status_code=201,
    dependencies=[Depends(require_doctor_key)],
)
def create_review(scan_id: str, payload: ReviewRequest, db: Session = Depends(get_session)):
    # ASSUMPTION (not verifiable without the real crud.py): get_scan(db, scan_id)
    # returns the Scan row or None, mirroring the existing GET /scans/{id} 404
    # pattern. If your real signature differs (arg order, or it raises instead
    # of returning None), adjust this one line.
    scan = get_scan(db, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    if payload.override_risk_level is not None and payload.override_risk_level not in VALID_RISK_LEVELS:
        raise HTTPException(
            status_code=422,
            detail="override_risk_level must be one of: low, medium, high",
        )

    review = Review(
        id=str(uuid.uuid4()),
        scan_id=scan_id,
        reviewer_note=payload.note,
        override_risk_level=payload.override_risk_level,
    )
    db.add(review)
    db.commit()
    db.refresh(review)  # populate the server-generated reviewed_at

    return _serialize(review)


@router.get("/scans/{scan_id}/reviews", response_model=list[ReviewResponse])
def list_reviews(scan_id: str, db: Session = Depends(get_session)):
    reviews = (
        db.query(Review)
        .filter(Review.scan_id == scan_id)
        .order_by(Review.reviewed_at.asc())
        .all()
    )
    return [_serialize(r) for r in reviews]
