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

    copy_message orqali:
    - matn;
    - rasm;
    - video;
    - animatsiya;
    - audio;
    - hujjat;
    - sticker;
    - forward qilingan xabarlar

    tarqatilishi mumkin.
    """
    users = await db.get_all_users()

    total = len(users)
    success_count = 0
    failed_count = 0
    blocked_count = 0

    if total == 0:
        await bot.send_message(
            admin_chat_id,
            "ℹ️ Reklama yuborish uchun foydalanuvchilar topilmadi."
        )
        return

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

        await asyncio.sleep(0.05)

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

    result_text = (
        "✅ <b>Reklama tarqatish yakunlandi!</b>\n\n"
        f"👤 Jami foydalanuvchilar: <b>{total}</b>\n"
        f"✅ Muvaffaqiyatli yuborildi: <b>{success_count}</b>\n"
        f"🚫 Botni bloklagan: <b>{blocked_count}</b>\n"
        f"❌ Yuborilmadi: <b>{failed_count}</b>"
    )

    try:
        await status_message.edit_text(result_text)
    except TelegramBadRequest:
        await bot.send_message(admin_chat_id, result_text)


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
# JARAYONNI BEKOR QILISH
# =========================================================

@router.message(Command("cancel"), F.from_user.id.in_(ADMINS))
async def cancel_admin_process(
    message: Message,
    state: FSMContext
):
    """
    Har qanday admin jarayonini bekor qiladi.
    """
    current_state = await state.get_state()

    if current_state is None:
        return await message.answer(
            "ℹ️ Hozir faol jarayon mavjud emas.",
            reply_markup=admin_menu()
        )

    await state.clear()

    await message.answer(
        "❌ Jarayon bekor qilindi.",
        reply_markup=admin_menu()
    )


# =========================================================
# SERIAL QO'SHISHNI YAKUNLASH
# =========================================================

@router.message(
    Command("finish"),
    MovieAdd.waiting_for_episodes,
    F.from_user.id.in_(ADMINS)
)
async def process_finish(
    message: Message,
    state: FSMContext
):
    """
    Serial qismlarini qo'shish jarayonini tugatadi.

    Bu handler umumiy waiting_for_episodes handleridan
    oldin turishi shart.
    """
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
        f"🎞 Qismlar soni: <b>{episode_count}</b>",
        reply_markup=admin_menu()
    )


# =========================================================
# ANIMENI TO'LIQ O'CHIRISH
# =========================================================

@router.message(Command("del"), F.from_user.id.in_(ADMINS))
async def delete_movie_handler(
    message: Message,
    state: FSMContext,
    command: CommandObject
):
    """
    Anime, qismlar, reytinglar va favorites yozuvlarini
    to'liq o'chiradi.
    """
    await state.clear()

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

    movie_before = await db.get_movie(code)

    if movie_before is None:
        return await message.answer(
            f"ℹ️ <b>{code}</b> kodida anime topilmadi."
        )

    episodes_before = await db.get_episodes(code)

    deleted = await db.delete_movie(code)

    movie_after = await db.get_movie(code)
    episodes_after = await db.get_episodes(code)

    if deleted and movie_after is None and len(episodes_after) == 0:
        return await message.answer(
            f"🗑 <b>{code}</b> kodidagi anime to'liq o'chirildi.\n\n"
            f"🎞 O'chirilgan qismlar: <b>{len(episodes_before)}</b>\n"
            "⭐ Reytinglar va saqlanganlar ham tozalandi."
        )

    await message.answer(
        "❌ <b>O'chirish yakunlanmadi.</b>\n\n"
        f"Kod: <code>{code}</code>\n"
        f"Anime hali mavjud: <code>{movie_after is not None}</code>\n"
        f"Qolgan qismlar: <code>{len(episodes_after)}</code>"
    )


# =========================================================
# BITTA QISMNI O'CHIRISH
# =========================================================

@router.message(Command("delpart"), F.from_user.id.in_(ADMINS))
async def delete_part_handler(
    message: Message,
    state: FSMContext,
    command: CommandObject
):
    """
    Bitta qismni o'chiradi va qolgan qismlarni
    qayta raqamlaydi.
    """
    await state.clear()

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

    remaining_episodes = await db.get_episodes(code)

    await message.answer(
        f"✅ <b>{code}</b> kodidagi "
        f"<b>{part}-qism</b> o'chirildi.\n\n"
        "Qolgan qismlar 1, 2, 3... tartibida qayta raqamlandi.\n"
        f"🎞 Hozirgi qismlar soni: <b>{len(remaining_episodes)}</b>"
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
    /broadcast XABAR orqali matn tarqatadi.

    Argument bo'lmasa, keyingi xabarni kutadi.
    """
    await state.clear()

    text = command.args.strip() if command.args else ""

    if not text:
        await state.set_state(BroadcastState.waiting_for_message)

        return await message.answer(
            "📢 <b>Reklama yuborish rejimi</b>\n\n"
            "Endi tarqatmoqchi bo'lgan xabaringizni yuboring.\n\n"
            "Matn, rasm, video, forward yoki fayl yuborishingiz mumkin.\n\n"
            "Bekor qilish: <code>/cancel</code>"
        )

    users = await db.get_all_users()

    total = len(users)
    success_count = 0
    failed_count = 0
    blocked_count = 0

    if total == 0:
        return await message.answer(
            "ℹ️ Reklama yuborish uchun foydalanuvchilar topilmadi."
        )

    status_message = await message.answer(
        "📢 Reklama tarqatish boshlandi...\n\n"
        f"👤 Jami foydalanuvchilar: <b>{total}</b>"
    )

    for index, user_id in enumerate(users, start=1):
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

            except Exception as retry_error:
                failed_count += 1
                logger.warning(
                    "Text broadcast retry error. user_id=%s error=%s",
                    user_id,
                    retry_error
                )

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
            f"✅ Yuborildi: <b>{success_count}</b>\n"
            f"🚫 Botni bloklagan: <b>{blocked_count}</b>\n"
            f"❌ Xatolik: <b>{failed_count}</b>"
        )
    except TelegramBadRequest:
        pass


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
            "• kanaldan forward;\n"
            "• fayl;\n"
            "• boshqa Telegram xabari.\n\n"
            "Bekor qilish uchun: <code>/cancel</code>"
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
# ANIME YOKI SERIAL TURINI TANLASH
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
            "Videoni kanaldan forward qilishingiz ham mumkin.\n"
            "Video caption'i anime ta'rifi sifatida saqlanadi."
        )

    await state.set_state(MovieAdd.waiting_for_poster)


