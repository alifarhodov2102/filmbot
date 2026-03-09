import aiosqlite

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def create_tables(self):
        """Jadvallarni yaratish va mavjud bazani yangilash (Migration)."""
        async with aiosqlite.connect(self.db_path) as db:
            # 1. Users jadvali
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    join_date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 2. Movies jadvali
            await db.execute("""
                CREATE TABLE IF NOT EXISTS movies (
                    movie_code TEXT PRIMARY KEY,
                    file_id TEXT, 
                    caption TEXT,
                    is_series INTEGER DEFAULT 0
                )
            """)

            # --- MIGRATION: is_series ustunini tekshirish ---
            try:
                await db.execute("ALTER TABLE movies ADD COLUMN is_series INTEGER DEFAULT 0")
                await db.commit()
            except:
                pass

            # 3. Episodes jadvali (Serial qismlari)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    movie_code TEXT,
                    part_number INTEGER,
                    file_id TEXT,
                    FOREIGN KEY (movie_code) REFERENCES movies (movie_code) ON DELETE CASCADE
                )
            """)

            # 4. Ratings jadvali
            await db.execute("""
                CREATE TABLE IF NOT EXISTS ratings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    movie_code TEXT,
                    rating INTEGER,
                    FOREIGN KEY (movie_code) REFERENCES movies (movie_code) ON DELETE CASCADE
                )
            """)

            # 5. Favorites jadvali (Mening kinolarim)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    movie_code TEXT,
                    UNIQUE(user_id, movie_code),
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
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO movies (movie_code, file_id, caption, is_series) VALUES (?, ?, ?, ?)",
                (code, file_id, caption, is_series)
            )
            await db.commit()

    async def add_episode(self, code: str, part: int, file_id: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO episodes (movie_code, part_number, file_id) VALUES (?, ?, ?)",
                (code, part, file_id)
            )
            await db.commit()

    async def get_movie(self, code: str):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT file_id, caption, is_series FROM movies WHERE movie_code = ?", (code,)
            ) as cursor:
                return await cursor.fetchone()

    async def get_episodes(self, code: str):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT part_number, file_id FROM episodes WHERE movie_code = ? ORDER BY part_number ASC", 
                (code,)
            ) as cursor:
                return await cursor.fetchall()

    async def delete_movie(self, code: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM movies WHERE movie_code = ?", (code,))
            await db.commit()

    # --- Reyting metodlari ---
    async def add_rating(self, user_id: int, movie_code: str, rating: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO ratings (user_id, movie_code, rating) VALUES (?, ?, ?)",
                (user_id, movie_code, rating)
            )
            await db.commit()

    # --- Favorites (Mening kinolarim) metodlari ---
    async def add_to_favorites(self, user_id: int, movie_code: str):
        """Kinoni sevimlilarga qo'shish."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO favorites (user_id, movie_code) VALUES (?, ?)",
                (user_id, movie_code)
            )
            await db.commit()

    async def get_favorites(self, user_id: int):
        """Foydalanuvchining barcha sevimlilarini olish."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT movie_code FROM favorites WHERE user_id = ?", (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def remove_from_favorites(self, user_id: int, movie_code: str):
        """Kinoni sevimlilardan o'chirish."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM favorites WHERE user_id = ? AND movie_code = ?",
                (user_id, movie_code)
            )
            await db.commit()