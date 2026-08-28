"""
Byte-oriented adapter between the API layer and model_backend.py.
The API layer only ever deals in bytes; model_backend only ever deals in PIL Images.
"""
import io

from PIL import Image

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
    """low | medium | high — placeholder thresholds (0.4 / 0.7 on the max of the two
    probabilities). ponytail: revisit once real model calibration is known."""
    max_probability = max(dr_probability, cataract_probability)
    if max_probability < 0.4:
        return "low"
    if max_probability < 0.7:
        return "medium"
    return "high"
