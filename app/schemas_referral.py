"""
app/schemas_referral.py — Agent O (Round 3): Pydantic schemas for the
referral & clinical escalation workflow.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

ReferralStatus = Literal["pending", "contacted", "completed", "declined"]


class ReferralCreate(BaseModel):
    facility_name: str
    facility_contact: Optional[str] = None
    notes: Optional[str] = None


class ReferralUpdate(BaseModel):
    # Literal here means FastAPI/Pydantic reject an out-of-set status with a
    # 422 automatically — satisfies the work order's validation requirement
    # without extra checks in the route itself.
    status: Optional[ReferralStatus] = None
    notes: Optional[str] = None


class ReferralResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    scan_id: str
    facility_name: str
    facility_contact: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class FacilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    city: str
    contact: str


class ReferralSuggestion(BaseModel):
    suggested: bool
    reason: Optional[str] = None
