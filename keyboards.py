from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_join_inline(channel_url: str):
    """Creates the 'Join Channel' buttons."""
    builder = InlineKeyboardBuilder()
    
    # Button to open the channel
    builder.row(InlineKeyboardButton(
        text="Join Channel 📢", 
        url=channel_url)
    )
    
    # Button for user to click after joining
    builder.row(InlineKeyboardButton(
        text="I have joined ✅", 
        callback_data="check_subs")
    )
    
    return builder.as_markup()

def admin_menu():
    """Simple buttons for the Admin Panel."""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast"))
    builder.row(InlineKeyboardButton(text="📊 Stats", callback_data="admin_stats"))
    
    return builder.as_markup()