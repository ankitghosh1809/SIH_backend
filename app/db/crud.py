"""CRUD functions for the `scans` and `model_metrics` tables.

Signatures are a fixed contract — Agent C and Agent D import and call these
by name, so don't change them.
"""
from app.db.models import ModelMetrics, Scan


def create_scan(db, *, scan_id: str, patient_name=None, patient_id=None, image_path, heatmap_path=None,
                 dr_probability, dr_positive, cataract_probability, cataract_positive,
                 risk_level, model_version, inference_ms):
    """Insert one scan row using the caller-supplied scan_id and return it."""
    scan = Scan(
        id=scan_id,
        patient_name=patient_name,
        patient_id=patient_id,
        image_path=image_path,
        heatmap_path=heatmap_path,
        dr_probability=dr_probability,
        dr_positive=dr_positive,
        cataract_probability=cataract_probability,
        cataract_positive=cataract_positive,
        risk_level=risk_level,
        model_version=model_version,
        inference_ms=inference_ms,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan


def get_scan(db, scan_id: str):
    """Return the Scan row with this id, or None."""
    return db.get(Scan, scan_id)


def list_scans(db, limit: int = 20):
    """Return up to `limit` scans, newest first."""
    return db.query(Scan).order_by(Scan.created_at.desc()).limit(limit).all()


def record_metrics(db, *, model_type: str, accuracy, precision, recall, f1, auc_roc,
                    test_set_size):
    """Persist one evaluation row for model_type ("classical" | "hybrid_quantum")."""
    metric = ModelMetrics(
        model_type=model_type,
        accuracy=accuracy,
        precision_score=precision,
        recall=recall,
        f1_score=f1,
        auc_roc=auc_roc,
        test_set_size=test_set_size,
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


def get_latest_metrics(db) -> dict:
    """Return {"classical": <row-or-None>, "hybrid_quantum": <row-or-None>} — latest per type."""
    latest = {}
    for model_type in ("classical", "hybrid_quantum"):
        latest[model_type] = (
            db.query(ModelMetrics)
            .filter(ModelMetrics.model_type == model_type)
            .order_by(ModelMetrics.evaluated_at.desc())
            .first()
        )
    return latest
