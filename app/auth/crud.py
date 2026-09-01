"""
app/auth/crud.py — Agent M

CRUD helpers for the `users` table. Same shape as app/db/crud.py: plain
functions taking a `db: Session` first arg, no repository class.
"""
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.auth.security import hash_password, verify_password
from app.db.auth_models import User


def create_user(
    db: Session, *, username: str, password: str, role: str, full_name: Optional[str] = None
) -> User:
    """Hash `password` and insert a new user row. Raises sqlalchemy.exc.IntegrityError
    on a duplicate username (UNIQUE constraint) — app/api/auth.py's /register
    handler is responsible for turning that into a 409 response."""
    user = User(
        id=str(uuid.uuid4()),
        username=username,
        hashed_password=hash_password(password),
        role=role,
        full_name=full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Return the User row if `username` exists and `password` matches its
    hash, else None. Callers turn a None into a 401."""
    user = get_user_by_username(db, username)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user
