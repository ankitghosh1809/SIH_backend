"""
Pull-based notification sync (Agent Q).

sync_notifications(db) generates notifications by scanning existing data —
Scan rows with risk_level == "high", and Review rows — rather than by
hooking into app/api/scans.py's or app/api/review.py's write paths. That's
the point of this design: this feature never needs those files to change,
or even to know it exists, so it can't go out of sync with whatever else is
landing on those branches in parallel. It's called at the top of
GET /api/v1/notifications (see app/api/notifications.py) so the list is
always fresh, with no background job or hook needed anywhere else.
"""
import uuid

from sqlalchemy.orm import Session

from app.db.models import Scan
from app.db.notification_models import Notification
from app.db.review_models import Review


def sync_notifications(db: Session) -> None:
    _sync_high_risk_scans(db)
    _sync_completed_reviews(db)
    db.commit()


def _existing_scan_ids_for(db: Session, event_type: str) -> set:
    rows = (
        db.query(Notification.scan_id)
        .filter(Notification.event_type == event_type)
        .all()
    )
    return {row.scan_id for row in rows}


def _sync_high_risk_scans(db: Session) -> None:
    already_notified = _existing_scan_ids_for(db, "high_risk_detected")
    high_risk_scans = db.query(Scan).filter(Scan.risk_level == "high").all()
    for scan in high_risk_scans:
        if scan.id in already_notified:
            continue
        db.add(
            Notification(
                id=str(uuid.uuid4()),
                event_type="high_risk_detected",
                scan_id=scan.id,
                message=f"High-risk scan detected (scan_id={scan.id}).",
            )
        )


def _sync_completed_reviews(db: Session) -> None:
    # NOTE / ASSUMPTION: dedup keys off scan_id, not a review id — Notification
    # has no review_id column per the work order's schema, and the sync rule is
    # stated in terms of scan_id ("doesn't yet have a notifications row with
    # event_type='review_completed' and the same scan_id"). One consequence:
    # if a single scan is reviewed more than once, only the FIRST review
    # produces a notification — a second review of the same scan is treated as
    # "already notified". That's what the literal spec implies; flagging it
    # here since it's easy to miss on a quick read and isn't exercised by the
    # self-test (which only reviews a scan once).
    already_notified = _existing_scan_ids_for(db, "review_completed")
    reviews = db.query(Review).all()
    for review in reviews:
        if review.scan_id in already_notified:
            continue
        db.add(
            Notification(
                id=str(uuid.uuid4()),
                event_type="review_completed",
                scan_id=review.scan_id,
                message=f"Doctor review completed for scan_id={review.scan_id}.",
            )
        )
