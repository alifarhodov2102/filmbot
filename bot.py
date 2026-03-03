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

# 1. Ma'lumotlar bazasini global darajada e'lon qilish
# Bu obyekt handlerlar va middleware-larda ishlatiladi
db = Database(DB_NAME)

async def main():
    # 2. Loggingni sozlash (Konsolda jarayonlarni kuzatish uchun)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    
    # 3. MA'LUMOTLAR BAZASI JADVALLARINI YARATISH
    # Bu qator polling boshlanishidan OLDIN bajarilishi shart.
    # U Railway Volume ichidagi bazada jadvallar borligini tekshiradi va yo'q bo'lsa yaratadi.
    logging.info("Ma'lumotlar bazasi jadvallari tekshirilmoqda...")
    await db.create_tables()
    logging.info("Baza tayyor!")
    
    # 4. Bot va Dispatcherni ishga tushirish
    bot = Bot(
        token=BOT_TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # 5. Middleware-larni ro'yxatdan o'tkazish
    # Bu qism foydalanuvchi kino kodini yuborganda obunani tekshiradi
    dp.message.outer_middleware(SubscriptionMiddleware())

    # 6. Routerni ulash (Tartib juda muhim: Admin birinchi, keyin User)
    dp.include_router(admin.router)
    dp.include_router(user.router)

    # 7. Eski kutilayotgan xabarlarni tozalash
    await bot.delete_webhook(drop_pending_updates=True)
    
    print("🚀 Bot muvaffaqiyatli ishga tushdi va 24/7 rejimida ishlamoqda...")
    
    try:
        # 8. Pollingni boshlash
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Polling davomida xatolik yuz berdi: {e}")
    finally:
        # Bot to'xtaganda ulanishni yopish
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot foydalanuvchi tomonidan to'xtatildi!")
