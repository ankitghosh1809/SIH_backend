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
