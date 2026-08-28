import random
def load_model():
    return {"stub": True}
def run_inference(model, image_bytes: bytes) -> dict:
    random.seed(len(image_bytes) or 1)
    return {"dr_probability": round(random.uniform(0.05, 0.95), 3),
            "cataract_probability": round(random.uniform(0.05, 0.95), 3),
            "heatmap_bytes": b"\x89PNG\r\n\x1a\n"}
def compute_risk_level(dr_probability, cataract_probability) -> str:
    top = max(dr_probability, cataract_probability)
    return "high" if top > 0.7 else "medium" if top > 0.4 else "low"
