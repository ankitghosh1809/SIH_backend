# SIH_backend

Backend & database for **SIH26139 — Hybrid Quantum Machine Learning Platform for Early Disease
Detection**, built for Smart India Hackathon 2026 (sponsor: **Egreen Quanta**, a real
quantum-computing R&D company). Applied to diabetic eye disease screening — detecting **diabetic
retinopathy** and **cataract** (diabetes accelerates cataract formation, so the two are screened
together) from retinal fundus photographs.

**This is a screening / decision-support aid, not a diagnostic replacement.** That framing should
hold everywhere this API's output reaches a human — reports, referral letters, explanations.

Verified against the real repo at commit `7f1cd06` (2026-09-02): **77 tests passing**, app boots
clean. Where this document says something works, it was actually run, not assumed.

## Team

| Person | Role |
|---|---|
| Ankit | Backend & database — this repo |
| Sheya & Shravani | Frontend & UI — separate repo |
| Arushi & Pramati | ML & quantum modelling — own the real hybrid-quantum model; this repo currently runs it as a placeholder stub with the exact interface their trained model drops into |

## Tech Stack

- **Language/runtime:** Python 3.12 (the Dockerfile hasn't caught up to this yet — see [Known Issues](#known-issues))
- **API framework:** FastAPI + Uvicorn
- **Data layer:** SQLAlchemy 2.x (classic `Column()` declarative mapping throughout), Pydantic v2 for every request/response contract
- **Database:** SQLite locally, zero config (`local_dev.db`) · PostgreSQL via [Neon](https://neon.tech) in production (`DATABASE_URL`)
- **Auth:** JWT (PyJWT, HS256) + `passlib[bcrypt]` password hashing, role-based (`admin` / `doctor` / `camp_staff`)
- **Rate limiting:** `slowapi`, keyed on client IP
- **PDF generation:** `reportlab` — clinical scan reports and referral letters
- **Image handling:** Pillow
- **ML integration:** PennyLane + PyTorch planned once the real hybrid-quantum model lands. **Not in `requirements.txt` yet** — the current model is a dependency-free placeholder stub
- **Deploy target:** Render or Railway — **not Vercel**, since PyTorch/PennyLane/Qiskit will exceed Vercel's serverless size and runtime limits once the real model is wired in
- **CI:** GitHub Actions (`.github/workflows/ci.yml`) — full test suite + an app-boot check on every push/PR to `main`

Two library choices worth knowing the reasoning behind, since both are pinned/chosen for
non-obvious reasons:
- **PyJWT, not `python-jose`**, for JWT — `python-jose` has been unmaintained since 2021 and has
  a live CVE (CVE-2024-33663). FastAPI's own docs now point to PyJWT instead.
- **`bcrypt==4.0.1`, pinned** — `passlib` 1.7.4 (its last release) can't read bcrypt's version
  string on bcrypt ≥ 4.1, and bcrypt 5.x doesn't just warn, it breaks `passlib`'s
  `hash()`/`verify()` outright. 4.0.1 is the newest version that still works. Bump only alongside
  a `passlib` fix.

## Architecture

```
Fundus image → Frontend (React, separate repo) → This API (FastAPI)
    → rate limit + auth/role check (JWT) where required
    → ML inference (stub today; real hybrid-quantum model pending handoff)
    → PostgreSQL (Neon): scans, patients, referrals, reviews, users, audit log, notifications
    → Response: prediction + uncertainty + risk level + heatmap URL
    → downstream: referral workflow, doctor review, audit trail, notifications
```

A single scan, end to end:
1. `POST /api/v1/scans` (rate-limited) — optionally linked to a `patient_id`, image checked for valid magic bytes
2. Run through `ml.inference.run_inference()` against one cached model instance (loaded exactly once for the process, however many requests come in)
3. Prediction, per-condition uncertainty, and risk level computed and persisted
4. `risk_level == "high"` → visible via `GET /scans/{id}/referral-suggestion`, can become a tracked referral through to a letter PDF
5. A doctor can review the scan and optionally override its risk level — role-gated
6. Every request lands in the audit log; high-risk detections and completed reviews surface through `GET /notifications`

## Database Schema

Eight tables, verified against the real ORM files. `patients`, `referrals`, `users`,
`audit_logs`, and `notifications` all reuse the same declarative `Base` from `app/db/models.py`
rather than each declaring their own — the established pattern in this codebase for adding a
table without touching `models.py` itself (only `patients` needed one small change there: a
nullable FK on `scans`).

```sql
-- scans
id                    VARCHAR(36) PRIMARY KEY        -- uuid4 as text
patient_name          VARCHAR(120) NULL              -- free-text, predates the patient registry
patient_id            VARCHAR(36) REFERENCES patients(id) NULL   -- optional, backward-compatible
image_path            TEXT NOT NULL
heatmap_path          TEXT NULL
dr_probability        FLOAT
dr_positive           BOOLEAN
cataract_probability  FLOAT
cataract_positive     BOOLEAN
risk_level            VARCHAR(10)                    -- low | medium | high
model_version         VARCHAR(40)
inference_ms          INTEGER
created_at            TIMESTAMP DEFAULT now()

-- model_metrics
id                SERIAL PRIMARY KEY
model_type        VARCHAR(20)                        -- classical | hybrid_quantum
accuracy          FLOAT
precision_score   FLOAT
recall            FLOAT
f1_score          FLOAT
auc_roc           FLOAT
test_set_size     INTEGER
evaluated_at      TIMESTAMP DEFAULT now()

-- reviews
id                    VARCHAR(36) PRIMARY KEY
scan_id               VARCHAR(36) REFERENCES scans(id)
reviewer_note         TEXT NULL
override_risk_level   VARCHAR(10) NULL                -- low | medium | high | NULL
reviewed_at           TIMESTAMP DEFAULT now()

-- users
id                VARCHAR(36) PRIMARY KEY
username          VARCHAR(60) UNIQUE NOT NULL
hashed_password   VARCHAR(255) NOT NULL
role              VARCHAR(20) NOT NULL               -- admin | doctor | camp_staff
full_name         VARCHAR(120) NULL
is_active         BOOLEAN DEFAULT TRUE
created_at        TIMESTAMP DEFAULT now()

-- patients
id              VARCHAR(36) PRIMARY KEY
full_name       VARCHAR(120) NOT NULL
age             INTEGER NULL
gender          VARCHAR(20) NULL
phone           VARCHAR(20) NULL
diabetes_type   VARCHAR(20) NULL                     -- freeform, never hard-rejected
created_at      TIMESTAMP DEFAULT now()

-- referrals
id                 VARCHAR(36) PRIMARY KEY
scan_id            VARCHAR(36) REFERENCES scans(id) NOT NULL
facility_name      VARCHAR(150) NOT NULL
facility_contact   VARCHAR(120) NULL
status             VARCHAR(20) DEFAULT 'pending'      -- pending | contacted | completed | declined
notes              TEXT NULL
created_at         TIMESTAMP DEFAULT now()
updated_at         TIMESTAMP DEFAULT now()

-- audit_logs
id             VARCHAR(36) PRIMARY KEY
actor          VARCHAR(120) NULL                     -- "authenticated" | "anonymous" (coarse, see below)
action         VARCHAR(80) NOT NULL                  -- e.g. "POST /api/v1/scans"
resource_type  VARCHAR(40) NULL                       -- reserved, unused today
resource_id    VARCHAR(36) NULL                       -- reserved, unused today
ip_address     VARCHAR(45) NULL
created_at     TIMESTAMP DEFAULT now()

-- notifications
id           VARCHAR(36) PRIMARY KEY
event_type   VARCHAR(60) NOT NULL                    -- high_risk_detected | review_completed
scan_id      VARCHAR(36) NULL                        -- no FK constraint on purpose, see app/db/notification_models.py
channel      VARCHAR(20) DEFAULT 'in_app'             -- email/SMS delivery not built yet
message      TEXT NOT NULL
is_read      BOOLEAN DEFAULT FALSE
created_at   TIMESTAMP DEFAULT now()
```

**Local dev note:** SQLite's `create_all()` only creates tables that don't already exist — it
won't retroactively add the `patient_id` column to a `scans` table left over from before the
patient registry existed. If local scan creation starts failing after a pull, delete
`local_dev.db` and let `init_db()` recreate it fresh.

## API Reference

30 endpoints across 12 route groups. "Auth" column: **none** = open, a role name = requires a
valid JWT with that role (or higher — `admin` can do anything `doctor` can on gated endpoints
that list both).

### Core
| Method & Path | Auth | Notes |
|---|---|---|
| `GET /api/v1/health` | none | `{"status": "ok"}` |
| `GET /api/v1/metrics` | none | Latest `classical` vs `hybrid_quantum` model metrics |

### Scans
| Method & Path | Auth | Notes |
|---|---|---|
| `POST /api/v1/scans` | none, rate-limited | multipart: `file`, optional `patient_name`, optional `patient_id` → 201 `ScanResponse` |
| `GET /api/v1/scans/{id}` | none | `ScanResponse` or 404 |
| `GET /api/v1/scans?limit=20` | none | `list[ScanListItem]` |
| `GET /api/v1/scans/{id}/heatmap` | none | PNG or 404 |
| `GET /api/v1/scans/{id}/report` | none | PDF clinical report |

### Batch
| Method & Path | Auth | Notes |
|---|---|---|
| `POST /api/v1/batch` | none, rate-limited | multipart: `files` (max 50) → per-file results + summary; one bad file doesn't abort the rest |

### Doctor Review
| Method & Path | Auth | Notes |
|---|---|---|
| `POST /api/v1/scans/{id}/review` | `doctor` or `admin` | note + optional risk override → 201 |
| `GET /api/v1/scans/{id}/reviews` | none | `list[ReviewResponse]`, empty list if none yet |

### Admin
| Method & Path | Auth | Notes |
|---|---|---|
| `GET /api/v1/admin/stats` | `admin` | Totals, breakdowns by risk/model, avg inference time |

### Auth
| Method & Path | Auth | Notes |
|---|---|---|
| `POST /api/v1/auth/register` | none | Open to any role for demo purposes — see `app/api/auth.py`'s docstring on restricting this before real deployment |
| `POST /api/v1/auth/login` | none | OAuth2 password form (works with `/docs`' built-in Authorize button) → JWT |
| `GET /api/v1/auth/me` | any valid token | Current user |

### Patients
| Method & Path | Auth | Notes |
|---|---|---|
| `POST /api/v1/patients` | none | Create a patient |
| `GET /api/v1/patients?search=` | none | Search by name substring, or most recent |
| `GET /api/v1/patients/{id}` | none | Patient detail |
| `GET /api/v1/patients/{id}/scans` | none | Full scan history, newest first |
| `GET /api/v1/patients/{id}/trend` | none | Risk/probability time series, oldest first (chart-ready) |

### Referrals
| Method & Path | Auth | Notes |
|---|---|---|
| `GET /api/v1/facilities` | none | Static directory of referral facilities |
| `GET /api/v1/scans/{id}/referral-suggestion` | none | `{suggested, reason}` — advisory, `true` when `risk_level == "high"` |
| `POST /api/v1/scans/{id}/referral` | none | Create a referral (any risk level) |
| `GET /api/v1/referrals?status=` | none | List, optionally filtered |
| `GET /api/v1/referrals/{id}` | none | Detail |
| `PATCH /api/v1/referrals/{id}` | none | Update status/notes |
| `GET /api/v1/referrals/{id}/letter` | none | Referral letter PDF |

### Explainability
| Method & Path | Auth | Notes |
|---|---|---|
| `GET /api/v1/scans/{id}/explain` | none | Per-condition uncertainty + explanation text (honestly generic until the real model's Grad-CAM output lands — see [Known Issues](#known-issues)) |

### Audit
| Method & Path | Auth | Notes |
|---|---|---|
| `GET /api/v1/audit/logs?action=&limit=50` | none — flagged `# TODO` to protect | Every request, best-effort logged |

### Notifications
| Method & Path | Auth | Notes |
|---|---|---|
| `GET /api/v1/notifications?unread_only=` | none | Pull-based — regenerated from current scan/review data on every call, not from a write-time hook |
| `PATCH /api/v1/notifications/{id}/read` | none | Mark read |

## Auth & Roles

Three roles: **`admin`** (everything), **`doctor`** (can review scans), **`camp_staff`** (base
level — everything that doesn't need a role). Registration (`POST /auth/register`) is
deliberately open to any role for the hackathon build; lock this down (e.g. admin-invited-only
for privileged roles) before any real deployment. Tokens are JWT, HS256, 60-minute expiry by
default (`ACCESS_TOKEN_EXPIRE_MINUTES`). `SECRET_KEY` has a dev-only default that a real
deployment **must** override.

## Getting Started

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

No environment variables required for local dev. Everything has a working default:

| Variable | Local default |
|---|---|
| `DATABASE_URL` | `sqlite:///./local_dev.db` |
| `MODEL_PATH` | `./models/model_weights.pt` |
| `MODEL_VERSION` | `stub-v0` |
| `RISK_THRESHOLD_MEDIUM` / `RISK_THRESHOLD_HIGH` | `0.4` / `0.7` |
| `ALLOWED_ORIGINS` | `http://localhost:3000` |
| `SECRET_KEY` | dev-only insecure default — **override in production** |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` |
| `UPLOAD_RATE_LIMIT` | `25/minute` |

Visit `http://localhost:8000/docs` for interactive Swagger UI — includes a working "Authorize"
button for the JWT flow.

## Testing

```bash
pip install pytest && pytest tests/ -q
```

**77 tests, all passing** (verified 2026-09-02 against `main` at `7f1cd06`). Breakdown: referrals
(12), auth (10), patients (9), scans (7), review (6), notifications (6), audit (5), ML
cleanup (4), inference (3), explainability (3), batch (3), app shell (3), admin (3), reports (2),
db (1). `.github/workflows/ci.yml` runs this plus an app-boot check on every push/PR to `main`.

## Deployment

Render or Railway (`Dockerfile` provided), Postgres via Neon. Set `DATABASE_URL` to the real Neon
connection string, `ALLOWED_ORIGINS` to the deployed frontend's URL, `SECRET_KEY` to a real
secret, and `MODEL_PATH` once a real model checkpoint exists.

## Development Workflow

Built in three rounds of parallel AI coding agents, each on its own branch, each owning a
disjoint set of files so branches merge back with minimal conflict. The one recurring, expected
exception: every agent adds a couple of lines to `app/main.py` to register its router — always a
trivial, easy-to-resolve conflict, never a logic one.

- **Round 1** (`agent-a-db`, `agent-b-ml`, `agent-c-api`, `agent-d-app`) — database layer, ML
  integration wrapper, scan API, app shell + deploy config. Work orders: `docs/agent-work-orders/`.
- **Round 2** (`agent-e-reports`, `agent-f-batch`, `agent-g-review`, `agent-h-observability`) —
  PDF reports, batch screening, doctor review, admin stats + CI.
- **Round 3** (`agent-m-auth-security`, `agent-n-patient-registry`, `agent-o-referral-workflow`,
  `agent-p-model-confidence`, `agent-q-audit-notifications`) — everything described in this
  document beyond the original scan/batch/report/review/admin core.

`ASSUMPTIONS_AND_TODO.md` at the repo root is worth a read: Agent O's referral workflow was built
without any access to the real repo or a way to run tests, so it made a few explicit, documented
guesses (import names, `Scan` field names). They turned out correct — 12 passing tests confirm
it — but it's a good illustration of why giving an agent real repo + terminal access (rather than
just the work order text) produces more reliable results, when that's an option.

`docs/COMPLIANCE_NOTES.md` covers where this system currently stands against India's DPDP Act
2023 — a gap analysis, not a compliance claim.

## Known Issues

- **Dockerfile still pins `python:3.11-slim`.** PennyLane (needed the moment the real model
  lands) requires Python 3.12+. CI already runs on 3.12, which means CI passing currently masks
  this — the mismatch would only surface at actual Docker build time. One-line fix:
  `FROM python:3.11-slim` → `FROM python:3.12-slim`.
- **`app/ml/model_backend.py` is still a stub** — random probabilities, a flat placeholder
  heatmap with zero real spatial data. Swapping in the real model is a body-only change to this
  one file by design; nothing importing it should need to change.
- **`/explain`'s explanation text is deliberately generic** until the real model's Grad-CAM output
  exists — inventing specific-sounding clinical claims against a flat placeholder heatmap would be
  fabrication, not explanation.
- **`GET /api/v1/audit/logs` has no auth** — flagged with its own `# TODO`, same open-with-a-flag
  pattern `admin.py`'s stats endpoint used before Round 3 closed that one.
- **Referral/notification email or SMS delivery isn't built** — `notifications.channel` defaults
  to `"in_app"` and stays there; there's a documented hook point for real delivery later.
