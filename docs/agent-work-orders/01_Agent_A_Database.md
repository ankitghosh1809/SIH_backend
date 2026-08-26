# Backend Work Order — Agent A: Database & Data Access Layer

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
- Your branch: **`agent-a-db`**
- Your local folder: **`~/Downloads/SIH_backend-A-database`** (already cloned and checked out to your branch if
  `setup_agents.sh` has been run — if not, ask Ankit to run it first)
- Work in this folder only. Commit as you go with clear messages; push to `origin/agent-a-db`
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


## Your Job — Agent A


**You own:** `app/db/database.py`, `app/db/models.py`, `app/db/crud.py`, and `app/schemas.py`
(shared contract, create it verbatim from above).

**No dependency on any other agent.** Build and test standalone against local SQLite (fast) or a
real Postgres if you want to test closer to prod — the real deploy target is Neon Postgres via a
`DATABASE_URL` env var, but SQLite behaves identically for everything this module does.

### Task 1 — `app/db/models.py`
SQLAlchemy ORM models for the two tables in the schema above. Use `String(36)` for the scan `id`
(uuid4 stored as text) rather than a Postgres-specific UUID type, so the same models work against
SQLite in tests and Postgres in prod without changes.

### Task 2 — `app/db/database.py`
Engine + session setup, reading `DATABASE_URL` from the environment (default to
`sqlite:///./dev.db` if unset, so it runs with zero config out of the box). Expose:
```python
def init_db(): ...          # creates tables if they don't exist
def get_session(): ...      # generator — yields a session, closes it after (FastAPI Depends-style)
```

### Task 3 — `app/db/crud.py`
Implement these exact functions — **signatures are fixed**, Agent C and Agent D import and call
them by name. Note `create_scan` takes `scan_id` from the **caller** rather than generating its
own — the route generates one id and reuses it for the image file, the heatmap file, and the DB
row, so all three agree:
```python
def create_scan(db, *, scan_id: str, patient_name=None, image_path, heatmap_path=None,
                 dr_probability, dr_positive, cataract_probability, cataract_positive,
                 risk_level, model_version, inference_ms): ...   # returns the created Scan row

def get_scan(db, scan_id: str): ...                          # returns a Scan row or None

def list_scans(db, limit: int = 20): ...                      # returns a list of Scan rows, newest first

def record_metrics(db, *, model_type: str, accuracy, precision, recall, f1, auc_roc,
                    test_set_size): ...                        # persists one evaluation row

def get_latest_metrics(db) -> dict: ...
    # returns {"classical": <row-or-None>, "hybrid_quantum": <row-or-None>} — the latest row per model_type
```

### Self-test
Write `tests/test_db.py`: call `init_db()` against a throwaway SQLite file, `create_scan(db,
scan_id="test-1", ...)`, `get_scan(db, "test-1")` and confirm it round-trips (including that
`row.id == "test-1"`), `list_scans(...)`, `record_metrics(...)` once for `"classical"` and once
for `"hybrid_quantum"`, then `get_latest_metrics(...)` and confirm both keys are populated.

### Definition of done
- [ ] `init_db()` creates both tables with no errors against a fresh SQLite file
- [ ] All 5 crud functions implemented with the exact signatures above
- [ ] `tests/test_db.py` passes


## Dependencies you're adding to `requirements.txt`

```
sqlalchemy>=2.0
psycopg2-binary   # Postgres driver for prod (Neon)
pytest
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
