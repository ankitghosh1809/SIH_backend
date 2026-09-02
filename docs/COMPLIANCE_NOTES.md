# Compliance Notes — DPDP Act 2023 Gap Analysis

A short, honest look at where this system stands against India's Digital Personal Data
Protection Act 2023 (DPDP Act) expectations. **This is a gap list for a hackathon build, not a
compliance certification or legal opinion.** Full DPDP compliance is genuinely out of scope here
— nothing below should be read as a claim that this system is DPDP-compliant today.

## What personal / health data this system stores today

- Patient identifiers, via the patient registry (`app/db/patient_models.py`, linked from
  `Scan.patient_id`).
- Retinal fundus scan images and the heatmaps generated from them.
- Diagnostic probabilities and risk levels per scan (diabetic retinopathy, cataract).
- Doctor review notes and risk-level overrides (`app/db/review_models.py`).
- Referral details, where the referral workflow has been used.
- Coarse per-request audit metadata (this task): actor (authenticated/anonymous), action, IP
  address, timestamp. This doesn't include patient data itself, but IP address is personal data
  under the DPDP Act.

## Where this currently falls short of DPDP Act 2023 expectations

- **No explicit consent capture at upload time.** Scans are created with no recorded consent
  from the patient (or guardian) for this specific processing purpose.
- **No defined data-retention or deletion policy.** Scan images, diagnostic results, and review
  records are kept indefinitely, with no scheduled purge or patient-initiated deletion path.
- **No stated encryption-at-rest posture.** Images and records sit on local disk / Postgres
  (Neon) with no documented at-rest encryption guarantee beyond whatever the hosting provider
  does by default.
- **No data-subject access or erasure mechanism.** There's no endpoint or process today for a
  patient to request a copy of, or the deletion of, their own data — both are Data Principal
  rights under the DPDP Act.
- **No documented processing-purpose statement or grievance-officer contact**, both of which the
  Act expects a Data Fiduciary to maintain.

## Concrete, low-effort near-term recommendations

- Add a `consent_given` (and `consent_recorded_at`) flag captured at scan upload time.
- Add a configurable retention period (e.g. a `DATA_RETENTION_DAYS` setting) with a scheduled
  job to purge or anonymize records past that window.
- Document data flows — what's collected, where it's stored, who can access it — as a starting
  point for a future formal DPDP assessment. This document is a first step toward that, not the
  assessment itself.
- Add a minimal data-subject request path (even a manually-actioned support inbox to start)
  before this system handles any real patient data outside a hackathon/demo context.

## Scope note

Written as part of the Round-3 audit-logging-and-notifications work order. It reflects this
system's state at that point (Round 3, Agents M/N/O/P already merged) and should be revisited
whenever new personal-data fields or processing paths are added.
