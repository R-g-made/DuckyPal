from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from datetime import datetime, timedelta
from app.database.connection import SessionLocal
from app.database.crud import action as action_crud
from app.database.crud import farm as farm_crud
from app.database.crud import league as league_crud
from app.database.crud import user as user_crud
from app.database.models import ActionType, League
from app.utils.keyboards import get_start_inline_keyboard, get_invite_keyboard
from app.utils import points as points_utils
from app.core import messages

router = Router()

def get_time_until_reset():
    """
    Calculates time until the next league reset (every 3 days).
    For simulation, let's say it's every 3 days from a fixed point.
    """
    now = datetime.utcnow()
    # Simple logic: reset every 3 days
    # In a real app, you might store the next_reset_at in the database
    days_to_add = 3 - (now.day % 3)
    reset_time = (now + timedelta(days=days_to_add)).replace(hour=0, minute=0, second=0, microsecond=0)
    delta = reset_time - now
    
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if days > 0:
        return f"{days}д {hours}ч {minutes}м"
    return f"{hours}ч {minutes}м"

async def show_gastro_farm(callback: types.CallbackQuery):
    """
    Helper to show/refresh the gastro farm view.
    """
    with SessionLocal() as db:
        active_cards = farm_crud.get_user_cards(db, callback.from_user.id, only_active=True)
        stats = farm_crud.get_farm_stats(db, callback.from_user.id)
        
        builder = InlineKeyboardBuilder()
        # 3 Slots logic
        for i in range(3):
            if i < len(active_cards):
                card = active_cards[i]
                btn_text = f"{card.food_name} ({int(card.points_per_hour)}/ч)"
            else:
                btn_text = "Пока пусто"
            
            builder.row(types.InlineKeyboardButton(text=btn_text, callback_data=f"farm_slot_{i}"))
        
        # Claim points button with dynamic style and timer
        if stats["can_claim"]:
            claim_text = "Забрать награду"
            claim_style = "success"
        else:
            hours, remainder = divmod(stats["time_to_claim_seconds"], 3600)
            minutes, _ = divmod(remainder, 60)
            time_str = f"{hours}ч {minutes}м" if hours > 0 else f"{minutes}м"
            claim_text = f"Забрать награду ({time_str})"
            claim_style = "primary"

        builder.row(types.InlineKeyboardButton(
            text=claim_text, 
            callback_data="claim_farm_points",
            style=claim_style,
            icon_custom_emoji_id = "5415594207068822547"
        ))
        
        # Back button
        builder.row(types.InlineKeyboardButton(text="Назад", callback_data="back_to_main", icon_custom_emoji_id = "5877629862306385808"))
        
        text = messages.FARM_MAIN.format(
            hourly_income=stats['hourly_income'],
            available_points=stats['available_points']
        )

        try:
            await callback.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
        except Exception:
            # If text is the same, Telegram raises an error, we can ignore it
            pass

