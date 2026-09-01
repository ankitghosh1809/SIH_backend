# app/schemas_patient.py — request/response contract for the patient registry
# (Round 3, Agent N). Kept separate from the shared app/schemas.py contract, same
# reasoning as review.py keeping its own request/response models: this is an
# additive, single-branch feature, not something every agent builds against.
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class PatientCreate(BaseModel):
    full_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    diabetes_type: Optional[str] = None  # freeform, see patient_models.Patient


class PatientResponse(BaseModel):
    id: str
    full_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    diabetes_type: Optional[str] = None
    created_at: datetime


class PatientScanSummary(BaseModel):
    """One row of a patient's scan history (GET /patients/{id}/scans).

    Richer than schemas.ScanListItem, which is the generic/all-patients scan
    list — this is a clinical history view, so it includes the probabilities
    and risk level directly rather than just enough to link out to a scan.
    """

    scan_id: str
    created_at: datetime
    risk_level: Optional[str] = None
    dr_probability: Optional[float] = None
    cataract_probability: Optional[float] = None


class TrendPoint(BaseModel):
    created_at: datetime
    dr_probability: Optional[float] = None
    cataract_probability: Optional[float] = None
    risk_level: Optional[str] = None


class TrendResponse(BaseModel):
    patient_id: str
    points: List[TrendPoint]
