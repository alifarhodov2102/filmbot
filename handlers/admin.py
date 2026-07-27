import asyncio
import logging

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import (
    TelegramForbiddenError,
    TelegramBadRequest,
    TelegramRetryAfter,
)

from database import Database
from config import ADMINS, DB_NAME
from keyboards import series_confirm_kb, admin_menu


router = Router()
db = Database(DB_NAME)

logger = logging.getLogger(__name__)


# =========================================================
# FSM STATES
# =========================================================

class MovieAdd(StatesGroup):
    waiting_for_type = State()
    waiting_for_poster = State()
    waiting_for_caption = State()
    waiting_for_episodes = State()


class BroadcastState(StatesGroup):
    waiting_for_message = State()


# =========================================================
# YORDAMCHI FUNKSIYALAR
# =========================================================

def is_admin(user_id: int) -> bool:
    """
    Foydalanuvchi admin ekanini tekshiradi.
    """
    return user_id in ADMINS


async def send_stats(target: Message):
    """
    Admin statistikasini chiqaradi.
    """
    stats = await db.get_detailed_stats()

    await target.answer(
        "📊 <b>Bot statistikasi</b>\n\n"
        f"👤 Foydalanuvchilar: <b>{stats['users']}</b>\n"
        f"🎬 Animelar: <b>{stats['movies']}</b>\n"
        f"🎞 Serial qismlari: <b>{stats['episodes']}</b>\n"
        f"❤️ Saqlanganlar: <b>{stats['favorites']}</b>\n"
        f"⭐ Baholar: <b>{stats['ratings']}</b>"
    )


async def distribute_message(
    bot: Bot,
    source_message: Message,
    admin_chat_id: int
):
    """
    Admin yuborgan xabarni barcha foydalanuvchilarga tarqatadi.

    copy_message ishlatilgani sababli quyidagilarni tarqata oladi:
    - matn;
    - rasm;
    - video;
    - animatsiya;
    - audio;
    - hujjat;
    - sticker;
    - boshqa Telegram xabar turlari.
    """
    users = await db.get_all_users()

    total = len(users)
    success_count = 0
    failed_count = 0
    blocked_count = 0

    status_message = await bot.send_message(
        admin_chat_id,
        "📢 Reklama tarqatish boshlandi...\n\n"
        f"👤 Jami foydalanuvchilar: <b>{total}</b>"
    )

    for index, user_id in enumerate(users, start=1):
        try:
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=source_message.chat.id,
                message_id=source_message.message_id
            )

            success_count += 1

        except TelegramRetryAfter as error:
            # Telegram flood limit bersa, kerakli vaqt kutamiz
            await asyncio.sleep(error.retry_after)

            try:
                await bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=source_message.chat.id,
                    message_id=source_message.message_id
                )
                success_count += 1

            except TelegramForbiddenError:
                blocked_count += 1

            except Exception as retry_error:
                failed_count += 1
                logger.warning(
                    "Broadcast retry error. user_id=%s error=%s",
                    user_id,
                    retry_error
                )

        except TelegramForbiddenError:
            # Foydalanuvchi botni bloklagan yoki chatga kirish yo'q
            blocked_count += 1

        except TelegramBadRequest as error:
            failed_count += 1
            logger.warning(
                "Broadcast bad request. user_id=%s error=%s",
                user_id,
                error
            )

        except Exception as error:
            failed_count += 1
            logger.exception(
                "Broadcast error. user_id=%s error=%s",
                user_id,
                error
            )

        # Telegram limitiga tushmaslik uchun kichik pauza
        await asyncio.sleep(0.05)

        # Har 100 ta foydalanuvchida statusni yangilash
        if index % 100 == 0:
            try:
                await status_message.edit_text(
                    "📢 Reklama tarqatilmoqda...\n\n"
                    f"⏳ Jarayon: <b>{index}/{total}</b>\n"
                    f"✅ Yuborildi: <b>{success_count}</b>\n"
                    f"🚫 Botni bloklagan: <b>{blocked_count}</b>\n"
                    f"❌ Xatolik: <b>{failed_count}</b>"
                )
            except TelegramBadRequest:
                pass

    try:
        await status_message.edit_text(
            "✅ <b>Reklama tarqatish yakunlandi!</b>\n\n"
            f"👤 Jami foydalanuvchilar: <b>{total}</b>\n"
            f"✅ Muvaffaqiyatli yuborildi: <b>{success_count}</b>\n"
            f"🚫 Botni bloklagan: <b>{blocked_count}</b>\n"
            f"❌ Yuborilmadi: <b>{failed_count}</b>"
        )
    except TelegramBadRequest:
        await bot.send_message(
            admin_chat_id,
            "✅ <b>Reklama tarqatish yakunlandi!</b>\n\n"
            f"👤 Jami foydalanuvchilar: <b>{total}</b>\n"
            f"✅ Muvaffaqiyatli yuborildi: <b>{success_count}</b>\n"
            f"🚫 Botni bloklagan: <b>{blocked_count}</b>\n"
            f"❌ Yuborilmadi: <b>{failed_count}</b>"
        )


