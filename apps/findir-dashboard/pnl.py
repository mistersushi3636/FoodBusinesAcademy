"""
PNL расчёты для PNP MR.SUSHI.

Логика:
- Выручка = доставка + самовывоз (по филиалу/общая)
- Средний чек = выручка / заказы
- Food cost % = food_supply / выручка × 100
- EBITDA = выручка − food_supply − опер.расходы
- ЧП = EBITDA − налоги − кредиты

Опер. расходы агрегируют:
- daily_expenses (магазин, хоз/тара) — фиксированные ежедневные
- daily_extra_costs (любая категория) — ad-hoc, через CostBlock
- monthly_costs — по категории
- salary_payments — ФОТ
"""
from __future__ import annotations

from calendar import monthrange
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta

import db


@dataclass
class RevenueBlock:
    delivery: float = 0.0
    pickup: float = 0.0
    orders_delivery: int = 0
    orders_pickup: int = 0

    @property
    def total(self) -> float:
        return self.delivery + self.pickup

    @property
    def total_orders(self) -> int:
        return self.orders_delivery + self.orders_pickup

    @property
    def avg_check_delivery(self) -> float:
        return self.delivery / self.orders_delivery if self.orders_delivery else 0.0

    @property
    def avg_check_pickup(self) -> float:
        return self.pickup / self.orders_pickup if self.orders_pickup else 0.0

    @property
    def avg_check_total(self) -> float:
        return self.total / self.total_orders if self.total_orders else 0.0

    @property
    def delivery_share_pct(self) -> float:
        return self.delivery / self.total * 100 if self.total else 0.0

    @property
    def pickup_share_pct(self) -> float:
        return self.pickup / self.total * 100 if self.total else 0.0


@dataclass
class CostBlock:
    food_supply: float = 0.0
    daily_shop: float = 0.0
    daily_household: float = 0.0
    staff_meals: float = 0.0
    fot_total: float = 0.0
    fot_by_category: dict[str, float] = field(default_factory=dict)
    internet_phone: float = 0.0
    equipment: float = 0.0
    bank_credit: float = 0.0
    bank_commission: float = 0.0
    communal_rent: float = 0.0
    marketing_blogger: float = 0.0
    marketing_smm: float = 0.0
    ya_eda: float = 0.0
    kuper: float = 0.0
    ya_direct: float = 0.0
    revvy: float = 0.0
    site: float = 0.0
    taxes: float = 0.0
    other: float = 0.0

    @property
    def marketing_total(self) -> float:
        return (self.marketing_blogger + self.marketing_smm + self.ya_eda
                + self.kuper + self.ya_direct + self.revvy)

    @property
    def operating_total(self) -> float:
        return (self.daily_shop + self.daily_household + self.staff_meals
                + self.fot_total + self.internet_phone + self.equipment
                + self.bank_commission + self.communal_rent + self.marketing_total
                + self.site + self.other)

    @property
    def total(self) -> float:
        return (self.food_supply + self.operating_total + self.bank_credit + self.taxes)


@dataclass
class PNLReport:
    period: str
    branch_id: int | None
    branch_name: str
    revenue: RevenueBlock
    costs: CostBlock

    @property
    def food_cost_pct(self) -> float:
        return self.costs.food_supply / self.revenue.total * 100 if self.revenue.total else 0.0

    @property
    def fot_pct(self) -> float:
        return self.costs.fot_total / self.revenue.total * 100 if self.revenue.total else 0.0

    @property
    def marketing_pct(self) -> float:
        return self.costs.marketing_total / self.revenue.total * 100 if self.revenue.total else 0.0

    @property
    def ebitda(self) -> float:
        return self.revenue.total - self.costs.food_supply - self.costs.operating_total

    @property
    def ebitda_pct(self) -> float:
        return self.ebitda / self.revenue.total * 100 if self.revenue.total else 0.0

    @property
    def net_profit(self) -> float:
        return self.ebitda - self.costs.taxes - self.costs.bank_credit

    @property
    def net_profit_pct(self) -> float:
        return self.net_profit / self.revenue.total * 100 if self.revenue.total else 0.0


# ── Period helpers ───────────────────────────────────────────────────────────

