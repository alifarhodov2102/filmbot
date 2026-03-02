# 🎬 Telegram Film Bot (aiogram 3.x)

A high-performance Telegram bot built with **aiogram 3.x** and **aiosqlite**. This bot allows users to find movies using unique codes, but only after they have subscribed to your mandatory Telegram channel.

## 🚀 Features
* **Mandatory Subscription:** Users must join your channel to access the bot.
* **Telegram-as-DB:** Uses Telegram's servers to store movies via `file_id` (Zero hosting cost for videos).
* **Admin Panel:** * `/add CODE` (Reply to a video to save it).
    * `/broadcast` (Send ads/messages to all users).
    * `/stats` (Monitor user growth).
* **24/7 Deployment:** Fully compatible with Railway.app and Docker.

---

## 🛠 Tech Stack
* **Language:** Python 3.11+
* **Framework:** [aiogram 3.x](https://docs.aiogram.dev/)
* **Database:** SQLite (via `aiosqlite`)
* **Storage:** Private Telegram Channel

---

## 📂 Project Structure
```text
filmbot/
├── handlers/          # Admin and User logic
├── bot.py             # Entry point
├── database.py        # SQL queries
├── keyboards.py       # Inline buttons
├── middlewares.py     # Subscription gatekeeper
├── config.py          # Environment settings
└── Dockerfile         # Deployment config
```
## ⚙️ Installation & Setup

* **Clone the repository:**
```text
git clone [https://github.com/AliCapone21/filmbot.git](https://github.com/AliCapone21/filmbot.git)
cd filmbot
```

* **Create a .env file:**
```text
BOT_TOKEN=your_bot_token
ADMIN_ID=your_telegram_id
CHANNEL_ID=-100xxxxxxxxxx
```
* **Install dependencies:**
```text
pip install -r requirements.txt
```

* **Run the bot:**
```text
python bot.py
```

## ☁️ Deployment (Railway)

Connect your GitHub repository to Railway.app.

Create a Volume in Railway and mount it to /app/data.

In Railway Variables, set DB_NAME to /app/data/bot_data.db.

The Dockerfile will handle the rest.

## 🤝 Contribution

Feel free to fork this project and submit pull requests for new features!

