_FAKE_FILES = {}
def save_upload(scan_id, image_bytes):
    _FAKE_FILES[f"upload:{scan_id}"] = image_bytes
    return f"stub/uploads/{scan_id}.png"
def save_heatmap(scan_id, heatmap_bytes):
    _FAKE_FILES[f"heatmap:{scan_id}"] = heatmap_bytes
    return f"stub/heatmaps/{scan_id}.png"
def read_heatmap(scan_id):
    return _FAKE_FILES.get(f"heatmap:{scan_id}")
