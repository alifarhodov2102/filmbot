from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from database import Database

router = Router()
db = Database("bot_data.db")

@router.message(CommandStart())
async def start_handler(message: Message):
    # Save user to DB for future broadcasts
    await db.add_user(message.from_user.id, message.from_user.username)
    await message.answer("👋 **Welcome to the Film Bot!**\n\n"
                         "Send me a movie code to get your video.")

@router.message(F.text)
async def movie_request(message: Message):
    code = message.text.strip()
    movie = await db.get_movie(code)
    
    if movie:
        file_id, caption = movie
        # Use send_copy or send_video to send the stored file_id
        await message.answer_video(video=file_id, caption=caption)
    else:
        await message.answer("❌ **Invalid Code.** Please check the code and try again.")