# =========================================================
# POSTER YOKI ODDIY VIDEO QABUL QILISH
# =========================================================

@router.message(
    MovieAdd.waiting_for_poster,
    F.photo,
    F.from_user.id.in_(ADMINS)
)
async def process_poster(
    message: Message,
    state: FSMContext
):
    """
    Serial uchun poster rasmini qabul qiladi.
    """
    data = await state.get_data()

    if data.get("is_series") != 1:
        return await message.answer(
            "⚠️ Oddiy anime uchun rasm emas, video yuboring."
        )

    poster_id = message.photo[-1].file_id

    await state.update_data(poster_id=poster_id)

    await message.answer(
        "✍️ Serial haqida <b>ta'rif</b> yuboring:"
    )

    await state.set_state(MovieAdd.waiting_for_caption)


@router.message(
    MovieAdd.waiting_for_poster,
    F.video,
    F.from_user.id.in_(ADMINS)
)
async def process_movie_video(
    message: Message,
    state: FSMContext
):
    """
    Oddiy anime videosini qabul qiladi.

    Kanaldan forward qilingan video ham F.video sifatida keladi.
    """
    data = await state.get_data()

    if data.get("is_series") != 0:
        return await message.answer(
            "⚠️ Serial uchun avval muqova rasmini yuboring."
        )

    movie_code = data.get("movie_code")
    caption = message.caption or "Yoqimli tomosha!"

    added = await db.add_movie(
        code=movie_code,
        file_id=message.video.file_id,
        caption=caption,
        is_series=0
    )

    if not added:
        await state.clear()

        return await message.answer(
            f"⚠️ <b>{movie_code}</b> kodi allaqachon mavjud.\n\n"
            "Video saqlanmadi. Boshqa kod tanlang."
        )

    await state.clear()

    await message.answer(
        "✅ <b>Video muvaffaqiyatli saqlandi!</b>\n\n"
        f"🔢 Kodi: <code>{movie_code}</code>",
        reply_markup=admin_menu()
    )


