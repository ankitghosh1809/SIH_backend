"""
app/api/reports.py — Agent E

GET /api/v1/scans/{scan_id}/report -> downloadable PDF clinical report for one scan.
Pulls the scan row via app.db.crud.get_scan and the heatmap via app.ml.storage.read_heatmap,
then hands both to app.reports.pdf_generator.build_scan_report_pdf.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.db import crud
from app.db.database import get_session
from app.ml import storage
from app.reports.pdf_generator import build_scan_report_pdf

router = APIRouter(prefix="/api/v1/scans", tags=["reports"])


@router.get("/{scan_id}/report")
def get_scan_report(scan_id: str, db=Depends(get_session)):
    scan = crud.get_scan(db, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found.")

    heatmap_bytes = storage.read_heatmap(scan_id)
    pdf_bytes = build_scan_report_pdf(scan, heatmap_bytes)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="scan_{scan_id}_report.pdf"'},
    )
