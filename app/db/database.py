"""Engine + session setup.

Reads DATABASE_URL from the environment; defaults to a local SQLite file so
the app runs with zero config out of the box. Point DATABASE_URL at Neon
Postgres in prod.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./dev.db")

# SQLite needs this since FastAPI can hand a request to a different thread
# than the one that opened the connection; Postgres doesn't need it.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create the scans / model_metrics tables if they don't already exist."""
    Base.metadata.create_all(bind=engine)


def get_session():
    """FastAPI Depends-style generator: yields a session, closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
