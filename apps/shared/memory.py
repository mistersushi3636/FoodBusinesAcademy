"""
Memory layer: SQLite task state + patterns/learnings.md.
Replaces Memory MCP — simpler, no external deps, server-friendly.
"""
import sqlite3
from datetime import datetime
from enum import Enum
from pathlib import Path

from loguru import logger


class TaskState(str, Enum):
    IDLE       = "idle"
    CAPTURED   = "captured"
    DRAFTING   = "drafting"
    VISUALIZING = "visualizing"
    REVIEWING  = "reviewing"
    AWAITING   = "awaiting"     # waiting for Anton approval
    PUBLISHING = "publishing"
    LEARNING   = "learning"
    DONE       = "done"
    CANCELLED  = "cancelled"
    FAILED     = "failed"


def get_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(db_path: Path) -> None:
    conn = get_db(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            state       TEXT NOT NULL DEFAULT 'idle',
            source_type TEXT,            -- 'voice' | 'text' | 'cron'
            source_file TEXT,            -- path to transcript/idea file
            idea_slug   TEXT,
            platforms   TEXT,            -- JSON list: ["telegram","instagram"]
            draft_tg    TEXT,            -- path to TG draft
            draft_ig    TEXT,
            draft_yt    TEXT,
            image_path  TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
            meta        TEXT             -- JSON freeform
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id     INTEGER NOT NULL,
            role        TEXT NOT NULL,   -- 'user' | 'assistant'
            content     TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_tasks_state   ON tasks(state);
        CREATE INDEX IF NOT EXISTS idx_conv_chat_id  ON conversations(chat_id);
    """)
    conn.commit()
    conn.close()
    logger.info(f"DB initialised: {db_path}")


def create_task(db_path: Path, source_type: str, source_file: str = "") -> int:
    conn = get_db(db_path)
    cur = conn.execute(
        "INSERT INTO tasks (state, source_type, source_file) VALUES (?,?,?)",
        (TaskState.CAPTURED, source_type, source_file),
    )
    conn.commit()
    task_id = cur.lastrowid
    conn.close()
    logger.info(f"Task created: id={task_id} source={source_type}")
    return task_id


def update_task(db_path: Path, task_id: int, **fields) -> None:
    fields["updated_at"] = datetime.utcnow().isoformat()
    set_clause = ", ".join(f"{k}=?" for k in fields)
    values = list(fields.values()) + [task_id]
    conn = get_db(db_path)
    conn.execute(f"UPDATE tasks SET {set_clause} WHERE id=?", values)
    conn.commit()
    conn.close()


def get_task(db_path: Path, task_id: int) -> dict | None:
    conn = get_db(db_path)
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_pending_tasks(db_path: Path) -> list[dict]:
    conn = get_db(db_path)
    rows = conn.execute(
        "SELECT * FROM tasks WHERE state NOT IN (?,?,?) ORDER BY id",
        (TaskState.DONE, TaskState.CANCELLED, TaskState.FAILED),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Chat history (for /chat multi-turn) ─────────────────────────────────────

def save_message(db_path: Path, chat_id: int, role: str, content: str) -> None:
    conn = get_db(db_path)
    conn.execute(
        "INSERT INTO conversations (chat_id, role, content) VALUES (?,?,?)",
        (chat_id, role, content),
    )
    conn.commit()
    conn.close()


def get_history(db_path: Path, chat_id: int, limit: int = 20) -> list[dict]:
    conn = get_db(db_path)
    rows = conn.execute(
        """SELECT role, content FROM conversations
           WHERE chat_id=? ORDER BY id DESC LIMIT ?""",
        (chat_id, limit),
    ).fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


# ─── Learnings file ───────────────────────────────────────────────────────────

def append_learning(learnings_path: Path, week: str, platform: str,
                    pillar: str, worked: str, metric: str,
                    hypothesis: str, apply: str) -> None:
    """Append one learning entry to patterns/learnings.md."""
    entry = f"""
## {week} · {platform} · {pillar}

**Сработало:** {worked}
**Метрика:** {metric}
**Гипотеза:** {hypothesis}
**Применять:** {apply}
"""
    content = learnings_path.read_text(encoding="utf-8")
    marker = "## Записи"
    idx = content.find(marker)
    if idx == -1:
        learnings_path.write_text(content + entry, encoding="utf-8")
    else:
        insert_at = idx + len(marker) + 1
        new_content = content[:insert_at] + "\n" + entry + content[insert_at:]
        learnings_path.write_text(new_content, encoding="utf-8")
    logger.info(f"Learning appended: {week} {platform}")
