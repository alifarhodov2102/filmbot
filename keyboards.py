from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_join_inline(channel_url: str):
    """Kanalga a'zo bo'lish tugmalarini yaratadi."""
    builder = InlineKeyboardBuilder()
    
    # Kanalga o'tish tugmasi
    builder.row(InlineKeyboardButton(
        text="Kanalga a'zo bo'lish 📢", 
        url=channel_url)
    )
    
    # Tasdiqlash tugmasi
    builder.row(InlineKeyboardButton(
        text="Tasdiqlash ✅", 
        callback_data="check_subs")
    )
    
    return builder.as_markup()

def get_rating_keyboard(movie_code: str):
    """Kino uchun 1 dan 5 gacha yulduzcha rating tugmalarini yaratadi."""
    builder = InlineKeyboardBuilder()
    
    # 1 dan 5 gacha bo'lgan yulduzchalarni bitta qatorga teradi
    for i in range(1, 6):
        builder.add(InlineKeyboardButton(
            text=f"{i} ⭐", 
            callback_data=f"rate_{i}_{movie_code}")
        )
    
    # Tugmalarni chiroyli ko'rinishga keltirish (har bir qatorda nechtadan bo'lishi)
    builder.adjust(5) 
    return builder.as_markup()

def admin_menu():
    """Admin paneli uchun asosiy tugmalar."""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(text="📢 Reklama yuborish", callback_data="admin_broadcast"))
    builder.row(InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"))
    
    return builder.as_markup()
