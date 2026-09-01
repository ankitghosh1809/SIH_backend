"""SQLAlchemy ORM models for the `scans` and `model_metrics` tables.

`Scan.id` uses String(36) (uuid4 stored as text) rather than a Postgres-specific
UUID type, so these models work unchanged against SQLite (tests/dev) and
Postgres / Neon (prod).
"""
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Scan(Base):
    __tablename__ = "scans"

    id = Column(String(36), primary_key=True)  # uuid4, stored as string
    patient_name = Column(String(120), nullable=True)
    # Round 3 / Agent N: optional link to a real patients row. Nullable so every
    # existing call site and all old data (patient_name only, no patient_id)
    # keeps working completely unchanged — see app/api/patients.py.
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=True)
    image_path = Column(Text, nullable=False)
    heatmap_path = Column(Text, nullable=True)
    dr_probability = Column(Float)
    dr_positive = Column(Boolean)
    cataract_probability = Column(Float)
    cataract_positive = Column(Boolean)
    risk_level = Column(String(10))  # "low" | "medium" | "high"
    model_version = Column(String(40))
    inference_ms = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())


class ModelMetrics(Base):
    __tablename__ = "model_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_type = Column(String(20))  # "classical" | "hybrid_quantum"
    accuracy = Column(Float)
    precision_score = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    auc_roc = Column(Float)
    test_set_size = Column(Integer)
    evaluated_at = Column(DateTime, server_default=func.now())
