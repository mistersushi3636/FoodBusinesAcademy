"""
PNP MR.SUSHI Dashboard — FastAPI entry.
URL prod: https://findir.mistersushi36.pro
URL dev:  http://localhost:8001
"""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request, Form, HTTPException, Header
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
    load_dotenv(Path(__file__).parents[2] / ".env")
except ImportError:
    pass

import auth
import db
import pnl

DASHBOARD_API_KEY = os.getenv("DASHBOARD_API_KEY", "")

app = FastAPI(title="PNP MR.SUSHI — Финдир", docs_url=None, redoc_url=None)

_static = Path(__file__).parent / "static"
_static.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_static)), name="static")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

templates.env.globals["COST_CATEGORIES"] = db.COST_CATEGORIES
templates.env.globals["EMPLOYEE_CATEGORIES"] = db.EMPLOYEE_CATEGORIES
templates.env.globals["MANAGER_HIDDEN_EMPLOYEE_CATS"] = db.MANAGER_HIDDEN_EMPLOYEE_CATS

db.init_db()


def _require_session(request: Request):
    s = auth.get_session(request)
    if not s:
        return None
    user = db.get_user_by_id(s["uid"])
    return user or None


def _require_owner(request: Request):
    user = _require_session(request)
    if not user or user["role"] != "owner":
        return None
    return user


def _ctx(request: Request, user, **extra) -> dict:
    base = {
        "request": request,
        "user": dict(user) if user else None,
        "is_owner": user["role"] == "owner" if user else False,
        "branches": db.list_branches(),
        "today": date.today().isoformat(),
        "current_period": pnl.current_period(),
    }
    base.update(extra)
    return base


# ── Login ────────────────────────────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str | None = None):
    return templates.TemplateResponse(
        request=request, name="login.html",
        context={"request": request, "error": error},
    )


@app.post("/login")
async def login_submit(request: Request,
                        username: str = Form(...),
                        password: str = Form(...)):
    user = db.get_user_by_username(username)
    if not user or not auth.verify_password(password, user["pw_hash"]):
        return RedirectResponse(url="/login?error=1", status_code=302)
    token = auth.make_cookie(user["id"], user["role"])
    resp = RedirectResponse(url="/", status_code=302)
    resp.set_cookie(auth.COOKIE_NAME, token, httponly=True,
                    samesite="lax", max_age=auth.SESSION_TTL)
    return resp


@app.get("/logout")
async def logout():
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie(auth.COOKIE_NAME)
    return resp


# ── Dashboard ────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, period: str | None = None,
                    branch_id: str | None = None):
    user = _require_session(request)
    if not user:
        return auth.redirect_login()

    period = period or pnl.current_period()
    bid = int(branch_id) if branch_id and branch_id != "all" else None

    reports = pnl.build_all_branches(period)
    main_report = next((r for r in reports if r.branch_id == bid), reports[-1])
    combined = pnl.combined_revenue_series(period)

    avg_checks: list[dict] = []
    for b in db.list_branches():
        ac = pnl.avg_check_with_delta(b["id"])
        ac["branch_id"] = b["id"]
        ac["branch_name"] = b["name"]
        avg_checks.append(ac)
    ac_total = pnl.avg_check_with_delta(None)
    ac_total["branch_id"] = None
    ac_total["branch_name"] = "Общий"
    avg_checks.append(ac_total)

    return templates.TemplateResponse(
        request=request, name="dashboard.html",
        context=_ctx(request, user, period=period, branch_id=bid,
                     reports=reports, report=main_report,
                     combined=combined, avg_checks=avg_checks),
    )


# ── PNL ──────────────────────────────────────────────────────────────────────

@app.get("/pnl", response_class=HTMLResponse)
async def pnl_table(request: Request, period: str | None = None):
    user = _require_session(request)
    if not user:
        return auth.redirect_login()
    period = period or pnl.current_period()
    reports = pnl.build_all_branches(period)
    return templates.TemplateResponse(
        request=request, name="pnl_table.html",
        context=_ctx(request, user, period=period, reports=reports),
    )


