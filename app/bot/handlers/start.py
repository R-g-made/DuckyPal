from aiogram import Router, types
from aiogram.filters import CommandStart
import asyncio
from datetime import datetime, timedelta
from app.database.connection import SessionLocal
from app.database.crud import user as user_crud
from app.database.crud import action as action_crud
from app.database.crud import invite as invite_crud
from app.database.crud import league as league_crud
from app.database.models import ActionType, InviteType
from app.utils.keyboards import get_start_inline_keyboard
from app.utils import points as points_utils
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database.crud import push as push_crud
from app.core import messages

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message, bot: types.Bot, command: types.BotCommand = None):
    """
    Handler for /start command.
    Registers user and handles referrals if present.
    """
    telegram_id = message.from_user.id
    args = message.text.split()[1] if len(message.text.split()) > 1 else None

    with SessionLocal() as db:
        user = user_crud.get_user_with_recharge(db, telegram_id)
        is_new_user = False
        if not user:
            is_new_user = True
            user = user_crud.create_user(
                db, 
                telegram_id=telegram_id, 
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                language_code=message.from_user.language_code,
                is_premium=message.from_user.is_premium,
                is_bot=message.from_user.is_bot
            )
            
            # Handle referral/invite if present
            if args:
                invite_type = InviteType.AD if args.startswith("ad_") else InviteType.FRIEND
                invite_crud.create_invite(
                    db,
                    telegram_id=telegram_id,
                    invite_type=invite_type,
                    referrer_id=args
                )
                
                # If it's a friend invite, reward the referrer
                if invite_type == InviteType.FRIEND:
                    try:
                        referrer_id = int(args)
                        referrer_league = league_crud.join_league_group(db, referrer_id)
                        league_mult = points_utils.get_league_multiplier(referrer_league.league)
                        bonus_points = 1500 * league_mult
                        
                        # Add points and multiplier to referrer
                        user_crud.increment_photo_stats(db, referrer_id, points=bonus_points)
                        league_crud.add_league_points(db, referrer_id, points=bonus_points)
                        user_crud.add_multiplier(db, referrer_id, multiplier=2.0, duration_hours=12)
                        
                        # Notify referrer
                        friend_name = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
                        notify_text = (
                            f"К нам пришел ваш друг {friend_name}!\n"
                            f"<blockquote>Мы уже начислили вам ваш бонус 🐥🎁</blockquote>"
                        )
                        await bot.send_message(referrer_id, notify_text, parse_mode="HTML")
                    except Exception as e:
                        # Log error but don't stop the flow
                        import logging
                        logging.error(f"Error rewarding referrer {args}: {e}")
        
        # Ensure user is in a league
        user_league = league_crud.join_league_group(db, telegram_id)
        league_name = user_league.league.value if hasattr(user_league.league, 'value') else user_league.league
        
        # Log start action
        action_crud.log_action(db, telegram_id, ActionType.START)
        
        # Prepare data for message
        attempts = user.analysis_attempts
        points = int(user.points)
        
        # Check for active multiplier
        active_mult = user_crud.get_active_multiplier(db, telegram_id)
        multiplier_text = ""
        if active_mult:
            if active_mult.expires_at:
                now = datetime.utcnow()
                remaining = active_mult.expires_at - now
                hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                time_str = f"{hours}ч {minutes}м" if hours > 0 else f"{minutes}м"
                bonus_info = f"активирован ({time_str})"
            else:
                bonus_info = f"активирован (осталось {active_mult.uses_left} исп.)"
                
            multiplier_text = f"\n\n<blockquote>🏎 <b>Бонус x{int(active_mult.multiplier)} {bonus_info}</b></blockquote>"

        # Check for onboarding x2 offer (if no meals set up)
        schedule = push_crud.get_push_schedule(db, telegram_id)
        meals_count = 0
        if schedule:
            if schedule.meal_1_time: meals_count += 1
            if schedule.meal_2_time: meals_count += 1
            if schedule.meal_3_time: meals_count += 1
        
        show_x2_offer = meals_count == 0
    
    response_text = messages.MAIN_MENU.format(
        attempts=attempts,
        points=points,
        league_name=league_name,
        multiplier_text=multiplier_text
    )
    
    await message.answer(
        text=response_text,
        parse_mode="HTML",
        reply_markup=get_start_inline_keyboard()
    )
    
    if show_x2_offer:
        async def delayed_offer():
            await asyncio.sleep(20)
            # Send a separate message for the bonus offer
            offer_text = messages.OFFER_X2
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="Хочу! 🙋‍♂️", callback_data="onboard_start|2"))
            
            try:
                await message.answer(offer_text, parse_mode="HTML", reply_markup=builder.as_markup())
            except Exception as e:
                import logging
                logging.error(f"Error sending delayed x2 offer: {e}")

        asyncio.create_task(delayed_offer())
