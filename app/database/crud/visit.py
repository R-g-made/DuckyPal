from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database.models import UserVisit, PushNotification, Invite, AttributionType, InviteType
from datetime import datetime

def get_last_visit(db: Session, telegram_id: int):
    return db.query(UserVisit).filter(UserVisit.telegram_id == telegram_id).order_by(desc(UserVisit.visit_time)).first()

def log_new_visit(db: Session, telegram_id: int):
    """
    Determines attribution and logs a new visit.
    Logic: Compares the time of the last Push and the initial Invite.
    Attributes the visit to the event that is closest in time to the current moment.
    """
    # 1. Find most recent Push
    last_push = db.query(PushNotification).filter(
        PushNotification.telegram_id == telegram_id
    ).order_by(desc(PushNotification.sent_at)).first()

    # 2. Find initial Invite
    last_invite = db.query(Invite).filter(
        Invite.telegram_id == telegram_id
    ).order_by(desc(Invite.created_at)).first()

    now = datetime.utcnow()
    attr_type = AttributionType.DIRECT
    attr_id = None
    
    # Collect available trigger events
    events = []
    if last_push:
        events.append((AttributionType.PUSH, last_push.sent_at, last_push.id))
    if last_invite:
        inv_type = AttributionType.AD if last_invite.invite_type == InviteType.AD else AttributionType.FRIEND
        events.append((inv_type, last_invite.created_at, last_invite.id))

    if events:
        # Sort by absolute time difference to 'now'.
        # The event with the smallest difference is the closest trigger.
        events.sort(key=lambda x: abs((now - x[1]).total_seconds()))
        closest = events[0]
        
        attr_type = closest[0]
        attr_id = closest[2]

    new_visit = UserVisit(
        telegram_id=telegram_id,
        visit_time=now,
        attribution_type=attr_type,
        attribution_id=attr_id
    )
    db.add(new_visit)
    db.commit()
    db.refresh(new_visit)
    return new_visit