# ── Daily input (фикс выручка/расходы + ad-hoc) ─────────────────────────────

@app.get("/input/daily", response_class=HTMLResponse)
async def input_daily_page(request: Request, d: str | None = None):
    user = _require_session(request)
    if not user:
        return auth.redirect_login()
    d = d or date.today().isoformat()
    existing: dict = {}
    extras: dict = {}
    for b in db.list_branches():
        rev_rows = db.get_daily_revenue_range(d, d, b["id"])
        exp_rows = db.get_daily_expenses_range(d, d, b["id"])
        existing[b["id"]] = {
            "revenue": dict(rev_rows[0]) if rev_rows else {},
            "expense": dict(exp_rows[0]) if exp_rows else {},
        }
        extras[b["id"]] = [dict(r) for r in db.get_daily_extra_costs(d, b["id"])]
    common_extras = [dict(r) for r in db.get_daily_extra_costs(d, None)]
    return templates.TemplateResponse(
        request=request, name="input_daily.html",
        context=_ctx(request, user, d=d, existing=existing,
                     extras=extras, common_extras=common_extras),
    )


@app.post("/input/daily")
async def input_daily_submit(request: Request,
                              d: str = Form(...),
                              branch_id: int = Form(...),
                              revenue_delivery: float = Form(0),
                              revenue_pickup: float = Form(0),
                              orders_delivery: int = Form(0),
                              orders_pickup: int = Form(0),
                              shop_purchase: float = Form(0),
                              household: float = Form(0),
                              note: str = Form("")):
    user = _require_session(request)
    if not user:
        return auth.redirect_login()
    db.upsert_daily_revenue(d, branch_id, revenue_delivery, revenue_pickup,
                             orders_delivery, orders_pickup, user["id"])
    db.upsert_daily_expense(d, branch_id, shop_purchase, household,
                             note or None, user["id"])
    return RedirectResponse(url=f"/input/daily?d={d}&saved=1", status_code=302)


@app.post("/input/daily/extra")
async def input_daily_extra_submit(request: Request,
                                    d: str = Form(...),
                                    branch_id: str = Form(""),
                                    category: str = Form(...),
                                    subcategory: str = Form(""),
                                    amount: float = Form(...),
                                    note: str = Form("")):
    user = _require_session(request)
    if not user:
        return auth.redirect_login()
    bid = int(branch_id) if branch_id else None
    db.add_daily_extra_cost(d, bid, category, subcategory or None,
                             amount, note or None, user["id"])
    return RedirectResponse(url=f"/input/daily?d={d}&saved=1", status_code=302)


@app.post("/input/daily/extra/{cost_id}/delete")
async def input_daily_extra_delete(cost_id: int, request: Request,
                                    d: str = Form(...)):
    user = _require_session(request)
    if not user:
        return auth.redirect_login()
    db.delete_daily_extra_cost(cost_id)
    return RedirectResponse(url=f"/input/daily?d={d}", status_code=302)


# ── Monthly costs (owner) ────────────────────────────────────────────────────

@app.get("/input/monthly", response_class=HTMLResponse)
async def input_monthly_page(request: Request, period: str | None = None):
    user = _require_owner(request)
    if not user:
        return auth.redirect_login()
    period = period or pnl.current_period()
    costs_per_branch = {b["id"]: db.get_monthly_costs(period, b["id"]) for b in db.list_branches()}
    costs_per_branch["common"] = [c for c in db.get_monthly_costs(period) if c["branch_id"] is None]
    return templates.TemplateResponse(
        request=request, name="input_monthly.html",
        context=_ctx(request, user, period=period, costs_per_branch=costs_per_branch),
    )


