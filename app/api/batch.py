"""Agent F — batch upload endpoint for camp / community screening mode.

Runs the same per-file logic as app.api.scans.create_scan (validate -> infer -> store ->
persist), looped over multiple files with per-item error isolation so one bad upload
doesn't abort the whole batch. No new DB table: a batch is just N ordinary scan rows.
"""

import time
import uuid
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from app import config
from app.db import crud
from app.db.database import get_session
from app.ml import inference, storage

router = APIRouter(prefix="/api/v1/batch", tags=["batch"])

# Screening-camp tool, not a bulk importer.
MAX_BATCH_SIZE = 50


class BatchItemResult(BaseModel):
    filename: str
    scan_id: str | None
    risk_level: str | None
    error: str | None


class BatchSummary(BaseModel):
    total: int
    succeeded: int
    failed: int
    low_risk: int
    medium_risk: int
    high_risk: int


class BatchResponse(BaseModel):
    results: List[BatchItemResult]
    summary: BatchSummary


@router.post("", response_model=BatchResponse, status_code=200)
async def create_batch(
    files: List[UploadFile] = File(...),
    db=Depends(get_session),
    model=Depends(inference.get_model),
):
    if len(files) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=422,
            detail=f"Batch of {len(files)} files exceeds the {MAX_BATCH_SIZE}-file limit per request.",
        )

    results: List[BatchItemResult] = []
    risk_counts = {"low": 0, "medium": 0, "high": 0}
    succeeded = 0

    for file in files:
        filename = file.filename or "unnamed"
        try:
            image_bytes = await file.read()
            scan_id = str(uuid.uuid4())

            # No separate "looks like an image" pre-check here (unlike scans.py):
            # run_inference's Image.open()/.load() already raises on unreadable bytes,
            # and that's what routes this item into the except branch below.
            start = time.perf_counter()
            result = inference.run_inference(model, image_bytes)
            inference_ms = int((time.perf_counter() - start) * 1000)

            dr_probability = result["dr_probability"]
            cataract_probability = result["cataract_probability"]
            risk_level = inference.compute_risk_level(dr_probability, cataract_probability)

            image_path = storage.save_upload(scan_id, image_bytes)
            heatmap_path = storage.save_heatmap(scan_id, result["heatmap_bytes"])

            row = crud.create_scan(
                db,
                scan_id=scan_id,
                image_path=image_path,
                heatmap_path=heatmap_path,
                dr_probability=dr_probability,
                dr_positive=dr_probability > 0.5,
                cataract_probability=cataract_probability,
                cataract_positive=cataract_probability > 0.5,
                risk_level=risk_level,
                model_version=config.MODEL_VERSION,
                inference_ms=inference_ms,
            )

            results.append(BatchItemResult(
                filename=filename, scan_id=row.id, risk_level=row.risk_level, error=None,
            ))
            succeeded += 1
            risk_counts[row.risk_level] += 1
        except Exception as exc:
            db.rollback()  # clears any half-done transaction so the next file isn't affected
            results.append(BatchItemResult(
                filename=filename, scan_id=None, risk_level=None, error=str(exc),
            ))

    total = len(files)
    summary = BatchSummary(
        total=total,
        succeeded=succeeded,
        failed=total - succeeded,
        low_risk=risk_counts["low"],
        medium_risk=risk_counts["medium"],
        high_risk=risk_counts["high"],
    )
    return BatchResponse(results=results, summary=summary)
