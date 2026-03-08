from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from database import Database
from config import CHANNELS, DB_NAME 
from keyboards import get_rating_keyboard, get_episodes_kb

router = Router()

# Railway Volume yo'lini ko'rishi uchun configdagi DB_NAME ishlatiladi
db = Database(DB_NAME)

@router.message(CommandStart())
async def start_handler(message: Message):
    # Foydalanuvchini bazaga qo'shish
    await db.add_user(message.from_user.id, message.from_user.username)
    
    welcome_text = (
        f"👋 <b>Assalomu alaykum, {message.from_user.first_name}!</b>\n\n"
        "🎬 <b>KinoBot-ga xush kelibsiz!</b>\n\n"
        "Kinolarni yoki seriallarni ko'rish uchun <b>kodni</b> yuboring.\n\n"
        "📌 <i>Masalan: 505</i>\n\n"
        "🚀 <b>Marhamat, kodingizni kiriting:</b>"
    )
    await message.answer(welcome_text)

@router.callback_query(F.data == "check_subs")
async def verify_subscription(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    all_joined = True
    
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
        await callback.message.answer("Endi kodni qaytadan yuborishingiz mumkin. 🍿")
    else:
        await callback.answer("Siz hali barcha kanallarga a'zo bo'lmadingiz! ❌", show_alert=True)

@router.message(F.text.regexp(r'^\d+$')) 
async def movie_request(message: Message):
    code = message.text.strip()
    movie = await db.get_movie(code) # (file_id, caption, is_series) qaytaradi
    
    if movie:
        file_id, caption, is_series = movie
        
        if is_series:
            # SERIAL: Poster (rasm) va qismlar tugmalarini chiqarish
            episodes = await db.get_episodes(code)
            await message.answer_photo(
                photo=file_id,
                caption=f"🎬 <b>{caption}</b>\n\n🍿 Qismni tanlang:",
                reply_markup=get_episodes_kb(code, episodes)
            )
        else:
            # KINO: Videoning o'zini yuborish
            await message.answer_video(
                video=file_id, 
                caption=f"{caption}\n\n🎬 <b>Filmni baholang:</b>",
                reply_markup=get_rating_keyboard(code)
            )
    else:
        await message.answer(
            "❌ <b>Bunday kodli film yoki serial topilmadi.</b>\n"
            "Kodni to'g'ri kiritganingizni tekshiring."
        )

# Serial qismi tanlanganda videoni yuborish
@router.callback_query(F.data.startswith("ep_"))
async def handle_episode_request(callback: CallbackQuery):
    # Callback format: ep_CODE_PART
    _, movie_code, part_num = callback.data.split("_")
    
    # Bazadan videoning file_id sini olish uchun qismlarni qayta qidiramiz
    episodes = await db.get_episodes(movie_code)
    video_id = next((ep[1] for ep in episodes if str(ep[0]) == part_num), None)
    
    if video_id:
        await callback.message.answer_video(
            video=video_id,
            caption=f"🎬 {movie_code} - <b>{part_num}-qism</b>\n\nYoqimli tomosha!",
            reply_markup=get_rating_keyboard(movie_code)
        )
        await callback.answer()
    else:
        await callback.answer("⚠️ Kechirasiz, bu qism topilmadi.", show_alert=True)

@router.callback_query(F.data.startswith("rate_"))
async def handle_rating(callback: CallbackQuery):
    rating = callback.data.split("_")[1]
    movie_code = callback.data.split("_")[2]
    
    await db.add_rating(callback.from_user.id, movie_code, int(rating))
    await callback.answer(f"Rahmat! Siz {rating} ball berdingiz ⭐", show_alert=False)

@router.message(F.text)
async def non_code_request(message: Message):
    if not message.text.startswith("/"):
        await message.answer("⚠️ Iltimos, faqat kod (raqam) yuboring.")