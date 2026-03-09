from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_join_inline(invite_links: list):
    """Har bir kanal uchun alohida a'zo bo'lish tugmalarini yaratadi."""
    builder = InlineKeyboardBuilder()
    
    # Ro'yxatdagi har bir kanal linki uchun alohida tugma
    for i, link in enumerate(invite_links, 1):
        builder.row(InlineKeyboardButton(
            text=f"{i}-kanalga a'zo bo'lish 📢", 
            url=link)
        )
    
    # Tasdiqlash tugmasi
    builder.row(InlineKeyboardButton(
        text="Tasdiqlash ✅", 
        callback_data="check_subs")
    )
    
    return builder.as_markup()

def get_episodes_kb(movie_code: str, episodes: list):
    """
    Serial qismlarini dinamik ravishda chiqaruvchi tugmalar.
    episodes: [(part_number, file_id), ...] shaklida keladi.
    """
    builder = InlineKeyboardBuilder()
    
    for part_num, _ in episodes:
        builder.add(InlineKeyboardButton(
            text=f"{part_num}", 
            callback_data=f"ep_{movie_code}_{part_num}")
        )
    
    # Har qatorda 5 tadan qism tugmasi bo'ladi
    builder.adjust(5) 
    return builder.as_markup()

def get_rating_keyboard(movie_code: str):
    """Kino uchun 1 dan 5 gacha yulduzcha rating tugmalarini yaratadi."""
    builder = InlineKeyboardBuilder()
    
    for i in range(1, 6):
        builder.add(InlineKeyboardButton(
            text=f"{i} ⭐", 
            callback_data=f"rate_{i}_{movie_code}")
        )
    
    builder.adjust(5) 
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
    
