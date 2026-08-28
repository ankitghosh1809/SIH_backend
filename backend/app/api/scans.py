from fastapi import APIRouter
router = APIRouter()

@router.post("/api/v1/scans")
def _stub_create_scan():
    return {"stub": "replace with Agent C's real app/api/scans.py at stitch time"}

@router.get("/api/v1/scans/{scan_id}")
def _stub_get_scan(scan_id: str):
    return {"stub": True, "scan_id": scan_id}

@router.get("/api/v1/scans")
def _stub_list_scans():
    return []

@router.get("/api/v1/scans/{scan_id}/heatmap")
def _stub_heatmap(scan_id: str):
    return {"stub": True}
