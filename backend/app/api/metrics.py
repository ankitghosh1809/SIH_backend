"""
app/api/metrics.py — Agent D

GET /api/v1/metrics -> schemas.MetricsResponse, built from db.crud.get_latest_metrics()
GET /api/v1/health   -> schemas.HealthResponse, always {"status": "ok"}
"""

from fastapi import APIRouter

from app import schemas
from app.db import crud

router = APIRouter()


@router.get("/api/v1/metrics", response_model=schemas.MetricsResponse)
def get_metrics() -> schemas.MetricsResponse:
    data = crud.get_latest_metrics()
    return schemas.MetricsResponse(
        classical=data.get("classical"),
        hybrid_quantum=data.get("hybrid_quantum"),
        evaluated_on=data.get("evaluated_on"),
    )


@router.get("/api/v1/health", response_model=schemas.HealthResponse)
def get_health() -> schemas.HealthResponse:
    return schemas.HealthResponse(status="ok")
