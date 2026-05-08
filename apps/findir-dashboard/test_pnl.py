"""
Глубокий тест PNL расчётов: ввод → синхронизация → проверка чисел.
Запуск: python test_pnl.py
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

# тест-БД — отдельный файл, не findir.db
_tmpdb = Path(tempfile.gettempdir()) / "findir-test.db"
if _tmpdb.exists():
    _tmpdb.unlink()
os.environ["DASHBOARD_DB_PATH"] = str(_tmpdb)
os.environ["OWNER_PASSWORD"] = "test"
os.environ["MANAGER_PASSWORD"] = "test"

import sys
sys.path.insert(0, str(Path(__file__).parent))

import db
import pnl

db.init_db()

passed, failed = 0, 0


def _check(name: str, got, expected, tol: float = 0.01) -> None:
    global passed, failed
    if isinstance(expected, (int, float)) and isinstance(got, (int, float)):
        ok = abs(got - expected) <= tol
    else:
        ok = got == expected
    mark = "✓" if ok else "✗"
    print(f"  {mark} {name}: got={got!r} expected={expected!r}")
    if ok:
        passed += 1
    else:
        failed += 1


# ─────────────────────────────────────────────────────────────────────────────
print("\n# 1. Выручка → расчёт ср. чека и долей")
# Ростовская: доставка 100000 ₽ / 80 заказов; самовывоз 50000 ₽ / 50 заказов
db.upsert_daily_revenue("2026-05-08", 1, 100_000, 50_000, 80, 50, None)
# 9 Января: доставка 60000 / 50; самовывоз 30000 / 25
db.upsert_daily_revenue("2026-05-08", 2, 60_000, 30_000, 50, 25, None)

r1 = pnl.build_pnl("2026-05", 1)
_check("Ростов выручка total", r1.revenue.total, 150_000)
_check("Ростов заказов всего", r1.revenue.total_orders, 130)
_check("Ростов ср. чек total", r1.revenue.avg_check_total, 150_000 / 130)
_check("Ростов ср. чек доставка", r1.revenue.avg_check_delivery, 100_000 / 80)
_check("Ростов ср. чек самовывоз", r1.revenue.avg_check_pickup, 50_000 / 50)
_check("Ростов доля доставки %", r1.revenue.delivery_share_pct, 100_000 / 150_000 * 100)

r_all = pnl.build_pnl("2026-05", None)
_check("Общая выручка", r_all.revenue.total, 240_000)
_check("Общие заказы", r_all.revenue.total_orders, 205)
_check("Общий ср. чек", r_all.revenue.avg_check_total, 240_000 / 205)


# ─────────────────────────────────────────────────────────────────────────────
print("\n# 2. Food supply (поставщики) → food_cost %")
db.add_monthly_cost("2026-05", 1, "food_supply", None, 45_000, "test", None)
db.add_monthly_cost("2026-05", 2, "food_supply", None, 27_000, "test", None)
r1 = pnl.build_pnl("2026-05", 1)
_check("Ростов food_supply", r1.costs.food_supply, 45_000)
_check("Ростов food_cost %", r1.food_cost_pct, 45_000 / 150_000 * 100)
r_all = pnl.build_pnl("2026-05", None)
_check("Общий food_supply", r_all.costs.food_supply, 72_000)
_check("Общий food_cost %", r_all.food_cost_pct, 72_000 / 240_000 * 100)


# ─────────────────────────────────────────────────────────────────────────────
print("\n# 3. Daily fixed expenses (магазин + хоз)")
db.upsert_daily_expense("2026-05-08", 1, 5_000, 2_000, "test", None)
db.upsert_daily_expense("2026-05-08", 2, 3_000, 1_500, "test", None)
r1 = pnl.build_pnl("2026-05", 1)
_check("Ростов daily_shop", r1.costs.daily_shop, 5_000)
_check("Ростов daily_household", r1.costs.daily_household, 2_000)


# ─────────────────────────────────────────────────────────────────────────────
print("\n# 4. Daily extra cost (ad-hoc) → попадает в нужную категорию")
# Еда персонала через ad-hoc → должна попасть в costs.staff_meals
db.add_daily_extra_cost("2026-05-08", 1, "staff_meals", None, 1_500, "обед", None)
# Маркетинг через ad-hoc → marketing_smm
db.add_daily_extra_cost("2026-05-08", 1, "marketing_smm", "boost", 4_500, None, None)
# Произвольная неизвестная категория → попадёт в other (защита _add_to_costs)
db.add_daily_extra_cost("2026-05-08", 1, "unknown_cat", None, 999, None, None)

r1 = pnl.build_pnl("2026-05", 1)
_check("Ростов staff_meals из ad-hoc", r1.costs.staff_meals, 1_500)
_check("Ростов marketing_smm из ad-hoc", r1.costs.marketing_smm, 4_500)
_check("Ростов other (unknown категория)", r1.costs.other, 999)


# ─────────────────────────────────────────────────────────────────────────────
print("\n# 5. ФОТ — выплаты по сотрудникам с агрегатом по категориям")
emp1 = db.add_employee("Тест Шеф", "chef", 1)
emp2 = db.add_employee("Тест Курьер", "courier", 1)
emp3 = db.add_employee("Тест Управляющий", "managing", None)
db.add_salary_payment("2026-05", emp1, 55_000, "2026-05-15", None, None)
db.add_salary_payment("2026-05", emp2, 50_000, "2026-05-15", None, None)
db.add_salary_payment("2026-05", emp3, 90_000, "2026-05-15", None, None)
r1 = pnl.build_pnl("2026-05", 1)
_check("Ростов fot_total (chef+courier+managing-без-филиала)", r1.costs.fot_total, 55_000 + 50_000 + 90_000)
_check("Ростов fot chef", r1.costs.fot_by_category.get("chef", 0), 55_000)
_check("Ростов fot courier", r1.costs.fot_by_category.get("courier", 0), 50_000)
_check("Ростов fot managing", r1.costs.fot_by_category.get("managing", 0), 90_000)


# ─────────────────────────────────────────────────────────────────────────────
print("\n# 6. EBITDA и ЧП")
# Налоги
db.add_monthly_cost("2026-05", None, "taxes", None, 12_000, None, None)
# Кредиты
db.add_monthly_cost("2026-05", None, "bank_credit", None, 8_000, None, None)
r1 = pnl.build_pnl("2026-05", 1)
expected_op = (5_000 + 2_000 + 1_500 + (55_000 + 50_000 + 90_000)
               + 4_500 + 999)  # fot + staff_meals + marketing_smm + other
_check("Ростов operating_total", r1.costs.operating_total, expected_op)
expected_ebitda = 150_000 - 45_000 - expected_op
_check("Ростов EBITDA", r1.ebitda, expected_ebitda)
expected_net = expected_ebitda - 12_000 - 8_000
_check("Ростов ЧП", r1.net_profit, expected_net)
_check("Ростов ЧП %", r1.net_profit_pct, expected_net / 150_000 * 100)


# ─────────────────────────────────────────────────────────────────────────────
print("\n# 7. Combined revenue series (общая + 2 филиала в одном графике)")
db.upsert_daily_revenue("2026-05-09", 1, 110_000, 40_000, 90, 35, None)
db.upsert_daily_revenue("2026-05-09", 2, 70_000, 35_000, 60, 30, None)
combined = pnl.combined_revenue_series("2026-05")
_check("combined.labels тип", isinstance(combined["labels"], list), True)
_check("combined есть 'all' dataset", "all" in combined["datasets"], True)
_check("combined есть branch_id=1 dataset", 1 in combined["datasets"], True)
_check("combined есть branch_id=2 dataset", 2 in combined["datasets"], True)
# Сумма 'all' за 2026-05-09 = 110+40+70+35 = 255k
idx_09 = combined["labels"].index("2026-05-09")
_check("combined all[09]", combined["datasets"]["all"]["data"][idx_09], 255_000)
_check("combined Ростов[09]", combined["datasets"][1]["data"][idx_09], 150_000)
_check("combined 9Янв[09]", combined["datasets"][2]["data"][idx_09], 105_000)


# ─────────────────────────────────────────────────────────────────────────────
print("\n# 8. Avg-check delta (день к дню) — цвет/тренд")
# 2026-05-08 ср.чек = 240000/205 = 1170.7
# 2026-05-09 ср.чек = 255000/215 = 1186.0 → up, +1.3%
ac = pnl.avg_check_with_delta(None)
_check("avg_check today date", ac["today"]["date"], "2026-05-09")
_check("avg_check today avg", ac["today"]["avg"], 255_000 / 215)
_check("avg_check prev date", ac["prev"]["date"], "2026-05-08")
_check("avg_check prev avg", ac["prev"]["avg"], 240_000 / 205)
_check("avg_check trend", ac["trend"], "up")
expected_delta_pct = (255_000 / 215 - 240_000 / 205) / (240_000 / 205) * 100
_check("avg_check delta %", ac["delta_pct"], expected_delta_pct)

# Падение
db.upsert_daily_revenue("2026-05-10", 1, 50_000, 20_000, 70, 40, None)
db.upsert_daily_revenue("2026-05-10", 2, 30_000, 10_000, 50, 20, None)
ac2 = pnl.avg_check_with_delta(None)
_check("avg_check today после падения date", ac2["today"]["date"], "2026-05-10")
_check("avg_check trend = down", ac2["trend"], "down")
_check("avg_check delta_pct < 0", ac2["delta_pct"] < 0, True)


# ─────────────────────────────────────────────────────────────────────────────
print("\n# 9. Audit log — все 5 типов событий присутствуют")
events = db.audit_log(limit=200)
kinds = {e["kind"] for e in events}
_check("audit revenue", "revenue" in kinds, True)
_check("audit expense", "expense" in kinds, True)
_check("audit extra", "extra" in kinds, True)
_check("audit monthly", "monthly" in kinds, True)
_check("audit salary", "salary" in kinds, True)
_check("audit фильтр по kind=extra", all(e["kind"] == "extra" for e in db.audit_log(kind="extra")), True)
_check("audit фильтр по branch_id=1",
       all(e["branch_id"] == 1 for e in db.audit_log(branch_id=1) if e["branch_id"] is not None),
       True)


# ─────────────────────────────────────────────────────────────────────────────
print("\n# 10. Plan / Fact")
db.upsert_plan("2026-05", None, "food_supply", 80_000)
db.upsert_plan("2026-05", None, "marketing_smm", 5_000)
rows = pnl.plan_fact("2026-05", None)
food = next((r for r in rows if r["category"] == "food_supply"), None)
_check("plan_fact food_supply plan", food["plan"], 80_000)
_check("plan_fact food_supply fact", food["fact"], 72_000)
_check("plan_fact food_supply delta", food["delta"], 72_000 - 80_000)
mkt = next((r for r in rows if r["category"] == "marketing_smm"), None)
_check("plan_fact marketing_smm fact (из ad-hoc)", mkt["fact"], 4_500)


# ─────────────────────────────────────────────────────────────────────────────
print(f"\n═══════════════════════════════════════════")
print(f"  PASSED: {passed}  FAILED: {failed}")
print(f"═══════════════════════════════════════════")

# Cleanup
if _tmpdb.exists():
    _tmpdb.unlink()

import sys
sys.exit(0 if failed == 0 else 1)
