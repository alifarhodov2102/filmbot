import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Bot settings
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Enter your Telegram ID and any other admin IDs here
ADMINS = [int(os.getenv("ADMIN_ID", 0))] 

# Agarda Railway-da bo'lsa Volume-dan foydalanadi, bo'lmasa lokal baza
DB_NAME = os.getenv("DB_PATH", "/app/data/bot_data.db")

# Channel ID (e.g., -100123456789) where users must subscribe
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))

# Database file name
DB_NAME = "bot_data.db"
