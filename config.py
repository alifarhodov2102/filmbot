import os
from dotenv import load_dotenv

# .env faylidan o'zgaruvchilarni yuklash
load_dotenv()

# 1. Bot Tokeni
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 2. Adminlar ro'yxati
# .env ichida ADMIN_ID=1092121944,1272624863 shaklida yoziladi
admin_ids_raw = os.getenv("ADMIN_ID", "")
ADMINS = [int(admin_id.strip()) for admin_id in admin_ids_raw.split(",") if admin_id.strip()]

# 3. Ma'lumotlar bazasi (Database)
# Railway-da Volume ishlatish uchun /app/data/bot_data.db manzilini oladi.
# Agarda DB_PATH topilmasa, lokal 'bot_data.db' dan foydalanadi.
DB_NAME = os.getenv("DB_PATH", "bot_data.db")

# 4. Majburiy obuna kanali ID-si
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))
