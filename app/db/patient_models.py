"""
ORM model for the patient registry (Round 3, Agent N).

Kept in its own module rather than added to app/db/models.py so this
feature's schema stays isolated on this branch — same pattern as
app/db/review_models.py for the doctor review workflow. It reuses the
existing Base, so SQLAlchemy registers `patients` alongside `scans`,
`model_metrics`, and `reviews` as soon as this module is imported anywhere
in the app (it's imported at the top of app/api/patients.py, which itself
is imported by app/main.py when the router is registered).
"""
from sqlalchemy import Column, DateTime, Integer, String, func

from app.db.models import Base  # reuse the EXISTING Base — do not create a new one


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String(36), primary_key=True)  # uuid4, stored as string — same convention as scans.id
    full_name = Column(String(120), nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    phone = Column(String(20), nullable=True)
    # Freeform on purpose (work order: "validate loosely, don't hard-reject unknown
    # strings") — 'type1' | 'type2' | 'unknown' | any other string | NULL. No CHECK
    # constraint / enum here so an unexpected value from the frontend can never 500.
    diabetes_type = Column(String(20), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
