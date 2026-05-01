"""
FBA 2.0 Dashboard — мультипроектный дашборд.
Доступ: https://mistersushi36.pro
"""
from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from pathlib import Path

# shared libs доступны через vault root
_vault = Path(__file__).parents[2]
if str(_vault) not in sys.path:
    sys.path.insert(0, str(_vault))

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import db as _db
import auth as _auth

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

app = FastAPI(title="FBA Dashboard", docs_url=None, redoc_url=None)
_static = Path(__file__).parent / "static"
_static.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_static)), name="static")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

_db.init_master_db()


# ── helpers ──────────────────────────────────────────────────────────────────

def _render(request: Request, tpl: str, ctx: dict) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name=tpl, context=ctx)


def _authed(request: Request, slug: str):
    """Return project dict if authed, else RedirectResponse."""
    session_slug = _auth.get_session_slug(request)
    if session_slug != slug:
        return _auth.redirect_to_login(slug)
    project = _db.get_project(slug)
    if not project:
        return RedirectResponse("/", status_code=302)
    return project


def _week_bounds() -> tuple[str, str]:
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")


async def _analyze_metrics(project_name: str, week_start: str,
                            raw_data: dict) -> str:
    if not ANTHROPIC_API_KEY:
        return "Anthropic API ключ не настроен — анализ недоступен."
    try:
        from apps.shared.anthropic_client import ask
        import json

        lines = []
        for platform, fields in _db.METRICS_FIELDS.items():
            label = _db.PLATFORM_LABELS.get(platform, platform.upper())
            lines.append(f"\n{label}:")
            pdata = raw_data.get(platform, {})
            for key, ru_label in fields:
                val = pdata.get(key, "—")
                lines.append(f"  {ru_label}: {val}")

        extra = raw_data.get("extra", {})
        if extra.get("best_content"):
            lines.append(f"\nЛучший контент: {extra['best_content']}")
        if extra.get("main_insight"):
            lines.append(f"Главный вывод: {extra['main_insight']}")

        prompt = (
            f"Проанализируй метрики за неделю {week_start} "
            f"для проекта «{project_name}»:\n"
            + "\n".join(lines)
            + "\n\nНапиши анализ (~250 слов):\n"
            "1. Оценка недели (1–10) с кратким обоснованием\n"
            "2. Главные достижения (2–3 пункта)\n"
            "3. Проблемные зоны (2–3 пункта)\n"
            "4. Три конкретных действия на следующую неделю\n\n"
            "Конкретно, используй числа из данных."
        )
        return await ask(
            api_key=ANTHROPIC_API_KEY,
            system="Ты стратегический аналитик контента для ресторанного бизнеса.",
            user=prompt,
            max_tokens=1200,
        )
    except Exception as e:
        return f"Ошибка анализа: {e}"


# ── Landing ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    projects = _db.get_all_projects()
    return _render(request, "index.html", {"projects": projects})


# ── Create project ────────────────────────────────────────────────────────────

@app.get("/create", response_class=HTMLResponse)
async def create_form(request: Request):
    return _render(request, "create.html", {"error": None})


@app.post("/create")
async def create_project(
    request: Request,
    name: str = Form(...),
    slug: str = Form(...),
    description: str = Form(""),
    password: str = Form(...),
    confirm: str = Form(...),
):
    slug = slug.strip().lower().replace(" ", "-")
    error = None
    if not slug or not name or not password:
        error = "Заполни все обязательные поля."
    elif password != confirm:
        error = "Пароли не совпадают."
    elif _db.get_project(slug):
        error = f"Проект «{slug}» уже существует."
    elif len(password) < 6:
        error = "Пароль минимум 6 символов."

    if error:
        return _render(request, "create.html", {"error": error})

    pw_hash = _auth.hash_password(password)
    _db.create_project(name, slug, description, "", pw_hash)
    return RedirectResponse(f"/p/{slug}/login", status_code=302)


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.get("/p/{slug}/login", response_class=HTMLResponse)
async def login_form(request: Request, slug: str):
    project = _db.get_project(slug)
    if not project:
        return RedirectResponse("/", status_code=302)
    # Already authed?
    if _auth.get_session_slug(request) == slug:
        return RedirectResponse(f"/p/{slug}/", status_code=302)
    return _render(request, "login.html", {"project": project, "error": None})


