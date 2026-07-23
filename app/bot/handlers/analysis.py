from aiogram import Router, types, F, Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
import asyncio
import os
from app.services.ai_service import ai_service
from app.services.cloudinary_service import cloudinary_service
from app.database.connection import SessionLocal
from app.database.crud import user as user_crud
from app.database.crud import action as action_crud
from app.database.crud import photo as photo_crud
from app.database.crud import farm as farm_crud
from app.database.crud import push as push_crud
from app.database.models import ActionType
from app.utils.points import calculate_farm_income, calculate_new_farm_card_income
from app.utils.image_generator import generate_health_card
from app.utils.keyboards import get_start_inline_keyboard
import html
from datetime import datetime, timedelta
from app.core import messages

router = Router()

@router.message(F.photo)
async def handle_food_photo(message: types.Message, bot: Bot):
    """
    Handler for food photos.
    Downloads the image and sends it to AIService.
    """
    # 1. Check Limits
    with SessionLocal() as db:
        db_user = user_crud.get_user_with_recharge(db, message.from_user.id)
        if not db_user:
            db_user = user_crud.create_user(db, message.from_user.id, username=message.from_user.username)
            
        if db_user.analysis_attempts <= 0:
            time_left = user_crud.get_time_to_next_attempt(db_user)
            await message.answer(
                messages.LIMITS_REACHED.format(time_left=time_left),
                parse_mode="HTML"
            )
            return

    # 2. Proceed with analysis
    processing_msg = await message.answer(messages.ANALYSIS_PROCESSING)
    
    try:
        photo = message.photo[-1]
        
        # Get Telegram file link
        file = await bot.get_file(photo.file_id)
        telegram_link = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
        
        file_content = await bot.download(photo.file_id)
        image_bytes = file_content.read()
        
        ai_result = await ai_service.analyze_food_image(image_bytes)
        
        if ai_result.get("error"):
            await processing_msg.edit_text(
                messages.ANALYSIS_ERROR,
                parse_mode="HTML"
            )
            return

        if not ai_result.get("is_food"):
            await processing_msg.edit_text(
                messages.ANALYSIS_NOT_FOOD.format(comment=ai_result.get('comment')),
                parse_mode="HTML"
            )
            # Deduct attempt even if it's not food
            # with SessionLocal() as db:
            #     user_crud.use_analysis_attempt(db, message.from_user.id)
            return

        # 3. Process results and prepare response
        # Calculate farm card income ONCE (with luck) using current active cards
        with SessionLocal() as db:
            active_cards = farm_crud.get_user_cards(db, message.from_user.id, only_active=True)
        
        farm_card_income = calculate_new_farm_card_income(active_cards)
        
        # Generate and upload health card image
        score = ai_result.get("food_score", 0)
        temp_img_path = f"temp_card_{message.from_user.id}_{int(datetime.now().timestamp())}.png"
        image_url = ""
        try:
            generate_health_card(f"{score}/100", output_path=temp_img_path)
            image_url = await cloudinary_service.upload_image(temp_img_path)
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)
        except Exception as e:
            import logging
            logging.error(f"Image gen/upload error: {e}")

        with SessionLocal() as db:
            # Check for active multiplier
            active_mult = user_crud.get_active_multiplier(db, message.from_user.id)
            multiplier_val = active_mult.multiplier if active_mult else 1.0
            
            # Store multiplier info for later use outside session
            mult_id_to_consume = active_mult.id if active_mult and active_mult.uses_left is not None else None
            
            analysis_record, point_data = photo_crud.log_photo_analysis(
                db, 
                message.from_user.id, 
                ai_result, 
                file_path=image_url or telegram_link, # Use Cloudinary URL if available
                multiplier=multiplier_val
            )
            
            final_points = point_data['total']
            luck_mult = point_data.get('luck_multiplier', 1.0)
            action_crud.log_action(db, message.from_user.id, ActionType.PHOTO_ANALYSIS)
            analysis_id = analysis_record.id
        
        # Step 1: Simple text results
        bonus_text = f" (x{int(multiplier_val)} бонус!) 🐥" if multiplier_val > 1.0 else ""
        jackpot_text = f" (ты урвал x{int(luck_mult)} джекпот)" if luck_mult > 1.0 else ""
        
        response_text = messages.ANALYSIS_RESULTS.format(
            image_url=image_url or "https://i.ibb.co/SwVQtQCx/Main-v1.png", # Fallback
            comment=ai_result['comment'],
            final_points=int(final_points),
            jackpot_text=jackpot_text,
            bonus_text=bonus_text
        )
        
        builder = InlineKeyboardBuilder()
        callback_data = f"analysis_step2|{analysis_id}|{farm_card_income}"
        builder.row(types.InlineKeyboardButton(text="Продолжить", callback_data=callback_data))
        
        try:
            await processing_msg.edit_text(response_text, parse_mode="HTML", reply_markup=builder.as_markup())
            # ONLY consume attempt and multiplier if message was sent successfully
            with SessionLocal() as db:
                user_crud.use_analysis_attempt(db, message.from_user.id)
                # If multiplier was usage-based, decrement it
                if mult_id_to_consume:
                    user_crud.consume_multiplier_use(db, mult_id_to_consume)
                
                # Auto-assign meal time based on photo (non-priority variant)
                push_crud.auto_assign_meal_time(db, message.from_user.id, datetime.now())
        except Exception as e:
            # If telegram fails to send the result (e.g. parsing error), we don't count the attempt
            import logging
            logging.error(f"Telegram send error: {e}")
            await processing_msg.edit_text(
                messages.ANALYSIS_ERROR,
                parse_mode="HTML"
            )
        
    except Exception as e:
        import logging
        logging.error(f"General analysis error: {e}")
        await processing_msg.edit_text(
            messages.ANALYSIS_ERROR,
            parse_mode="HTML"
        )

