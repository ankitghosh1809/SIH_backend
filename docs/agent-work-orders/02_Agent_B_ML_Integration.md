# Backend Work Order — Agent B: ML Model Integration Wrapper

> One of 4 parallel work orders that split **Ankit's** Backend & Database track (SIH26139 —
> Hybrid Quantum ML Platform for Early Disease Detection, applied to diabetic retinopathy +
> cataract screening) into 4 independent modules, so 4 coding agents can build them **at the
> same time** instead of one agent doing it serially. Full team: Ankit (backend & DB — this is
> his work, split 4 ways), Sheya & Shravani (frontend), Arushi & Pramati (ML/quantum modelling).
>
> Every module below is built against a **fixed contract** (schemas + function signatures), not
> against another agent's actual code — so none of you waits on anyone else. Where your module
> calls into someone else's, you're given a small stub matching their exact signature to build
> and test against; at stitch time the stub gets deleted and the real file drops into the same
> path. If you followed the signatures exactly, no code you write should need to change.


## Repository & Your Branch

- Repo: `https://github.com/ankitghosh1809/SIH_backend.git`
- Your branch: **`agent-b-ml`**
- Your local folder: **`~/Downloads/SIH_backend-B-ml`** (already cloned and checked out to your branch if
  `setup_agents.sh` has been run — if not, ask Ankit to run it first)
- Work in this folder only. Commit as you go with clear messages; push to `origin/agent-b-ml`
  whenever you hit a checkpoint below, and definitely once "Definition of done" is fully checked.


## Repo Layout — who owns what

```
backend/
├── app/
│   ├── main.py                 <- Agent D
│   ├── config.py                <- Agent D
│   ├── schemas.py                <- SHARED CONTRACT below — create verbatim, byte-identical everywhere
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py           <- Agent A
│   │   ├── models.py              <- Agent A
│   │   └── crud.py                 <- Agent A
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── inference.py            <- Agent B
│   │   ├── storage.py               <- Agent B
│   │   └── model_backend.py          <- Agent B (stub content now; Arushi & Pramati's real model
│   │                                    replaces the BODY of this file later — path never changes)
│   └── api/
│       ├── __init__.py
│       ├── scans.py                  <- Agent C
│       └── metrics.py                 <- Agent D
├── tests/                               <- each agent adds their own test file here
├── requirements.txt                      <- merged at stitch time (see bottom of this file)
└── Dockerfile                             <- Agent D
```

No two agents write to the same file — merging the 4 branches back together should be conflict-free
by construction. If git ever reports a conflict, it means the ownership map above was violated.

## Running 4 agents at once

Give each agent its own git branch or worktree off the same base commit
(e.g. `git worktree add ../backend-agent-a agent-a-db`) so you're not fighting over one working
directory. Because ownership never overlaps, merging all 4 branches into `main` should be a clean,
automatic merge.

## Shared Contract — `app/schemas.py`

```python
# app/schemas.py — SHARED CONTRACT. Every agent creates this file identically.
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class PredictionField(BaseModel):
    positive: bool
    probability: float

class Prediction(BaseModel):
    diabetic_retinopathy: PredictionField
    cataract: PredictionField

class ScanResponse(BaseModel):
    scan_id: str
    created_at: datetime
    prediction: Prediction
    risk_level: str          # "low" | "medium" | "high"
    heatmap_url: str
    model_version: str

class ScanListItem(BaseModel):
    scan_id: str
    created_at: datetime
    risk_level: str
    thumbnail_url: str

class ModelMetrics(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1: float
    auc_roc: float

class MetricsResponse(BaseModel):
    classical: Optional[ModelMetrics] = None
    hybrid_quantum: Optional[ModelMetrics] = None
    evaluated_on: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
```

## Database schema (reference — Agent A implements this; everyone else just needs to know the shape)

```
scans
  id                    VARCHAR(36) PRIMARY KEY   -- uuid4, stored as string for SQLite/Postgres portability
  patient_name          VARCHAR(120) NULL
  image_path            TEXT NOT NULL
  heatmap_path           TEXT NULL
  dr_probability          FLOAT
  dr_positive              BOOLEAN
  cataract_probability      FLOAT
  cataract_positive          BOOLEAN
  risk_level                  VARCHAR(10)     -- low | medium | high
  model_version                VARCHAR(40)
  inference_ms                  INTEGER
  created_at                     TIMESTAMP DEFAULT now()

model_metrics
  id                SERIAL PRIMARY KEY
  model_type         VARCHAR(20)   -- 'classical' | 'hybrid_quantum'
  accuracy            FLOAT
  precision_score      FLOAT
  recall               FLOAT
  f1_score             FLOAT
  auc_roc              FLOAT
  test_set_size         INTEGER
  evaluated_at          TIMESTAMP DEFAULT now()
```


