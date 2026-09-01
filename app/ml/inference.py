"""
Byte-oriented adapter between the API layer and model_backend.py.
The API layer only ever deals in bytes; model_backend only ever deals in PIL Images.
"""
import io
from functools import lru_cache

from PIL import Image

from app import config
from . import model_backend


def load_model():
    """Called once at FastAPI startup."""
    try:
        from app.config import MODEL_PATH
    except ImportError:
        # ponytail: config.py doesn't exist yet (Agent D, parallel track) — falls back to None,
        # which model_backend.load_model() already accepts. Drop the try/except once it lands.
        MODEL_PATH = None
    return model_backend.load_model(MODEL_PATH)


@lru_cache(maxsize=1)
def get_model():
    """Cached single-load entry point (Round 3 / Agent P). The model used to be loaded
    three times independently: at import time in scans.py, again at import time in
    batch.py, and again in main.py's startup lifespan. lru_cache makes this the one
    place construction actually happens — whichever caller runs first (lifespan
    warming it at startup, or a route's Depends(get_model) on the first real request,
    which is what happens under the test suite since lifespan doesn't run there)
    builds it once; everyone after gets the same cached object back. Route handlers
    should depend on this, not call load_model() directly."""
    return load_model()


def run_inference(model, image_bytes: bytes) -> dict:
    """bytes in -> PIL -> model_backend.predict() -> bytes back out.
    Returns {"dr_probability": float, "cataract_probability": float, "heatmap_bytes": bytes}"""
    image = Image.open(io.BytesIO(image_bytes))
    image.load()

    result = model_backend.predict(model, image)

    heatmap_buffer = io.BytesIO()
    result["heatmap"].save(heatmap_buffer, format="PNG")

    return {
        "dr_probability": float(result["dr_probability"]),
        "cataract_probability": float(result["cataract_probability"]),
        "heatmap_bytes": heatmap_buffer.getvalue(),
    }


def compute_risk_level(dr_probability: float, cataract_probability: float) -> str:
    """low | medium | high, from the max of the two probabilities against the named,
    configurable band cutoffs in app.config (RISK_THRESHOLD_MEDIUM / _HIGH). Same
    comparison logic as before (was hardcoded 0.4 / 0.7); Round 3 (Agent P) only
    moved the numbers into config so recalibration doesn't mean hunting through
    this file."""
    max_probability = max(dr_probability, cataract_probability)
    if max_probability < config.RISK_THRESHOLD_MEDIUM:
        return "low"
    if max_probability < config.RISK_THRESHOLD_HIGH:
        return "medium"
    return "high"


def compute_uncertainty(probability: float) -> float:
    """Placeholder uncertainty proxy: highest (1.0) at probability=0.5 (model maximally
    undecided), lowest (0.0) at probability=0 or 1 (model fully confident either way).
    PLACEHOLDER — once the real model lands, replace with its actual predictive
    variance / quantum measurement variance if that's richer than this proxy; call
    sites don't need to change either way, only this function's body."""
    return round(1.0 - 2.0 * abs(probability - 0.5), 3)
