from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import aiosqlite

from config import settings

DB_PATH = settings.vault_path / "bots" / "anton-assistant" / "planner.db"


async def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                task_date TEXT,
                task_time TEXT,
                is_done INTEGER DEFAULT 0,
                is_important INTEGER DEFAULT 0,
                remind_1h INTEGER DEFAULT 1,
                remind_at_time INTEGER DEFAULT 1,
                reminded_1h INTEGER DEFAULT 0,
                reminded_at INTEGER DEFAULT 0,
                recurring TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS planner_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        await db.commit()


async def add_task(
    title: str,
    task_date: Optional[str] = None,
    task_time: Optional[str] = None,
    is_important: bool = False,
    recurring: Optional[str] = None,
) -> int:
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO tasks
               (title, task_date, task_time, is_important, recurring, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (title, task_date, task_time, int(is_important), recurring, now, now),
        )
        await db.commit()
        return cursor.lastrowid


async def get_task(task_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_tasks_for_date(date_str: str) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT * FROM tasks
               WHERE task_date = ? AND is_done = 0
               ORDER BY task_time ASC""",
            (date_str,),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_overdue_tasks(before_date: str) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT * FROM tasks
               WHERE task_date < ? AND is_done = 0 AND task_date IS NOT NULL
               ORDER BY task_date ASC, task_time ASC""",
            (before_date,),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_all_pending() -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT * FROM tasks WHERE is_done = 0
               ORDER BY task_date ASC, task_time ASC"""
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def mark_done(task_id: int) -> None:
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tasks SET is_done = 1, updated_at = ? WHERE id = ?", (now, task_id)
        )
        await db.commit()


async def update_task(task_id: int, **kwargs) -> None:
    if not kwargs:
        return
    kwargs["updated_at"] = datetime.now().isoformat()
    set_clause = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [task_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", vals)
        await db.commit()


async def delete_task(task_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        await db.commit()


async def get_pending_reminders_1h(date_str: str, time_str: str) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT * FROM tasks
               WHERE task_date = ? AND task_time = ?
               AND is_done = 0 AND remind_1h = 1 AND reminded_1h = 0""",
            (date_str, time_str),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_pending_reminders_at(date_str: str, time_str: str) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT * FROM tasks
               WHERE task_date = ? AND task_time = ?
               AND is_done = 0 AND remind_at_time = 1 AND reminded_at = 0""",
            (date_str, time_str),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_setting(key: str, default: str = "") -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT value FROM planner_settings WHERE key = ?", (key,))
        row = await cur.fetchone()
        return row[0] if row else default


async def set_setting(key: str, value: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO planner_settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        await db.commit()
