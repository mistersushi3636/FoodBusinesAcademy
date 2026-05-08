"""HTTP клиент к dashboard FastAPI."""
from __future__ import annotations

import httpx
from config import settings


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.dashboard_api_key}"}


async def post_daily(date: str, branch_id: int, tg_user_id: int,
                      revenue_delivery: float = 0, revenue_pickup: float = 0,
                      orders_delivery: int = 0, orders_pickup: int = 0,
                      shop_purchase: float = 0, household: float = 0,
                      note: str | None = None) -> dict:
    payload = {
        "date": date, "branch_id": branch_id, "tg_user_id": tg_user_id,
        "revenue_delivery": revenue_delivery, "revenue_pickup": revenue_pickup,
        "orders_delivery": orders_delivery, "orders_pickup": orders_pickup,
        "shop_purchase": shop_purchase, "household": household, "note": note,
    }
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(f"{settings.dashboard_api_url}/api/daily",
                         json=payload, headers=_headers())
        r.raise_for_status()
        return r.json()


async def post_daily_extra(date: str, branch_id: int | None, category: str,
                            amount: float, tg_user_id: int,
                            subcategory: str | None = None,
                            note: str | None = None) -> dict:
    payload = {
        "date": date, "branch_id": branch_id, "category": category,
        "subcategory": subcategory, "amount": amount, "note": note,
        "tg_user_id": tg_user_id,
    }
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(f"{settings.dashboard_api_url}/api/daily/extra",
                         json=payload, headers=_headers())
        r.raise_for_status()
        return r.json()


async def post_monthly(period: str, category: str, amount: float,
                        tg_user_id: int, branch_id: int | None = None,
                        subcategory: str | None = None,
                        note: str | None = None) -> dict:
    payload = {
        "period": period, "branch_id": branch_id, "category": category,
        "subcategory": subcategory, "amount": amount, "note": note,
        "tg_user_id": tg_user_id,
    }
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(f"{settings.dashboard_api_url}/api/monthly",
                         json=payload, headers=_headers())
        r.raise_for_status()
        return r.json()


async def get_summary(period: str | None = None, branch_id: int | None = None) -> dict:
    params = {}
    if period:
        params["period"] = period
    if branch_id:
        params["branch_id"] = branch_id
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"{settings.dashboard_api_url}/api/summary",
                        params=params, headers=_headers())
        r.raise_for_status()
        return r.json()