# =========================================================
# ADMIN PANEL
# =========================================================

@router.message(Command("admin"), F.from_user.id.in_(ADMINS))
async def admin_panel(message: Message, state: FSMContext):
    """
    Admin boshqaruv panelini ochadi.
    """
    await state.clear()

    await message.answer(
        "🛠 <b>Admin Boshqaruv Paneli</b>\n\n"
        "1️⃣ <b>Qo'shish:</b> <code>/add KOD</code>\n"
        "2️⃣ <b>To'liq o'chirish:</b> <code>/del KOD</code>\n"
        "3️⃣ <b>Qismni o'chirish:</b> "
        "<code>/delpart KOD QISM</code>\n"
        "4️⃣ <b>Statistika:</b> <code>/stats</code>\n"
        "5️⃣ <b>Reklama:</b> <code>/broadcast XABAR</code>\n\n"
        "Jarayonni bekor qilish: <code>/cancel</code>",
        reply_markup=admin_menu()
    )


# =========================================================
# ADMIN PANEL CALLBACK TUGMALARI
# =========================================================

@router.callback_query(
    F.data == "admin_stats",
    F.from_user.id.in_(ADMINS)
)
async def admin_stats_callback(callback: CallbackQuery):
    """
    Admin panelidagi Statistika tugmasi.
    """
    await callback.answer()

    if callback.message:
        await send_stats(callback.message)


@router.callback_query(
    F.data == "admin_broadcast",
    F.from_user.id.in_(ADMINS)
)
async def admin_broadcast_callback(
    callback: CallbackQuery,
    state: FSMContext
):
    """
    Admin panelidagi Reklama yuborish tugmasi.
    """
    await callback.answer()

    await state.clear()
    await state.set_state(BroadcastState.waiting_for_message)

    if callback.message:
        await callback.message.answer(
            "📢 <b>Reklama yuborish rejimi</b>\n\n"
            "Tarqatmoqchi bo'lgan xabaringizni yuboring.\n\n"
            "Quyidagilarni yuborishingiz mumkin:\n"
            "• matn;\n"
            "• rasm va caption;\n"
            "• video va caption;\n"
            "• fayl;\n"
            "• boshqa Telegram xabari.\n\n"
            "Bekor qilish uchun: <code>/cancel</code>"
        )


# =========================================================
# JARAYONNI BEKOR QILISH
# =========================================================

@router.message(Command("cancel"), F.from_user.id.in_(ADMINS))
async def cancel_admin_process(
    message: Message,
    state: FSMContext
):
    """
    Har qanday admin FSM jarayonini bekor qiladi.
    """
    current_state = await state.get_state()

    if current_state is None:
        return await message.answer(
            "ℹ️ Hozir faol jarayon mavjud emas."
        )

    await state.clear()

    await message.answer(
        "❌ Jarayon bekor qilindi.",
        reply_markup=admin_menu()
    )


# =========================================================
# YANGI ANIME YOKI SERIAL QO'SHISH
# =========================================================

@router.message(Command("add"), F.from_user.id.in_(ADMINS))
async def add_start(
    message: Message,
    state: FSMContext,
    command: CommandObject
):
    """
    Yangi anime yoki serial qo'shish jarayonini boshlaydi.
    """
    await state.clear()

    if not command.args:
        return await message.answer(
            "❌ Kodni kiriting!\n"
            "Masalan: <code>/add 1</code>"
        )

    code = command.args.strip()

    if not code.isdigit():
        return await message.answer(
            "⚠️ <b>Xato!</b>\n"
            "Kod faqat raqamlardan iborat bo'lishi kerak."
        )

    # Kod oldin ishlatilganini tekshiramiz
    if await db.movie_exists(code):
        return await message.answer(
            f"⚠️ <b>{code}</b> kodida allaqachon anime mavjud!\n\n"
            "Yangi anime qo'shish uchun boshqa kod tanlang.\n\n"
            "Mavjud animeni o'chirish uchun:\n"
            f"<code>/del {code}</code>"
        )

    await state.update_data(movie_code=code)

    await message.answer(
        f"🔢 Kodi: <b>{code}</b>\n\n"
        "Yuklama turini tanlang:",
        reply_markup=series_confirm_kb()
    )

    await state.set_state(MovieAdd.waiting_for_type)