@app.post("/p/{slug}/login")
async def login_submit(request: Request, slug: str, password: str = Form(...)):
    project = _db.get_project(slug)
    if not project:
        return RedirectResponse("/", status_code=302)

    if not _auth.verify_password(password, project["password_hash"]):
        return _render(request, "login.html", {
            "project": project,
            "error": "Неверный пароль."
        })

    response = RedirectResponse(f"/p/{slug}/", status_code=302)
    response.set_cookie(
        key=_auth.COOKIE_NAME,
        value=_auth.make_cookie(slug),
        max_age=_auth.SESSION_TTL,
        httponly=True,
        samesite="lax",
    )
    return response


@app.get("/p/{slug}/logout")
async def logout(slug: str):
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie(_auth.COOKIE_NAME)
    return response


# ── Overview ──────────────────────────────────────────────────────────────────

@app.get("/p/{slug}/", response_class=HTMLResponse)
async def overview(request: Request, slug: str):
    result = _authed(request, slug)
    if isinstance(result, RedirectResponse):
        return result
    project = result
    pdb = _db.project_db_path(project)
    _db.init_project_db(pdb)

    stats = _db.get_stats(pdb)
    recent_events = _db.get_events_range(
        pdb,
        (date.today() - timedelta(days=7)).strftime("%Y-%m-%d"),
        (date.today() + timedelta(days=30)).strftime("%Y-%m-%d"),
    )
    recent_reports = _db.get_reports(pdb, limit=3)
    recent_ideas = _db.get_ideas(pdb, status="new", limit=5)

    return _render(request, "overview.html", {
        "project": project,
        "tab": "overview",
        "stats": stats,
        "recent_events": recent_events,
        "recent_reports": recent_reports,
        "recent_ideas": recent_ideas,
        "platform_labels": _db.PLATFORM_LABELS,
        "metrics_fields": _db.METRICS_FIELDS,
    })


@app.post("/p/{slug}/architecture")
async def update_arch(request: Request, slug: str, architecture: str = Form("")):
    result = _authed(request, slug)
    if isinstance(result, RedirectResponse):
        return result
    _db.update_architecture(slug, architecture)
    return RedirectResponse(f"/p/{slug}/", status_code=302)


# ── Calendar ──────────────────────────────────────────────────────────────────

@app.get("/p/{slug}/calendar", response_class=HTMLResponse)
async def calendar_view(request: Request, slug: str,
                         year: int = 0, month: int = 0):
    result = _authed(request, slug)
    if isinstance(result, RedirectResponse):
        return result
    project = result
    pdb = _db.project_db_path(project)

    today = date.today()
    y = year or today.year
    m = month or today.month

    from datetime import date as dt
    import calendar as cal
    _, last_day = cal.monthrange(y, m)
    events = _db.get_events_range(
        pdb,
        f"{y:04d}-{m:02d}-01",
        f"{y:04d}-{m:02d}-{last_day:02d}",
    )
    grid = _db.build_month_grid(y, m, events)

    return _render(request, "calendar.html", {
        "project": project,
        "tab": "calendar",
        "grid": grid,
        "today": today.strftime("%Y-%m-%d"),
        "event_types": ["task", "milestone", "meeting", "content", "other"],
        "event_type_labels": {
            "task": "Задача", "milestone": "Веха",
            "meeting": "Встреча", "content": "Контент", "other": "Другое",
        },
        "status_labels": {
            "planned": "Запланировано", "done": "Выполнено", "cancelled": "Отменено"
        },
    })


@app.post("/p/{slug}/calendar/add")
async def calendar_add(
    request: Request, slug: str,
    event_date: str = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    event_type: str = Form("task"),
    status: str = Form("planned"),
):
    result = _authed(request, slug)
    if isinstance(result, RedirectResponse):
        return result
    pdb = _db.project_db_path(result)
    _db.add_event(pdb, event_date, title, description, status, event_type)
    y, m = event_date[:4], event_date[5:7]
    return RedirectResponse(f"/p/{slug}/calendar?year={y}&month={m}", status_code=302)


