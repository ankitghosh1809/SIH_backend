from typing import Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_session
from app.db.models import Scan

router = APIRouter(prefix="/api/v1/admin")


class AdminStatsResponse(BaseModel):
    total_scans: int
    by_risk_level: Dict[str, int]       # e.g. {"low": 10, "medium": 3, "high": 1}
    avg_inference_ms: float | None      # None if there are zero scans yet
    by_model_version: Dict[str, int]    # e.g. {"stub-v0": 14, "hybrid-quantum-v1": 6}


# TODO: consider protecting this with the same API-key pattern the review
# endpoint uses, once that lands — operational stats probably shouldn't stay
# fully public forever.
@router.get("/stats", response_model=AdminStatsResponse)
def get_admin_stats(db: Session = Depends(get_session)) -> AdminStatsResponse:
    total_scans = db.query(func.count(Scan.id)).scalar() or 0

    risk_rows = (
        db.query(Scan.risk_level, func.count(Scan.id))
        .group_by(Scan.risk_level)
        .all()
    )
    by_risk_level = {level: count for level, count in risk_rows if level is not None}

    version_rows = (
        db.query(Scan.model_version, func.count(Scan.id))
        .group_by(Scan.model_version)
        .all()
    )
    by_model_version = {v: count for v, count in version_rows if v is not None}

    avg_ms = db.query(func.avg(Scan.inference_ms)).scalar()

    return AdminStatsResponse(
        total_scans=total_scans,
        by_risk_level=by_risk_level,
        avg_inference_ms=float(avg_ms) if avg_ms is not None else None,
        by_model_version=by_model_version,
    )
