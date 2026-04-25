from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from database import Database
from config import CHANNELS, DB_NAME 
from keyboards import get_rating_keyboard, get_episodes_kb, get_movie_kb

router = Router()
db = Database(DB_NAME)

@router.message(CommandStart())
async def start_handler(message: Message):
    """Foydalanuvchini ro'yxatga olish va kutib olish."""
    await db.add_user(message.from_user.id, message.from_user.username)
    
    welcome_text = (
        f"👋 <b>Assalomu alaykum, {message.from_user.first_name}!</b>\n\n"
        "🎬 <b>KinoBot-ga xush kelibsiz!</b>\n\n"
        "Kino yoki serial ko'rish uchun <b>kodni</b> yuboring.\n"
        "🚀 <b>Marhamat, kodingizni kiriting:</b>"
    )
    await message.answer(welcome_text)

# --- SAHIFALASH (PAGINATION) HANDLER ---

@router.callback_query(F.data.startswith("pg_"))
async def handle_pagination(callback: CallbackQuery):
    """Serial qismlari sahifasini yangilash."""
    _, movie_code, page = callback.data.split("_")
    page = int(page)
    
    episodes = await db.get_episodes(movie_code)
    
    if episodes:
        await callback.message.edit_reply_markup(
            reply_markup=get_episodes_kb(movie_code, episodes, page)
        )
    await callback.answer()

@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    """Hech narsa qilmaydigan tugmalar uchun."""
    await callback.answer()

# --- SHAXSIY TO'PLAM (/my) ---

@router.message(Command("my"))
async def my_movies_handler(message: Message):
    favorites = await db.get_favorites(message.from_user.id)
    
    if not favorites:
        return await message.answer(
            "📭 <b>Sizning to'plamingiz bo'sh.</b>\n\n"
            "Kinolarni ❤️ tugmasi orqali saqlashingiz mumkin."
        )
    
    text = "❤️ <b>Siz saqlagan kinolar ro'yxati:</b>\n\n"
    for code in favorites:
        text += f"🎬 Kino kodi: <code>{code}</code>\n"
    
    text += "\n🍿 <i>Ko'rish uchun kodni yuboring!</i>"
    await message.answer(text)

# --- KLAVIATURA BOSHQARUVI ---

@router.callback_query(F.data == "close_msg")
async def close_message(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()

@router.callback_query(F.data.startswith("show_rate_"))
async def show_rating_options(callback: CallbackQuery):
    movie_code = callback.data.split("_")[2]
    await callback.message.edit_reply_markup(
        reply_markup=get_rating_keyboard(movie_code)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("back_to_movie_"))
async def back_to_main_kb(callback: CallbackQuery):
    movie_code = callback.data.split("_")[3]
    movie = await db.get_movie(movie_code)
    
    if movie and movie[2]: # Serial bo'lsa
        episodes = await db.get_episodes(movie_code)
        kb = get_episodes_kb(movie_code, episodes, page=0)
    else:
        kb = get_movie_kb(movie_code)
        
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()

# --- KINO SO'ROVI ---

@router.message(F.text.regexp(r'^\d+$')) 
async def movie_request(message: Message):
    code = message.text.strip()
    movie = await db.get_movie(code) 
    
    if movie:
        file_id, caption, is_series = movie
        
        if is_series:
            episodes = await db.get_episodes(code)
            await message.answer_photo(
                photo=file_id,
                caption=f"🎬 <b>{caption}</b>\n\n🍿 Qismni tanlang:",
                reply_markup=get_episodes_kb(code, episodes, page=0)
            )
        else:
            await message.answer_video(
                video=file_id, 
                caption=caption,
                reply_markup=get_movie_kb(code)
            )
    else:
        await message.answer("❌ <b>Bunday kodli film yoki serial topilmadi.</b>")

@router.callback_query(F.data.startswith("ep_"))
async def handle_episode_request(callback: CallbackQuery):
    _, movie_code, part_num = callback.data.split("_")
    episodes = await db.get_episodes(movie_code)
    video_id = next((ep[1] for ep in episodes if str(ep[0]) == part_num), None)
    
    if video_id:
        await callback.message.answer_video(
            video=video_id,
            caption=f"🎬 {movie_code} - <b>{part_num}-qism</b>",
            reply_markup=get_movie_kb(movie_code)
        )
        await callback.answer()
    else:
        await callback.answer("⚠️ Qism topilmadi.", show_alert=True)

# --- REYTING VA FAVORITES ---

@router.callback_query(F.data.startswith("rate_"))
async def handle_rating(callback: CallbackQuery):
    rating = callback.data.split("_")[1]
    movie_code = callback.data.split("_")[2]
    
    await db.add_rating(callback.from_user.id, movie_code, int(rating))
    
    movie = await db.get_movie(movie_code)
    if movie[2]:
        episodes = await db.get_episodes(movie_code)
        kb = get_episodes_kb(movie_code, episodes, page=0)
    else:
        kb = get_movie_kb(movie_code)
    
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer(f"Rahmat! Siz {rating} ball berdingiz ⭐")

@router.callback_query(F.data.startswith("fav_add_"))
async def handle_favorites_addition(callback: CallbackQuery):
    movie_code = callback.data.split("_")[2]
    await db.add_to_favorites(callback.from_user.id, movie_code)
    await callback.answer("✅ To'plamga qo'shildi!", show_alert=True)

# --- OBUNA TEKSHIRUV ---

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
        await callback.answer("✅ Hamma kanallarga a'zo bo'ldingiz!", show_alert=True)
        await callback.message.delete() 
        await callback.message.answer("Endi kodni qaytadan yuborishingiz mumkin. 🍿")
    else:
        await callback.answer("❌ Siz hali barcha kanallarga a'zo bo'lmadingiz!", show_alert=True)

@router.message(F.text)
async def non_code_request(message: Message):
    if not message.text.startswith("/"):
        await message.answer("⚠️ Iltimos, faqat kod (raqam) yuboring.")
