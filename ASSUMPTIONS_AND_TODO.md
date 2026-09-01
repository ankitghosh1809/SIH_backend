# Agent O — referral workflow: assumptions to verify

This was implemented without being able to read the real repo — GitHub's
robots.txt blocks this session's fetch tool, and this chat's code sandbox
has no internet access at all, so `git clone`, `pip install`, and `pytest`
weren't possible either. Treat this as a strong first draft built entirely
from `R3_Agent_O_Referral_Workflow.md`, not a verified-against-your-code
implementation.

Things to check, roughly in order of "most likely to actually break
something":

1. **DB session dependency** (`app/api/referrals.py`) — imported as
   `get_db` from `app.db.database`. If the real dependency lives somewhere
   else, or is named differently, this is a one-line import fix.

2. **`Base` import** (`app/db/referral_models.py`) — imported from
   `app.db.models`, matching what the work order says `review_models.py`
   does. Confirm against the real `review_models.py`, including whether it
   uses classic `Column()` mapping (what's used here) or the newer
   `Mapped[]` / `mapped_column()` style.

3. **`Scan` field names for the two probabilities**
   (`app/reports/referral_letter.py`) — the real attribute names aren't
   confirmed, so `_get_first_attr()` tries a few plausible ones
   (`dr_probability` / `diabetic_retinopathy_probability` / `dr_prob`,
   etc.) and falls back to `"N/A"` instead of crashing. Swap in the real
   names once you've checked `app/db/models.py`.

4. **Test fixture** (`tests/test_referrals.py`, `_create_scan()`) — the
   single biggest unknown in this deliverable. It's a best-effort guess at
   what fields a `Scan` row needs to construct, not a copy of the real
   `_create_scan()` helper in `tests/test_review.py`. Reconcile the two
   before trusting this file to even collect properly.

5. **Reportlab style** (`app/reports/referral_letter.py`) — built with
   Platypus (`SimpleDocTemplate` + `Paragraph` + `Table`), a reasonable
   guess for a report-style PDF, but not matched against the real
   `pdf_generator.py` fonts, margins, or layout helpers.

6. **`app/main.py`** — not touched here (no safe way to edit a file I
   can't see). Add, near the other `include_router` calls:

   ```python
   app.include_router(referrals.router)
   ```

   (plus `from app.api import referrals`, or whatever this file's existing
   import convention is for the other routers.)

Everything else — the `referrals` table schema, all six endpoint
contracts, status values, the five Pydantic schema shapes, the exact
positioning line text, and the self-test coverage — was implemented
directly from the work order, which was detailed enough that none of it
needed the real repo.

## To finish this off

Either:

- Paste in / upload `PROJECT_CONTEXT.md`, `app/db/models.py`,
  `app/db/review_models.py`, and `tests/test_review.py` so items 1–4 above
  can be closed out precisely, or
- Hand this whole `payload/` folder plus the real repo to a coding agent
  with actual repo + terminal access (e.g. Claude Code), which can read
  the real files, run the test suite, and fix any mismatches itself.

Either way, before calling this done:

```
pytest tests/ -q
python -c "from app.main import app"
```
