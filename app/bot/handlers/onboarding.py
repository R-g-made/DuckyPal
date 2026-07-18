from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from datetime import datetime, timedelta
from app.database.connection import SessionLocal
from app.database.crud import push as push_crud
from app.database.crud import user as user_crud
from app.utils.keyboards import get_start_inline_keyboard
from app.core import messages

router = Router()

@router.callback_query(F.data.startswith("onboard_start|"))
async def onboarding_start(callback: types.CallbackQuery):
    """
    Step 1: Choose meal type.
    """
    multiplier = int(callback.data.split("|")[1])
    
    with SessionLocal() as db:
        schedule = push_crud.get_push_schedule(db, callback.from_user.id)
        
    # Check which meals are already set MANUALLY
    meals = []
    if not (schedule and schedule.meal_1_manual): meals.append(("Завтрак ☕️", 1))
    if not (schedule and schedule.meal_2_manual): meals.append(("Обед 🍲", 2))
    if not (schedule and schedule.meal_3_manual): meals.append(("Ужин 🌙", 3))
    
    empty_slots_count = len(meals)
    if empty_slots_count == 0:
        try:
            await callback.answer("Все приемы пищи уже настроены!")
        except TelegramBadRequest:
            pass
        return

    builder = InlineKeyboardBuilder()
    row_btns = []
    for label, idx in meals:
        row_btns.append(types.InlineKeyboardButton(
            text=label, 
            callback_data=f"onboard_meal|{idx}|{multiplier}"
        ))
    builder.row(*row_btns)
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main"))

    text = messages.ONBOARDING_BONUS_INFO.format(multiplier=multiplier)
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass

@router.callback_query(F.data.startswith("onboard_meal|"))
async def onboarding_meal_select(callback: types.CallbackQuery):
    """
    Step 2: Choose time offset.
    """
    parts = callback.data.split("|")
    meal_idx = int(parts[1])
    multiplier = int(parts[2])
    
    builder = InlineKeyboardBuilder()
    
    # 30m and 45m in one row
    builder.row(
        types.InlineKeyboardButton(text="30 мин", callback_data=f"onboard_time|{meal_idx}|{multiplier}|30"),
        types.InlineKeyboardButton(text="45 мин", callback_data=f"onboard_time|{meal_idx}|{multiplier}|45")
    )
    
    # 1h-8h by 2 in a row
    for h in range(1, 9):
        if h % 2 == 1:
            builder.row(
                types.InlineKeyboardButton(text=f"{h} ч", callback_data=f"onboard_time|{meal_idx}|{multiplier}|{h*60}"),
                types.InlineKeyboardButton(text=f"{h+1} ч", callback_data=f"onboard_time|{meal_idx}|{multiplier}|{(h+1)*60}")
            )
            
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"onboard_start|{multiplier}"))

    text = messages.ONBOARDING_TIME_PROMPT
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass

@router.callback_query(F.data.startswith("onboard_time|"))
async def onboarding_time_select(callback: types.CallbackQuery):
    """
    Step 3: Save and grant reward.
    """
    parts = callback.data.split("|")
    meal_idx = int(parts[1])
    multiplier = int(parts[2])
    offset_minutes = int(parts[3])
    
    # Calculate push time: (Now + Offset) - 15 minutes
    now = datetime.now() # Using local time for user's convenience
    push_datetime = now + timedelta(minutes=offset_minutes - 15)
    push_time_str = push_datetime.strftime("%H:%M")
    
    with SessionLocal() as db:
        # Save to DB with manual flag
        update_data = {
            f"meal_{meal_idx}_time": push_time_str,
            f"meal_{meal_idx}_manual": True
        }
        push_crud.create_or_update_push_schedule(db, callback.from_user.id, **update_data)
        
        # Grant usage-based multiplier (1 use)
        user_crud.add_multiplier(db, callback.from_user.id, multiplier=float(multiplier), uses=1)
        
        # Prepare data for return
        user = user_crud.get_user_with_recharge(db, callback.from_user.id)
        if not user:
            user = user_crud.create_user(
                db, 
                telegram_id=callback.from_user.id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                last_name=callback.from_user.last_name
            )
        from app.database.crud import league as league_crud
        user_league = league_crud.join_league_group(db, callback.from_user.id)
        league_name = user_league.league.value if hasattr(user_league.league, 'value') else user_league.league
        
        attempts = user.analysis_attempts
        points = int(user.points)
        
        # Check for active multiplier (the one we just added)
        active_mult = user_crud.get_active_multiplier(db, callback.from_user.id)
        multiplier_text = ""
        if active_mult:
            bonus_info = f"активирован (осталось {active_mult.uses_left} исп.)"
            multiplier_text = f"\n\n<blockquote>🏎 <b>Бонус x{int(active_mult.multiplier)} {bonus_info}</b></blockquote>"

    try:
        await callback.answer(messages.ONBOARDING_SUCCESS_ALERT.format(multiplier=multiplier), show_alert=True)
    except TelegramBadRequest:
        pass
    
    # Return to main menu
    response_text = messages.MAIN_MENU.format(
        attempts=attempts,
        points=points,
        league_name=league_name,
        multiplier_text=multiplier_text
    )
    
    await callback.message.edit_text(
        text=response_text,
        parse_mode="HTML",
        reply_markup=get_start_inline_keyboard()
    )

