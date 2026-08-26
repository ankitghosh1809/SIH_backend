# Backend Work Order — Agent D: App Shell, Metrics & Deployment

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
- Your branch: **`agent-d-app`**
- Your local folder: **`~/Downloads/SIH_backend-D-appshell`** (already cloned and checked out to your branch if
  `setup_agents.sh` has been run — if not, ask Ankit to run it first)
- Work in this folder only. Commit as you go with clear messages; push to `origin/agent-d-app`
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


## Your Job — Agent D


**You own:** `app/main.py`, `app/config.py`, `app/api/metrics.py`, `Dockerfile` (+ a
`render.yaml` or `Procfile`), and the final merged `requirements.txt`.

### Stub files to create for your own standalone dev — STUB, DELETE AT STITCH TIME

`app/db/database.py` and `app/db/crud.py`: identical to Agent C's stubs — copy them verbatim (see
Agent C's work order, or just reuse the file if you're in the same repo). You only need
`get_latest_metrics()` from these for the metrics endpoint, but the full stub is harmless to keep.

`app/ml/inference.py` (stub — only `load_model()` matters for you, to prove startup wiring works):
```python
def load_model():
    return {"stub": True}
```

`app/api/scans.py` (stub router — proves mounting + routing works before Agent C's real one lands):
```python
from fastapi import APIRouter
router = APIRouter()

@router.post("/api/v1/scans")
def _stub_create_scan():
    return {"stub": "replace with Agent C's real app/api/scans.py at stitch time"}

@router.get("/api/v1/scans/{scan_id}")
def _stub_get_scan(scan_id: str):
    return {"stub": True, "scan_id": scan_id}

@router.get("/api/v1/scans")
def _stub_list_scans():
    return []

@router.get("/api/v1/scans/{scan_id}/heatmap")
def _stub_heatmap(scan_id: str):
    return {"stub": True}
```

### Task 1 — `app/config.py`
Read from environment (with sane local defaults): `DATABASE_URL`, `MODEL_PATH`,
`ALLOWED_ORIGINS` (comma-separated list — the Vercel frontend URL(s) for CORS).

### Task 2 — `app/api/metrics.py`
```python
# GET /api/v1/metrics  -> schemas.MetricsResponse, built from db.crud.get_latest_metrics()
# GET /api/v1/health    -> schemas.HealthResponse, always {"status": "ok"}
```

### Task 3 — `app/main.py`
Create the `FastAPI()` app; add CORS middleware using `config.ALLOWED_ORIGINS`; on startup, call
`db.database.init_db()` and `ml.inference.load_model()` (store the loaded model on `app.state` so
`scans.py` can reach it); `include_router()` for both `api.scans.router` and `api.metrics.router`.

### Task 4 — Deployment
Per the deployment note in Ankit's original Backend & Database brief: **not Vercel** — PyTorch /
PennyLane / Qiskit dependencies exceed its serverless limits. Write a `Dockerfile` (or a
`render.yaml` / `Procfile`) targeting **Render or Railway**, reading `DATABASE_URL` and
`MODEL_PATH` from the platform's env var settings.

### Self-test
Run the app standalone against your stubs: `uvicorn app.main:app --reload`, hit `/api/v1/health`
and `/api/v1/metrics` (should return `null`s gracefully with no data yet, not crash), confirm CORS
headers appear on a cross-origin request, confirm the stub scans routes are reachable through the
mounted router.

### Definition of done
- [ ] App boots cleanly with `uvicorn app.main:app`
- [ ] `/api/v1/health` and `/api/v1/metrics` both work against the stub DB
- [ ] CORS configured and verified
- [ ] Dockerfile / render config builds and runs locally (`docker build && docker run`, or
      platform-equivalent)


## Dependencies you're adding to `requirements.txt`

```
fastapi
uvicorn[standard]
python-dotenv
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
