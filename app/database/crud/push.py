from sqlalchemy.orm import Session
from app.database.models import UserPushSchedule
from datetime import datetime, timedelta

def get_push_schedule(db: Session, telegram_id: int):
    return db.query(UserPushSchedule).filter(UserPushSchedule.telegram_id == telegram_id).first()

def create_or_update_push_schedule(db: Session, telegram_id: int, **kwargs):
    schedule = get_push_schedule(db, telegram_id)
    if not schedule:
        schedule = UserPushSchedule(telegram_id=telegram_id)
        db.add(schedule)
    
    if "meal_1_time" in kwargs:
        schedule.meal_1_time = kwargs["meal_1_time"]
        if kwargs.get("meal_1_manual"): schedule.meal_1_manual = True
    if "meal_2_time" in kwargs:
        schedule.meal_2_time = kwargs["meal_2_time"]
        if kwargs.get("meal_2_manual"): schedule.meal_2_manual = True
    if "meal_3_time" in kwargs:
        schedule.meal_3_time = kwargs["meal_3_time"]
        if kwargs.get("meal_3_manual"): schedule.meal_3_manual = True
    if "is_enabled" in kwargs:
        schedule.is_enabled = kwargs["is_enabled"]
        
    db.commit()
    db.refresh(schedule)
    return schedule

def get_all_active_schedules(db: Session):
    return db.query(UserPushSchedule).filter(UserPushSchedule.is_enabled == True).all()

def auto_assign_meal_time(db: Session, telegram_id: int, photo_time: datetime):
    """
    Automatically assigns a meal slot based on photo time.
    Only fills slots that are NOT set manually.
    """
    schedule = get_push_schedule(db, telegram_id)
    if not schedule:
        schedule = UserPushSchedule(telegram_id=telegram_id)
        db.add(schedule)
        db.commit()
        db.refresh(schedule)

    # Calculate push time (15 mins before photo)
    push_time_str = (photo_time - timedelta(minutes=15)).strftime("%H:%M")
    
    # Check for empty or non-manual slots to fill
    # We prioritize filling empty slots first
    if not schedule.meal_1_time and not schedule.meal_1_manual:
        schedule.meal_1_time = push_time_str
    elif not schedule.meal_2_time and not schedule.meal_2_manual:
        schedule.meal_2_time = push_time_str
    elif not schedule.meal_3_time and not schedule.meal_3_manual:
        schedule.meal_3_time = push_time_str
    else:
        # If all slots are filled but some are not manual, we could potentially update them, 
        # but for now let's just keep the first auto-assigned one to avoid jumping times.
        return schedule

    # Sort ONLY if we don't have manual constraints that would be violated
    # For simplicity, if ANY slot is manual, we don't auto-sort all of them 
    # as it might move a manual "Lunch" to "Breakfast" slot.
    if not (schedule.meal_1_manual or schedule.meal_2_manual or schedule.meal_3_manual):
        times = []
        if schedule.meal_1_time: times.append(schedule.meal_1_time)
        if schedule.meal_2_time: times.append(schedule.meal_2_time)
        if schedule.meal_3_time: times.append(schedule.meal_3_time)
        times.sort()
        
        schedule.meal_1_time = times[0] if len(times) > 0 else None
        schedule.meal_2_time = times[1] if len(times) > 1 else None
        schedule.meal_3_time = times[2] if len(times) > 2 else None
    
    db.commit()
    db.refresh(schedule)
    return schedule