def period_bounds(period: str) -> tuple[str, str]:
    y, m = map(int, period.split("-"))
    last = monthrange(y, m)[1]
    return f"{y:04d}-{m:02d}-01", f"{y:04d}-{m:02d}-{last:02d}"


def current_period() -> str:
    return date.today().strftime("%Y-%m")


def date_range_iter(start: str, end: str):
    s = date.fromisoformat(start)
    e = date.fromisoformat(end)
    cur = s
    while cur <= e:
        yield cur.isoformat()
        cur += timedelta(days=1)


def _add_to_costs(costs: CostBlock, category: str, amount: float) -> None:
    if hasattr(costs, category):
        setattr(costs, category, getattr(costs, category) + amount)
    else:
        costs.other += amount


# ── Build report ─────────────────────────────────────────────────────────────

def build_pnl(period: str, branch_id: int | None) -> PNLReport:
    start, end = period_bounds(period)
    branch_name = "Общие"
    if branch_id is not None:
        for b in db.list_branches():
            if b["id"] == branch_id:
                branch_name = b["name"]
                break

    rev = RevenueBlock()
    for r in db.get_daily_revenue_range(start, end, branch_id):
        rev.delivery += r["revenue_delivery"] or 0
        rev.pickup += r["revenue_pickup"] or 0
        rev.orders_delivery += r["orders_delivery"] or 0
        rev.orders_pickup += r["orders_pickup"] or 0

    costs = CostBlock()
    for e in db.get_daily_expenses_range(start, end, branch_id):
        costs.daily_shop += e["shop_purchase"] or 0
        costs.daily_household += e["household"] or 0
        costs.staff_meals += e["staff_meals"] or 0  # legacy column

    for x in db.get_daily_extra_costs_range(start, end, branch_id):
        _add_to_costs(costs, x["category"], x["amount"] or 0)

    for c in db.get_monthly_costs(period, branch_id):
        _add_to_costs(costs, c["category"], c["amount"] or 0)

    fot_by_cat: dict[str, float] = defaultdict(float)
    for s in db.get_salary_payments(period, branch_id):
        fot_by_cat[s["category"]] += s["amount"] or 0
    costs.fot_total = sum(fot_by_cat.values())
    costs.fot_by_category = dict(fot_by_cat)

    return PNLReport(
        period=period,
        branch_id=branch_id,
        branch_name=branch_name,
        revenue=rev,
        costs=costs,
    )


def build_all_branches(period: str) -> list[PNLReport]:
    out = []
    for b in db.list_branches():
        out.append(build_pnl(period, b["id"]))
    out.append(build_pnl(period, None))
    return out


# ── Plan / Fact ──────────────────────────────────────────────────────────────

def plan_fact(period: str, branch_id: int | None) -> list[dict]:
    plans = {p["category"]: p["planned_amount"] for p in db.get_plans(period, branch_id)}
    report = build_pnl(period, branch_id)
    fact_map = {
        "food_supply": report.costs.food_supply,
        "daily_shop": report.costs.daily_shop,
        "daily_household": report.costs.daily_household,
        "staff_meals": report.costs.staff_meals,
        "fot_total": report.costs.fot_total,
        "internet_phone": report.costs.internet_phone,
        "equipment": report.costs.equipment,
        "bank_commission": report.costs.bank_commission,
        "communal_rent": report.costs.communal_rent,
        "marketing_blogger": report.costs.marketing_blogger,
        "marketing_smm": report.costs.marketing_smm,
        "ya_eda": report.costs.ya_eda,
        "kuper": report.costs.kuper,
        "ya_direct": report.costs.ya_direct,
        "revvy": report.costs.revvy,
        "site": report.costs.site,
        "taxes": report.costs.taxes,
    }
    rows = []
    keys = sorted(set(plans) | set(fact_map))
    for k in keys:
        plan = plans.get(k, 0.0)
        fact = fact_map.get(k, 0.0)
        delta = fact - plan
        delta_pct = (delta / plan * 100) if plan else 0.0
        rows.append({
            "category": k,
            "label": db.COST_CATEGORIES.get(k, k),
            "plan": plan,
            "fact": fact,
            "delta": delta,
            "delta_pct": delta_pct,
        })
    return rows


# ── Daily series ─────────────────────────────────────────────────────────────

