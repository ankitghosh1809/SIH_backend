# app/schemas.py — SHARED CONTRACT. Every agent creates this file identically.
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class PredictionField(BaseModel):
    positive: bool
    probability: float

class Prediction(BaseModel):
    diabetic_retinopathy: PredictionField
    cataract: PredictionField

class ScanResponse(BaseModel):
    scan_id: str
    created_at: datetime
    prediction: Prediction
    risk_level: str          # "low" | "medium" | "high"
    heatmap_url: str
    model_version: str

class ScanListItem(BaseModel):
    scan_id: str
    created_at: datetime
    risk_level: str
    thumbnail_url: str

class ModelMetrics(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1: float
    auc_roc: float

class MetricsResponse(BaseModel):
    classical: Optional[ModelMetrics] = None
    hybrid_quantum: Optional[ModelMetrics] = None
    evaluated_on: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