# =========================================================
# SERIAL QO'SHISH
# =========================================================

@router.callback_query(
    MovieAdd.waiting_for_type,
    F.data == "type_series",
    F.from_user.id.in_(ADMINS)
)
async def process_series_type(
    callback: CallbackQuery,
    state: FSMContext
):
    await callback.answer()

    await state.update_data(is_series=1)

    if callback.message:
        await callback.message.edit_text(
            "🖼 Serial uchun <b>muqova rasmini</b> yuboring:"
        )

    await state.set_state(MovieAdd.waiting_for_poster)


@router.message(
    MovieAdd.waiting_for_poster,
    F.photo,
    F.from_user.id.in_(ADMINS)
)
async def process_poster(
    message: Message,
    state: FSMContext
):
    data = await state.get_data()

    # Bu handler faqat serial uchun ishlashi kerak
    if data.get("is_series") != 1:
        return

    poster_id = message.photo[-1].file_id

    await state.update_data(poster_id=poster_id)

    await message.answer(
        "✍️ Serial haqida <b>ta'rif</b> yuboring:"
    )

    await state.set_state(MovieAdd.waiting_for_caption)


@router.message(
    MovieAdd.waiting_for_poster,
    F.from_user.id.in_(ADMINS)
)
async def wrong_poster_type(
    message: Message,
    state: FSMContext
):
    """
    Serial poster bosqichida rasm o'rniga boshqa narsa yuborilsa.
    """
    data = await state.get_data()

    if data.get("is_series") == 1:
        await message.answer(
            "⚠️ Iltimos, serial muqovasini <b>rasm</b> sifatida yuboring."
        )


@router.message(
    MovieAdd.waiting_for_caption,
    F.text,
    F.from_user.id.in_(ADMINS)
)
async def process_caption(
    message: Message,
    state: FSMContext
):
    data = await state.get_data()

    movie_code = data.get("movie_code")
    poster_id = data.get("poster_id")
    caption = message.text.strip()

    if not caption:
        return await message.answer(
            "⚠️ Ta'rif bo'sh bo'lishi mumkin emas."
        )

    # Jarayon davomida boshqa admin bir xil kodni qo'shgan bo'lishi mumkin.
    added = await db.add_movie(
        code=movie_code,
        file_id=poster_id,
        caption=caption,
        is_series=1
    )

    if not added:
        await state.clear()

        return await message.answer(
            f"⚠️ <b>{movie_code}</b> kodi allaqachon mavjud.\n\n"
            "Serial saqlanmadi. Boshqa kod bilan qayta urinib ko'ring."
        )

    await state.update_data(ep_count=0)

    await message.answer(
        "✅ Serialning asosiy ma'lumoti yaratildi!\n\n"
        "Endi <b>1-qism videosini</b> yuboring.\n\n"
        "Barcha qismlarni yuborib bo'lgach:\n"
        "<code>/finish</code>"
    )

    await state.set_state(MovieAdd.waiting_for_episodes)


@router.message(
    MovieAdd.waiting_for_caption,
    F.from_user.id.in_(ADMINS)
)
async def wrong_caption_type(message: Message):
    """
    Caption o'rniga boshqa xabar yuborilsa.
    """
    await message.answer(
        "⚠️ Serial ta'rifini oddiy <b>matn</b> sifatida yuboring."
    )


@router.message(
    MovieAdd.waiting_for_episodes,
    F.video,
    F.from_user.id.in_(ADMINS)
)
async def process_episode(
    message: Message,
    state: FSMContext
):
    data = await state.get_data()

    movie_code = data.get("movie_code")
    current_count = int(data.get("ep_count", 0))
    new_count = current_count + 1

    added = await db.add_episode(
        code=movie_code,
        part=new_count,
        file_id=message.video.file_id
    )

    if not added:
        return await message.answer(
            f"⚠️ {new_count}-qismni saqlab bo'lmadi.\n\n"
            "Bu qism oldin saqlangan yoki anime kodi topilmadi."
        )

    await state.update_data(ep_count=new_count)

    await message.answer(
        f"✅ <b>{new_count}-qism</b> saqlandi!\n\n"
        "Keyingi qismni yuboring yoki "
        "<code>/finish</code> buyrug'ini bosing."
    )


