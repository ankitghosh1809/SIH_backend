"""Agent C — scan orchestration routes.

Wires app.db.crud (Agent A) and app.ml.inference / app.ml.storage (Agent B)
behind the 4 scan endpoints from the shared API contract. Built and tested
against the stub versions of those modules below; nothing here should need
to change once the real db/ml modules land at the same paths.
"""

import time
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from app import config, schemas
from app.db import crud
from app.db.database import get_session
from app.ml import inference, storage

router = APIRouter(prefix="/api/v1/scans", tags=["scans"])

# Enough of a signature check to reject obviously-not-an-image uploads
# before they reach inference, without adding an image-decoding dependency
# to this file. Real format/corruption validation belongs in the eventual
# non-stub ml.inference.
_IMAGE_SIGNATURES = (
    b"\x89PNG\r\n\x1a\n",  # PNG
    b"\xff\xd8\xff",        # JPEG
    b"GIF87a",               # GIF
    b"GIF89a",
    b"BM",                    # BMP
    b"II*\x00",                # TIFF, little-endian
    b"MM\x00*",                 # TIFF, big-endian
)


def _looks_like_image(data: bytes) -> bool:
    return any(data.startswith(sig) for sig in _IMAGE_SIGNATURES)


def _to_scan_response(row) -> schemas.ScanResponse:
    return schemas.ScanResponse(
        scan_id=row.id,
        created_at=row.created_at,
        prediction=schemas.Prediction(
            diabetic_retinopathy=schemas.PredictionField(
                positive=row.dr_positive,
                probability=row.dr_probability,
                uncertainty=inference.compute_uncertainty(row.dr_probability),
            ),
            cataract=schemas.PredictionField(
                positive=row.cataract_positive,
                probability=row.cataract_probability,
                uncertainty=inference.compute_uncertainty(row.cataract_probability),
            ),
        ),
        risk_level=row.risk_level,
        heatmap_url=f"/api/v1/scans/{row.id}/heatmap",
        model_version=row.model_version,
    )


@router.post("", response_model=schemas.ScanResponse, status_code=201)
async def create_scan(
    file: UploadFile = File(...),
    patient_name: Optional[str] = Form(None),
    db=Depends(get_session),
    model=Depends(inference.get_model),
):
    image_bytes = await file.read()
    if not image_bytes or not _looks_like_image(image_bytes):
        raise HTTPException(status_code=422, detail="Uploaded file is not a readable image.")

    scan_id = str(uuid.uuid4())

    start = time.perf_counter()
    result = inference.run_inference(model, image_bytes)
    inference_ms = int((time.perf_counter() - start) * 1000)

    dr_probability = result["dr_probability"]
    cataract_probability = result["cataract_probability"]
    dr_positive = dr_probability > 0.5
    cataract_positive = cataract_probability > 0.5
    risk_level = inference.compute_risk_level(dr_probability, cataract_probability)

    image_path = storage.save_upload(scan_id, image_bytes)
    heatmap_path = storage.save_heatmap(scan_id, result["heatmap_bytes"])

    row = crud.create_scan(
        db,
        scan_id=scan_id,
        patient_name=patient_name,
        image_path=image_path,
        heatmap_path=heatmap_path,
        dr_probability=dr_probability,
        dr_positive=dr_positive,
        cataract_probability=cataract_probability,
        cataract_positive=cataract_positive,
        risk_level=risk_level,
        model_version=config.MODEL_VERSION,
        inference_ms=inference_ms,
    )

    return _to_scan_response(row)


@router.get("/{scan_id}", response_model=schemas.ScanResponse)
def get_scan(scan_id: str, db=Depends(get_session)):
    row = crud.get_scan(db, scan_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Scan not found.")
    return _to_scan_response(row)


@router.get("", response_model=List[schemas.ScanListItem])
def list_scans(limit: int = 20, db=Depends(get_session)):
    rows = crud.list_scans(db, limit=limit)
    return [
        schemas.ScanListItem(
            scan_id=row.id,
            created_at=row.created_at,
            risk_level=row.risk_level,
            # No dedicated "original image" / thumbnail endpoint exists in
            # the API contract yet, so this reuses the heatmap endpoint —
            # the only servable image URL currently defined. See handoff
            # notes.
            thumbnail_url=f"/api/v1/scans/{row.id}/heatmap",
        )
        for row in rows
    ]


@router.get("/{scan_id}/heatmap")
def get_scan_heatmap(scan_id: str):
    heatmap_bytes = storage.read_heatmap(scan_id)
    if heatmap_bytes is None:
        raise HTTPException(status_code=404, detail="Heatmap not found.")
    return Response(content=heatmap_bytes, media_type="image/png")
