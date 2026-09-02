"""
Best-effort request audit log middleware (Agent Q).

Logs every request that passes through the app. Deliberately fails soft:
the actual DB write is wrapped in a try/except that swallows (and prints,
for local debugging) any failure, so a broken audit log can never turn into
a 500 for the person calling the API — logging is a side effect here, never
a gate on the request it's observing. See tests/test_audit.py for the test
that simulates a write failure and checks the wrapped request still
succeeds.

Coarse actor signal, deliberately not wired into app/auth/: this checks
only whether an Authorization header is present, not whether it's a real,
valid token. Agent M's real per-user JWT auth may or may not be merged by
the time this runs, and this file must not depend on merge order — see the
work order's "On authentication" section. Once real auth has landed for
good, `actor` here could be upgraded to decode the actual username instead
of this authenticated/anonymous flag; that upgrade is out of scope for this
task.
"""
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.db.audit_models import AuditLog  # import registers the `audit_logs` table
from app.db.database import SessionLocal


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Always get the real response first. Logging happens after, and only
        # ever affects whether a log row exists — never whether this response
        # is the one returned.
        response = await call_next(request)
        self._log_best_effort(request)
        return response

    def _log_best_effort(self, request: Request) -> None:
        try:
            actor = "authenticated" if request.headers.get("authorization") else "anonymous"

            db = SessionLocal()
            try:
                db.add(
                    AuditLog(
                        id=str(uuid.uuid4()),
                        actor=actor,
                        action=f"{request.method} {request.url.path}",
                        resource_type=None,
                        resource_id=None,
                        ip_address=request.client.host if request.client else None,
                    )
                )
                db.commit()
            finally:
                db.close()
        except Exception as exc:  # noqa: BLE001 — deliberately broad: see module docstring
            # Best-effort only. Printed for local visibility; never re-raised.
            print(f"[audit] failed to write audit log row: {exc!r}")
