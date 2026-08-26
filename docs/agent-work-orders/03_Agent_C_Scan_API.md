# Backend Work Order — Agent C: Scan API Routes

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
- Your branch: **`agent-c-api`**
- Your local folder: **`~/Downloads/SIH_backend-C-api`** (already cloned and checked out to your branch if
  `setup_agents.sh` has been run — if not, ask Ankit to run it first)
- Work in this folder only. Commit as you go with clear messages; push to `origin/agent-c-api`
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


## Your Job — Agent C


**You own:** `app/api/scans.py` — the main orchestration route. It calls Agent A's `db.crud`
functions and Agent B's `ml.inference` / `ml.storage` functions. Since those may not exist yet in
your branch, build the 4 stub files below **first** (exact code given — just paste them in),
write `scans.py` importing from the real final paths (`app.db.crud`, `app.db.database`,
`app.ml.inference`, `app.ml.storage`) so it needs **zero changes later**, test everything against
your stubs, then delete the stubs at stitch time.

### Stub files to create for your own standalone dev — STUB, DELETE AT STITCH TIME

`app/db/database.py`:
```python
_FAKE_STORE = {"scans": {}, "metrics": []}
def get_session():
    yield _FAKE_STORE
def init_db():
    pass
```

`app/db/crud.py`:
```python
from types import SimpleNamespace
from datetime import datetime

def create_scan(db, *, scan_id, patient_name=None, image_path, heatmap_path=None, dr_probability,
                 dr_positive, cataract_probability, cataract_positive, risk_level,
                 model_version, inference_ms):
    row = SimpleNamespace(id=scan_id, patient_name=patient_name, image_path=image_path,
                           heatmap_path=heatmap_path, dr_probability=dr_probability,
                           dr_positive=dr_positive, cataract_probability=cataract_probability,
                           cataract_positive=cataract_positive, risk_level=risk_level,
                           model_version=model_version, inference_ms=inference_ms,
                           created_at=datetime.utcnow())
    db["scans"][row.id] = row
    return row

def get_scan(db, scan_id):
    return db["scans"].get(scan_id)

def list_scans(db, limit=20):
    return list(db["scans"].values())[:limit]

def record_metrics(db, **kwargs):
    db["metrics"].append(SimpleNamespace(**kwargs))

def get_latest_metrics(db):
    out = {"classical": None, "hybrid_quantum": None}
    for m in db["metrics"]:
        out[m.model_type] = m
    return out
```

`app/ml/inference.py`:
```python
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
```

`app/ml/storage.py`:
```python
_FAKE_FILES = {}
def save_upload(scan_id, image_bytes):
    _FAKE_FILES[f"upload:{scan_id}"] = image_bytes
    return f"stub/uploads/{scan_id}.png"
def save_heatmap(scan_id, heatmap_bytes):
    _FAKE_FILES[f"heatmap:{scan_id}"] = heatmap_bytes
    return f"stub/heatmaps/{scan_id}.png"
def read_heatmap(scan_id):
    return _FAKE_FILES.get(f"heatmap:{scan_id}")
```

### Task — `app/api/scans.py`
Implement, as a FastAPI `APIRouter`:

- **`POST /api/v1/scans`** — accept `multipart/form-data` (`file`, optional `patient_name`),
  generate `scan_id = str(uuid.uuid4())` **once** and reuse it for everything below (the image
  file, the heatmap file, and the DB row all need to agree on the same id), read the upload
  bytes, time the call, call `ml.inference.run_inference()`, derive
  `dr_positive`/`cataract_positive` as `probability > 0.5`, call
  `ml.inference.compute_risk_level()`, save the original image and the heatmap via `ml.storage`
  (keyed on `scan_id`), persist via `db.crud.create_scan(db, scan_id=scan_id, ...)`, return
  `schemas.ScanResponse` (201). Return 422 on an unreadable/invalid image.
- **`GET /api/v1/scans/{scan_id}`** — `db.crud.get_scan()`, 404 if missing, else `ScanResponse`.
- **`GET /api/v1/scans?limit=20`** — `db.crud.list_scans()`, returns `list[schemas.ScanListItem]`.
- **`GET /api/v1/scans/{scan_id}/heatmap`** — `ml.storage.read_heatmap()`, 404 if missing, else a
  `Response(content=..., media_type="image/png")`.

### Self-test
`tests/test_scans_api.py` using FastAPI's `TestClient` against your stubs: `POST` a small dummy
PNG, assert `201` and the response matches `ScanResponse`'s shape, `GET` it back by id, `GET` the
heatmap bytes back, `GET` the list and confirm the scan appears.

### Definition of done
- [ ] All 4 routes implemented and returning the exact shapes in `schemas.py`
- [ ] 404s handled for a missing scan / missing heatmap
- [ ] `tests/test_scans_api.py` passes end-to-end against the stubs above


## Dependencies you're adding to `requirements.txt`

```
fastapi
python-multipart   # required for file upload parsing
httpx   # test client
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
