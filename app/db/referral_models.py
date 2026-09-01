"""
app/db/referral_models.py — Agent O (Round 3): the `referrals` table.

New file, following the same pattern as the existing app/db/review_models.py
(reuses the shared declarative Base from app.db.models rather than
declaring a new one).

ASSUMPTION — I could not read the real app/db/review_models.py in this
session (see chat for why), so the exact style below — Column-based
declarative mapping, a uuid4-string primary key, server-side now() for
timestamps — is a best-effort match for a SQLAlchemy 2.x FastAPI project
like this one, not a confirmed copy of your conventions. If
review_models.py actually uses the newer Mapped[]/mapped_column() style,
mirror that here instead. See ASSUMPTIONS_AND_TODO.md.
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func

from app.db.models import Base


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id = Column(String(36), ForeignKey("scans.id"), nullable=False)
    facility_name = Column(String(150), nullable=False)
    facility_contact = Column(String(120), nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
