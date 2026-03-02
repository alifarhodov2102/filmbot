from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from database import Database

router = Router()
db = Database("bot_data.db")

@router.message(CommandStart())
async def start_handler(message: Message):
    # Foydalanuvchini bazaga qo'shish (Ads/Broadcast uchun)
    await db.add_user(message.from_user.id, message.from_user.username)
    
    welcome_text = (
        f"👋 <b>Assalomu alaykum, {message.from_user.first_name}!</b>\n\n"
        "🎬 <b>KinoBot-ga xush kelibsiz!</b>\n\n"
        "Bu yerda siz eng so'nggi va eng sara filmlarni topishingiz mumkin. "
        "Kinolarni ko'rish uchun <b>kino kodini</b> yuboring.\n\n"
        "📌 <i>Masalan: 505</i>\n\n"
        "🚀 <b>Marhamat, kodingizni kiriting:</b>"
    )
    
    await message.answer(welcome_text)

@router.message(F.text)
async def movie_request(message: Message):
    code = message.text.strip()
    movie = await db.get_movie(code)
    
    if movie:
        file_id, caption = movie
        await message.answer_video(video=file_id, caption=caption)
    else:
        await message.answer(
            "❌ <b>Kechirasiz, bunday kod topilmadi.</b>\n\n"
            "Iltimos, kodni to'g'ri kiritganingizni tekshirib ko'ring yoki "
            "kanaldan yangi kodlarni qidiring!"
        )
