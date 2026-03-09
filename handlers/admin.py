from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database
from config import ADMINS, DB_NAME
from keyboards import series_confirm_kb, admin_menu 

router = Router()
db = Database(DB_NAME)

# Serial qo'shish bosqichlari (FSM States)
class MovieAdd(StatesGroup):
    waiting_for_type = State()     # Anime yoki Serial tanlash
    waiting_for_poster = State()   # Poster (rasm) yuklash
    waiting_for_caption = State()  # Ta'rif yozish
    waiting_for_episodes = State() # Serial qismlarini bittalab yuborish

@router.message(Command("admin"), F.from_user.id.in_(ADMINS))
async def admin_panel(message: Message):
    """Admin boshqaruv paneli menyusi."""
    await message.answer(
        "🛠 <b>Admin Boshqaruv Paneli</b>\n\n"
        "1️⃣ <b>Qo'shish:</b> <code>/add KOD</code>\n"
        "2️⃣ <b>To'liq o'chirish:</b> <code>/del KOD</code>\n"
        "3️⃣ <b>Qismni o'chirish:</b> <code>/delpart KOD QISM</code>\n"
        "4️⃣ <b>Statistika:</b> <code>/stats</code>\n"
        "5️⃣ <b>Reklama:</b> <code>/broadcast XABAR</code>",
        reply_markup=admin_menu()
    )

@router.message(Command("add"), F.from_user.id.in_(ADMINS))
async def add_start(message: Message, state: FSMContext, command: CommandObject):
    """Yangi anime qo'shish jarayonini boshlash."""
    if not command.args:
        return await message.answer("❌ Kodni kiriting! Masalan: <code>/add 1</code>")
    
    code = command.args.strip()
    
    if not code.isdigit():
        return await message.answer("⚠️ <b>Xato!</b> Kod faqat raqamlardan iborat bo'lishi kerak.")
    
    await state.update_data(movie_code=code)
    await message.answer(
        f"Kodi: <b>{code}</b>\nBu yuklama turini tanlang:",
        reply_markup=series_confirm_kb()
    )
    await state.set_state(MovieAdd.waiting_for_type)

# --- SERIAL (ANIME) QO'SHISH BOSQICHLARI ---

@router.callback_query(F.data == "type_series", MovieAdd.waiting_for_type)
async def process_series_type(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_series=1)
    await callback.message.edit_text("🖼 Serial uchun <b>Muqova (Poster)</b> rasmini yuboring:")
    await state.set_state(MovieAdd.waiting_for_poster)

@router.message(MovieAdd.waiting_for_poster, F.photo)
async def process_poster(message: Message, state: FSMContext):
    await state.update_data(poster_id=message.photo[-1].file_id)
    await message.answer("✍️ Serial haqida <b>ta'rif (caption)</b> yuboring:")
    await state.set_state(MovieAdd.waiting_for_caption)

@router.message(MovieAdd.waiting_for_caption)
async def process_caption(message: Message, state: FSMContext):
    data = await state.get_data()
    # Asosiy ma'lumotni bazaga saqlaymiz
    await db.add_movie(data['movie_code'], data['poster_id'], message.text, 1)
    
    await state.update_data(ep_count=0)
    await message.answer(
        "✅ Serial asosi yaratildi!\n\nEndi <b>1-qismni (video)</b> yuboring.\n"
        "Tugagach <b>/finish</b> buyrug'ini yuboring."
    )
    await state.set_state(MovieAdd.waiting_for_episodes)

@router.message(MovieAdd.waiting_for_episodes, F.video)
async def process_episode(message: Message, state: FSMContext):
    data = await state.get_data()
    new_count = data['ep_count'] + 1
    
    await db.add_episode(data['movie_code'], new_count, message.video.file_id)
    await state.update_data(ep_count=new_count)
    await message.answer(f"✅ {new_count}-qism saqlandi! Keyingisini yuboring yoki /finish bosing.")

@router.message(Command("finish"), MovieAdd.waiting_for_episodes)
async def process_finish(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🚀 Barcha qismlar muvaffaqiyatli saqlandi!")

# --- ODDIY VIDEO QO'SHISH ---

@router.callback_query(F.data == "type_movie", MovieAdd.waiting_for_type)
async def process_movie_type(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_series=0)
    await callback.message.edit_text("🎞 Videoni (faylni) yuboring:")
    await state.set_state(MovieAdd.waiting_for_poster) 

@router.message(MovieAdd.waiting_for_poster, F.video)
async def process_movie_video(message: Message, state: FSMContext):
    data = await state.get_data()
    caption = message.caption or "Yoqimli tomosha!"
    await db.add_movie(data['movie_code'], message.video.file_id, caption, 0)
    await state.clear()
    await message.answer(f"✅ Video saqlandi! Kodi: <code>{data['movie_code']}</code>")

# --- O'CHIRISH VA BOSHQARUV ---

@router.message(Command("del"), F.from_user.id.in_(ADMINS))
async def delete_movie_handler(message: Message, command: CommandObject):
    """Butun boshli kodni (anime/kino) o'chirish."""
    if not command.args:
        return await message.answer("❌ Kodni yozing. Masalan: <code>/del 1</code>")
    
    code = command.args.strip()
    await db.delete_movie(code)
    await message.answer(f"🗑 Kodi <code>{code}</code> bo'lgan barcha ma'lumotlar o'chirildi.")

@router.message(Command("delpart"), F.from_user.id.in_(ADMINS))
async def delete_part_handler(message: Message, command: CommandObject):
    """Faqat bitta qismni o'chirish va raqamlarni reset qilish."""
    if not command.args or len(command.args.split()) < 2:
        return await message.answer("❌ Format: <code>/delpart KOD QISM</code>\nMasalan: <code>/delpart 1 5</code>")
    
    try:
        args = command.args.split()
        code, part = args[0], int(args[1])
        await db.delete_episode(code, part)
        await message.answer(f"✅ {code}-kodli animening {part}-qismi o'chirildi va qolganlari qayta tartiblandi.")
    except ValueError:
        await message.answer("⚠️ Qism raqami butun son bo'lishi kerak!")

@router.message(Command("stats"), F.from_user.id.in_(ADMINS))
async def stats_handler(message: Message):
    u_count, m_count = await db.get_stats()
    await message.answer(f"📊 <b>Statistika:</b>\n👤 Foydalanuvchilar: {u_count}\n🎬 Animelar: {m_count}")

@router.message(Command("broadcast"), F.from_user.id.in_(ADMINS))
async def broadcast_handler(message: Message, bot: Bot):
    text = message.text.replace("/broadcast ", "")
    if text == "/broadcast" or not text.strip():
        return await message.answer("❌ Reklama matnini yozing!")
        
    users = await db.get_all_users()
    count = 0
    for user_id in users:
        try:
            await bot.send_message(user_id, text)
            count += 1
        except:
            continue
    await message.answer(f"📢 Reklama {count} ta foydalanuvchiga yuborildi.")