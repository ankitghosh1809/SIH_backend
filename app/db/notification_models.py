"""
ORM model for the notifications table (Agent Q).

Same Base-reuse pattern as app/db/review_models.py and app/db/audit_models.py:
reuses the existing Base so SQLAlchemy registers `notifications` alongside
the other tables as soon as this module is imported anywhere in the app
(it's imported at the top of app/notifications/service.py and
app/api/notifications.py).

No ForeignKey on scan_id: the work order's column spec lists it as a plain
nullable VARCHAR(36), not an explicit reference, and — unlike Review, which
only ever means one specific scan — future event_types (see
app/notifications/service.py) might not all be scan-shaped. Kept loose on
purpose rather than adding a constraint nothing asked for.
"""
from sqlalchemy import Boolean, Column, DateTime, String, Text, func

from app.db.models import Base  # reuse the EXISTING Base — do not create a new one


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True)
    event_type = Column(String(60), nullable=False)  # "high_risk_detected" | "review_completed"
    scan_id = Column(String(36), nullable=True)
    channel = Column(String(20), nullable=False, default="in_app")
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())
