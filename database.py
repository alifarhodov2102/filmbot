import aiosqlite

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def create_tables(self):
        async with aiosqlite.connect(self.db_path) as db:
            # Table for Users (for broadcasting ads)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    join_date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Table for Movies (Code -> File ID mapping)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS movies (
                    movie_code TEXT PRIMARY KEY,
                    file_id TEXT,
                    caption TEXT
                )
            """)
            await db.commit()

    # --- User Methods ---
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

    # --- Movie Methods ---
    async def add_movie(self, code: str, file_id: str, caption: str = ""):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO movies (movie_code, file_id, caption) VALUES (?, ?, ?)",
                (code, file_id, caption)
            )
            await db.commit()

    async def get_movie(self, code: str):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT file_id, caption FROM movies WHERE movie_code = ?", (code,)
            ) as cursor:
                return await cursor.fetchone()

    async def delete_movie(self, code: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM movies WHERE movie_code = ?", (code,))
            await db.commit()