@router.message(
    MovieAdd.waiting_for_episodes,
    F.from_user.id.in_(ADMINS)
)
async def wrong_episode_type(message: Message):
    """
    Serial qismi o'rniga video bo'lmagan xabar yuborilsa.
    """
    await message.answer(
        "⚠️ Iltimos, serial qismini <b>video</b> sifatida yuboring.\n\n"
        "Tugatish uchun: <code>/finish</code>"
    )


@router.message(
    Command("finish"),
    MovieAdd.waiting_for_episodes,
    F.from_user.id.in_(ADMINS)
)
async def process_finish(
    message: Message,
    state: FSMContext
):
    data = await state.get_data()
    episode_count = int(data.get("ep_count", 0))
    movie_code = data.get("movie_code")

    await state.clear()

    if episode_count == 0:
        return await message.answer(
            f"⚠️ <b>{movie_code}</b> kodi yaratildi, "
            "lekin unga hech qanday qism qo'shilmadi."
        )

    await message.answer(
        "🚀 <b>Barcha qismlar muvaffaqiyatli saqlandi!</b>\n\n"
        f"🔢 Anime kodi: <code>{movie_code}</code>\n"
        f"🎞 Qismlar soni: <b>{episode_count}</b>"
    )


# =========================================================
# ODDIY VIDEO QO'SHISH
# =========================================================

@router.callback_query(
    MovieAdd.waiting_for_type,
    F.data == "type_movie",
    F.from_user.id.in_(ADMINS)
)
async def process_movie_type(
    callback: CallbackQuery,
    state: FSMContext
):
    await callback.answer()

    await state.update_data(is_series=0)

    if callback.message:
        await callback.message.edit_text(
            "🎞 Animeni <b>video</b> sifatida yuboring.\n\n"
            "Video caption'i anime ta'rifi sifatida saqlanadi."
        )

    await state.set_state(MovieAdd.waiting_for_poster)


@router.message(
    MovieAdd.waiting_for_poster,
    F.video,
    F.from_user.id.in_(ADMINS)
)
async def process_movie_video(
    message: Message,
    state: FSMContext
):
    data = await state.get_data()

    # Bu handler faqat oddiy anime uchun ishlashi kerak
    if data.get("is_series") != 0:
        return

    movie_code = data.get("movie_code")
    caption = message.caption or "Yoqimli tomosha!"

    added = await db.add_movie(
        code=movie_code,
        file_id=message.video.file_id,
        caption=caption,
        is_series=0
    )

    await state.clear()

    if not added:
        return await message.answer(
            f"⚠️ <b>{movie_code}</b> kodi allaqachon mavjud.\n\n"
            "Video saqlanmadi. Boshqa kod tanlang."
        )

    await message.answer(
        "✅ <b>Video muvaffaqiyatli saqlandi!</b>\n\n"
        f"🔢 Kodi: <code>{movie_code}</code>"
    )


# =========================================================
# ANIMENI TO'LIQ O'CHIRISH
# =========================================================

@router.message(Command("del"), F.from_user.id.in_(ADMINS))
async def delete_movie_handler(
    message: Message,
    command: CommandObject
):
    """
    Anime, qismlar, reyting va favorites yozuvlarini to'liq o'chiradi.
    """
    if not command.args:
        return await message.answer(
            "❌ Kodni yozing.\n"
            "Masalan: <code>/del 1</code>"
        )

    code = command.args.strip()

    if not code.isdigit():
        return await message.answer(
            "⚠️ Kod faqat raqamlardan iborat bo'lishi kerak."
        )

    deleted = await db.delete_movie(code)

    if not deleted:
        return await message.answer(
            f"ℹ️ <b>{code}</b> kodida anime topilmadi."
        )

    await message.answer(
        f"🗑 <b>{code}</b> kodidagi anime to'liq o'chirildi.\n\n"
        "Unga tegishli qismlar, reytinglar va saqlanganlar ham tozalandi."
    )


# =========================================================
# BITTA QISMNI O'CHIRISH
# =========================================================

