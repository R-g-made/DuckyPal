from sqlalchemy.orm import Session
from app.database.models import UserAction, ActionType

def log_action(db: Session, telegram_id: int, action_type: ActionType):
    """
    Logs a user action in the database.
    """
    db_action = UserAction(
        telegram_id=telegram_id,
        action_type=action_type
    )
    db.add(db_action)
    db.commit()
    db.refresh(db_action)
    return db_action