@app.post("/input/monthly")
async def input_monthly_submit(request: Request,
                                period: str = Form(...),
                                branch_id: str = Form(""),
                                category: str = Form(...),
                                subcategory: str = Form(""),
                                amount: float = Form(...),
                                note: str = Form("")):
    user = _require_owner(request)
    if not user:
        return auth.redirect_login()
    bid = int(branch_id) if branch_id else None
    db.add_monthly_cost(period, bid, category, subcategory or None, amount,
                        note or None, user["id"])
    return RedirectResponse(url=f"/input/monthly?period={period}", status_code=302)


@app.post("/input/monthly/{cost_id}/delete")
async def input_monthly_delete(cost_id: int, request: Request, period: str = Form(...)):
    user = _require_owner(request)
    if not user:
        return auth.redirect_login()
    db.delete_monthly_cost(cost_id)
    return RedirectResponse(url=f"/input/monthly?period={period}", status_code=302)


# ── Employees & ФОТ (owner) ──────────────────────────────────────────────────

@app.get("/employees", response_class=HTMLResponse)
async def employees_page(request: Request, period: str | None = None):
    user = _require_owner(request)
    if not user:
        return auth.redirect_login()
    period = period or pnl.current_period()
    emps = db.list_employees()
    payments = db.get_salary_payments(period)
    pay_by_emp: dict[int, float] = {}
    for p in payments:
        pay_by_emp[p["employee_id"]] = pay_by_emp.get(p["employee_id"], 0) + p["amount"]
    return templates.TemplateResponse(
        request=request, name="employees.html",
        context=_ctx(request, user, period=period, employees=emps, pay_by_emp=pay_by_emp),
    )


@app.post("/employees/add")
async def employees_add(request: Request,
                         full_name: str = Form(...),
                         category: str = Form(...),
                         branch_id: str = Form("")):
    user = _require_owner(request)
    if not user:
        return auth.redirect_login()
    bid = int(branch_id) if branch_id else None
    db.add_employee(full_name, category, bid)
    return RedirectResponse(url="/employees", status_code=302)


@app.post("/employees/{emp_id}/deactivate")
async def employees_deactivate(emp_id: int, request: Request):
    user = _require_owner(request)
    if not user:
        return auth.redirect_login()
    db.deactivate_employee(emp_id)
    return RedirectResponse(url="/employees", status_code=302)


@app.post("/employees/pay")
async def employees_pay(request: Request,
                         employee_id: int = Form(...),
                         period: str = Form(...),
                         amount: float = Form(...),
                         paid_at: str = Form(...),
                         note: str = Form("")):
    user = _require_owner(request)
    if not user:
        return auth.redirect_login()
    db.add_salary_payment(period, employee_id, amount, paid_at, note or None, user["id"])
    return RedirectResponse(url=f"/employees?period={period}", status_code=302)


# ── План/факт (owner) ───────────────────────────────────────────────────────

@app.get("/plan-fact", response_class=HTMLResponse)
async def plan_fact_page(request: Request, period: str | None = None,
                          branch_id: str | None = None):
    user = _require_owner(request)
    if not user:
        return auth.redirect_login()
    period = period or pnl.current_period()
    bid = int(branch_id) if branch_id and branch_id != "all" else None
    rows = pnl.plan_fact(period, bid)
    weekday = pnl.weekday_avg(period, bid)
    return templates.TemplateResponse(
        request=request, name="plan_fact.html",
        context=_ctx(request, user, period=period, branch_id=bid,
                     rows=rows, weekday=weekday),
    )


@app.post("/plan-fact/save")
async def plan_fact_save(request: Request,
                          period: str = Form(...),
                          branch_id: str = Form(""),
                          category: str = Form(...),
                          planned_amount: float = Form(...)):
    user = _require_owner(request)
    if not user:
        return auth.redirect_login()
    bid = int(branch_id) if branch_id else None
    db.upsert_plan(period, bid, category, planned_amount)
    return RedirectResponse(url=f"/plan-fact?period={period}", status_code=302)


