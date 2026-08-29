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

# Comma-separated in the environment, e.g.
#   ALLOWED_ORIGINS=https://sih-frontend.vercel.app,http://localhost:3000
# parsed into a list for FastAPI's CORSMiddleware.
ALLOWED_ORIGINS: list[str] = _split_origins(
    os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
)
