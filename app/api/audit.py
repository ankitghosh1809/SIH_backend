"""
Read-only audit log endpoint (Agent Q), prefix /api/v1/audit.

Unauthenticated for now — see the TODO below for why, and for the
discrepancy with app/api/admin.py this task's work order pointed at.
"""
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.audit_models import AuditLog
from app.db.database import get_session

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


class AuditLogResponse(BaseModel):
    id: str
    actor: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    ip_address: Optional[str]
    created_at: Optional[str]


def _serialize(row: AuditLog) -> AuditLogResponse:
    return AuditLogResponse(
        id=row.id,
        actor=row.actor,
        action=row.action,
        resource_type=row.resource_type,
        resource_id=row.resource_id,
        ip_address=row.ip_address,
        created_at=row.created_at.isoformat() if row.created_at else None,
    )


# TODO: protect once role-based auth is settled for read-only admin/audit
# endpoints, matching app/api/admin.py's existing GET /stats convention.
#
# ASSUMPTION / note on this comment: the work order for this task says to
# copy app/api/admin.py's existing "# TODO: consider protecting this..."
# comment verbatim. By the time this was implemented, Agent M's auth had
# already landed on main and admin.py's GET /stats now actually uses
# Depends(require_role("admin")) instead of that open-with-a-TODO pattern —
# so there's nothing left to copy verbatim. This endpoint still doesn't
# import from app/auth/ (per this task's own explicit rule), so it stays
# open with this flag rather than reaching for that same dependency.
@router.get("/logs", response_model=list[AuditLogResponse])
def get_audit_logs(
    action: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_session),
):
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action.contains(action))
    rows = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [_serialize(r) for r in rows]
