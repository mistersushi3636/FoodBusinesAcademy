"""
FBA 2.0 Dashboard — FastAPI web app.
Shows: pipeline tasks, recent drafts, metrics, learnings, plan.
Access: https://mistersushi36.pro
"""
import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

VAULT = Path(__file__).parents[2]
DB_PATH = VAULT / "apps" / "anton-assistant" / "fba.db"
TEMPLATES = Path(__file__).parent / "templates"

app = FastAPI(title="FBA 2.0 Dashboard", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES))


def _db():
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _get_tasks(limit: int = 20) -> list[dict]:
    conn = _db()
    if not conn:
        return []
    rows = conn.execute(
        "SELECT * FROM tasks ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _get_recent_plans(limit: int = 3) -> list[dict]:
    plans_dir = VAULT / "content" / "plans"
    if not plans_dir.exists():
        return []
    files = sorted(plans_dir.glob("*.md"), reverse=True)[:limit]
    result = []
    for f in files:
        content = f.read_text(encoding="utf-8")
        preview = content[:500].replace("<", "&lt;").replace(">", "&gt;")
        result.append({"name": f.stem, "preview": preview})
    return result


def _get_learnings_preview() -> str:
    lf = VAULT / "patterns" / "learnings.md"
    if not lf.exists():
        return "Записей пока нет."
    content = lf.read_text(encoding="utf-8")
    entries = [l for l in content.split("##") if "20" in l]
    if not entries:
        return "Записей пока нет."
    return ("## " + entries[0])[:800]


def _count_drafts() -> dict:
    drafts_dir = VAULT / "content" / "drafts"
    if not drafts_dir.exists():
        return {"total": 0}
    files = list(drafts_dir.glob("*.md"))
    return {"total": len(files)}


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    tasks = _get_tasks(20)
    state_counts: dict[str, int] = {}
    for t in tasks:
        s = t.get("state", "?")
        state_counts[s] = state_counts.get(s, 0) + 1

    return templates.TemplateResponse("index.html", {
        "request": request,
        "now": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "tasks": tasks[:10],
        "state_counts": state_counts,
        "plans": _get_recent_plans(),
        "learnings": _get_learnings_preview(),
        "drafts": _count_drafts(),
    })


@app.get("/health")
async def health():
    return {"status": "ok", "vault": str(VAULT), "db": DB_PATH.exists()}