## API contract (reference — the full system's 6 endpoints; you may only be building one or two of these)

| Method & Path | Owner | Purpose |
|---|---|---|
| `POST /api/v1/scans` | Agent C | Upload a fundus image, run inference, return `ScanResponse` |
| `GET /api/v1/scans/{scan_id}` | Agent C | Retrieve one stored scan |
| `GET /api/v1/scans` | Agent C | List past scans (`list[ScanListItem]`) |
| `GET /api/v1/scans/{scan_id}/heatmap` | Agent C | Grad-CAM heatmap image (PNG) |
| `GET /api/v1/metrics` | Agent D | `MetricsResponse` — classical vs hybrid-quantum |
| `GET /api/v1/health` | Agent D | `{"status": "ok"}` |


## Your Job — Agent B


**You own:** `app/ml/inference.py`, `app/ml/storage.py`, `app/ml/model_backend.py`.

**No dependency on the DB or API code.** You're building the adapter between "whatever Arushi &
Pramati's real model looks like" and "what the API layer needs" — bytes in, bytes out, with a
risk-level judgement call in between. Their real `inference.py` (see their ML & Quantum Modelling
brief) exposes `load_model(checkpoint_path)` and `predict(model, image: PIL.Image) -> dict` with
`dr_probability`, `cataract_probability`, `heatmap` (a PIL Image) — `model_backend.py` below
already matches that exact shape, so when their real model is ready, only the **body** of
`model_backend.py` changes, not its interface.

### Task 1 — `app/ml/model_backend.py` (stub content now, real content later — same file, same path)
```python
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
```

### Task 2 — `app/ml/inference.py`
The byte-oriented adapter the API layer actually calls:
```python
def load_model():
    """Called once at FastAPI startup."""
    ...   # calls model_backend.load_model(), passing MODEL_PATH from config once that exists

def run_inference(model, image_bytes: bytes) -> dict:
    """bytes in -> PIL -> model_backend.predict() -> bytes back out.
    Returns {"dr_probability": float, "cataract_probability": float, "heatmap_bytes": bytes}"""
    ...

def compute_risk_level(dr_probability: float, cataract_probability: float) -> str:
    """low | medium | high — placeholder thresholds (0.4 / 0.7 on the max of the two
    probabilities), flag this as worth revisiting once real model calibration is known."""
    ...
```

### Task 3 — `app/ml/storage.py`
```python
def save_upload(scan_id: str, image_bytes: bytes) -> str: ...    # saves to disk, returns the path
def save_heatmap(scan_id: str, heatmap_bytes: bytes) -> str: ...  # saves to disk, returns the path
def read_heatmap(scan_id: str) -> bytes | None: ...                # reads it back for serving
```
Local disk under a `storage/` folder is fine for the hackathon — no need for S3/Cloudinary.

### Self-test
`tests/test_inference.py` — `load_model()`, `run_inference()` on a small in-memory dummy image
(e.g. a 10×10 solid-colour PNG built with Pillow), assert the returned dict has all 3 keys with
the right types, then `save_heatmap`/`read_heatmap` round-trip.

### Definition of done
- [ ] `model_backend.py` matches the exact interface Arushi & Pramati already committed to
- [ ] `run_inference()` never crashes on a valid image and always returns all 3 keys
- [ ] `compute_risk_level()` covers all 3 bands
- [ ] `tests/test_inference.py` passes


## Dependencies you're adding to `requirements.txt`

```
Pillow
numpy
# once the real model swaps in, Arushi & Pramati's own deps apply here too:
# torch, torchvision, pennylane, qiskit-machine-learning, pytorch-grad-cam
```


## Stitching Plan (run this after all 4 agents finish)

1. Merge all 4 branches into one `backend/` tree — file ownership is disjoint, so this should be
   conflict-free.
2. Delete every file marked **STUB — DELETE AT STITCH TIME** below and confirm the real file from
   the owning agent sits at the same path with the same function signatures. `scans.py`,
   `metrics.py`, and `main.py` should need **zero code changes** — only file swaps.
3. Merge `requirements.txt` — union of the dependency lists at the bottom of all 4 work orders,
   de-duplicated.
4. Set real environment variables (`DATABASE_URL` from Neon) and, once Arushi & Pramati hand off
   their trained model, replace the body of `app/ml/model_backend.py` with their real
   `load_model()` / `predict()` — that file's path never changes, so nothing importing it needs
   to change either.
5. Run `uvicorn app.main:app --reload`, then walk the flow in order:
   `GET /api/v1/health` → `POST` an image to `/api/v1/scans` → `GET /api/v1/scans/{id}` →
   `GET /api/v1/scans` → `GET /api/v1/scans/{id}/heatmap` → `GET /api/v1/metrics`.
   All 6 responding correctly means the stitch is done.
