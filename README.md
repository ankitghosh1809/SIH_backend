# SIH_backend

Backend & database for SIH26139 — Hybrid Quantum Machine Learning Platform for Early Disease
Detection (Egreen Quanta), applied to diabetic retinopathy + cataract screening from retinal
fundus images. Full team: Ankit (backend & DB), Sheya & Shravani (frontend & UI), Arushi & Pramati
(ML & quantum modelling).

This backend is being built by **4 coding agents working in parallel**, each on their own branch,
each touching a disjoint set of files so the branches merge back with no conflicts.

| Branch | Owns | Work order |
|---|---|---|
| `agent-a-db` | `app/db/` | [`docs/agent-work-orders/01_Agent_A_Database.md`](docs/agent-work-orders/01_Agent_A_Database.md) |
| `agent-b-ml` | `app/ml/` | [`docs/agent-work-orders/02_Agent_B_ML_Integration.md`](docs/agent-work-orders/02_Agent_B_ML_Integration.md) |
| `agent-c-api` | `app/api/scans.py` | [`docs/agent-work-orders/03_Agent_C_Scan_API.md`](docs/agent-work-orders/03_Agent_C_Scan_API.md) |
| `agent-d-app` | `app/main.py`, `app/config.py`, `app/api/metrics.py`, deploy config | [`docs/agent-work-orders/04_Agent_D_AppShell_Deploy.md`](docs/agent-work-orders/04_Agent_D_AppShell_Deploy.md) |

`app/schemas.py` is the shared contract every branch builds against — already in place on `main`.
Every other `.py` file under `app/` is a placeholder pointing back to whichever work order fills
it in.

## Stitching

Once all 4 branches are done: merge each into `main` (should be conflict-free by construction —
ownership never overlaps), delete anything marked *STUB — DELETE AT STITCH TIME* in the work
orders, merge `requirements.txt`, and run through the Stitching Plan at the bottom of any work
order file.