@app.post("/p/{slug}/calendar/{event_id}/done")
async def event_done(request: Request, slug: str, event_id: int):
    result = _authed(request, slug)
    if isinstance(result, RedirectResponse):
        return result
    _db.update_event_status(_db.project_db_path(result), event_id, "done")
    return RedirectResponse(f"/p/{slug}/calendar", status_code=302)


@app.post("/p/{slug}/calendar/{event_id}/delete")
async def event_delete(request: Request, slug: str, event_id: int):
    result = _authed(request, slug)
    if isinstance(result, RedirectResponse):
        return result
    _db.delete_event(_db.project_db_path(result), event_id)
    return RedirectResponse(f"/p/{slug}/calendar", status_code=302)


# ── Reports ───────────────────────────────────────────────────────────────────

@app.get("/p/{slug}/reports", response_class=HTMLResponse)
async def reports_list(request: Request, slug: str, period: str = "week"):
    result = _authed(request, slug)
    if isinstance(result, RedirectResponse):
        return result
    project = result
    pdb = _db.project_db_path(project)

    reports = _db.get_reports(pdb, period_type=period if period != "all" else None)

    ws, _ = _week_bounds()
    return _render(request, "reports.html", {
        "project": project,
        "tab": "reports",
        "reports": reports,
        "period_filter": period,
        "metrics_fields": _db.METRICS_FIELDS,
        "platform_labels": _db.PLATFORM_LABELS,
        "current_week": ws,
    })


@app.get("/p/{slug}/reports/new", response_class=HTMLResponse)
async def report_new_form(request: Request, slug: str):
    result = _authed(request, slug)
    if isinstance(result, RedirectResponse):
        return result
    project = result
    ws, we = _week_bounds()
    return _render(request, "report_form.html", {
        "project": project,
        "tab": "reports",
        "metrics_fields": _db.METRICS_FIELDS,
        "platform_labels": _db.PLATFORM_LABELS,
        "week_start": ws,
        "week_end": we,
        "error": None,
    })


@app.post("/p/{slug}/reports/new")
async def report_submit(request: Request, slug: str):
    result = _authed(request, slug)
    if isinstance(result, RedirectResponse):
        return result
    project = result
    pdb = _db.project_db_path(project)

    form = await request.form()
    week_start = str(form.get("week_start", ""))
    week_end = str(form.get("week_end", ""))

    raw_data: dict = {}
    for platform, fields in _db.METRICS_FIELDS.items():
        raw_data[platform] = {}
        for key, _ in fields:
            val = str(form.get(f"{platform}_{key}", "")).strip()
            raw_data[platform][key] = val

    raw_data["extra"] = {
        "best_content": str(form.get("best_content", "")),
        "main_insight": str(form.get("main_insight", "")),
    }

    _db.save_metrics(pdb, week_start, raw_data)
    analysis = await _analyze_metrics(project["name"], week_start, raw_data)
    _db.save_report(pdb, week_start, week_end, "week", raw_data, analysis)

    return RedirectResponse(f"/p/{slug}/reports", status_code=302)


@app.get("/p/{slug}/reports/{report_id}", response_class=HTMLResponse)
async def report_detail(request: Request, slug: str, report_id: int):
    result = _authed(request, slug)
    if isinstance(result, RedirectResponse):
        return result
    project = result
    pdb = _db.project_db_path(project)
    report = _db.get_report(pdb, report_id)
    if not report:
        return RedirectResponse(f"/p/{slug}/reports", status_code=302)
    return _render(request, "report_detail.html", {
        "project": project,
        "tab": "reports",
        "report": report,
        "metrics_fields": _db.METRICS_FIELDS,
        "platform_labels": _db.PLATFORM_LABELS,
    })


# ── Ideas ─────────────────────────────────────────────────────────────────────

