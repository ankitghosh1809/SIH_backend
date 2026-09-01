"""
app/main.py — Agent D

Builds the FastAPI app, wires CORS from config.ALLOWED_ORIGINS, runs startup hooks
(db init + model load), and mounts both routers.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app import config
from app.db import database
from app.ml import inference
from app.api import scans, metrics, reports
from app.api import admin
from app.api import auth
from app.api import review
from app.api import batch
from app.api import referrals


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    # Stashed on app.state so scans.py can reach it via request.app.state.model.
    app.state.model = inference.load_model()
    yield


app = FastAPI(title="SIH26139 — Hybrid Quantum ML Diagnostics API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Agent M: rate limiting. The Limiter instance itself lives in app.config (see
# that file for why); this is just the per-app wiring slowapi needs — the
# @limiter.limit(...) decorators are on the two routes in scans.py/batch.py.
app.state.limiter = config.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(scans.router)
app.include_router(metrics.router)
app.include_router(reports.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(review.router)
app.include_router(batch.router)
app.include_router(referrals.router)
