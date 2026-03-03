from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_join_inline(invite_links: list):
    """Har bir kanal uchun alohida a'zo bo'lish tugmalarini yaratadi."""
    builder = InlineKeyboardBuilder()
    
    # Ro'yxatdagi har bir kanal linki uchun alohida tugma yaratish
    for i, link in enumerate(invite_links, 1):
        builder.row(InlineKeyboardButton(
            text=f"{i}-kanalga a'zo bo'lish 📢", 
            url=link)
        )
    
    # Tasdiqlash tugmasi (barcha kanallarga a'zo bo'lgach bosiladi)
    builder.row(InlineKeyboardButton(
        text="Tasdiqlash ✅", 
        callback_data="check_subs")
    )
    
    return builder.as_markup()

def get_rating_keyboard(movie_code: str):
    """Kino uchun 1 dan 5 gacha yulduzcha rating tugmalarini yaratadi."""
    builder = InlineKeyboardBuilder()
    
    # 1 dan 5 gacha bo'lgan yulduzchalarni terish
    for i in range(1, 6):
        builder.add(InlineKeyboardButton(
            text=f"{i} ⭐", 
            callback_data=f"rate_{i}_{movie_code}")
        )
    
    # Tugmalarni bitta qatorda 5 ta qilib tekislash
    builder.adjust(5) 
    return builder.as_markup()

def admin_menu():
    """Admin paneli uchun asosiy tugmalar."""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(text="📢 Reklama yuborish", callback_data="admin_broadcast"))
    builder.row(InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"))
    
    return builder.as_markup()
