from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from app.database.connection import SessionLocal
from app.database.crud import user as user_crud
from app.database.crud import visit as visit_crud
from datetime import datetime, timedelta, date

class LastSeenMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Get user from event data
        user: User = data.get("event_from_user")
        
        if user:
            with SessionLocal() as db:
                # 1. Update last_seen in User table (legacy/cache)
                db_user = user_crud.get_user_by_telegram_id(db, user.id)
                if db_user:
                    # Update date if changed
                    if db_user.last_seen != date.today():
                        user_crud.update_last_seen(db, user.id)
                
                # 2. Check and log Session (UserVisit)
                last_visit = visit_crud.get_last_visit(db, user.id)
                
                now = datetime.utcnow()
                if not last_visit or (now - last_visit.visit_time) > timedelta(minutes=30):
                    visit_crud.log_new_visit(db, user.id)
        
        return await handler(event, data)
