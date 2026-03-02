from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from database import Database
from keyboards import get_rating_keyboard

router = Router()
db = Database("bot_data.db")

@router.message(CommandStart())
async def start_handler(message: Message):
    await db.add_user(message.from_user.id, message.from_user.username)
    
    welcome_text = (
        f"👋 <b>Assalomu alaykum, {message.from_user.first_name}!</b>\n\n"
        "🎬 <b>KinoBot-ga xush kelibsiz!</b>\n\n"
        "Kinolarni ko'rish uchun <b>kino kodini</b> yuboring.\n\n"
        "📌 <i>Masalan: 505</i>\n\n"
        "🚀 <b>Marhamat, kodingizni kiriting:</b>"
    )
    await message.answer(welcome_text)

@router.callback_query(F.data == "check_subs")
async def verify_subscription(callback: CallbackQuery):
    # MUHIM: Cheksiz yuklanishni (loading) to'xtatish uchun answer() shart
    await callback.answer("Tekshirildi ✅") 
    await callback.message.answer("A'zolik tasdiqlandi! Endi kino kodini yuborishingiz mumkin. 🍿")
    await callback.message.delete()

@router.message(F.text.regexp(r'^\d+$')) # Faqat raqamlardan iborat xabarlarga javob beradi
async def movie_request(message: Message):
    code = message.text.strip()
    movie = await db.get_movie(code)
    
    if movie:
        file_id, caption = movie
        await message.answer_video(
            video=file_id, 
            caption=f"{caption}\n\n🎬 <b>Filmni baholang:</b>",
            reply_markup=get_rating_keyboard(code)
        )
    else:
        await message.answer(
            "❌ <b>Bunday kodli film topilmadi.</b>\n"
            "Kodni to'g'ri kiritganingizni tekshiring."
        )

@router.callback_query(F.data.startswith("rate_"))
async def handle_rating(callback: CallbackQuery):
    rating = callback.data.split("_")[1]
    # Hozircha shunchaki rahmat aytadi, xohlasangiz bazaga saqlash mantiqini qo'shish mumkin
    await callback.answer(f"Rahmat! Siz {rating} ball berdingiz ⭐", show_alert=False)

# Raqam bo'lmagan matnlarga javob (ixtiyoriy)
@router.message(F.text)
async def non_code_request(message: Message):
    if not message.text.startswith("/"):
        await message.answer("⚠️ Iltimos, faqat film kodini (raqam) yuboring.")