@router.callback_query(F.data.startswith("analysis_step2"))
async def show_farm_card_step(callback: types.CallbackQuery):
    """
    Step 2: Show farm card details and slot selection.
    """
    parts = callback.data.split("|")
    analysis_id = int(parts[1])
    farm_card_income = float(parts[2])
    
    with SessionLocal() as db:
        from app.database.models import PhotoAnalysis
        analysis = db.query(PhotoAnalysis).filter(PhotoAnalysis.id == analysis_id).first()
        if not analysis:
            try:
                await callback.answer("Ошибка: данные не найдены")
            except TelegramBadRequest:
                pass
            return
            
        import json
        ai_result = json.loads(analysis.result_text)
        
        # Recalculate income (or we could have stored it)
        income = farm_card_income
        food = ai_result.get('food_name', 'Еда')
    
    text = messages.FARM_CARD_INFO.format(
        food=food,
        income=income
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Положить в гастроферму", callback_data=f"farm_slots|{analysis_id}|{farm_card_income}",icon_custom_emoji_id="5472178859300363509"))
    builder.row(types.InlineKeyboardButton(text="Пропустить", callback_data="back_to_main"))
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass

@router.callback_query(F.data.startswith("farm_slots"))
async def select_farm_slot(callback: types.CallbackQuery):
    """
    Step 3: Select specific slot to add/replace.
    """
    parts = callback.data.split("|")
    analysis_id = int(parts[1])
    farm_card_income = float(parts[2])
    
    with SessionLocal() as db:
        active_cards = farm_crud.get_user_cards(db, callback.from_user.id, only_active=True)
    
    builder = InlineKeyboardBuilder()
    for i in range(3):
        if i < len(active_cards):
            card = active_cards[i]
            btn_text = f"{card.food_name} ({card.points_per_hour}/ч)"
            icon_emoji_id = "5845943483382110702"
        else:
            btn_text = "Добавить сюда"
            icon_emoji_id = "5877307202888273539"
        
        builder.row(types.InlineKeyboardButton(
            text=btn_text, 
            callback_data=f"confirm_farm|{i}|{analysis_id}|{farm_card_income}",
            icon_custom_emoji_id = icon_emoji_id
        ))
    
    builder.row(types.InlineKeyboardButton(text="Назад", callback_data=f"analysis_step2|{analysis_id}", icon_custom_emoji_id="5375049032894819368"))
    
    await callback.message.edit_text(
        text=messages.FARM_SLOT_SELECT,
        reply_markup=builder.as_markup()
    )
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
@router.callback_query(F.data.startswith("confirm_farm"))
async def confirm_farm_addition(callback: types.CallbackQuery):
    """
    Final step: Save to DB and return to main menu.
    """
    parts = callback.data.split("|")
    slot_idx = int(parts[1])
    analysis_id = int(parts[2])
    farm_card_income = float(parts[3])
    
    with SessionLocal() as db:
        from app.database.models import PhotoAnalysis
        analysis = db.query(PhotoAnalysis).filter(PhotoAnalysis.id == analysis_id).first()
        if not analysis:
            try:
                await callback.answer("Ошибка: данные не найдены")
            except TelegramBadRequest:
                pass
            return
            
        import json
        ai_result = json.loads(analysis.result_text)
        food = ai_result.get('food_name', 'Еда')
        
        income = farm_card_income

        farm_crud.add_to_farm_logic(db, callback.from_user.id, income, food_name=food, slot_idx=slot_idx)
         
        try:
            await callback.answer(messages.FARM_ADDED_SUCCESS)
        except TelegramBadRequest:
            pass
        
        # Show main menu
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
        from app.database.crud import push as push_crud
        user_league = league_crud.join_league_group(db, callback.from_user.id)
        league_name = user_league.league.value if hasattr(user_league.league, 'value') else user_league.league
        
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

        # Onboarding x3/x4 offer logic
        schedule = push_crud.get_push_schedule(db, callback.from_user.id)
        manual_meals_count = 0
        if schedule:
            if schedule.meal_1_manual: manual_meals_count += 1
            if schedule.meal_2_manual: manual_meals_count += 1
            if schedule.meal_3_manual: manual_meals_count += 1
        
        has_offer = False
        if manual_meals_count < 3:
            has_offer = True

        response_text = messages.MAIN_MENU.format(
            attempts=user.analysis_attempts,
            points=int(user.points),
            league_name=league_name,
            multiplier_text=multiplier_text
        )
        
        # Now we can just edit_text because it's always a text message (with a hidden image link)
        await callback.message.edit_text(
            text=response_text,
            parse_mode="HTML",
            reply_markup=get_start_inline_keyboard()
        )

        if has_offer:
            async def delayed_offer(m_count, msg):
                await asyncio.sleep(20)
                # Send separate message for the bonus offer
                multiplier = 3 if m_count == 1 else 4
                if m_count >= 2: multiplier = 5 # Example for 3rd meal if you want
                
                offer_text = messages.OFFER_GENERIC.format(multiplier=multiplier)
                builder = InlineKeyboardBuilder()
                builder.row(types.InlineKeyboardButton(text="Давай", callback_data=f"onboard_start|{multiplier}"))
                
                try:
                    await msg.answer(offer_text, parse_mode="HTML", reply_markup=builder.as_markup())
                except Exception as e:
                    import logging
                    logging.error(f"Error sending delayed x{multiplier} offer: {e}")

            asyncio.create_task(delayed_offer(manual_meals_count, callback.message))