# ── Audit log / История ─────────────────────────────────────────────────────

@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request, kind: str | None = None,
                        branch_id: str | None = None, limit: int = 200):
    user = _require_session(request)
    if not user:
        return auth.redirect_login()
    bid = int(branch_id) if branch_id and branch_id != "all" else None
    events = db.audit_log(limit=limit, kind=kind or None, branch_id=bid)
    return templates.TemplateResponse(
        request=request, name="history.html",
        context=_ctx(request, user, events=events, kind=kind or "",
                     branch_id=bid, limit=limit),
    )


# ── API for bot ──────────────────────────────────────────────────────────────

def _check_api_key(authorization: str | None) -> bool:
    if not DASHBOARD_API_KEY:
        return False
    return authorization == f"Bearer {DASHBOARD_API_KEY}"


@app.post("/api/daily")
async def api_daily(request: Request, authorization: str | None = Header(None)):
    if not _check_api_key(authorization):
        raise HTTPException(401, "unauthorized")
    payload = await request.json()
    tg_id = payload.get("tg_user_id")
    user = db.get_user_by_tg_id(tg_id) if tg_id else None
    db.upsert_daily_revenue(
        payload["date"], payload["branch_id"],
        payload.get("revenue_delivery", 0), payload.get("revenue_pickup", 0),
        payload.get("orders_delivery", 0), payload.get("orders_pickup", 0),
        user["id"] if user else None,
    )
    db.upsert_daily_expense(
        payload["date"], payload["branch_id"],
        payload.get("shop_purchase", 0), payload.get("household", 0),
        payload.get("note"), user["id"] if user else None,
    )
    return JSONResponse({"ok": True})


@app.post("/api/daily/extra")
async def api_daily_extra(request: Request, authorization: str | None = Header(None)):
    if not _check_api_key(authorization):
        raise HTTPException(401, "unauthorized")
    payload = await request.json()
    tg_id = payload.get("tg_user_id")
    user = db.get_user_by_tg_id(tg_id) if tg_id else None
    cost_id = db.add_daily_extra_cost(
        payload["date"], payload.get("branch_id"),
        payload["category"], payload.get("subcategory"),
        payload["amount"], payload.get("note"),
        user["id"] if user else None,
    )
    return JSONResponse({"ok": True, "id": cost_id})


@app.post("/api/monthly")
async def api_monthly(request: Request, authorization: str | None = Header(None)):
    if not _check_api_key(authorization):
        raise HTTPException(401, "unauthorized")
    payload = await request.json()
    tg_id = payload.get("tg_user_id")
    user = db.get_user_by_tg_id(tg_id) if tg_id else None
    if user and user["role"] != "owner":
        raise HTTPException(403, "owner only")
    cost_id = db.add_monthly_cost(
        payload["period"], payload.get("branch_id"),
        payload["category"], payload.get("subcategory"),
        payload["amount"], payload.get("note"),
        user["id"] if user else None,
    )
    return JSONResponse({"ok": True, "id": cost_id})


@app.get("/api/summary")
async def api_summary(period: str | None = None, branch_id: int | None = None,
                       authorization: str | None = Header(None)):
    if not _check_api_key(authorization):
        raise HTTPException(401, "unauthorized")
    period = period or pnl.current_period()
    r = pnl.build_pnl(period, branch_id)
    return {
        "period": r.period,
        "branch": r.branch_name,
        "revenue": r.revenue.total,
        "orders": r.revenue.total_orders,
        "avg_check": r.revenue.avg_check_total,
        "food_cost_pct": r.food_cost_pct,
        "fot_pct": r.fot_pct,
        "ebitda": r.ebitda,
        "ebitda_pct": r.ebitda_pct,
        "net_profit": r.net_profit,
        "net_profit_pct": r.net_profit_pct,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
