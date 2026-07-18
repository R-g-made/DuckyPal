from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database.models import FarmCard, User
from app.database.crud import league as league_crud

def create_farm_card(db: Session, telegram_id: int, points_per_hour: float, food_name: str = None, is_active: bool = True):
    """
    Создает новую карточку для гастро-фермы.
    """
    db_card = FarmCard(
        telegram_id=telegram_id,
        food_name=food_name,
        points_per_hour=points_per_hour,
        is_active=is_active
    )
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card

def get_farm_stats(db: Session, telegram_id: int):
    """
    Calculates current hourly income and total points available for claim.
    """
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        # Fallback if user not found (shouldn't happen in normal flow)
        return {
            "hourly_income": 0,
            "available_points": 0,
            "time_to_claim_seconds": 0,
            "can_claim": True
        }
    
    active_cards = get_user_cards(db, telegram_id, only_active=True)
    
    hourly_income = sum(card.points_per_hour for card in active_cards)
    
    # Calculate points earned since last claim
    now = datetime.utcnow()
    
    if user.last_farm_claim_at:
        start_time = user.last_farm_claim_at
        can_claim_immediately = False
    else:
        # Если еще ни разу не забирали, считаем от момента создания самой старой активной карточки
        if active_cards:
            start_time = min(card.created_at for card in active_cards)
        else:
            start_time = now
        can_claim_immediately = True

    time_passed = now - start_time
    hours_passed = time_passed.total_seconds() / 3600
    available_points = hourly_income * hours_passed
    
    if can_claim_immediately:
        time_to_claim_seconds = 0
        can_claim = True
    else:
        # Time until next claim (8 hours)
        next_claim = start_time + timedelta(hours=8)
        time_to_claim = next_claim - now
        can_claim = time_to_claim.total_seconds() <= 0
        time_to_claim_seconds = max(0, int(time_to_claim.total_seconds()))
    
    return {
        "hourly_income": int(hourly_income),
        "available_points": int(available_points),
        "time_to_claim_seconds": time_to_claim_seconds,
        "can_claim": can_claim
    }

def claim_farm_points(db: Session, telegram_id: int):
    """
    Claims farm points and updates user's total points and last_claim time.
    """
    stats = get_farm_stats(db, telegram_id)
    if not stats["can_claim"]:
        return False, 0
    
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    points_to_add = stats["available_points"]
    
    # Update global balance
    user.points += points_to_add
    
    # Update current league score
    league_crud.add_league_points(db, telegram_id, points=points_to_add)
    
    user.last_farm_claim_at = datetime.utcnow()
    db.commit()
    return True, points_to_add

def get_user_cards(db: Session, telegram_id: int, only_active: bool = False):
    """
    Возвращает список карточек пользователя.
    """
    query = db.query(FarmCard).filter(FarmCard.telegram_id == telegram_id)
    if only_active:
        query = query.filter(FarmCard.is_active == True)
    return query.all()

def toggle_card_status(db: Session, card_id: int, is_active: bool):
    """
    Активирует или деактивирует карточку.
    """
    db_card = db.query(FarmCard).filter(FarmCard.id == card_id).first()
    if db_card:
        db_card.is_active = is_active
        db.commit()
        db.refresh(db_card)
    return db_card

def update_card_points(db: Session, card_id: int, new_points: float):
    """
    Обновляет доходность карточки.
    """
    db_card = db.query(FarmCard).filter(FarmCard.id == card_id).first()
    if db_card:
        db_card.points_per_hour = new_points
        db.commit()
        db.refresh(db_card)
    return db_card

def add_to_farm_logic(db: Session, telegram_id: int, hourly_income: float, food_name: str = None, slot_idx: int = None):
    """
    Handles the logic of adding a card to the farm:
    - If slot_idx is provided, it replaces the card in that slot or adds to it.
    - Otherwise, default behavior (max 3, FIFO).
    """
    active_cards = get_user_cards(db, telegram_id, only_active=True)
    
    if slot_idx is not None:
        # Sort by creation date to find the correct slot (0, 1, 2)
        active_cards.sort(key=lambda x: x.created_at)
        if slot_idx < len(active_cards):
            # Deactivate existing card in this slot
            active_cards[slot_idx].is_active = False
            db.commit()
    else:
        if len(active_cards) >= 3:
            # Sort by creation date and archive the oldest
            active_cards.sort(key=lambda x: x.created_at)
            oldest_card = active_cards[0]
            oldest_card.is_active = False
            db.commit()

    # Create new active card
    return create_farm_card(db, telegram_id, hourly_income, food_name=food_name, is_active=True)
