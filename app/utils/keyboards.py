from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CopyTextButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_invite_keyboard(bot_username: str, telegram_id: int) -> InlineKeyboardMarkup:
    """
    Keyboard for Invite Friends section.
    """
    builder = InlineKeyboardBuilder()
    
    ref_link = f"https://t.me/{bot_username}?start={telegram_id}"
    share_url = f"https://t.me/share/url?url={ref_link}&text=Присоединяйся к UtyaPal и начни контролировать свое питание вместе со мной!"
    
    builder.row(InlineKeyboardButton(text="Поделиться", url=share_url, icon_custom_emoji_id = "5201990176175299013"))
    builder.row(InlineKeyboardButton(
        text="Скопировать ссылку", 
        copy_text=CopyTextButton(text=ref_link)
    ))
    builder.row(InlineKeyboardButton(text="Назад", callback_data="back_to_main", icon_custom_emoji_id = "5877629862306385808"))
    
    return builder.as_markup()

def get_start_inline_keyboard() -> InlineKeyboardMarkup:
    """
    Creates the main menu inline keyboard for /start command.
    Layout:
    1. Гастро-ферма
    2. Лидерборд
    3. Магазин
    4. Пригласить друзей
    5. Faq | Поддержка (2 in row)
    """
    builder = InlineKeyboardBuilder()
    
    # Single row buttons
    builder.row(types.InlineKeyboardButton(text="Гастро-ферма", callback_data="gastro_farm", icon_custom_emoji_id="5472178859300363509"))
    builder.row(types.InlineKeyboardButton(text="Лидерборд", callback_data="leaderboard", icon_custom_emoji_id="5190428893013615098"))
    builder.row(types.InlineKeyboardButton(text="Магазин", callback_data="shop_main", icon_custom_emoji_id="5193065010795911968"))
    builder.row(types.InlineKeyboardButton(text="Пригласить друзей", callback_data="invite_friends", icon_custom_emoji_id="5395357957552609518",style="primary"))
    
    # Two buttons in one row
    builder.row(
        InlineKeyboardButton(text="Как это работает?", callback_data="how_it_works_1", style="primary"),
        InlineKeyboardButton(text="Поддержка", url="https://t.me/real_glory")
    )
    
    return builder.as_markup()
