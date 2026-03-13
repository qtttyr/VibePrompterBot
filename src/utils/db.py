import aiosqlite
import os
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
_DEFAULT_DB_PATH = os.path.join(_PROJECT_ROOT, "data", "prompter.db")


class Database:
    def __init__(self, db_path: str = _DEFAULT_DB_PATH):
        self.db_path = db_path

    async def setup(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS usage (
                    user_id INTEGER,
                    usage_date TEXT,
                    count INTEGER,
                    PRIMARY KEY (user_id, usage_date)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS generations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    project_info TEXT,
                    editor TEXT,
                    stack TEXT,
                    idea TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS folder_gen_usage (
                    user_id INTEGER,
                    usage_date TEXT,
                    count INTEGER,
                    PRIMARY KEY (user_id, usage_date)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    user_id INTEGER PRIMARY KEY,
                    plan TEXT,
                    expires_at TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    language TEXT DEFAULT 'ru'
                )
            """)
            await db.commit()

    async def get_user_usage(self, user_id: int) -> int:
        today = date.today().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT count FROM usage WHERE user_id = ? AND usage_date = ?",
                (user_id, today)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def save_generation(self, user_id: int, data: dict):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO generations (user_id, project_info, editor, stack, idea)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, data.get('project_info'), data.get('editor'), data.get('stack'), data.get('idea')))
            await db.commit()

    async def save_generation_history(self, user_id: int, data: dict, result: dict):
        # Placeholder for extended history if needed, 
        # for now we use save_generation for the dashboard
        pass

    async def get_last_generations(self, user_id: int, limit: int = 5):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT project_info, editor, stack, idea, created_at FROM generations WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit)
            ) as cursor:
                return await cursor.fetchall()

    async def check_limit(self, user_id: int) -> bool:
        # 1. Check if user is PRO
        sub = await self.get_user_subscription(user_id)
        if sub and sub["expires_at"] > datetime.utcnow().isoformat():
            return True  # PRO users have no hard limits (or you can add a soft high limit here)

        today = date.today().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT count FROM usage WHERE user_id = ? AND usage_date = ?",
                (user_id, today)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row[0] < 2  # Free tier: 2 prompts / day
                return True

    async def increment_usage(self, user_id: int):
        today = date.today().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO usage (user_id, usage_date, count)
                VALUES (?, ?, 1)
                ON CONFLICT(user_id, usage_date) DO UPDATE SET count = count + 1
            """, (user_id, today))
            await db.commit()

    async def check_folder_gen_limit(self, user_id: int) -> bool:
        """Returns True if the user can still generate a structure today (limit: 1/day)."""
        # 1. Check if user is PRO
        sub = await self.get_user_subscription(user_id)
        if sub and sub["expires_at"] > datetime.utcnow().isoformat():
            return True  # PRO users bypass the limit

        today = date.today().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT count FROM folder_gen_usage WHERE user_id = ? AND usage_date = ?",
                (user_id, today)
            ) as cursor:
                row = await cursor.fetchone()
                return (row[0] if row else 0) < 1

    async def increment_folder_gen_usage(self, user_id: int) -> None:
        """Increment folder generation count for today."""
        today = date.today().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO folder_gen_usage (user_id, usage_date, count)
                VALUES (?, ?, 1)
                ON CONFLICT(user_id, usage_date) DO UPDATE SET count = count + 1
            """, (user_id, today))
            await db.commit()

    async def get_user_projects(self, user_id: int, limit: int = 5) -> list:
        """Return distinct recent projects for this user (project_info + stack)."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT project_info, stack
                FROM generations
                WHERE user_id = ?
                GROUP BY project_info
                ORDER BY MAX(created_at) DESC
                LIMIT ?
                """,
                (user_id, limit)
            ) as cursor:
                return await cursor.fetchall()

    # ─── Subscriptions ───────────────────────────────────────────────────────

    async def get_user_subscription(self, user_id: int) -> dict | None:
        """Returns the user's active subscription info, or None."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT plan, expires_at FROM subscriptions WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {"plan": row["plan"], "expires_at": row["expires_at"]}
                return None

    async def grant_subscription(self, user_id: int, plan: str, expires_at: str) -> None:
        """Upserts a subscription for the user."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO subscriptions (user_id, plan, expires_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    plan = excluded.plan,
                    expires_at = excluded.expires_at
            """, (user_id, plan, expires_at))
            await db.commit()

    async def get_user_language(self, user_id: int) -> str:
        """Returns the user's preferred language, defaulting to 'ru'."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT language FROM users WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else "ru"

    async def set_user_language(self, user_id: int, lang: str) -> None:
        """Updates or sets the user's language preference."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO users (user_id, language)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET language = excluded.language
            """, (user_id, lang))
            await db.commit()

db = Database()
