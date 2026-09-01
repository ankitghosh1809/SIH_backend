"""
app/auth/security.py — Agent M

Password hashing and JWT issuance/verification for the role-based auth
system that replaces the single shared DOCTOR_API_KEY on the doctor-review
endpoint and adds auth to the previously-open GET /admin/stats.

Library choices (work order left both open, to be checked at build time):
- passlib[bcrypt] for hashing, as specified.
- PyJWT over python-jose for the JWT itself: python-jose has had no release
  since 2021 and has a real CVE (CVE-2024-33663, an algorithm-confusion
  issue); FastAPI's own docs moved to recommending PyJWT for the same
  reason. The OAuth2PasswordBearer + OAuth2PasswordRequestForm flow the work
  order asks for (so Swagger's "Authorize" button works at /docs) is a
  fastapi.security class, independent of which JWT library backs it, so
  swapping the encode/decode library doesn't change that pattern at all.
- requirements.txt also pins `bcrypt==4.0.1`: passlib 1.7.4 (its last
  release) can't read the version string on bcrypt>=4.1 and, with bcrypt 5.x
  specifically, this isn't just a cosmetic warning — password hashing
  outright raises ValueError. Confirmed empirically while building this:
  bcrypt 5.0.0 breaks passlib's hash()/verify() entirely; bcrypt==4.0.1
  works cleanly. Revisit the pin if passlib ever ships a fix.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app import config
from app.db.auth_models import User
from app.db.database import get_session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# tokenUrl points at the real login route so Swagger's "Authorize" button at
# /docs knows where to POST username/password to get a token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_session)
) -> User:
    # ASSUMPTION: the token's "sub" claim is the username (not the user id),
    # matching the well-trodden FastAPI OAuth2+JWT tutorial pattern the work
    # order points at, and matching get_user_by_username being the crud
    # function the work order asks for (rather than get_user_by_id).
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    # Local import to avoid a circular import: app.auth.crud imports
    # hash_password/verify_password from this module at module load time, so
    # this module can't import app.auth.crud back at *its* module load time
    # too — only inside a function body, once both modules have already
    # finished loading.
    from app.auth.crud import get_user_by_username

    user = get_user_by_username(db, username)
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_role(*roles: str):
    """Dependency factory: Depends(require_role("admin")) or
    Depends(require_role("doctor", "admin")). Role is re-checked against the
    DB on every request (via get_current_user, not a role baked into the
    token) so a role change or deactivation takes effect on the user's very
    next request rather than only once their current token expires."""

    def _require_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(roles)}",
            )
        return current_user

    return _require_role
