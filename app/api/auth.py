"""
app/api/auth.py — Agent M

Registration, login, and "who am I" for the JWT-based auth system. This is
what app/api/review.py and app/api/admin.py now depend on (via
app.auth.security.require_role) instead of the single shared DOCTOR_API_KEY
and the previously-open GET /admin/stats.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import crud
from app.auth.schemas import Token, UserCreate, UserResponse
from app.auth.security import create_access_token, get_current_user
from app.db.auth_models import User  # import registers the `users` table
from app.db.database import get_session

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

VALID_ROLES = {"admin", "doctor", "camp_staff"}


def _to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        full_name=user.full_name,
        is_active=user.is_active,
    )


# Registration is open to any role for hackathon-demo purposes: anyone can
# currently create a `doctor` or `admin` account with no invite or approval
# step. This is a deliberate scope decision for a short build, same spirit
# as the DOCTOR_API_KEY docstring this system replaces — restrict this
# (e.g. admin-invited-only for privileged roles, or a separate admin-only
# "create user" endpoint) before this goes anywhere near a real deployment
# with real patients.
@router.post("/register", response_model=UserResponse, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_session)):
    if payload.role not in VALID_ROLES:
        raise HTTPException(
            status_code=422,
            detail=f"role must be one of: {', '.join(sorted(VALID_ROLES))}",
        )
    try:
        user = crud.create_user(
            db,
            username=payload.username,
            password=payload.password,
            role=payload.role,
            full_name=payload.full_name,
        )
    except IntegrityError:
        # ASSUMPTION: the work order doesn't specify a status code for a
        # duplicate username. 409 Conflict (rather than the 400 the plain
        # FastAPI tutorial uses) to match this repo's existing habit of
        # precise status codes elsewhere (404 for a missing scan, 422 for an
        # invalid override_risk_level).
        db.rollback()
        raise HTTPException(status_code=409, detail="Username already registered")
    return _to_user_response(user)


# OAuth2PasswordRequestForm (username/password as form fields, not JSON) is
# what makes /docs' built-in "Authorize" button work out of the box — see
# work order.
@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return _to_user_response(current_user)
