from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command
from database import Database
from config import ADMINS

router = Router()
db = Database("bot_data.db")

@router.message(Command("admin"), F.from_user.id.in_(ADMINS))
async def admin_panel(message: Message):
    await message.answer(
        "🛠 <b>Admin Panel</b>\n\n"
        "1️⃣ Kino qo'shish: Videoga reply qilib <code>/add KOD</code> yuboring\n"
        "2️⃣ Kino o'chirish: <code>/del KOD</code> buyrug'ini yuboring\n"
        "3️⃣ Reklama: <code>/broadcast XABAR</code>\n"
        "4️⃣ Statistika: /stats"
    )

@router.message(Command("add"), F.from_user.id.in_(ADMINS))
async def add_movie_handler(message: Message):
    if not message.reply_to_message or not (message.reply_to_message.video or message.reply_to_message.document):
        return await message.answer("❌ Kinoni saqlash uchun videoga reply qiling!")
    
    parts = message.text.split()
    if len(parts) < 2:
        return await message.answer("❌ Kodni kiritishni unutdingiz. Masalan: <code>/add 505</code>")
        
    code = parts[1]
    file_id = message.reply_to_message.video.file_id if message.reply_to_message.video else message.reply_to_message.document.file_id
    caption = message.reply_to_message.caption or "Yoqimli tomosha!"
    
    await db.add_movie(code, file_id, caption)
    await message.answer(f"✅ Kino saqlandi! Kod: <code>{code}</code>")

@router.message(Command("del"), F.from_user.id.in_(ADMINS))
async def delete_movie_handler(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        return await message.answer("❌ O'chirish uchun kodni yozing. Masalan: <code>/del 505</code>")
    
    code = parts[1]
    await db.delete_movie(code)
    await message.answer(f"🗑 Kodi <code>{code}</code> bo'lgan film bazadan o'chirildi.")

@router.message(Command("stats"), F.from_user.id.in_(ADMINS))
async def stats_handler(message: Message):
    users = await db.get_all_users()
    await message.answer(f"📊 <b>Bot statistikasi:</b>\n\nJami foydalanuvchilar: {len(users)} ta")

@router.message(Command("broadcast"), F.from_user.id.in_(ADMINS))
async def broadcast_handler(message: Message, bot: Bot):
    text = message.text.replace("/broadcast ", "")
    if text == "/broadcast":
        return await message.answer("❌ Reklama matnini kiriting!")
        
    users = await db.get_all_users()
    count = 0
    
    for user_id in users:
        try:
            await bot.send_message(user_id, text)
            count += 1
        except:
            pass
    await message.answer(f"📢 Reklama {count} ta foydalanuvchiga yuborildi.")
