from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command
from database import Database
from config import ADMINS

router = Router()
db = Database("bot_data.db")

# Simple check to see if user is Admin
def is_admin(message: Message):
    return message.from_user.id in ADMINS

@router.message(Command("admin"), F.from_user.id.in_(ADMINS))
async def admin_panel(message: Message):
    await message.answer("🛠 **Admin Panel**\n\n"
                         "1. Send a video with caption: `/add CODE`\n"
                         "2. Use `/broadcast MESSAGE` to send ads\n"
                         "3. Use `/stats` to see user count")

@router.message(Command("add"), F.from_user.id.in_(ADMINS))
async def add_movie_handler(message: Message):
    if not message.reply_to_message or not (message.reply_to_message.video or message.reply_to_message.document):
        return await message.answer("❌ Reply to a video/file with `/add CODE`")
    
    code = message.text.split()[1]
    file_id = message.reply_to_message.video.file_id if message.reply_to_message.video else message.reply_to_message.document.file_id
    caption = message.reply_to_message.caption or "Enjoy your movie!"
    
    await db.add_movie(code, file_id, caption)
    await message.answer(f"✅ Movie saved! Code: `{code}`")

@router.message(Command("broadcast"), F.from_user.id.in_(ADMINS))
async def broadcast_handler(message: Message, bot: Bot):
    text = message.text.replace("/broadcast ", "")
    users = await db.get_all_users()
    count = 0
    
    for user_id in users:
        try:
            await bot.send_message(user_id, text)
            count += 1
        except:
            pass
    await message.answer(f"📢 Broadcast sent to {count} users.")