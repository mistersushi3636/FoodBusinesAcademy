from __future__ import annotations

import calendar as cal_mod
import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path

MASTER_DB = Path(__file__).parent / "dashboard.db"
PROJECTS_DIR = Path(__file__).parent / "projects"

MONTH_RU = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь",
}

METRICS_FIELDS = {
    "telegram": [
        ("subscribers_total",  "Подписчиков всего"),
        ("subscribers_growth", "Прирост за неделю"),
        ("views_avg",          "Просмотры на пост (среднее)"),
        ("reactions_avg",      "Реакции на пост (среднее)"),
        ("posts_count",        "Постов опубликовано"),
        ("leads_count",        "Лидов в бот"),
    ],
    "instagram": [
        ("subscribers_total",  "Подписчиков всего"),
        ("subscribers_growth", "Прирост за неделю"),
        ("reach_avg",          "Охват на пост (среднее)"),
        ("likes_avg",          "Лайки (среднее)"),
        ("saves_avg",          "Сохранения (среднее)"),
        ("posts_count",        "Постов/Reels опубликовано"),
    ],
    "youtube": [
        ("subscribers_total",  "Подписчиков всего"),
        ("subscribers_growth", "Прирост за неделю"),
        ("views_week",         "Просмотров за неделю"),
        ("videos_count",       "Видео/Shorts опубликовано"),
    ],
    "business": [
        ("inquiries",      "Обращений / заявок"),
        ("consultations",  "Консультаций проведено"),
    ],
}

PLATFORM_LABELS = {
    "telegram": "Telegram",
    "instagram": "Instagram",
    "youtube": "YouTube",
    "business": "Бизнес",
}


def _conn(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_master_db() -> None:
    PROJECTS_DIR.mkdir(exist_ok=True)
    conn = _conn(MASTER_DB)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT NOT NULL,
            slug         TEXT UNIQUE NOT NULL,
            description  TEXT DEFAULT '',
            architecture TEXT DEFAULT '',
            password_hash TEXT NOT NULL,
            db_path      TEXT NOT NULL,
            created_at   TEXT DEFAULT (datetime('now','localtime'))
        );
    """)
    conn.commit()
    conn.close()


def init_project_db(db_path: Path) -> None:
    conn = _conn(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS calendar_events (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            event_date   TEXT NOT NULL,
            title        TEXT NOT NULL,
            description  TEXT DEFAULT '',
            status       TEXT DEFAULT 'planned',
            event_type   TEXT DEFAULT 'task',
            created_at   TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS metrics (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start   TEXT NOT NULL,
            platform     TEXT NOT NULL,
            metric_name  TEXT NOT NULL,
            metric_value TEXT DEFAULT '0',
            created_at   TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS reports (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            period_start TEXT NOT NULL,
            period_end   TEXT NOT NULL,
            period_type  TEXT DEFAULT 'week',
            raw_data     TEXT DEFAULT '{}',
            analysis     TEXT DEFAULT '',
            created_at   TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS ideas (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            source     TEXT DEFAULT 'manual',
            content    TEXT NOT NULL,
            category   TEXT DEFAULT 'idea',
            status     TEXT DEFAULT 'new',
            tags       TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
    """)
    conn.commit()
    conn.close()


# ── Projects ────────────────────────────────────────────────────────────────

