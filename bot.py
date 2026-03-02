import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Import our custom modules
from config import BOT_TOKEN, DB_NAME
from database import Database
from middlewares import SubscriptionMiddleware
from handlers import admin, user

async def main():
    # Setup logging to see what's happening in the console
    logging.basicConfig(level=logging.INFO)
    
    # Initialize Bot and Dispatcher
    # DefaultBotProperties ensures all messages can use HTML formatting
    bot = Bot(
        token=BOT_TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # 1. Initialize Database Tables
    db = Database(DB_NAME)
    await db.create_tables()

    # 2. Register Middlewares
    # This checks subscription BEFORE any handler is called
    dp.message.outer_middleware(SubscriptionMiddleware())

    # 3. Register Routers (Order matters: Admin first, then User)
    dp.include_router(admin.router)
    dp.include_router(user.router)

    # 4. Remove old updates and start listening
    await bot.delete_webhook(drop_pending_updates=True)
    print("🚀 Bot is running 24/7...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
        