from sqlalchemy.orm import Session
from app.database.models import ShopItem, UserShopPurchase, User
from datetime import datetime, timedelta

def get_active_shop_items(db: Session):
    """
    Returns all active shop items.
    Initializes the database with default items if empty.
    """
    items = db.query(ShopItem).filter(ShopItem.is_active == True).all()
    if not items:
        # Initialize default items
        extra_attempt = ShopItem(
            name="Доп. попытка",
            code="extra_attempt",
            base_price=250.0
        )
        db.add(extra_attempt)
        db.commit()
        db.refresh(extra_attempt)
        items = [extra_attempt]
    return items

def get_shop_item_by_code(db: Session, code: str):
    return db.query(ShopItem).filter(ShopItem.code == code, ShopItem.is_active == True).first()

def get_user_purchases_today(db: Session, telegram_id: int, item_code: str):
    """
    Returns count of specific item purchases by user in the last 12 hours.
    (Since the shop updates every 12 hours).
    """
    # Calculate shop reset time (every 12 hours)
    now = datetime.utcnow()
    # If now is 15:00, last reset was at 12:00. If 03:00, last reset was 00:00.
    last_reset_hour = (now.hour // 12) * 12
    last_reset = now.replace(hour=last_reset_hour, minute=0, second=0, microsecond=0)
    
    return db.query(UserShopPurchase).join(ShopItem).filter(
        UserShopPurchase.telegram_id == telegram_id,
        ShopItem.code == item_code,
        UserShopPurchase.purchased_at >= last_reset
    ).count()

def record_purchase(db: Session, telegram_id: int, item_id: int, price: float):
    purchase = UserShopPurchase(
        telegram_id=telegram_id,
        item_id=item_id,
        price_paid=price
    )
    db.add(purchase)
    db.commit()
    return purchase
