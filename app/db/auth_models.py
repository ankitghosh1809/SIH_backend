"""
ORM model for user accounts (Agent M) — replaces the single shared
DOCTOR_API_KEY (app/api/review.py) and the fully-open GET /admin/stats
(app/api/admin.py) with real per-user, role-based credentials.

Kept in its own module rather than added to app/db/models.py, same pattern
as app/db/review_models.py: reuses the existing Base, so SQLAlchemy
registers `users` alongside `scans`, `model_metrics`, and `reviews` as soon
as this module is imported anywhere in the app (it's imported at the top of
app/api/auth.py and app/auth/security.py, both pulled in transitively via
app/main.py when the auth router is registered — see app/main.py).
"""
from sqlalchemy import Boolean, Column, DateTime, String, func

from app.db.models import Base  # reuse the EXISTING Base — do not create a new one


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)  # uuid4 as text, same convention as scans.id
    username = Column(String(60), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # 'admin' | 'doctor' | 'camp_staff'
    full_name = Column(String(120), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