def get_all_projects() -> list[dict]:
    conn = _conn(MASTER_DB)
    rows = conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_project(slug: str) -> dict | None:
    conn = _conn(MASTER_DB)
    row = conn.execute("SELECT * FROM projects WHERE slug=?", (slug,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_project(name: str, slug: str, description: str,
                   architecture: str, password_hash: str) -> None:
    db_path = PROJECTS_DIR / f"{slug}.db"
    init_project_db(db_path)
    conn = _conn(MASTER_DB)
    conn.execute(
        "INSERT INTO projects (name,slug,description,architecture,password_hash,db_path) "
        "VALUES (?,?,?,?,?,?)",
        (name, slug, description, architecture, password_hash, str(db_path)),
    )
    conn.commit()
    conn.close()


def update_architecture(slug: str, text: str) -> None:
    conn = _conn(MASTER_DB)
    conn.execute("UPDATE projects SET architecture=? WHERE slug=?", (text, slug))
    conn.commit()
    conn.close()


def project_db_path(project: dict) -> Path:
    return Path(project["db_path"])


# ── Calendar ─────────────────────────────────────────────────────────────────

def add_event(db: Path, event_date: str, title: str,
              description: str, status: str, event_type: str) -> None:
    conn = _conn(db)
    conn.execute(
        "INSERT INTO calendar_events (event_date,title,description,status,event_type) "
        "VALUES (?,?,?,?,?)",
        (event_date, title, description, status, event_type),
    )
    conn.commit()
    conn.close()


def get_events_range(db: Path, start: str, end: str) -> list[dict]:
    conn = _conn(db)
    rows = conn.execute(
        "SELECT * FROM calendar_events WHERE event_date BETWEEN ? AND ? ORDER BY event_date",
        (start, end),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_event_status(db: Path, event_id: int, status: str) -> None:
    conn = _conn(db)
    conn.execute("UPDATE calendar_events SET status=? WHERE id=?", (status, event_id))
    conn.commit()
    conn.close()


def delete_event(db: Path, event_id: int) -> None:
    conn = _conn(db)
    conn.execute("DELETE FROM calendar_events WHERE id=?", (event_id,))
    conn.commit()
    conn.close()


def build_month_grid(year: int, month: int, events: list[dict]) -> dict:
    by_date: dict[str, list] = {}
    for e in events:
        by_date.setdefault(e["event_date"], []).append(e)

    c = cal_mod.Calendar(firstweekday=0)
    today = date.today()
    weeks = []
    for week in c.monthdatescalendar(year, month):
        days = []
        for d in week:
            ds = d.strftime("%Y-%m-%d")
            days.append({
                "date": ds,
                "day": d.day,
                "cur": d.month == month,
                "today": d == today,
                "events": by_date.get(ds, []),
            })
        weeks.append(days)

    pm = month - 1 if month > 1 else 12
    py = year if month > 1 else year - 1
    nm = month + 1 if month < 12 else 1
    ny = year if month < 12 else year + 1

    return {
        "weeks": weeks,
        "year": year, "month": month,
        "month_name": MONTH_RU[month],
        "py": py, "pm": pm,
        "ny": ny, "nm": nm,
    }


# ── Metrics / Reports ─────────────────────────────────────────────────────────

def save_metrics(db: Path, week_start: str, data: dict) -> None:
    conn = _conn(db)
    conn.execute("DELETE FROM metrics WHERE week_start=?", (week_start,))
    for platform, values in data.items():
        if isinstance(values, dict):
            for name, val in values.items():
                conn.execute(
                    "INSERT INTO metrics (week_start,platform,metric_name,metric_value) VALUES (?,?,?,?)",
                    (week_start, platform, name, str(val)),
                )
    conn.commit()
    conn.close()


def get_metrics_week(db: Path, week_start: str) -> dict:
    conn = _conn(db)
    rows = conn.execute("SELECT * FROM metrics WHERE week_start=?", (week_start,)).fetchall()
    conn.close()
    result: dict = {}
    for r in rows:
        result.setdefault(r["platform"], {})[r["metric_name"]] = r["metric_value"]
    return result


def get_all_week_starts(db: Path) -> list[str]:
    conn = _conn(db)
    rows = conn.execute(
        "SELECT DISTINCT week_start FROM metrics ORDER BY week_start DESC"
    ).fetchall()
    conn.close()
    return [r["week_start"] for r in rows]


def save_report(db: Path, period_start: str, period_end: str,
                period_type: str, raw_data: dict, analysis: str) -> None:
    conn = _conn(db)
    exists = conn.execute(
        "SELECT id FROM reports WHERE period_start=? AND period_type=?",
        (period_start, period_type),
    ).fetchone()
    payload = json.dumps(raw_data, ensure_ascii=False)
    if exists:
        conn.execute(
            "UPDATE reports SET raw_data=?,analysis=?,period_end=? WHERE id=?",
            (payload, analysis, period_end, exists["id"]),
        )
    else:
        conn.execute(
            "INSERT INTO reports (period_start,period_end,period_type,raw_data,analysis) "
            "VALUES (?,?,?,?,?)",
            (period_start, period_end, period_type, payload, analysis),
        )
    conn.commit()
    conn.close()


def get_reports(db: Path, period_type: str | None = None, limit: int = 30) -> list[dict]:
    conn = _conn(db)
    if period_type:
        rows = conn.execute(
            "SELECT * FROM reports WHERE period_type=? ORDER BY period_start DESC LIMIT ?",
            (period_type, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM reports ORDER BY period_start DESC LIMIT ?", (limit,)
        ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["raw_data"] = json.loads(d["raw_data"])
        except Exception:
            d["raw_data"] = {}
        result.append(d)
    return result


def get_report(db: Path, report_id: int) -> dict | None:
    conn = _conn(db)
    row = conn.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    try:
        d["raw_data"] = json.loads(d["raw_data"])
    except Exception:
        d["raw_data"] = {}
    return d


# ── Ideas ─────────────────────────────────────────────────────────────────────

IDEA_CATEGORIES = ["idea", "note", "insight", "task"]
IDEA_CATEGORY_LABELS = {
    "idea": "Идея", "note": "Заметка", "insight": "Инсайт", "task": "Задача"
}

def add_idea(db: Path, content: str, source: str = "manual",
             category: str = "idea", tags: str = "") -> None:
    conn = _conn(db)
    conn.execute(
        "INSERT INTO ideas (content,source,category,tags) VALUES (?,?,?,?)",
        (content, source, category, tags),
    )
    conn.commit()
    conn.close()


def get_ideas(db: Path, category: str | None = None,
              status: str | None = None, limit: int = 60) -> list[dict]:
    conn = _conn(db)
    q = "SELECT * FROM ideas WHERE 1=1"
    params: list = []
    if category:
        q += " AND category=?"; params.append(category)
    if status:
        q += " AND status=?"; params.append(status)
    q += " ORDER BY created_at DESC LIMIT ?"; params.append(limit)
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_idea_status(db: Path, idea_id: int, status: str) -> None:
    conn = _conn(db)
    conn.execute("UPDATE ideas SET status=? WHERE id=?", (status, idea_id))
    conn.commit()
    conn.close()


def delete_idea(db: Path, idea_id: int) -> None:
    conn = _conn(db)
    conn.execute("DELETE FROM ideas WHERE id=?", (idea_id,))
    conn.commit()
    conn.close()


# ── Overview stats ────────────────────────────────────────────────────────────

def get_stats(db: Path) -> dict:
    conn = _conn(db)
    s = {}
    def one(q, *a):
        r = conn.execute(q, a).fetchone()
        return r[0] if r else 0

    s["events_done"]    = one("SELECT COUNT(*) FROM calendar_events WHERE status='done'")
    s["events_planned"] = one("SELECT COUNT(*) FROM calendar_events WHERE status='planned'")
    s["events_total"]   = one("SELECT COUNT(*) FROM calendar_events")
    s["ideas_new"]      = one("SELECT COUNT(*) FROM ideas WHERE status='new'")
    s["ideas_total"]    = one("SELECT COUNT(*) FROM ideas")
    s["reports_total"]  = one("SELECT COUNT(*) FROM reports")

    r = conn.execute("SELECT week_start FROM metrics ORDER BY week_start DESC LIMIT 1").fetchone()
    s["latest_week"] = r["week_start"] if r else None

    # Latest metrics for overview
    if s["latest_week"]:
        rows = conn.execute(
            "SELECT platform,metric_name,metric_value FROM metrics WHERE week_start=?",
            (s["latest_week"],)
        ).fetchall()
        latest: dict = {}
        for row in rows:
            latest.setdefault(row["platform"], {})[row["metric_name"]] = row["metric_value"]
        s["latest_metrics"] = latest
    else:
        s["latest_metrics"] = {}

    conn.close()
    return s
