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
agent-p-model-confidence
from app.api import explain
from app.api import referrals
from app.api import patients
main


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    # Round 3 (Agent P): warms inference.get_model()'s lru_cache before serving
    # traffic, purely for its side effect — nothing reads the return value, and
    # app.state.model is gone (nothing read that either). Routes that need the
    # model take it as a Depends(inference.get_model) parameter instead (see
    # app/api/scans.py, app/api/batch.py). That's a deliberate choice, not an
    # oversight: reading request.app.state.model from route handlers would break
    # under most of this test suite, since lifespan only runs when TestClient is
    # entered via `with TestClient(app) as client:` (tests/test_review.py has the
    # full explanation), which most of the existing tests don't do. The
    # lru_cache'd dependency gives a true single load either way — whichever
    # caller resolves it first, this warm-up or a route's first real request,
    # builds it once and everyone after reuses that same object.
    inference.get_model()
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
agent-p-model-confidence
app.include_router(explain.router)
app.include_router(referrals.router)
app.include_router(patients.router)
main
