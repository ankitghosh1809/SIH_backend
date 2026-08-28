"""
Placeholder model backend. Arushi & Pramati's real load_model()/predict() replaces the BODY of
this file when their model is ready (matches the interface in their ML brief already) —
inference.py imports from this exact path and never needs to change.
"""
import random
from PIL import Image

def load_model(checkpoint_path: str = None):
    return {"stub": True}

def predict(model, image: Image.Image) -> dict:
    random.seed(image.size[0] + image.size[1])
    heatmap = Image.new("RGB", image.size, (255, 0, 0))   # flat placeholder "heatmap"
    return {
        "dr_probability": round(random.uniform(0.05, 0.95), 3),
        "cataract_probability": round(random.uniform(0.05, 0.95), 3),
        "heatmap": heatmap,
    }