@router.callback_query()
async def handle_all_callbacks(callback: types.CallbackQuery):
    """
    Universal handler for logging all button clicks.
    """
    action_type = None
    
    # Map callback data to ActionType enum
    if callback.data == "gastro_farm":
        action_type = ActionType.GASTRO_FARM
    elif callback.data == "leaderboard":
        action_type = ActionType.LEADERBOARD
    elif callback.data == "invite_friends":
        action_type = ActionType.INVITE_FRIENDS
    elif callback.data == "claim_farm_points":
        action_type = ActionType.GASTRO_FARM
    elif callback.data.startswith("how_it_works_"):
        action_type = ActionType.FAQ  # Reuse FAQ action type
    elif callback.data.startswith("onboard_"):
        # This is for onboarding, let it pass through to its own router
        return

    if action_type:
        with SessionLocal() as db:
            action_crud.log_action(db, callback.from_user.id, action_type)
        
        # If it was gastro_farm request from main menu
        if callback.data == "gastro_farm":
            await show_gastro_farm(callback)
            try:
                await callback.answer()
            except TelegramBadRequest:
                pass
            return
        
        elif callback.data == "claim_farm_points":
            with SessionLocal() as db:
                success, points = farm_crud.claim_farm_points(db, callback.from_user.id)
                try:
                    if success:
                        await callback.answer(f"✅ Вы забрали {points} баллов!", show_alert=True)
                        # Refresh the farm view
                        await show_gastro_farm(callback)
                    else:
                        stats = farm_crud.get_farm_stats(db, callback.from_user.id)
                        hours, remainder = divmod(stats["time_to_claim_seconds"], 3600)
                        minutes, _ = divmod(remainder, 60)
                        time_str = f"{hours}ч {minutes}м" if hours > 0 else f"{minutes}м"
                        await callback.answer(f"⏳ Награда будет доступна через {time_str}", show_alert=True)
                except TelegramBadRequest:
                    pass
            return

        elif callback.data == "leaderboard":
            with SessionLocal() as db:
                # Get user league info
                user_league = league_crud.join_league_group(db, callback.from_user.id)
                leaderboard = league_crud.get_leaderboard_data(db, user_league.group_id)
                time_left = get_time_until_reset()
                
                builder = InlineKeyboardBuilder()
                
                # Add leaderboard entries as buttons
                for i, entry in enumerate(leaderboard):
                    place = i + 1
                    medal = "🥇" if place == 1 else "🥈" if place == 2 else "🥉" if place == 3 else f"{place}."
                    is_current_user = not entry["is_bot"] and entry["id"] == callback.from_user.id
                    user_label = " (Вы)" if is_current_user else ""
                    
                    btn_text = f"{medal} {entry['name']}{user_label} — {int(entry['points'])} очков"
                    builder.row(types.InlineKeyboardButton(text=btn_text, callback_data=f"lb_user_{entry['id']}"))
                
                builder.row(types.InlineKeyboardButton(text="Назад", callback_data="back_to_main", icon_custom_emoji_id = "5877629862306385808"))
                
                league_name = user_league.league.value if hasattr(user_league.league, 'value') else user_league.league
                
                text = messages.LEADERBOARD_TITLE.format(
                    league_name=league_name,
                    time_left=time_left
                )
                
                await callback.message.edit_text(
                    text,
                    parse_mode="HTML",
                    reply_markup=builder.as_markup()
                )
                try:
                    await callback.answer()
                except TelegramBadRequest:
                    pass
            return

        elif callback.data.startswith("how_it_works_"):
            page = int(callback.data.split("_")[-1])
            
            current_page = messages.FAQ_PAGES.get(page)
            text = f'<a href="{current_page["img"]}">&#8203;</a>{current_page["text"]}'
            
            builder = InlineKeyboardBuilder()
            
            # Navigation row
            nav_buttons = []
            if page > 1:
                nav_buttons.append(types.InlineKeyboardButton(text="Назад", callback_data=f"how_it_works_{page-1}", icon_custom_emoji_id = "5375049032894819368"))
            if page < 3:
                nav_buttons.append(types.InlineKeyboardButton(text="Дальше", callback_data=f"how_it_works_{page+1}"))
            
            if nav_buttons:
                builder.row(*nav_buttons)
            
            # Back to menu row
            builder.row(types.InlineKeyboardButton(text="В меню", callback_data="back_to_main", icon_custom_emoji_id = "5877629862306385808"))
            
            await callback.message.edit_text(
                text=text,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
            try:
                await callback.answer()
            except TelegramBadRequest:
                pass
            return

        elif callback.data == "invite_friends":
            bot_info = await callback.bot.get_me()
            
            with SessionLocal() as db:
                user_league = league_crud.join_league_group(db, callback.from_user.id)
                league_mult = points_utils.get_league_multiplier(user_league.league)
                bonus_points = int(1500 * league_mult)
            
            text = messages.INVITE_TEXT.format(bonus_points=bonus_points)
            
            await callback.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=get_invite_keyboard(bot_info.username, callback.from_user.id)
            )
            try:
                await callback.answer()
            except TelegramBadRequest:
                pass
            return
    else:
        # Handle farm specific callbacks
        if callback.data.startswith("add_farm_"):
            parts = callback.data.split("_")
            hourly_income = float(parts[2])
            food_name = "_".join(parts[3:]) if len(parts) > 3 else "Еда"
            
            with SessionLocal() as db:
                farm_crud.add_to_farm_logic(db, callback.from_user.id, hourly_income, food_name=food_name)
                action_crud.log_action(db, callback.from_user.id, ActionType.GASTRO_FARM)
            
            await callback.message.edit_text(
                f"{callback.message.text}\n\n✅ <b>{messages.FARM_ADDED_SUCCESS}</b>",
                parse_mode="HTML"
            )
            try:
                await callback.answer("Успешно добавлено!")
            except TelegramBadRequest:
                pass
            
        elif callback.data == "cancel_farm":
            await callback.message.edit_reply_markup(reply_markup=None)
            try:
                await callback.answer("Действие отменено")
            except TelegramBadRequest:
                pass
        elif callback.data == "back_to_main":
            with SessionLocal() as db:
                user = user_crud.get_user_with_recharge(db, callback.from_user.id)
                if not user:
                    user = user_crud.create_user(
                        db, 
                        telegram_id=callback.from_user.id,
                        username=callback.from_user.username,
                        first_name=callback.from_user.first_name,
                        last_name=callback.from_user.last_name
                    )
                
                user_league = league_crud.join_league_group(db, callback.from_user.id)
                league_name = user_league.league.value if hasattr(user_league.league, 'value') else user_league.league
                
                attempts = user.analysis_attempts
                points = int(user.points)

                # Check for active multiplier
                active_mult = user_crud.get_active_multiplier(db, callback.from_user.id)
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
            try:
                await callback.answer()
            except TelegramBadRequest:
                pass
        else:
            try:
                await callback.answer()
            except TelegramBadRequest:
                pass

