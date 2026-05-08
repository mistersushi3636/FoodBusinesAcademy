"""
Seed демо-данных для теста UI.
Запуск: python seed_demo.py
"""
from __future__ import annotations

import os
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

os.environ.setdefault("OWNER_PASSWORD", "demo123")
os.environ.setdefault("MANAGER_PASSWORD", "demo123")

import auth  # noqa: E402
import db    # noqa: E402

random.seed(42)

db.init_db()
print("✓ DB inited")

# Сотрудники
employees = [
    ("Иванов Алексей", "managing", None),
    ("Петров Сергей", "sushef", 1),
    ("Сидоров Иван", "sushef", 2),
    ("Кузнецов Михаил", "chef", 1),
    ("Смирнов Дмитрий", "chef", 1),
    ("Васильев Артём", "chef", 2),
    ("Попова Анна", "admin", 1),
    ("Морозова Ольга", "admin", 2),
    ("Новиков Павел", "courier", 1),
    ("Фёдоров Игорь", "courier", 2),
    ("Соколов Илья", "courier", 1),
    ("Лебедев Антон", "chef_trainee", 1),
    ("Семёнова Мария", "admin_trainee", 2),
    ("Бухгалтерова Татьяна", "accounting", None),
    ("Маркетингов Виктор", "marketing", None),
]
with db.conn() as c:
    if c.execute("SELECT COUNT(*) FROM employees").fetchone()[0] == 0:
        for name, cat, bid in employees:
            c.execute(
                "INSERT INTO employees(full_name, category, branch_id) VALUES (?, ?, ?)",
                (name, cat, bid),
            )
        print(f"✓ {len(employees)} employees seeded")

today = date.today()
period = today.strftime("%Y-%m")

# Дневная выручка за текущий месяц до сегодня
days_back = today.day
start = today.replace(day=1)
for i in range(days_back):
    d = start + timedelta(days=i)
    if d > today:
        break
    weekday = d.weekday()
    weekend_boost = 1.4 if weekday >= 5 else 1.0
    for branch_id in (1, 2):
        branch_factor = 1.15 if branch_id == 1 else 0.95
        rev_del = random.randint(80_000, 130_000) * weekend_boost * branch_factor
        rev_pick = random.randint(20_000, 45_000) * weekend_boost * branch_factor
        ord_del = int(rev_del / random.randint(1100, 1400))
        ord_pick = int(rev_pick / random.randint(900, 1200))
        db.upsert_daily_revenue(
            d.isoformat(), branch_id,
            round(rev_del, 2), round(rev_pick, 2),
            ord_del, ord_pick, user_id=None,
        )
        db.upsert_daily_expense(
            d.isoformat(), branch_id,
            shop_purchase=random.randint(2000, 6500),
            household=random.randint(800, 2500),
            note=None, user_id=None,
        )
print(f"✓ Daily revenue+expenses for {days_back} days × 2 branches")

# Несколько ad-hoc daily extra costs (для теста архива истории)
with db.conn() as c:
    if c.execute("SELECT COUNT(*) FROM daily_extra_costs").fetchone()[0] == 0:
        owner = c.execute("SELECT id FROM users WHERE role='owner'").fetchone()
        owner_id = owner[0] if owner else None
        extras = [
            (today.isoformat(), 1, "staff_meals", None, 1800, "Обеды поваров"),
            (today.isoformat(), 2, "staff_meals", None, 1500, "Обеды смены"),
            ((today - timedelta(days=1)).isoformat(), 1, "equipment", "Холодильник", 8500, "Срочный ремонт"),
            ((today - timedelta(days=2)).isoformat(), None, "marketing_smm", "Reels", 4500, "Boost постов"),
            ((today - timedelta(days=3)).isoformat(), 2, "other", "Канцелярия", 1200, None),
        ]
        for d, bid, cat, sub, amt, note in extras:
            db.add_daily_extra_cost(d, bid, cat, sub, amt, note, owner_id)
        print(f"✓ {len(extras)} ad-hoc daily extra costs seeded")

# Месячные расходы
with db.conn() as c:
    if c.execute("SELECT COUNT(*) FROM monthly_costs WHERE period=?", (period,)).fetchone()[0] == 0:
        monthly_data = [
            (1, "food_supply", 850_000, "Поставщики Ростовская"),
            (2, "food_supply", 720_000, "Поставщики 9 Января"),
            (1, "communal_rent", 145_000, "Аренда + ЖКХ + охрана"),
            (2, "communal_rent", 130_000, "Аренда + ЖКХ + охрана"),
            (1, "internet_phone", 4_500, None),
            (2, "internet_phone", 4_500, None),
            (1, "equipment", 22_000, "Ремонт холодильника"),
            (2, "equipment", 8_000, None),
            (None, "bank_credit", 75_000, "Кредит на оборудование"),
            (1, "bank_commission", 18_500, "СБЕР + ТОЧКА"),
            (2, "bank_commission", 16_200, "СБЕР + ТОЧКА"),
            (None, "marketing_blogger", 65_000, "Блогеры Воронежа"),
            (None, "marketing_smm", 48_000, "SMM-агентство"),
            (1, "ya_eda", 185_000, "Комиссия + тариф"),
            (2, "ya_eda", 165_000, "Комиссия + тариф"),
            (1, "kuper", 42_000, None),
            (2, "kuper", 38_000, None),
            (None, "ya_direct", 35_000, None),
            (None, "revvy", 8_900, "Подписка"),
            (None, "site", 6_500, "goulash.tech"),
            (None, "taxes", 280_000, "АУСН 8%"),
        ]
        for bid, cat, amt, note in monthly_data:
            c.execute(
                """INSERT INTO monthly_costs(period, branch_id, category, amount, note)
                   VALUES (?, ?, ?, ?, ?)""",
                (period, bid, cat, amt, note),
            )
        print(f"✓ Monthly costs for {period}")

# ФОТ
with db.conn() as c:
    if c.execute("SELECT COUNT(*) FROM salary_payments WHERE period=?", (period,)).fetchone()[0] == 0:
        fot_amounts = {
            "managing": 90_000, "sushef": 75_000, "chef": 55_000, "admin": 45_000,
            "courier": 50_000, "chef_trainee": 32_000, "admin_trainee": 28_000,
            "accounting": 40_000, "marketing": 60_000,
        }
        for emp in db.list_employees():
            amt = fot_amounts.get(emp["category"], 40_000)
            db.add_salary_payment(period, emp["id"], amt,
                                   today.replace(day=min(today.day, 15)).isoformat(),
                                   None, None)
        print(f"✓ Salaries for {period}")

# Планы
with db.conn() as c:
    if c.execute("SELECT COUNT(*) FROM monthly_plans WHERE period=?", (period,)).fetchone()[0] == 0:
        plans = [
            ("food_supply", 1_500_000),
            ("communal_rent", 280_000),
            ("marketing_blogger", 70_000),
            ("marketing_smm", 50_000),
            ("ya_eda", 350_000),
            ("kuper", 80_000),
            ("ya_direct", 30_000),
            ("equipment", 25_000),
            ("taxes", 290_000),
            ("fot_total", 900_000),
        ]
        for cat, amt in plans:
            db.upsert_plan(period, None, cat, amt)
        print(f"✓ Plans for {period}")

print("\n🎉 Seed complete!")
print(f"\nЛогин для теста:")
print(f"  Владелец:    anton / {os.getenv('OWNER_PASSWORD')}")
print(f"  Управляющий: manager / {os.getenv('MANAGER_PASSWORD')}")