@app.get("/p/{slug}/ideas", response_class=HTMLResponse)
async def ideas_list(request: Request, slug: str,
                      category: str = "", status: str = "new"):
    result = _authed(request, slug)
    if isinstance(result, RedirectResponse):
        return result
    project = result
    pdb = _db.project_db_path(project)

    ideas = _db.get_ideas(
        pdb,
        category=category or None,
        status=status or None,
    )
    return _render(request, "ideas.html", {
        "project": project,
        "tab": "ideas",
        "ideas": ideas,
        "cat_filter": category,
        "status_filter": status,
        "categories": _db.IDEA_CATEGORIES,
        "cat_labels": _db.IDEA_CATEGORY_LABELS,
        "status_labels": {
            "new": "Новые", "reviewed": "Просмотрено", "archived": "Архив"
        },
    })


@app.post("/p/{slug}/ideas/add")
async def ideas_add(
    request: Request, slug: str,
    content: str = Form(...),
    category: str = Form("idea"),
    tags: str = Form(""),
):
    result = _authed(request, slug)
    if isinstance(result, RedirectResponse):
        return result
    _db.add_idea(_db.project_db_path(result), content, "manual", category, tags)
    return RedirectResponse(f"/p/{slug}/ideas", status_code=302)


@app.post("/p/{slug}/ideas/{idea_id}/archive")
async def idea_archive(request: Request, slug: str, idea_id: int):
    result = _authed(request, slug)
    if isinstance(result, RedirectResponse):
        return result
    _db.update_idea_status(_db.project_db_path(result), idea_id, "archived")
    return RedirectResponse(f"/p/{slug}/ideas", status_code=302)


@app.post("/p/{slug}/ideas/{idea_id}/review")
async def idea_review(request: Request, slug: str, idea_id: int):
    result = _authed(request, slug)
    if isinstance(result, RedirectResponse):
        return result
    _db.update_idea_status(_db.project_db_path(result), idea_id, "reviewed")
    return RedirectResponse(f"/p/{slug}/ideas", status_code=302)


@app.post("/p/{slug}/ideas/{idea_id}/delete")
async def idea_delete(request: Request, slug: str, idea_id: int):
    result = _authed(request, slug)
    if isinstance(result, RedirectResponse):
        return result
    _db.delete_idea(_db.project_db_path(result), idea_id)
    return RedirectResponse(f"/p/{slug}/ideas", status_code=302)


# ── Content plan ──────────────────────────────────────────────────────────────

@app.get("/p/{slug}/content", response_class=HTMLResponse)
async def content_list(request: Request, slug: str,
                        status: str = "", platform: str = ""):
    result = _authed(request, slug)
    if isinstance(result, RedirectResponse):
        return result
    project = result
    pdb = _db.project_db_path(project)
    _db.init_project_db(pdb)

    items = _db.get_content_items(
        pdb,
        status=status or None,
        platform=platform or None,
    )
    stats = _db.content_stats(pdb)
    return _render(request, "content.html", {
        "project": project,
        "tab": "content",
        "items": items,
        "stats": stats,
        "status_filter": status,
        "platform_filter": platform,
        "platforms": _db.CONTENT_PLATFORMS,
        "platform_labels": _db.CONTENT_PLATFORM_LABELS,
        "formats": _db.CONTENT_FORMATS,
        "statuses": _db.CONTENT_STATUSES,
        "status_labels": _db.CONTENT_STATUS_LABELS,
        "status_colors": _db.CONTENT_STATUS_COLORS,
    })


@app.get("/p/{slug}/content/{item_id}", response_class=HTMLResponse)
async def content_detail(request: Request, slug: str, item_id: int):
    result = _authed(request, slug)
    if isinstance(result, RedirectResponse):
        return result
    project = result
    pdb = _db.project_db_path(project)
    item = _db.get_content_item(pdb, item_id)
    if not item:
        return RedirectResponse(f"/p/{slug}/content", status_code=302)
    return _render(request, "content_card.html", {
        "project": project,
        "tab": "content",
        "item": item,
        "platform_labels": _db.CONTENT_PLATFORM_LABELS,
        "formats": _db.CONTENT_FORMATS,
        "statuses": _db.CONTENT_STATUSES,
        "status_labels": _db.CONTENT_STATUS_LABELS,
        "status_colors": _db.CONTENT_STATUS_COLORS,
    })


