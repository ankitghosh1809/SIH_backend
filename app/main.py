"""
app/main.py — Agent D

Builds the FastAPI app, wires CORS from config.ALLOWED_ORIGINS, runs startup hooks
(db init + model load), and mounts both routers.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.db import database
from app.ml import inference
from app.api import scans, metrics, reports
from app.api import review


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

app.include_router(scans.router)
app.include_router(metrics.router)
app.include_router(reports.router)
app.include_router(review.router)
