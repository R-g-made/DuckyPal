import json
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database.models import PhotoAnalysis, PushNotification, Invite, AttributionType, InviteType
from datetime import datetime
from app.database.crud import user as user_crud
from app.database.crud import league as league_crud
from app.utils.points import calculate_points
from app.database.models import PhotoAnalysis, PushNotification, Invite, AttributionType, InviteType, UserLeague, League

def log_photo_analysis(db: Session, telegram_id: int, ai_result: dict, file_path: str = None, trigger_card_id: int = None, multiplier: float = 1.0):
    """
    Determines attribution and logs a new photo analysis.
    Attributes the photo to the event that is closest in time (Push or Invite).
    Calculates and awards points.
    """
    # ... existing logic for last_push and last_invite ...
    last_push = db.query(PushNotification).filter(
        PushNotification.telegram_id == telegram_id
    ).order_by(desc(PushNotification.sent_at)).first()

    last_invite = db.query(Invite).filter(
        Invite.telegram_id == telegram_id
    ).order_by(desc(Invite.created_at)).first()

    now = datetime.utcnow()
    attr_type = AttributionType.DIRECT
    attr_id = None
    
    events = []
    if last_push:
        events.append((AttributionType.PUSH, last_push.sent_at, last_push.id))
    if last_invite:
        inv_type = AttributionType.AD if last_invite.invite_type == InviteType.AD else AttributionType.FRIEND
        events.append((inv_type, last_invite.created_at, last_invite.id))

    if events:
        events.sort(key=lambda x: abs((now - x[1]).total_seconds()))
        closest = events[0]
        attr_type = closest[0]
        attr_id = closest[2]

    # Calculate points
    user_league = db.query(UserLeague).filter(UserLeague.telegram_id == telegram_id).first()
    current_league = user_league.league if user_league else League.BEGINNER
    
    point_data = calculate_points(
        base_score=ai_result.get("food_score", 0),
        health_multiplier=ai_result.get("health_multiplier", 1.0),
        league=current_league
    )
    
    # Apply external multiplier (e.g. from onboarding or promo)
    if multiplier > 1.0:
        point_data["total"] = round(point_data["total"] * multiplier, 2)

    # Create detailed log with new fields
    new_analysis = PhotoAnalysis(
        telegram_id=telegram_id,
        created_at=now,
        description=ai_result.get("comment"), # Используем комментарий ИИ как описание
        file_path=file_path,                  # Путь к файлу
        result_text=json.dumps(ai_result, ensure_ascii=False),
        points_earned=point_data["total"],    # Начисленные поинты
        food_score=ai_result.get("food_score", 0),
        health_multiplier=ai_result.get("health_multiplier", 1.0),
        trigger_card_id=trigger_card_id,      # Связь с карточкой
        attribution_type=attr_type,
        attribution_id=attr_id
    )
    db.add(new_analysis)
    
    # Update general user stats and league points
    user_crud.increment_photo_stats(db, telegram_id, points=point_data["total"])
    if user_league:
        league_crud.add_league_points(db, telegram_id, points=point_data["total"])
    
    db.commit()
    db.refresh(new_analysis)
    return new_analysis, point_data
