"""
Notification endpoints (Agent Q), prefix /api/v1/notifications.

GET calls sync_notifications(db) first so the list is always fresh — see
app/notifications/service.py for why this is pull-based rather than a hook
into app/api/scans.py or app/api/review.py.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_session
from app.db.notification_models import Notification
from app.notifications.service import sync_notifications

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    id: str
    event_type: str
    scan_id: Optional[str]
    channel: str
    message: str
    is_read: bool
    created_at: Optional[str]


def _serialize(row: Notification) -> NotificationResponse:
    return NotificationResponse(
        id=row.id,
        event_type=row.event_type,
        scan_id=row.scan_id,
        channel=row.channel,
        message=row.message,
        is_read=row.is_read,
        created_at=row.created_at.isoformat() if row.created_at else None,
    )


@router.get("", response_model=list[NotificationResponse])
def get_notifications(unread_only: bool = False, db: Session = Depends(get_session)):
    sync_notifications(db)
    query = db.query(Notification)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))
    rows = query.order_by(Notification.created_at.desc()).all()
    return [_serialize(r) for r in rows]


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(notification_id: str, db: Session = Depends(get_session)):
    notification = db.get(Notification, notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return _serialize(notification)
