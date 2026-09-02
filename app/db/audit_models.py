"""
ORM model for the request audit log (Agent Q).

Kept in its own module, same pattern as app/db/review_models.py: reuses the
existing Base so SQLAlchemy registers `audit_logs` alongside `scans`,
`reviews`, etc. as soon as this module is imported anywhere in the app (it's
imported at the top of app/audit/middleware.py and app/api/audit.py).
"""
from sqlalchemy import Column, DateTime, String, func

from app.db.models import Base  # reuse the EXISTING Base — do not create a new one


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True)
    actor = Column(String(120), nullable=True)  # "authenticated" | "anonymous" — see
    # app/audit/middleware.py for why this is coarse rather than a real username.
    action = Column(String(80), nullable=False)  # e.g. "POST /api/v1/scans"
    resource_type = Column(String(40), nullable=True)  # unused for now — see middleware.py
    resource_id = Column(String(36), nullable=True)    # unused for now — see middleware.py
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
