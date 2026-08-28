"""
Disk-backed storage for uploaded scans and their generated heatmaps.
Local disk under storage/ (already in .gitignore) — no S3/Cloudinary needed for the hackathon.
"""
import os

_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ROOT_DIR = os.path.dirname(_APP_DIR)

STORAGE_ROOT = os.path.join(_ROOT_DIR, "storage")
UPLOADS_DIR = os.path.join(STORAGE_ROOT, "uploads")
HEATMAPS_DIR = os.path.join(STORAGE_ROOT, "heatmaps")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(HEATMAPS_DIR, exist_ok=True)


def save_upload(scan_id: str, image_bytes: bytes) -> str:
    """Saves the raw uploaded scan to disk, returns the path."""
    path = os.path.join(UPLOADS_DIR, scan_id)
    with open(path, "wb") as f:
        f.write(image_bytes)
    return path


def save_heatmap(scan_id: str, heatmap_bytes: bytes) -> str:
    """Saves the generated heatmap to disk, returns the path."""
    path = os.path.join(HEATMAPS_DIR, f"{scan_id}.png")
    with open(path, "wb") as f:
        f.write(heatmap_bytes)
    return path


def read_heatmap(scan_id: str) -> bytes | None:
    """Reads a saved heatmap back for serving. None if not found."""
    path = os.path.join(HEATMAPS_DIR, f"{scan_id}.png")
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f.read()
