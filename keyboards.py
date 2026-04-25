from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_join_inline(invite_links: list):
    builder = InlineKeyboardBuilder()
    for i, link in enumerate(invite_links, 1):
        builder.row(InlineKeyboardButton(text=f"{i}-kanalga a'zo bo'lish 📢", url=link))
    builder.row(InlineKeyboardButton(text="Tasdiqlash ✅", callback_data="check_subs"))
    return builder.as_markup()

def get_episodes_kb(movie_code: str, episodes: list, page: int = 0):
    """
    Serial qismlari uchun sahifalangan klaviatura.
    page: joriy sahifa indeksi (0 dan boshlanadi)
    """
    builder = InlineKeyboardBuilder()
    
    # Bir sahifadagi qismlar soni
    items_per_page = 25 
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    
    # Faqat joriy sahifaga tegishli qismlarni kesib olamiz
    current_episodes = episodes[start_idx:end_idx]
    
    for part_num, _ in current_episodes:
        builder.add(InlineKeyboardButton(
            text=f"{part_num}", 
            callback_data=f"ep_{movie_code}_{part_num}")
        )
    
    builder.adjust(5) # Qismlar 5 tadan qatorda

    # --- Sahifalash boshqaruvi (Pagination) ---
    total_pages = (len(episodes) - 1) // items_per_page + 1
    
    nav_row = []
    # Orqaga tugmasi
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"pg_{movie_code}_{page-1}"))
    else:
        nav_row.append(InlineKeyboardButton(text="❌", callback_data="close_msg")) # Agar birinchi sahifa bo'lsa yopish

    # Sahifa raqami
    nav_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="ignore"))

    # Oldinga tugmasi
    if end_idx < len(episodes):
        nav_row.append(InlineKeyboardButton(text="➡️", callback_data=f"pg_{movie_code}_{page+1}"))
    else:
        nav_row.append(InlineKeyboardButton(text="🏁", callback_data="ignore"))

    builder.row(*nav_row)

    # --- Funksional tugmalar ---
    builder.row(
        InlineKeyboardButton(text="Baholash ⭐", callback_data=f"show_rate_{movie_code}"),
        InlineKeyboardButton(text="❤️ Saqlash", callback_data=f"fav_add_{movie_code}")
    )
    builder.row(InlineKeyboardButton(
        text="Ulashish 🚀", 
        switch_inline_query=f"\nKino kodi: {movie_code}")
    )
    
    return builder.as_markup()

def get_movie_kb(movie_code: str):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌", callback_data="close_msg"),
        InlineKeyboardButton(text="Baholash ⭐", callback_data=f"show_rate_{movie_code}")
    )
    builder.row(InlineKeyboardButton(text="❤️ Mening kinolarimga qo'shish", callback_data=f"fav_add_{movie_code}"))
    builder.row(InlineKeyboardButton(text="Ulashish 🚀", switch_inline_query=f"\nKino kodi: {movie_code}"))
    return builder.as_markup()

def get_rating_keyboard(movie_code: str):
    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        builder.add(InlineKeyboardButton(text=f"{i} ⭐", callback_data=f"rate_{i}_{movie_code}"))
    builder.adjust(5)
    builder.row(InlineKeyboardButton(text="Back ⬅️", callback_data=f"back_to_movie_{movie_code}"))
    return builder.as_markup()

def series_confirm_kb():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🎬 Oddiy Kino", callback_data="type_movie"))
    builder.add(InlineKeyboardButton(text="🎞 Serial", callback_data="type_series"))
    return builder.as_markup()

def admin_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📢 Reklama yuborish", callback_data="admin_broadcast"))
    builder.row(InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"))
    return builder.as_markup()
