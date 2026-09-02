"""
app/auth/schemas.py — Agent M

Pydantic request/response contracts for the auth system. Kept separate from
app/schemas.py (the cross-agent scan/prediction contract) since auth is
Agent M's own concern, not something the ML/frontend tracks build against.
"""
from typing import Optional

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str
    role: str  # 'admin' | 'doctor' | 'camp_staff' — validated in app/api/auth.py's
    # /register handler (same manual-check-then-422 style app/api/review.py
    # already uses for override_risk_level), not here, so the 422 error body
    # stays consistent across both endpoints.
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    username: str
    role: str
    full_name: Optional[str] = None
    is_active: bool
    # Deliberately no hashed_password field: this is what every auth endpoint
    # returns, so leaving it out here is what makes "never return a password
    # hash" structurally true rather than something each endpoint has to
    # remember.


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
