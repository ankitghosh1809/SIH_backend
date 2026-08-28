from types import SimpleNamespace
from datetime import datetime

def create_scan(db, *, scan_id, patient_name=None, image_path, heatmap_path=None, dr_probability,
                 dr_positive, cataract_probability, cataract_positive, risk_level,
                 model_version, inference_ms):
    row = SimpleNamespace(id=scan_id, patient_name=patient_name, image_path=image_path,
                           heatmap_path=heatmap_path, dr_probability=dr_probability,
                           dr_positive=dr_positive, cataract_probability=cataract_probability,
                           cataract_positive=cataract_positive, risk_level=risk_level,
                           model_version=model_version, inference_ms=inference_ms,
                           created_at=datetime.utcnow())
    db["scans"][row.id] = row
    return row

def get_scan(db, scan_id):
    return db["scans"].get(scan_id)

def list_scans(db, limit=20):
    return list(db["scans"].values())[:limit]

def record_metrics(db, **kwargs):
    db["metrics"].append(SimpleNamespace(**kwargs))

def get_latest_metrics(db):
    out = {"classical": None, "hybrid_quantum": None}
    for m in db["metrics"]:
        out[m.model_type] = m
    return out
