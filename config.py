import os
from dotenv import load_dotenv

load_dotenv()

# Bot Tokeni
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Adminlar ro'yxati (vergul bilan ajratilgan IDlar: 123,456)
admin_ids_raw = os.getenv("ADMIN_ID", "")
ADMINS = [int(admin_id.strip()) for admin_id in admin_ids_raw.split(",") if admin_id.strip()]

# Majburiy kanallar ro'yxati (IDlarni vergul bilan yozing: -1001,-1002)
channel_ids_raw = os.getenv("CHANNEL_ID", "")
CHANNELS = [int(ch_id.strip()) for ch_id in channel_ids_raw.split(",") if ch_id.strip()]

# Ma'lumotlar bazasi (Railway Volume uchun)
DB_NAME = os.getenv("DB_PATH", "bot_data.db")
