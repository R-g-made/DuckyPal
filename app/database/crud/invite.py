from sqlalchemy.orm import Session
from app.database.models import Invite, InviteType

def create_invite(db: Session, telegram_id: int, invite_type: InviteType, referrer_id: str):
    """
    Logs an invitation record when a new user joins.
    """
    db_invite = Invite(
        telegram_id=telegram_id,
        invite_type=invite_type,
        referrer_id=referrer_id
    )
    db.add(db_invite)
    db.commit()
    db.refresh(db_invite)
    return db_invite

def get_invite_by_telegram_id(db: Session, telegram_id: int):
    """
    Retrieves the invite info for a specific user.
    """
    return db.query(Invite).filter(Invite.telegram_id == telegram_id).first()

def get_referral_count(db: Session, referrer_id: str):
    """
    Counts how many users were invited by a specific referrer ID.
    """
    return db.query(Invite).filter(Invite.referrer_id == referrer_id).count()
