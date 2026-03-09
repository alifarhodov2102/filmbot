from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_join_inline(invite_links: list):
    """Har bir kanal uchun alohida a'zo bo'lish tugmalarini yaratadi."""
    builder = InlineKeyboardBuilder()
    
    for i, link in enumerate(invite_links, 1):
        builder.row(InlineKeyboardButton(
            text=f"{i}-kanalga a'zo bo'lish 📢", 
            url=link)
        )
    
    builder.row(InlineKeyboardButton(
        text="Tasdiqlash ✅", 
        callback_data="check_subs")
    )
    
    return builder.as_markup()

def get_episodes_kb(movie_code: str, episodes: list):
    """
    Serial qismlari tugmalari va ularning pastidagi funksional tugmalar.
    """
    builder = InlineKeyboardBuilder()
    
    # Qismlar tugmalarini terish (1, 2, 3...)
    for part_num, _ in episodes:
        builder.add(InlineKeyboardButton(
            text=f"{part_num}", 
            callback_data=f"ep_{movie_code}_{part_num}")
        )
    
    builder.adjust(5) # Qismlar 5 tadan qatorda
    
    # Markaziy boshqaruv tugmalari
    builder.row(
        InlineKeyboardButton(text="❌", callback_data="close_msg"),
        InlineKeyboardButton(text="Baholash ⭐", callback_data=f"show_rate_{movie_code}")
    )
    
    # Sevimlilar va Ulashish tugmalari
    builder.row(InlineKeyboardButton(
        text="❤️ Mening kinolarimga qo'shish", 
        callback_data=f"fav_add_{movie_code}")
    )
    builder.row(InlineKeyboardButton(
        text="Ulashish 🚀", 
        switch_inline_query=f"\nKino kodi: {movie_code}")
    )
    
    return builder.as_markup()

def get_movie_kb(movie_code: str):
    """
    Oddiy kino pastidagi asosiy tugmalar.
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="❌", callback_data="close_msg"),
        InlineKeyboardButton(text="Baholash ⭐", callback_data=f"show_rate_{movie_code}")
    )
    
    builder.row(InlineKeyboardButton(
        text="❤️ Mening kinolarimga qo'shish", 
        callback_data=f"fav_add_{movie_code}")
    )
    
    builder.row(InlineKeyboardButton(
        text="Ulashish 🚀", 
        switch_inline_query=f"\nKino kodi: {movie_code}")
    )
    
    return builder.as_markup()

def get_rating_keyboard(movie_code: str):
    """
    Baholash bosilganda chiqadigan yulduzcha tugmalari.
    """
    builder = InlineKeyboardBuilder()
    
    for i in range(1, 6):
        builder.add(InlineKeyboardButton(
            text=f"{i} ⭐", 
            callback_data=f"rate_{i}_{movie_code}")
        )
    builder.adjust(5)
    
    builder.row(InlineKeyboardButton(
        text="Back ⬅️", 
        callback_data=f"back_to_movie_{movie_code}")
    )
    
    return builder.as_markup()

def series_confirm_kb():
    """Admin yangi kod qo'shayotganda turini tanlashi uchun tugmalar."""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="🎬 Oddiy Kino", callback_data="type_movie"))
    builder.add(InlineKeyboardButton(text="🎞 Serial", callback_data="type_series"))
    
    return builder.as_markup()

def admin_menu():
    """Admin paneli uchun asosiy boshqaruv tugmalari."""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(text="📢 Reklama yuborish", callback_data="admin_broadcast"))
    builder.row(InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"))
    
    return builder.as_markup()