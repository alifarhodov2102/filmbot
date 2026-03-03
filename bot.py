import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Maxsus modullarni import qilish
from config import BOT_TOKEN, DB_NAME
from database import Database
from middlewares import SubscriptionMiddleware
from handlers import admin, user

# Ma'lumotlar bazasini global darajada e'lon qilish
db = Database(DB_NAME)

async def main():
    # 1. Loggingni sozlash (Konsolda jarayonlarni kuzatish uchun)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    
    # 2. Ma'lumotlar bazasi jadvallarini yaratish
    # Bu qator OperationalError: no such table xatosini butunlay yo'qotadi
    await db.create_tables()
    
    # 3. Bot va Dispatcherni ishga tushirish
    bot = Bot(
        token=BOT_TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # 4. Middleware-larni ro'yxatdan o'tkazish
    # Obunani tekshirish har bir xabardan oldin ishlaydi
    dp.message.outer_middleware(SubscriptionMiddleware())

    # 5. Routerni ulash (Tartib muhim: Admin birinchi, keyin User)
    dp.include_router(admin.router)
    dp.include_router(user.router)

    # 6. Eski xabarlarni (updates) tozalash va pollingni boshlash
    await bot.delete_webhook(drop_pending_updates=True)
    
    print("🚀 Bot muvaffaqiyatli ishga tushdi va 24/7 rejimida ishlamoqda...")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot ishdan to'xtatildi!")
