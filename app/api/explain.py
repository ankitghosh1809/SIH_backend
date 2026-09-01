"""
Explainability endpoint (Round 3 / Agent P): GET /api/v1/scans/{scan_id}/explain.

Read-only companion to GET /api/v1/scans/{scan_id}: surfaces the same scan's
per-condition uncertainty (computed the same way _to_scan_response() does in
scans.py, via inference.compute_uncertainty() — not a stored column, since it's
a pure function of the already-persisted probability, see the comment above
compute_uncertainty() in app/ml/inference.py) alongside placeholder explanation
text. Doesn't modify the scan or create anything.

(The work order's stretch goal — a classical/quantum agreement field here —
wasn't built; see the FUTURE note in app/schemas_explain.py for why.)
"""
from fastapi import APIRouter, Depends, HTTPException

from app.db import crud
from app.db.database import get_session
from app.ml import inference
from app.ml.explain import generate_explanation
from app.schemas_explain import ExplainResponse

router = APIRouter(prefix="/api/v1", tags=["explain"])


@router.get("/scans/{scan_id}/explain", response_model=ExplainResponse)
def explain_scan(scan_id: str, db=Depends(get_session)):
    scan = crud.get_scan(db, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found.")

    return ExplainResponse(
        scan_id=scan.id,
        dr_uncertainty=inference.compute_uncertainty(scan.dr_probability),
        cataract_uncertainty=inference.compute_uncertainty(scan.cataract_probability),
        explanation_text=generate_explanation(scan.dr_probability, scan.cataract_probability),
    )
