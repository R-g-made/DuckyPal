from sqlalchemy.orm import Session
from app.database.models import User, UserMultiplier
from datetime import datetime, date, timedelta

def get_active_multiplier(db: Session, telegram_id: int):
    """
    Returns the highest active multiplier for the user.
    Handles both time-based and usage-based multipliers.
    """
    now = datetime.utcnow()
    # Check for active time-based or usage-based multipliers
    active = db.query(UserMultiplier).filter(
        UserMultiplier.telegram_id == telegram_id,
        UserMultiplier.is_active == True,
        (
            (UserMultiplier.expires_at > now) | # Time-based
            (UserMultiplier.uses_left > 0)     # Usage-based
        )
    ).order_by(UserMultiplier.multiplier.desc()).first()
    
    return active

def add_multiplier(db: Session, telegram_id: int, multiplier: float, duration_hours: int = None, uses: int = None):
    """
    Adds a new temporary multiplier (either time-based or usage-based).
    """
    expires_at = None
    if duration_hours:
        expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
    
    db_mult = UserMultiplier(
        telegram_id=telegram_id,
        multiplier=multiplier,
        expires_at=expires_at,
        uses_left=uses
    )
    db.add(db_mult)
    db.commit()
    db.refresh(db_mult)
    return db_mult

def consume_multiplier_use(db: Session, multiplier_id: int):
    """
    Decrements usage-based multiplier.
    """
    db_mult = db.query(UserMultiplier).filter(UserMultiplier.id == multiplier_id).first()
    if db_mult and db_mult.uses_left is not None:
        db_mult.uses_left -= 1
        if db_mult.uses_left <= 0:
            db_mult.is_active = False
        db.commit()
        db.refresh(db_mult)
    return db_mult

def get_user_by_telegram_id(db: Session, telegram_id: int):
    return db.query(User).filter(User.telegram_id == telegram_id).first()

def get_user_with_recharge(db: Session, telegram_id: int) -> User:
    """
    Gets user and updates their analysis attempts based on time passed.
    1 attempt every 8 hours, max 3.
    """
    db_user = get_user_by_telegram_id(db, telegram_id)
    if not db_user:
        return None
    
    now = datetime.utcnow()
    # Calculate how many 8-hour intervals passed since last_recharge_at
    time_passed = now - db_user.last_recharge_at
    recharged_units = int(time_passed.total_seconds() // (8 * 3600))
    
    if recharged_units > 0:
        # Update attempts
        new_attempts = min(3, db_user.analysis_attempts + recharged_units)
        
        # If we reached max, reset last_recharge_at to now
        if new_attempts == 3:
            db_user.last_recharge_at = now
        else:
            # Otherwise, move it forward by the number of units recharged
            db_user.last_recharge_at += timedelta(hours=recharged_units * 8)
            
        db_user.analysis_attempts = new_attempts
        db.commit()
        db.refresh(db_user)
        
    return db_user

def use_analysis_attempt(db: Session, telegram_id: int) -> bool:
    """
    Decrements analysis attempt if available.
    Returns True if successful, False if no attempts left.
    """
    db_user = get_user_with_recharge(db, telegram_id)
    if not db_user or db_user.analysis_attempts <= 0:
        return False
    
    # If using the first attempt from a full tank (3), start the timer
    if db_user.analysis_attempts == 3:
        db_user.last_recharge_at = datetime.utcnow()
        
    db_user.analysis_attempts -= 1
    db.commit()
    db.refresh(db_user)
    return True

def get_time_to_next_attempt(db_user: User) -> str:
    """
    Returns a human readable string of time left until next recharge.
    """
    if db_user.analysis_attempts >= 3:
        return "0м"
        
    now = datetime.utcnow()
    next_recharge = db_user.last_recharge_at + timedelta(hours=8)
    remaining = next_recharge - now
    
    if remaining.total_seconds() <= 0:
        return "0м"
        
    hours, remainder = divmod(int(remaining.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours}ч {minutes}м"
    return f"{minutes}м"

def create_user(db: Session, telegram_id: int, **kwargs):
    db_user = User(
        telegram_id=telegram_id,
        username=kwargs.get("username"),
        first_name=kwargs.get("first_name"),
        last_name=kwargs.get("last_name"),
        language_code=kwargs.get("language_code"),
        is_premium=kwargs.get("is_premium", False),
        is_bot=kwargs.get("is_bot", False),
        last_seen=date.today()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_last_seen(db: Session, telegram_id: int):
    db_user = get_user_by_telegram_id(db, telegram_id)
    if db_user:
        db_user.last_seen = date.today()
        db.commit()
        db.refresh(db_user)
    return db_user

def increment_photo_stats(db: Session, telegram_id: int, points: float = 0.0):
    db_user = get_user_by_telegram_id(db, telegram_id)
    if db_user:
        db_user.total_photos += 1
        db_user.points += points
        db_user.last_photo_at = datetime.utcnow()
        db_user.last_seen = date.today()
        db.commit()
        db.refresh(db_user)
    return db_user

def update_user_activity(db: Session, telegram_id: int, is_active: bool):
    db_user = get_user_by_telegram_id(db, telegram_id)
    if db_user:
        db_user.is_active = is_active
        db.commit()
        db.refresh(db_user)
    return db_user