@app.post("/p/{slug}/content/add")
async def content_add(
    request: Request, slug: str,
    platform: str = Form(...),
    format_type: str = Form(...),
    topic: str = Form(...),
    hook: str = Form(""),
    structure: str = Form(""),
    cta: str = Form(""),
    visual_prompt: str = Form(""),
    scheduled_date: str = Form(""),
):
    result = _authed(request, slug)
    if isinstance(result, RedirectResponse):
        return result
    pdb = _db.project_db_path(result)
    _db.add_content_item(
        pdb, platform, format_type, topic,
        hook=hook, structure=structure, cta=cta,
        visual_prompt=visual_prompt,
        scheduled_date=scheduled_date or None,
        status="pending",
    )
    return RedirectResponse(f"/p/{slug}/content", status_code=302)


@app.post("/p/{slug}/content/{item_id}/approve")
async def content_approve(request: Request, slug: str, item_id: int,
                           scheduled_date: str = Form("")):
    result = _authed(request, slug)
    if isinstance(result, RedirectResponse):
        return result
    pdb = _db.project_db_path(result)
    item = _db.get_content_item(pdb, item_id)
    if not item:
        return RedirectResponse(f"/p/{slug}/content", status_code=302)

    sched = scheduled_date or item.get("scheduled_date") or ""
    fields: dict = {"status": "approved"}
    if sched:
        fields["scheduled_date"] = sched
    _db.update_content_item(pdb, item_id, **fields)

    if sched:
        platform_lbl = _db.CONTENT_PLATFORM_LABELS.get(item["platform"], item["platform"])
        format_lbl = _db.CONTENT_FORMATS.get(item["format_type"], item["format_type"])
        _db.add_event(
            pdb, sched,
            f"📣 {platform_lbl} · {format_lbl}: {item['topic']}",
            f"Контент-план #{item_id}",
            "planned", "content",
        )

    return RedirectResponse(f"/p/{slug}/content/{item_id}", status_code=302)


@app.post("/p/{slug}/content/{item_id}/rework")
async def content_rework(request: Request, slug: str, item_id: int,
                          comment: str = Form(...)):
    result = _authed(request, slug)
    if isinstance(result, RedirectResponse):
        return result
    pdb = _db.project_db_path(result)
    _db.update_content_status(pdb, item_id, "draft", comment=comment)
    return RedirectResponse(f"/p/{slug}/content/{item_id}", status_code=302)


@app.post("/p/{slug}/content/{item_id}/status")
async def content_set_status(request: Request, slug: str, item_id: int,
                              status: str = Form(...)):
    result = _authed(request, slug)
    if isinstance(result, RedirectResponse):
        return result
    if status not in _db.CONTENT_STATUSES:
        return RedirectResponse(f"/p/{slug}/content/{item_id}", status_code=302)
    pdb = _db.project_db_path(result)
    _db.update_content_status(pdb, item_id, status)
    return RedirectResponse(f"/p/{slug}/content/{item_id}", status_code=302)


@app.post("/p/{slug}/content/{item_id}/edit")
async def content_edit(
    request: Request, slug: str, item_id: int,
    platform: str = Form(...),
    format_type: str = Form(...),
    topic: str = Form(...),
    hook: str = Form(""),
    structure: str = Form(""),
    cta: str = Form(""),
    visual_prompt: str = Form(""),
    scheduled_date: str = Form(""),
):
    result = _authed(request, slug)
    if isinstance(result, RedirectResponse):
        return result
    pdb = _db.project_db_path(result)
    _db.update_content_item(
        pdb, item_id,
        platform=platform, format_type=format_type, topic=topic,
        hook=hook, structure=structure, cta=cta,
        visual_prompt=visual_prompt,
        scheduled_date=scheduled_date or None,
    )
    return RedirectResponse(f"/p/{slug}/content/{item_id}", status_code=302)


@app.post("/p/{slug}/content/{item_id}/delete")
async def content_delete(request: Request, slug: str, item_id: int):
    result = _authed(request, slug)
    if isinstance(result, RedirectResponse):
        return result
    _db.delete_content_item(_db.project_db_path(result), item_id)
    return RedirectResponse(f"/p/{slug}/content", status_code=302)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "projects": len(_db.get_all_projects())}