@router.message(Command("delpart"), F.from_user.id.in_(ADMINS))
async def delete_part_handler(
    message: Message,
    command: CommandObject
):
    """
    Faqat bitta qismni o'chiradi va qolganlarini qayta raqamlaydi.
    """
    if not command.args:
        return await message.answer(
            "❌ Format:\n"
            "<code>/delpart KOD QISM</code>\n\n"
            "Masalan:\n"
            "<code>/delpart 1 5</code>"
        )

    args = command.args.split()

    if len(args) != 2:
        return await message.answer(
            "❌ Format noto'g'ri.\n\n"
            "To'g'ri format:\n"
            "<code>/delpart KOD QISM</code>"
        )

    code = args[0].strip()
    part_text = args[1].strip()

    if not code.isdigit():
        return await message.answer(
            "⚠️ Anime kodi faqat raqamlardan iborat bo'lishi kerak."
        )

    try:
        part = int(part_text)
    except ValueError:
        return await message.answer(
            "⚠️ Qism raqami butun son bo'lishi kerak."
        )

    if part < 1:
        return await message.answer(
            "⚠️ Qism raqami 1 yoki undan katta bo'lishi kerak."
        )

    if not await db.movie_exists(code):
        return await message.answer(
            f"ℹ️ <b>{code}</b> kodida anime topilmadi."
        )

    deleted = await db.delete_episode(code, part)

    if not deleted:
        return await message.answer(
            f"ℹ️ <b>{code}</b> kodidagi "
            f"<b>{part}-qism</b> topilmadi."
        )

    await message.answer(
        f"✅ <b>{code}</b> kodidagi "
        f"<b>{part}-qism</b> o'chirildi.\n\n"
        "Qolgan qismlar 1, 2, 3... tartibida qayta raqamlandi."
    )


# =========================================================
# STATISTIKA
# =========================================================

@router.message(Command("stats"), F.from_user.id.in_(ADMINS))
async def stats_handler(message: Message):
    await send_stats(message)


# =========================================================
# /broadcast MATN KOMANDASI
# =========================================================

@router.message(Command("broadcast"), F.from_user.id.in_(ADMINS))
async def broadcast_handler(
    message: Message,
    bot: Bot,
    state: FSMContext,
    command: CommandObject
):
    """
    /broadcast XABAR ko'rinishida matn tarqatadi.

    Agar argument bo'lmasa, reklama kutish rejimini yoqadi.
    """
    await state.clear()

    text = command.args.strip() if command.args else ""

    if not text:
        await state.set_state(BroadcastState.waiting_for_message)

        return await message.answer(
            "📢 <b>Reklama yuborish rejimi</b>\n\n"
            "Endi tarqatmoqchi bo'lgan xabaringizni yuboring.\n\n"
            "Matn, rasm, video yoki fayl yuborishingiz mumkin.\n\n"
            "Bekor qilish: <code>/cancel</code>"
        )

    # /broadcast dan keyingi matnni alohida xabar qilib yaratamiz.
    # Bu usul oddiy matnli broadcast uchun ishlaydi.
    users = await db.get_all_users()

    success_count = 0
    failed_count = 0
    blocked_count = 0

    status_message = await message.answer(
        "📢 Reklama tarqatish boshlandi...\n\n"
        f"👤 Jami foydalanuvchilar: <b>{len(users)}</b>"
    )

    for user_id in users:
        try:
            await bot.send_message(
                chat_id=user_id,
                text=text
            )

            success_count += 1

        except TelegramRetryAfter as error:
            await asyncio.sleep(error.retry_after)

            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=text
                )
                success_count += 1

            except TelegramForbiddenError:
                blocked_count += 1

            except Exception:
                failed_count += 1

        except TelegramForbiddenError:
            blocked_count += 1

        except Exception as error:
            failed_count += 1
            logger.warning(
                "Text broadcast error. user_id=%s error=%s",
                user_id,
                error
            )

        await asyncio.sleep(0.05)

    try:
        await status_message.edit_text(
            "✅ <b>Reklama tarqatish yakunlandi!</b>\n\n"
            f"✅ Yuborildi: <b>{success_count}</b>\n"
            f"🚫 Botni bloklagan: <b>{blocked_count}</b>\n"
            f"❌ Xatolik: <b>{failed_count}</b>"
        )
    except TelegramBadRequest:
        pass


# =========================================================
# TUGMA ORQALI REKLAMA YUBORISH
# =========================================================

@router.message(
    BroadcastState.waiting_for_message,
    F.from_user.id.in_(ADMINS)
)
async def receive_broadcast_message(
    message: Message,
    bot: Bot,
    state: FSMContext
):
    """
    Admin panelidagi Reklama yuborish tugmasidan keyin
    yuborilgan xabarni barcha foydalanuvchilarga tarqatadi.
    """
    # Komandalarni reklama qilib tarqatmaymiz
    if message.text and message.text.startswith("/"):
        return await message.answer(
            "⚠️ Reklama sifatida komanda yuborib bo'lmaydi.\n\n"
            "Oddiy matn, rasm, video yoki fayl yuboring.\n"
            "Bekor qilish: <code>/cancel</code>"
        )

    await state.clear()

    await distribute_message(
        bot=bot,
        source_message=message,
        admin_chat_id=message.chat.id
    )
