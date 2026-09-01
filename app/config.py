"""
app/config.py — Agent D

Reads deployment configuration from the environment, with sane local defaults so
the app boots standalone with zero setup.
"""

import os


def _split_origins(raw: str) -> list[str]:
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


# Local/dev default keeps standalone runs working with no env vars set; Render or
# Railway will inject the real Postgres URL (from Neon) at deploy time.
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./local_dev.db")

# Path Agent B's ml/inference.py (and eventually Arushi & Pramati's trained
# model) loads weights from.
MODEL_PATH: str = os.getenv("MODEL_PATH", "./models/model_weights.pt")

# Model version string surfaced in every ScanResponse / BatchItemResult. Round 3
# (Agent P) centralized this here — it used to be a literal "stub-v0" duplicated
# separately in app/api/scans.py and app/api/batch.py.
MODEL_VERSION: str = os.getenv("MODEL_VERSION", "stub-v0")

# compute_risk_level's band cutoffs (app/ml/inference.py), applied to the max of
# the two predicted probabilities: below MEDIUM -> "low", below HIGH -> "medium",
# else "high". Round 3 (Agent P) promoted these out of inference.py's hardcoded
# 0.4 / 0.7 so recalibration is a config change once real model calibration data
# exists. Values are unchanged for now — there's no calibration data yet.
RISK_THRESHOLD_MEDIUM: float = float(os.getenv("RISK_THRESHOLD_MEDIUM", "0.4"))
RISK_THRESHOLD_HIGH: float = float(os.getenv("RISK_THRESHOLD_HIGH", "0.7"))

# Comma-separated in the environment, e.g.
#   ALLOWED_ORIGINS=https://sih-frontend.vercel.app,http://localhost:3000
# parsed into a list for FastAPI's CORSMiddleware.
ALLOWED_ORIGINS: list[str] = _split_origins(
    os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
)

# --- Agent M additions: JWT auth + rate limiting -----------------------------

# DEV ONLY — override in production. Anyone with this value can mint a valid
# token for any user, so a real deployment MUST set SECRET_KEY in the
# environment rather than trust this default. Kept intentionally long so
# PyJWT's HS256 doesn't emit an "insecure key length" warning locally
# (RFC 7518 recommends >= 32 bytes for HS256).
SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-only-insecure-secret-key-change-me-before-any-real-deploy")
ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Applies to both POST /api/v1/scans and POST /api/v1/batch (see app/api/scans.py,
# app/api/batch.py). slowapi's decorator takes a ratelimit-string directly
# ("<n>/minute"), so we store the pre-formatted string rather than a bare int.
UPLOAD_RATE_LIMIT: str = os.getenv("UPLOAD_RATE_LIMIT", "25/minute")

# Single shared Limiter instance. Lives here (rather than in app/main.py, or a
# new module) so both app/main.py *and* the route modules that need the
# @limiter.limit(...) decorator (scans.py, batch.py) can import it without a
# circular import through main.py, which is what imports scans/batch/etc. in
# the first place. app.state.limiter and the exception handler are still
# wired up in app/main.py — constructing a Limiter doesn't need an app.
from slowapi import Limiter  # noqa: E402  (after the plain constants above, on purpose)
from slowapi.util import get_remote_address  # noqa: E402

limiter = Limiter(key_func=get_remote_address)
