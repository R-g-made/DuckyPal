import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from app.core.config import settings
from app.utils.logger import logger
from app.bot.handlers import start, analysis, menu, onboarding
from app.bot.handlers import start, analysis, menu, onboarding
from app.bot.middlewares.last_seen import LastSeenMiddleware
from app.database.connection import engine, Base
from app.services.push_worker import check_and_send_pushes

async def main():
    # Fix for Windows asyncio loop issues
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Initialize database
    Base.metadata.create_all(bind=engine)

    # Simple Bot initialization
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    dp = Dispatcher()

    # Register routers
    dp.include_router(onboarding.router)
    dp.include_router(start.router)
    dp.include_router(analysis.router)
    dp.include_router(menu.router)

    # Register middlewares
    dp.update.middleware(LastSeenMiddleware())

    # Start push worker in background
    asyncio.create_task(check_and_send_pushes(bot))

    # Start polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
