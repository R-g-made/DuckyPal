import asyncio
import random
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from aiogram import Bot

from app.database.connection import SessionLocal
from app.database.crud import push as push_crud
from app.database.crud import user as user_crud
from app.database.crud import farm as farm_crud
from app.database.crud import league as league_crud
from app.database.models import PushNotification, LeaderboardMovement, UserLeague
from app.core.push_templates import PUSH_TEMPLATES

async def check_and_send_pushes(bot: Bot):
    """
    Background task to check schedules and send push notifications.
    """
    while True:
        try:
            with SessionLocal() as db:
                now_str = datetime.now().strftime("%H:%M")
                # Get all active schedules
                schedules = push_crud.get_all_active_schedules(db)
                
                for schedule in schedules:
                    # Check if current time matches any of the meal push times
                    is_time_to_push = (
                        schedule.meal_1_time == now_str or 
                        schedule.meal_2_time == now_str or 
                        schedule.meal_3_time == now_str
                    )
                    
                    if is_time_to_push:
                        await process_user_push(db, bot, schedule.telegram_id)
            
            # Wait for 1 minute before next check
            await asyncio.sleep(60)
            
        except Exception as e:
            logging.error(f"Error in push worker: {e}")
            await asyncio.sleep(60)

async def process_user_push(db: Session, bot: Bot, telegram_id: int):
    """
    Decides which push to send based on availability and randomness.
    """
    available_pushes = [] # List of tuples: (type, context_data)
    
    # 0. Meal reminder is always an option if triggered
    available_pushes.append(("meal_reminder", {}))
    
    # 1. Check Farm Availability
    farm_stats = farm_crud.get_farm_stats(db, telegram_id)
    if farm_stats["can_claim"]:
        available_pushes.append(("farm", {}))
        
    # 2. Check Leaderboard (if overtaken)
    user_league = db.query(UserLeague).filter(UserLeague.telegram_id == telegram_id).first()
    if user_league:
        leaderboard = league_crud.get_leaderboard_data(db, user_league.group_id)
        current_rank = 0
        overtaker_name = "Кто-то"
        
        for i, entry in enumerate(leaderboard):
            if not entry["is_bot"] and entry["id"] == telegram_id:
                current_rank = i + 1
                # The person directly above the user
                if i > 0:
                    overtaker_name = leaderboard[i-1]["name"]
                break
        
        if current_rank > 1:
            available_pushes.append(("leaderboard", {"name": overtaker_name}))

    # 3. Check Attempts
    user = user_crud.get_user_with_recharge(db, telegram_id)
    if user.analysis_attempts > 0:
        available_pushes.append(("attempts", {}))
        
    if not available_pushes:
        return # Nothing to push about

    # Choose random push from available
    push_type, context = random.choice(available_pushes)
    template = random.choice(PUSH_TEMPLATES[push_type])
    
    # Format message with context data (like overtaker name)
    try:
        message = template.format(**context)
    except KeyError:
        message = template # Fallback if formatting fails
    
    try:
        await bot.send_message(telegram_id, message, parse_mode="HTML")
        
        # Log to DB
        new_push = PushNotification(
            telegram_id=telegram_id,
            push_type=push_type,
            message_text=message
        )
        db.add(new_push)
        db.commit()
        logging.info(f"Push sent to {telegram_id}: {push_type}")
    except Exception as e:
        logging.error(f"Failed to send push to {telegram_id}: {e}")
