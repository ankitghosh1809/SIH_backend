"""
ORM model for the doctor review workflow (Agent G).

Kept in its own module rather than added to app/db/models.py so this
feature's schema stays isolated on this branch. It reuses the existing
Base, so SQLAlchemy registers `reviews` alongside `scans` and
`model_metrics` as soon as this module is imported anywhere in the app
(it's imported at the top of app/api/review.py, which itself is imported
by app/main.py when the router is registered — see Task 3).
"""
from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func

from app.db.models import Base  # reuse the EXISTING Base — do not create a new one


class Review(Base):
    __tablename__ = "reviews"

    id = Column(String(36), primary_key=True)
    scan_id = Column(String(36), ForeignKey("scans.id"), nullable=False)
    reviewer_note = Column(Text, nullable=True)
    override_risk_level = Column(String(10), nullable=True)  # low | medium | high | None
    reviewed_at = Column(DateTime, server_default=func.now())
