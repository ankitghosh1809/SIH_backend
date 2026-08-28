"""Self-test for the ml integration wrapper (model_backend, inference, storage)."""
import io
import os

from PIL import Image

from app.ml import inference, storage


def _dummy_image_bytes() -> bytes:
    image = Image.new("RGB", (10, 10), (0, 128, 255))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_run_inference_returns_all_three_keys_with_correct_types():
    model = inference.load_model()
    result = inference.run_inference(model, _dummy_image_bytes())

    assert set(result.keys()) == {"dr_probability", "cataract_probability", "heatmap_bytes"}
    assert isinstance(result["dr_probability"], float)
    assert isinstance(result["cataract_probability"], float)
    assert isinstance(result["heatmap_bytes"], bytes)
    assert 0.0 <= result["dr_probability"] <= 1.0
    assert 0.0 <= result["cataract_probability"] <= 1.0
    assert len(result["heatmap_bytes"]) > 0


def test_compute_risk_level_covers_all_three_bands():
    assert inference.compute_risk_level(0.1, 0.2) == "low"
    assert inference.compute_risk_level(0.5, 0.3) == "medium"
    assert inference.compute_risk_level(0.9, 0.1) == "high"


def test_save_and_read_heatmap_round_trip():
    scan_id = "test-scan-roundtrip-0001"
    original_bytes = _dummy_image_bytes()

    assert storage.read_heatmap(scan_id) is None

    saved_path = storage.save_heatmap(scan_id, original_bytes)
    assert os.path.exists(saved_path)
    assert storage.read_heatmap(scan_id) == original_bytes

    os.remove(saved_path)
