import aiosqlite

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def create_tables(self):
        """Barcha kerakli jadvallarni (Users, Movies, Episodes, Ratings) yaratish."""
        async with aiosqlite.connect(self.db_path) as db:
            # 1. Foydalanuvchilar jadvali
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    join_date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # 2. Kinolar va Seriallar asosi
            # is_series: 0 - Oddiy kino, 1 - Serial
            await db.execute("""
                CREATE TABLE IF NOT EXISTS movies (
                    movie_code TEXT PRIMARY KEY,
                    file_id TEXT, 
                    caption TEXT,
                    is_series INTEGER DEFAULT 0
                )
            """)
            # 3. Serial qismlari jadvali
            await db.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    movie_code TEXT,
                    part_number INTEGER,
                    file_id TEXT,
                    FOREIGN KEY (movie_code) REFERENCES movies (movie_code) ON DELETE CASCADE
                )
            """)
            # 4. Baholash tizimi
            await db.execute("""
                CREATE TABLE IF NOT EXISTS ratings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    movie_code TEXT,
                    rating INTEGER,
                    FOREIGN KEY (movie_code) REFERENCES movies (movie_code) ON DELETE CASCADE
                )
            """)
            await db.commit()

    # --- Foydalanuvchi metodlari ---
    async def add_user(self, user_id: int, username: str = None):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
                (user_id, username)
            )
            await db.commit()

    async def get_all_users(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id FROM users") as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def get_stats(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as c1:
                u_count = (await c1.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM movies") as c2:
                m_count = (await c2.fetchone())[0]
            return u_count, m_count

    # --- Kino va Serial metodlari ---
    async def add_movie(self, code: str, file_id: str, caption: str, is_series: int = 0):
        """Kino yoki Serial asosini qo'shish."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO movies (movie_code, file_id, caption, is_series) VALUES (?, ?, ?, ?)",
                (code, file_id, caption, is_series)
            )
            await db.commit()

    async def add_episode(self, code: str, part: int, file_id: str):
        """Serialning alohida qismini qo'shish."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO episodes (movie_code, part_number, file_id) VALUES (?, ?, ?)",
                (code, part, file_id)
            )
            await db.commit()

    async def get_movie(self, code: str):
        """Kod orqali ma'lumot olish (file_id, caption, is_series)."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT file_id, caption, is_series FROM movies WHERE movie_code = ?", (code,)
            ) as cursor:
                return await cursor.fetchone()

    async def get_episodes(self, code: str):
        """Serialning barcha qismlarini olish."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT part_number, file_id FROM episodes WHERE movie_code = ? ORDER BY part_number ASC", 
                (code,)
            ) as cursor:
                return await cursor.fetchall()

    async def delete_movie(self, code: str):
        """Kino/Serialni va unga tegishli barcha qismlarni o'chirish."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM movies WHERE movie_code = ?", (code,))
            # FOREIGN KEY ON DELETE CASCADE bo'lgani uchun qismlar avtomat o'chadi
            await db.commit()

    # --- Reyting metodlari ---
    async def add_rating(self, user_id: int, movie_code: str, rating: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO ratings (user_id, movie_code, rating) VALUES (?, ?, ?)",
                (user_id, movie_code, rating)
            )
            await db.commit()