def daily_revenue_series(period: str, branch_id: int | None) -> list[dict]:
    start, end = period_bounds(period)
    rows = db.get_daily_revenue_range(start, end, branch_id)
    by_date: dict[str, dict] = {}
    for r in rows:
        d = r["date"]
        if d not in by_date:
            by_date[d] = {"date": d, "delivery": 0.0, "pickup": 0.0, "orders": 0}
        by_date[d]["delivery"] += r["revenue_delivery"] or 0
        by_date[d]["pickup"] += r["revenue_pickup"] or 0
        by_date[d]["orders"] += (r["orders_delivery"] or 0) + (r["orders_pickup"] or 0)
    out = []
    for d in date_range_iter(start, end):
        b = by_date.get(d, {"date": d, "delivery": 0.0, "pickup": 0.0, "orders": 0})
        b["total"] = b["delivery"] + b["pickup"]
        out.append(b)
    return out


def combined_revenue_series(period: str) -> dict:
    """
    Серии для одного графика: общая (по обоим), Ростовская, 9 Января.
    Сумма = доставка + самовывоз.
    """
    branches = db.list_branches()
    s_all = daily_revenue_series(period, None)
    series: dict = {
        "labels": [r["date"] for r in s_all],
        "datasets": {
            "all": {"label": "Общая", "data": [r["total"] for r in s_all]},
        },
    }
    for b in branches:
        s_b = daily_revenue_series(period, b["id"])
        series["datasets"][b["id"]] = {"label": b["name"],
                                        "data": [r["total"] for r in s_b]}
    return series


# ── Avg-check динамика по дням ───────────────────────────────────────────────

def avg_check_with_delta(branch_id: int | None) -> dict:
    """
    Берёт два последних дня с введённой выручкой, считает avg-check + дельту.
    """
    # Окно: последние 60 дней до сегодня + 30 дней вперёд (на случай ввода
    # за будущие даты — например, плановый ввод за выходной).
    end = (date.today() + timedelta(days=30)).isoformat()
    start = (date.today() - timedelta(days=60)).isoformat()
    rows = db.get_daily_revenue_range(start, end, branch_id)

    by_date: dict[str, dict] = {}
    for r in rows:
        d = r["date"]
        if d not in by_date:
            by_date[d] = {"revenue": 0.0, "orders": 0}
        by_date[d]["revenue"] += (r["revenue_delivery"] or 0) + (r["revenue_pickup"] or 0)
        by_date[d]["orders"] += (r["orders_delivery"] or 0) + (r["orders_pickup"] or 0)

    days = sorted([d for d, v in by_date.items() if v["orders"] > 0])
    if not days:
        return {"today": None, "prev": None, "delta_pct": 0.0, "trend": "none"}

    today_d = days[-1]
    today_v = by_date[today_d]
    today_avg = today_v["revenue"] / today_v["orders"]
    today = {"date": today_d, "avg": today_avg,
             "revenue": today_v["revenue"], "orders": today_v["orders"]}

    if len(days) < 2:
        return {"today": today, "prev": None, "delta_pct": 0.0, "trend": "none"}

    prev_d = days[-2]
    prev_v = by_date[prev_d]
    prev_avg = prev_v["revenue"] / prev_v["orders"]
    prev = {"date": prev_d, "avg": prev_avg,
            "revenue": prev_v["revenue"], "orders": prev_v["orders"]}

    delta_pct = (today_avg - prev_avg) / prev_avg * 100 if prev_avg else 0.0
    if abs(delta_pct) < 0.01:
        trend = "flat"
    elif delta_pct > 0:
        trend = "up"
    else:
        trend = "down"

    return {"today": today, "prev": prev, "delta_pct": delta_pct, "trend": trend}


def weekday_avg(period: str, branch_id: int | None, lookback_months: int = 3) -> dict[int, float]:
    end_d = date.fromisoformat(period_bounds(period)[1])
    start_d = (end_d.replace(day=1) - timedelta(days=lookback_months * 31))
    rows = db.get_daily_revenue_range(start_d.isoformat(), end_d.isoformat(), branch_id)
    by_wd: dict[int, list[float]] = defaultdict(list)
    for r in rows:
        d = date.fromisoformat(r["date"])
        total = (r["revenue_delivery"] or 0) + (r["revenue_pickup"] or 0)
        by_wd[d.weekday()].append(total)
    return {wd: sum(v) / len(v) for wd, v in by_wd.items() if v}
