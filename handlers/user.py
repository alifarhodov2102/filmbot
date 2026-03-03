from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from database import Database
# config dan CHANNELS va DB_NAME ni import qilamiz
from config import CHANNELS, DB_NAME 
from keyboards import get_rating_keyboard

router = Router()

# MUHIM: Bu yerda qat'iy ravishda config dagi DB_NAME ishlatilishi shart!
# Shunda u Railway Volume yo'lini (/app/data/...) ko'radi.
db = Database(DB_NAME)

@router.message(CommandStart())
async def start_handler(message: Message):
    # Foydalanuvchini bazaga qo'shish
    await db.add_user(message.from_user.id, message.from_user.username)
    
    welcome_text = (
        f"👋 <b>Assalomu alaykum, {message.from_user.first_name}!</b>\n\n"
        "🎬 <b>KinoBot-ga xush kelibsiz!</b>\n\n"
        "Kinolarni ko'rish uchun <b>kino kodini</b> (faqat raqam) yuboring.\n\n"
        "📌 <i>Masalan: 505</i>\n\n"
        "🚀 <b>Marhamat, kodingizni kiriting:</b>"
    )
    await message.answer(welcome_text)

@router.callback_query(F.data == "check_subs")
async def verify_subscription(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    all_joined = True
    
    # Foydalanuvchi barcha kanallarga a'zo bo'lganini tekshirish
    for channel_id in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                all_joined = False
                break
        except Exception:
            all_joined = False
            break

    if all_joined:
        await callback.answer("Tabriklaymiz, hamma kanallarga a'zo bo'ldingiz! ✅", show_alert=True)
        await callback.message.delete() 
        await callback.message.answer("Endi kino kodini qaytadan yuborishingiz mumkin. 🍿")
    else:
        await callback.answer("Siz hali barcha kanallarga a'zo bo'lmadingiz! ❌", show_alert=True)

@router.message(F.text.regexp(r'^\d+$')) 
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
    movie_code = callback.data.split("_")[2]
    
    # Reytingni bazaga saqlash
    await db.add_rating(callback.from_user.id, movie_code, int(rating))
    await callback.answer(f"Rahmat! Siz {rating} ball berdingiz ⭐", show_alert=False)

@router.message(F.text)
async def non_code_request(message: Message):
    if not message.text.startswith("/"):
        await message.answer("⚠️ Iltimos, faqat film kodini (raqam) yuboring.")
