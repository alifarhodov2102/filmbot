import aiosqlite

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def create_tables(self):
        """Barcha kerakli jadvallarni yaratish."""
        async with aiosqlite.connect(self.db_path) as db:
            # Foydalanuvchilar jadvali
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    join_date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Kinolar jadvali
            await db.execute("""
                CREATE TABLE IF NOT EXISTS movies (
                    movie_code TEXT PRIMARY KEY,
                    file_id TEXT,
                    caption TEXT
                )
            """)
            # Kinolarni baholash jadvali (ixtiyoriy, lekin foydali)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS ratings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    movie_code TEXT,
                    rating INTEGER,
                    FOREIGN KEY (movie_code) REFERENCES movies (movie_code)
                )
            """)
            await db.commit()

    # --- Foydalanuvchi metodlari ---
    async def add_user(self, user_id: int, username: str = None):
        """Yangi foydalanuvchini bazaga qo'shish."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
                (user_id, username)
            )
            await db.commit()

    async def get_all_users(self):
        """Reklama tarqatish uchun barcha foydalanuvchilarni olish."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id FROM users") as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def get_stats(self):
        """Statistika: foydalanuvchilar va kinolar soni."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as c1:
                users_count = (await c1.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM movies") as c2:
                movies_count = (await c2.fetchone())[0]
            return users_count, movies_count

    # --- Kino metodlari ---
    async def add_movie(self, code: str, file_id: str, caption: str = ""):
        """Bazaga yangi kino qo'shish yoki mavjudini yangilash."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO movies (movie_code, file_id, caption) VALUES (?, ?, ?)",
                (code, file_id, caption)
            )
            await db.commit()

    async def get_movie(self, code: str):
        """Kodni yuborganda kino ma'lumotlarini olish."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT file_id, caption FROM movies WHERE movie_code = ?", (code,)
            ) as cursor:
                return await cursor.fetchone()

    async def delete_movie(self, code: str):
        """Kino kodini bazadan o'chirish."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM movies WHERE movie_code = ?", (code,))
            await db.commit()

    # --- Reyting metodlari ---
    async def add_rating(self, user_id: int, movie_code: str, rating: int):
        """Foydalanuvchi bergan bahoni saqlash."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO ratings (user_id, movie_code, rating) VALUES (?, ?, ?)",
                (user_id, movie_code, rating)
            )
            await db.commit()
