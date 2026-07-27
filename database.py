import aiosqlite
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    @asynccontextmanager
    async def _connect(self) -> AsyncIterator[aiosqlite.Connection]:
        """
        Database bilan ulanish.

        SQLite'da foreign_keys har bir yangi connection uchun
        alohida yoqilishi kerak.
        """
        db = await aiosqlite.connect(self.db_path)

        try:
            await db.execute("PRAGMA foreign_keys = ON")
            await db.execute("PRAGMA journal_mode = WAL")
            await db.execute("PRAGMA busy_timeout = 5000")
            yield db
        finally:
            await db.close()

    async def create_tables(self):
        """
        Jadvallarni yaratadi va mavjud bazani xavfsiz yangilaydi.

        Muhim:
        - Mavjud database o'chirilmaydi.
        - DROP TABLE ishlatilmaydi.
        - Oldingi ma'lumotlar saqlanadi.
        """
        async with self._connect() as db:
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

            # Eski database'da is_series ustuni bo'lmasa qo'shamiz
            async with db.execute("PRAGMA table_info(movies)") as cursor:
                columns = await cursor.fetchall()

            column_names = {column[1] for column in columns}

            if "is_series" not in column_names:
                await db.execute("""
                    ALTER TABLE movies
                    ADD COLUMN is_series INTEGER DEFAULT 0
                """)

            # 3. Episodes jadvali
            await db.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    movie_code TEXT NOT NULL,
                    part_number INTEGER NOT NULL,
                    file_id TEXT NOT NULL,
                    FOREIGN KEY (movie_code)
                        REFERENCES movies (movie_code)
                        ON DELETE CASCADE
                )
            """)

            # 4. Ratings jadvali
            await db.execute("""
                CREATE TABLE IF NOT EXISTS ratings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    movie_code TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    FOREIGN KEY (movie_code)
                        REFERENCES movies (movie_code)
                        ON DELETE CASCADE
                )
            """)

            # 5. Favorites jadvali
            await db.execute("""
                CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    movie_code TEXT NOT NULL,
                    UNIQUE(user_id, movie_code),
                    FOREIGN KEY (movie_code)
                        REFERENCES movies (movie_code)
                        ON DELETE CASCADE
                )
            """)

            # Qidiruvlarni tezlashtirish uchun xavfsiz indexlar
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_episodes_movie_code
                ON episodes(movie_code)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_episodes_part_number
                ON episodes(movie_code, part_number)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_ratings_movie_code
                ON ratings(movie_code)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_ratings_user_id
                ON ratings(user_id)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_favorites_user_id
                ON favorites(user_id)
            """)

            await db.commit()

    # =========================================================
    # Foydalanuvchi metodlari
    # =========================================================

    async def add_user(
        self,
        user_id: int,
        username: Optional[str] = None
    ):
        """
        Yangi foydalanuvchini qo'shadi.

        Foydalanuvchi oldin mavjud bo'lsa username'ni yangilaydi.
        """
        async with self._connect() as db:
            await db.execute(
                """
                INSERT INTO users (user_id, username)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username
                """,
                (user_id, username)
            )
            await db.commit()

    async def get_all_users(self) -> list[int]:
        """
        Reklama tarqatish uchun barcha foydalanuvchi ID'larini qaytaradi.
        """
        async with self._connect() as db:
            async with db.execute(
                "SELECT user_id FROM users ORDER BY user_id ASC"
            ) as cursor:
                rows = await cursor.fetchall()

        return [row[0] for row in rows]

    async def get_stats(self) -> tuple[int, int]:
        """
        Foydalanuvchilar va animelar umumiy sonini qaytaradi.
        """
        async with self._connect() as db:
            async with db.execute(
                "SELECT COUNT(*) FROM users"
            ) as cursor:
                user_row = await cursor.fetchone()

            async with db.execute(
                "SELECT COUNT(*) FROM movies"
            ) as cursor:
                movie_row = await cursor.fetchone()

        user_count = user_row[0] if user_row else 0
        movie_count = movie_row[0] if movie_row else 0

        return user_count, movie_count

    async def get_detailed_stats(self) -> dict:
        """
        Admin paneli uchun batafsil statistika.
        """
        async with self._connect() as db:
            async with db.execute(
                "SELECT COUNT(*) FROM users"
            ) as cursor:
                users = (await cursor.fetchone())[0]

            async with db.execute(
                "SELECT COUNT(*) FROM movies"
            ) as cursor:
                movies = (await cursor.fetchone())[0]

            async with db.execute(
                "SELECT COUNT(*) FROM episodes"
            ) as cursor:
                episodes = (await cursor.fetchone())[0]

            async with db.execute(
                "SELECT COUNT(*) FROM favorites"
            ) as cursor:
                favorites = (await cursor.fetchone())[0]

            async with db.execute(
                "SELECT COUNT(*) FROM ratings"
            ) as cursor:
                ratings = (await cursor.fetchone())[0]

        return {
            "users": users,
            "movies": movies,
            "episodes": episodes,
            "favorites": favorites,
            "ratings": ratings,
        }

    # =========================================================
    # Anime va serial metodlari
    # =========================================================

    async def movie_exists(self, code: str) -> bool:
        """
        Berilgan kodda anime mavjudligini tekshiradi.
        """
        code = str(code).strip()

        async with self._connect() as db:
            async with db.execute(
                """
                SELECT 1
                FROM movies
                WHERE movie_code = ?
                LIMIT 1
                """,
                (code,)
            ) as cursor:
                row = await cursor.fetchone()

        return row is not None

    async def add_movie(
        self,
        code: str,
        file_id: str,
        caption: str,
        is_series: int = 0
    ) -> bool:
        """
        Yangi anime qo'shadi.

        Muhim:
        INSERT OR REPLACE ishlatilmaydi.

        Agar kod oldin mavjud bo'lsa:
        - eski anime almashtirilmaydi;
        - metod False qaytaradi.

        Muvaffaqiyatli qo'shilsa True qaytaradi.
        """
        code = str(code).strip()

        if not code:
            return False

        async with self._connect() as db:
            try:
                await db.execute(
                    """
                    INSERT INTO movies (
                        movie_code,
                        file_id,
                        caption,
                        is_series
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        code,
                        file_id,
                        caption,
                        int(bool(is_series))
                    )
                )

                await db.commit()
                return True

            except aiosqlite.IntegrityError:
                await db.rollback()
                return False

    async def update_movie(
        self,
        code: str,
        file_id: str,
        caption: str,
        is_series: int = 0
    ) -> bool:
        """
        Mavjud animeni ataylab yangilash uchun alohida metod.

        Oddiy add jarayonida bu metod ishlatilmaydi.
        """
        code = str(code).strip()

        async with self._connect() as db:
            cursor = await db.execute(
                """
                UPDATE movies
                SET file_id = ?,
                    caption = ?,
                    is_series = ?
                WHERE movie_code = ?
                """,
                (
                    file_id,
                    caption,
                    int(bool(is_series)),
                    code
                )
            )

            await db.commit()
            return cursor.rowcount > 0

    async def add_episode(
        self,
        code: str,
        part: int,
        file_id: str
    ) -> bool:
        """
        Serial qismini qo'shadi.

        Bir anime kodida bir xil qism raqami oldin mavjud bo'lsa,
        ikkinchi marta qo'shmaydi va False qaytaradi.
        """
        code = str(code).strip()

        try:
            part = int(part)
        except (TypeError, ValueError):
            return False

        if not code or part < 1:
            return False

        async with self._connect() as db:
            # Anime mavjudligini tekshiramiz
            async with db.execute(
                """
                SELECT 1
                FROM movies
                WHERE movie_code = ?
                LIMIT 1
                """,
                (code,)
            ) as cursor:
                movie = await cursor.fetchone()

            if movie is None:
                return False

            # Shu qism raqami avval mavjudligini tekshiramiz
            async with db.execute(
                """
                SELECT 1
                FROM episodes
                WHERE movie_code = ?
                  AND part_number = ?
                LIMIT 1
                """,
                (code, part)
            ) as cursor:
                existing_episode = await cursor.fetchone()

            if existing_episode is not None:
                return False

            await db.execute(
                """
                INSERT INTO episodes (
                    movie_code,
                    part_number,
                    file_id
                )
                VALUES (?, ?, ?)
                """,
                (code, part, file_id)
            )

            await db.commit()
            return True

    async def get_next_episode_number(self, code: str) -> int:
        """
        Serial uchun navbatdagi qism raqamini qaytaradi.

        Masalan, oxirgi qism 10 bo'lsa, 11 qaytaradi.
        """
        code = str(code).strip()

        async with self._connect() as db:
            async with db.execute(
                """
                SELECT COALESCE(MAX(part_number), 0)
                FROM episodes
                WHERE movie_code = ?
                """,
                (code,)
            ) as cursor:
                row = await cursor.fetchone()

        last_part = row[0] if row else 0
        return last_part + 1

    async def episode_exists(
        self,
        movie_code: str,
        part_num: int
    ) -> bool:
        """
        Berilgan qism mavjudligini tekshiradi.
        """
        movie_code = str(movie_code).strip()

        async with self._connect() as db:
            async with db.execute(
                """
                SELECT 1
                FROM episodes
                WHERE movie_code = ?
                  AND part_number = ?
                LIMIT 1
                """,
                (movie_code, part_num)
            ) as cursor:
                row = await cursor.fetchone()

        return row is not None

    async def delete_episode(
        self,
        movie_code: str,
        part_num: int
    ) -> bool:
        """
        Tanlangan qismni o'chiradi va qolgan qismlarni
        1, 2, 3... tartibida qayta raqamlaydi.

        Qism topilib o'chirilsa True qaytaradi.
        Topilmasa False qaytaradi.
        """
        movie_code = str(movie_code).strip()

        try:
            part_num = int(part_num)
        except (TypeError, ValueError):
            return False

        async with self._connect() as db:
            try:
                await db.execute("BEGIN IMMEDIATE")

                delete_cursor = await db.execute(
                    """
                    DELETE FROM episodes
                    WHERE movie_code = ?
                      AND part_number = ?
                    """,
                    (movie_code, part_num)
                )

                if delete_cursor.rowcount == 0:
                    await db.rollback()
                    return False

                # Qolgan qismlarni ID bo'yicha olamiz
                async with db.execute(
                    """
                    SELECT id
                    FROM episodes
                    WHERE movie_code = ?
                    ORDER BY part_number ASC, id ASC
                    """,
                    (movie_code,)
                ) as cursor:
                    rows = await cursor.fetchall()

                # Qismlarni 1 dan boshlab qayta raqamlaymiz
                for new_part_number, row in enumerate(rows, start=1):
                    episode_id = row[0]

                    await db.execute(
                        """
                        UPDATE episodes
                        SET part_number = ?
                        WHERE id = ?
                        """,
                        (new_part_number, episode_id)
                    )

                await db.commit()
                return True

            except Exception:
                await db.rollback()
                raise

    async def get_movie(self, code: str):
        """
        Anime ma'lumotlarini qaytaradi:

        (
            file_id,
            caption,
            is_series
        )
        """
        code = str(code).strip()

        async with self._connect() as db:
            async with db.execute(
                """
                SELECT file_id, caption, is_series
                FROM movies
                WHERE movie_code = ?
                """,
                (code,)
            ) as cursor:
                return await cursor.fetchone()

    async def get_episodes(self, code: str) -> list[tuple]:
        """
        Anime qismlarini tartib bilan qaytaradi:

        [
            (part_number, file_id),
            ...
        ]
        """
        code = str(code).strip()

        async with self._connect() as db:
            async with db.execute(
                """
                SELECT part_number, file_id
                FROM episodes
                WHERE movie_code = ?
                ORDER BY part_number ASC, id ASC
                """,
                (code,)
            ) as cursor:
                return await cursor.fetchall()

    async def delete_movie(self, code: str) -> bool:
        """
        Animeni barcha tegishli ma'lumotlari bilan to'liq o'chiradi.

        Explicit DELETE ishlatilgani sababli SQLite foreign key sozlamasi
        eski connectionlarda ishlamagan bo'lsa ham qoldiq qismlar qolmaydi.

        O'chiriladi:
        - episodes;
        - ratings;
        - favorites;
        - movies.

        Anime topilib o'chirilsa True qaytaradi.
        Topilmasa False qaytaradi.
        """
        code = str(code).strip()

        async with self._connect() as db:
            try:
                await db.execute("BEGIN IMMEDIATE")

                async with db.execute(
                    """
                    SELECT 1
                    FROM movies
                    WHERE movie_code = ?
                    LIMIT 1
                    """,
                    (code,)
                ) as cursor:
                    movie = await cursor.fetchone()

                if movie is None:
                    await db.rollback()
                    return False

                # Avval child jadvallarni tozalaymiz
                await db.execute(
                    "DELETE FROM episodes WHERE movie_code = ?",
                    (code,)
                )

                await db.execute(
                    "DELETE FROM ratings WHERE movie_code = ?",
                    (code,)
                )

                await db.execute(
                    "DELETE FROM favorites WHERE movie_code = ?",
                    (code,)
                )

                # Oxirida anime yozuvini o'chiramiz
                await db.execute(
                    "DELETE FROM movies WHERE movie_code = ?",
                    (code,)
                )

                await db.commit()
                return True

            except Exception:
                await db.rollback()
                raise

    # =========================================================
    # Ratings
    # =========================================================

    async def add_rating(
        self,
        user_id: int,
        movie_code: str,
        rating: int
    ) -> bool:
        """
        Anime uchun foydalanuvchi reytingini saqlaydi.

        Foydalanuvchi oldin baholagan bo'lsa,
        eski bahosi yangisi bilan almashtiriladi.
        """
        movie_code = str(movie_code).strip()

        try:
            rating = int(rating)
        except (TypeError, ValueError):
            return False

        if rating < 1 or rating > 5:
            return False

        async with self._connect() as db:
            # Anime mavjudligini tekshiramiz
            async with db.execute(
                """
                SELECT 1
                FROM movies
                WHERE movie_code = ?
                LIMIT 1
                """,
                (movie_code,)
            ) as cursor:
                movie = await cursor.fetchone()

            if movie is None:
                return False

            # Foydalanuvchining oldingi bahosini o'chiramiz
            await db.execute(
                """
                DELETE FROM ratings
                WHERE user_id = ?
                  AND movie_code = ?
                """,
                (user_id, movie_code)
            )

            # Yangi bahoni qo'shamiz
            await db.execute(
                """
                INSERT INTO ratings (
                    user_id,
                    movie_code,
                    rating
                )
                VALUES (?, ?, ?)
                """,
                (user_id, movie_code, rating)
            )

            await db.commit()
            return True

    async def get_movie_rating(
        self,
        movie_code: str
    ) -> tuple[float, int]:
        """
        Anime reytingining o'rtacha qiymati va ovozlar sonini qaytaradi.

        Misol:
        (4.7, 25)
        """
        movie_code = str(movie_code).strip()

        async with self._connect() as db:
            async with db.execute(
                """
                SELECT
                    COALESCE(AVG(rating), 0),
                    COUNT(*)
                FROM ratings
                WHERE movie_code = ?
                """,
                (movie_code,)
            ) as cursor:
                row = await cursor.fetchone()

        if not row:
            return 0.0, 0

        average = round(float(row[0]), 1)
        count = int(row[1])

        return average, count

    # =========================================================
    # Favorites — Mening animelarim
    # =========================================================

    async def add_to_favorites(
        self,
        user_id: int,
        movie_code: str
    ) -> bool:
        """
        Animeni foydalanuvchi sevimlilariga qo'shadi.

        Yangi qo'shilsa True.
        Oldin mavjud bo'lsa False.
        """
        movie_code = str(movie_code).strip()

        async with self._connect() as db:
            # Anime mavjudligini tekshiramiz
            async with db.execute(
                """
                SELECT 1
                FROM movies
                WHERE movie_code = ?
                LIMIT 1
                """,
                (movie_code,)
            ) as cursor:
                movie = await cursor.fetchone()

            if movie is None:
                return False

            cursor = await db.execute(
                """
                INSERT OR IGNORE INTO favorites (
                    user_id,
                    movie_code
                )
                VALUES (?, ?)
                """,
                (user_id, movie_code)
            )

            await db.commit()
            return cursor.rowcount > 0

    async def remove_from_favorites(
        self,
        user_id: int,
        movie_code: str
    ) -> bool:
        """
        Animeni foydalanuvchi sevimlilaridan olib tashlaydi.
        """
        movie_code = str(movie_code).strip()

        async with self._connect() as db:
            cursor = await db.execute(
                """
                DELETE FROM favorites
                WHERE user_id = ?
                  AND movie_code = ?
                """,
                (user_id, movie_code)
            )

            await db.commit()
            return cursor.rowcount > 0

    async def is_favorite(
        self,
        user_id: int,
        movie_code: str
    ) -> bool:
        """
        Anime foydalanuvchining sevimlilarida mavjudligini tekshiradi.
        """
        movie_code = str(movie_code).strip()

        async with self._connect() as db:
            async with db.execute(
                """
                SELECT 1
                FROM favorites
                WHERE user_id = ?
                  AND movie_code = ?
                LIMIT 1
                """,
                (user_id, movie_code)
            ) as cursor:
                row = await cursor.fetchone()

        return row is not None

    async def get_favorites(self, user_id: int) -> list[str]:
        """
        Foydalanuvchi saqlagan anime kodlarini qaytaradi.
        """
        async with self._connect() as db:
            async with db.execute(
                """
                SELECT favorites.movie_code
                FROM favorites
                INNER JOIN movies
                    ON movies.movie_code = favorites.movie_code
                WHERE favorites.user_id = ?
                ORDER BY favorites.id DESC
                """,
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()

        return [row[0] for row in rows]