@router.message(
    MovieAdd.waiting_for_poster,
    F.from_user.id.in_(ADMINS)
)
async def wrong_poster_or_movie_type(
    message: Message,
    state: FSMContext
):
    """
    Poster yoki video bosqichida noto'g'ri format yuborilsa.
    """
    data = await state.get_data()

    if data.get("is_series") == 1:
        await message.answer(
            "⚠️ Serial uchun muqovani <b>rasm</b> sifatida yuboring."
        )
    else:
        await message.answer(
            "⚠️ Oddiy anime uchun <b>video</b> yuboring.\n\n"
            "Videoni kanaldan forward qilish ham mumkin."
        )


# =========================================================
# SERIAL CAPTION QABUL QILISH
# =========================================================

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
        "Endi <b>1-qism videosini</b> yuboring.\n"
        "Videoni kanaldan forward qilishingiz mumkin.\n\n"
        "Barcha qismlarni yuborib bo'lgach:\n"
        "<code>/finish</code>"
    )

    await state.set_state(MovieAdd.waiting_for_episodes)


@router.message(
    MovieAdd.waiting_for_caption,
    F.from_user.id.in_(ADMINS)
)
async def wrong_caption_type(message: Message):
    await message.answer(
        "⚠️ Serial ta'rifini oddiy <b>matn</b> sifatida yuboring."
    )


# =========================================================
# SERIAL QISMLARINI QABUL QILISH
# =========================================================

@router.message(
    MovieAdd.waiting_for_episodes,
    F.video,
    F.from_user.id.in_(ADMINS)
)
async def process_episode(
    message: Message,
    state: FSMContext
):
    """
    Serial qismini saqlaydi.

    Kanaldan forward qilingan video ham message.video sifatida keladi.
    Database ichida faqat Telegram file_id saqlanadi.
    """
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
            "Bu qism raqami oldin saqlangan yoki anime kodi topilmadi."
        )

    await state.update_data(ep_count=new_count)

    await message.answer(
        f"✅ <b>{new_count}-qism</b> saqlandi!\n\n"
        "Keyingi videoni yuboring yoki kanaldan forward qiling.\n"
        "Tugatish uchun: <code>/finish</code>"
    )


@router.message(
    MovieAdd.waiting_for_episodes,
    F.from_user.id.in_(ADMINS)
)
async def wrong_episode_type(message: Message):
    """
    Serial qismi o'rniga boshqa turdagi xabar yuborilsa.

    /finish handleri ushbu handlerdan yuqorida ro'yxatdan o'tgan.
    """
    await message.answer(
        "⚠️ Serial qismini <b>video</b> sifatida yuboring "
        "yoki kanaldan forward qiling.\n\n"
        "Tugatish uchun: <code>/finish</code>"
    )


# =========================================================
# TUGMA ORQALI REKLAMA XABARINI QABUL QILISH
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
    Reklama tugmasidan keyin yuborilgan xabarni tarqatadi.
    """
    if message.text and message.text.startswith("/"):
        return await message.answer(
            "⚠️ Reklama sifatida komanda yuborib bo'lmaydi.\n\n"
            "Oddiy matn, rasm, video, forward yoki fayl yuboring.\n"
            "Bekor qilish: <code>/cancel</code>"
        )

    await state.clear()

    await distribute_message(
        bot=bot,
        source_message=message,
        admin_chat_id=message.chat.id
    )
