"""
SQLite слой PNP MR.SUSHI Финдир.

Структура:
- branches: справочник филиалов (Ростовская, 9 Января)
- users: владелец + управляющий
- daily_revenue: выручка по дням (доставка/самовывоз)
- daily_expenses: фиксированные ежедневные (магазин/хоз) [staff_meals оставлен для архива]
- daily_extra_costs: ad-hoc дневные расходы с любой категорией
- monthly_costs: месячные расходы (аренда, маркетинг, услуги, налоги и т.д.)
- employees: справочник сотрудников
- salary_payments: выплаты ФОТ
- monthly_plans: план/факт по категориям
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DB_PATH = Path(os.getenv("DASHBOARD_DB_PATH", Path(__file__).parent / "findir.db"))

COST_CATEGORIES = {
    "food_supply":       "Затраты на продукты (поставщики)",
    "staff_meals":       "Еда персонала",
    "internet_phone":    "Интернет + телефония",
    "equipment":         "Оборудование, инвентарь, ремонт",
    "bank_credit":       "Услуги банка (кредиты/займы)",
    "bank_commission":   "Банковские комиссии (терминал + тариф)",
    "communal_rent":     "Коммуналка + аренда + охрана/ПБ",
    "marketing_blogger": "Депозиты блогеров и партнёрства",
    "marketing_smm":     "SMM, таргет, реклама в соцсетях",
    "ya_eda":            "Яндекс Еда (комиссия 21,5% + тариф + возвраты)",
    "kuper":             "Купер (комиссия)",
    "ya_direct":         "Яндекс Директ",
    "revvy":             "Подписка REVVY",
    "site":              "Сайт (комиссия goulash.tech)",
    "taxes":             "Налоги (АУСН 8%)",
    "other":             "Прочее",
}

MARKETING_CATEGORIES = {"marketing_blogger", "marketing_smm", "ya_eda", "kuper", "ya_direct", "revvy"}

EMPLOYEE_CATEGORIES = {
    "managing":       "Управляющий",
    "sushef":         "Су-шеф",
    "chef":           "Повар",
    "admin":          "Администратор",
    "courier":        "Водитель-курьер",
    "chef_trainee":   "Повар-стажёр",
    "admin_trainee":  "Администратор-стажёр",
    "accounting":     "Бухгалтерия",
    "marketing":      "Маркетинг",
}

MANAGER_HIDDEN_EMPLOYEE_CATS = {"managing", "accounting", "marketing"}

BRANCHES = [
    (1, "Ростовская", "rostov"),
    (2, "9 Января",   "yan9"),
]


@contextmanager
def conn() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(DB_PATH))
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    try:
        yield c
        c.commit()
    finally:
        c.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS branches (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    pw_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('owner','manager')),
    branch_id INTEGER REFERENCES branches(id),
    tg_user_id INTEGER UNIQUE,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS daily_revenue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    branch_id INTEGER NOT NULL REFERENCES branches(id),
    revenue_delivery REAL DEFAULT 0,
    revenue_pickup REAL DEFAULT 0,
    orders_delivery INTEGER DEFAULT 0,
    orders_pickup INTEGER DEFAULT 0,
    created_by INTEGER REFERENCES users(id),
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(date, branch_id)
);

CREATE TABLE IF NOT EXISTS daily_expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    branch_id INTEGER NOT NULL REFERENCES branches(id),
    shop_purchase REAL DEFAULT 0,
    household REAL DEFAULT 0,
    staff_meals REAL DEFAULT 0,
    note TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(date, branch_id)
);

CREATE TABLE IF NOT EXISTS daily_extra_costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    branch_id INTEGER REFERENCES branches(id),
    category TEXT NOT NULL,
    subcategory TEXT,
    amount REAL NOT NULL,
    note TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS monthly_costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period TEXT NOT NULL,
    branch_id INTEGER REFERENCES branches(id),
    category TEXT NOT NULL,
    subcategory TEXT,
    amount REAL DEFAULT 0,
    note TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    category TEXT NOT NULL,
    branch_id INTEGER REFERENCES branches(id),
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS salary_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period TEXT NOT NULL,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    amount REAL NOT NULL,
    paid_at TEXT NOT NULL,
    note TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS monthly_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period TEXT NOT NULL,
    branch_id INTEGER REFERENCES branches(id),
    category TEXT NOT NULL,
    planned_amount REAL DEFAULT 0,
    UNIQUE(period, branch_id, category)
);

CREATE INDEX IF NOT EXISTS idx_daily_revenue_date ON daily_revenue(date);
CREATE INDEX IF NOT EXISTS idx_daily_expenses_date ON daily_expenses(date);
CREATE INDEX IF NOT EXISTS idx_daily_extra_date ON daily_extra_costs(date);
CREATE INDEX IF NOT EXISTS idx_monthly_costs_period ON monthly_costs(period);
CREATE INDEX IF NOT EXISTS idx_salary_period ON salary_payments(period);
"""


def init_db() -> None:
    with conn() as c:
        c.executescript(SCHEMA)
        for bid, name, slug in BRANCHES:
            c.execute(
                "INSERT OR IGNORE INTO branches(id, name, slug) VALUES (?, ?, ?)",
                (bid, name, slug),
            )
    _seed_default_users()


def _seed_default_users() -> None:
    import auth

    owner_u = os.getenv("OWNER_USERNAME", "anton")
    owner_p = os.getenv("OWNER_PASSWORD")
    mgr_u = os.getenv("MANAGER_USERNAME", "manager")
    mgr_p = os.getenv("MANAGER_PASSWORD")

    with conn() as c:
        if owner_p and not c.execute("SELECT 1 FROM users WHERE username=?", (owner_u,)).fetchone():
            c.execute(
                "INSERT INTO users(username, pw_hash, role) VALUES (?, ?, 'owner')",
                (owner_u, auth.hash_password(owner_p)),
            )
        if mgr_p and not c.execute("SELECT 1 FROM users WHERE username=?", (mgr_u,)).fetchone():
            c.execute(
                "INSERT INTO users(username, pw_hash, role) VALUES (?, ?, 'manager')",
                (mgr_u, auth.hash_password(mgr_p)),
            )


# ── Users ────────────────────────────────────────────────────────────────────

def get_user_by_username(username: str) -> sqlite3.Row | None:
    with conn() as c:
        return c.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()


def get_user_by_id(uid: int) -> sqlite3.Row | None:
    with conn() as c:
        return c.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()


def get_user_by_tg_id(tg_id: int) -> sqlite3.Row | None:
    with conn() as c:
        return c.execute("SELECT * FROM users WHERE tg_user_id=?", (tg_id,)).fetchone()


# ── Daily revenue & fixed expenses ───────────────────────────────────────────

def upsert_daily_revenue(date: str, branch_id: int, revenue_delivery: float,
                          revenue_pickup: float, orders_delivery: int,
                          orders_pickup: int, user_id: int | None = None) -> None:
    with conn() as c:
        c.execute(
            """
            INSERT INTO daily_revenue(date, branch_id, revenue_delivery, revenue_pickup,
                                      orders_delivery, orders_pickup, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date, branch_id) DO UPDATE SET
                revenue_delivery=excluded.revenue_delivery,
                revenue_pickup=excluded.revenue_pickup,
                orders_delivery=excluded.orders_delivery,
                orders_pickup=excluded.orders_pickup
            """,
            (date, branch_id, revenue_delivery, revenue_pickup,
             orders_delivery, orders_pickup, user_id),
        )


def upsert_daily_expense(date: str, branch_id: int, shop_purchase: float,
                          household: float, note: str | None,
                          user_id: int | None = None) -> None:
    with conn() as c:
        c.execute(
            """
            INSERT INTO daily_expenses(date, branch_id, shop_purchase, household,
                                       staff_meals, note, created_by)
            VALUES (?, ?, ?, ?, 0, ?, ?)
            ON CONFLICT(date, branch_id) DO UPDATE SET
                shop_purchase=excluded.shop_purchase,
                household=excluded.household,
                note=excluded.note
            """,
            (date, branch_id, shop_purchase, household, note, user_id),
        )


def get_daily_revenue_range(start: str, end: str, branch_id: int | None = None) -> list[sqlite3.Row]:
    sql = "SELECT * FROM daily_revenue WHERE date BETWEEN ? AND ?"
    args: list = [start, end]
    if branch_id:
        sql += " AND branch_id=?"
        args.append(branch_id)
    sql += " ORDER BY date, branch_id"
    with conn() as c:
        return list(c.execute(sql, args).fetchall())


def get_daily_expenses_range(start: str, end: str, branch_id: int | None = None) -> list[sqlite3.Row]:
    sql = "SELECT * FROM daily_expenses WHERE date BETWEEN ? AND ?"
    args: list = [start, end]
    if branch_id:
        sql += " AND branch_id=?"
        args.append(branch_id)
    sql += " ORDER BY date, branch_id"
    with conn() as c:
        return list(c.execute(sql, args).fetchall())


# ── Daily extra (ad-hoc) ─────────────────────────────────────────────────────

def add_daily_extra_cost(date: str, branch_id: int | None, category: str,
                          subcategory: str | None, amount: float,
                          note: str | None, user_id: int | None) -> int:
    with conn() as c:
        cur = c.execute(
            """INSERT INTO daily_extra_costs(date, branch_id, category, subcategory,
                                              amount, note, created_by)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (date, branch_id, category, subcategory, amount, note, user_id),
        )
        return cur.lastrowid


def get_daily_extra_costs(date: str, branch_id: int | None = None) -> list[sqlite3.Row]:
    sql = """SELECT e.*, b.name AS branch_name, u.username AS created_by_name
             FROM daily_extra_costs e
             LEFT JOIN branches b ON b.id = e.branch_id
             LEFT JOIN users u ON u.id = e.created_by
             WHERE e.date=?"""
    args: list = [date]
    if branch_id is not None:
        sql += " AND e.branch_id=?"
        args.append(branch_id)
    sql += " ORDER BY e.created_at DESC"
    with conn() as c:
        return list(c.execute(sql, args).fetchall())


def get_daily_extra_costs_range(start: str, end: str, branch_id: int | None = None) -> list[sqlite3.Row]:
    sql = "SELECT * FROM daily_extra_costs WHERE date BETWEEN ? AND ?"
    args: list = [start, end]
    if branch_id:
        sql += " AND branch_id=?"
        args.append(branch_id)
    with conn() as c:
        return list(c.execute(sql, args).fetchall())


def delete_daily_extra_cost(cost_id: int) -> None:
    with conn() as c:
        c.execute("DELETE FROM daily_extra_costs WHERE id=?", (cost_id,))


# ── Monthly costs ────────────────────────────────────────────────────────────

def add_monthly_cost(period: str, branch_id: int | None, category: str,
                      subcategory: str | None, amount: float,
                      note: str | None, user_id: int | None = None) -> int:
    with conn() as c:
        cur = c.execute(
            """INSERT INTO monthly_costs(period, branch_id, category, subcategory,
                                         amount, note, created_by)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (period, branch_id, category, subcategory, amount, note, user_id),
        )
        return cur.lastrowid


def get_monthly_costs(period: str, branch_id: int | None = None) -> list[sqlite3.Row]:
    sql = "SELECT * FROM monthly_costs WHERE period=?"
    args: list = [period]
    if branch_id:
        sql += " AND (branch_id=? OR branch_id IS NULL)"
        args.append(branch_id)
    sql += " ORDER BY category, subcategory"
    with conn() as c:
        return list(c.execute(sql, args).fetchall())


def delete_monthly_cost(cost_id: int) -> None:
    with conn() as c:
        c.execute("DELETE FROM monthly_costs WHERE id=?", (cost_id,))


# ── Employees & salary ───────────────────────────────────────────────────────

def list_employees(active_only: bool = True) -> list[sqlite3.Row]:
    sql = "SELECT e.*, b.name AS branch_name FROM employees e LEFT JOIN branches b ON b.id=e.branch_id"
    if active_only:
        sql += " WHERE e.is_active=1"
    sql += " ORDER BY e.category, e.full_name"
    with conn() as c:
        return list(c.execute(sql).fetchall())


def add_employee(full_name: str, category: str, branch_id: int | None) -> int:
    with conn() as c:
        cur = c.execute(
            "INSERT INTO employees(full_name, category, branch_id) VALUES (?, ?, ?)",
            (full_name, category, branch_id),
        )
        return cur.lastrowid


def deactivate_employee(emp_id: int) -> None:
    with conn() as c:
        c.execute("UPDATE employees SET is_active=0 WHERE id=?", (emp_id,))


def add_salary_payment(period: str, employee_id: int, amount: float,
                        paid_at: str, note: str | None, user_id: int | None) -> int:
    with conn() as c:
        cur = c.execute(
            """INSERT INTO salary_payments(period, employee_id, amount, paid_at, note, created_by)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (period, employee_id, amount, paid_at, note, user_id),
        )
        return cur.lastrowid


def get_salary_payments(period: str, branch_id: int | None = None) -> list[sqlite3.Row]:
    sql = """
    SELECT s.*, e.full_name, e.category, e.branch_id
    FROM salary_payments s
    JOIN employees e ON e.id = s.employee_id
    WHERE s.period=?
    """
    args: list = [period]
    if branch_id:
        sql += " AND (e.branch_id=? OR e.branch_id IS NULL)"
        args.append(branch_id)
    sql += " ORDER BY e.category, e.full_name"
    with conn() as c:
        return list(c.execute(sql, args).fetchall())


# ── Monthly plans ────────────────────────────────────────────────────────────

def upsert_plan(period: str, branch_id: int | None, category: str, amount: float) -> None:
    with conn() as c:
        c.execute(
            """INSERT INTO monthly_plans(period, branch_id, category, planned_amount)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(period, branch_id, category) DO UPDATE SET
                   planned_amount=excluded.planned_amount""",
            (period, branch_id, category, amount),
        )


def get_plans(period: str, branch_id: int | None = None) -> list[sqlite3.Row]:
    sql = "SELECT * FROM monthly_plans WHERE period=?"
    args: list = [period]
    if branch_id is not None:
        sql += " AND (branch_id=? OR branch_id IS NULL)"
        args.append(branch_id)
    with conn() as c:
        return list(c.execute(sql, args).fetchall())


def list_branches() -> list[sqlite3.Row]:
    with conn() as c:
        return list(c.execute("SELECT * FROM branches ORDER BY id").fetchall())


# ── Audit log ────────────────────────────────────────────────────────────────

def audit_log(limit: int = 200, kind: str | None = None,
               branch_id: int | None = None, user_id: int | None = None) -> list[dict]:
    """
    Объединённый журнал ввода данных.
    kind: 'revenue' | 'expense' | 'extra' | 'monthly' | 'salary' | None=все
    """
    parts = []
    if kind in (None, "revenue"):
        parts.append(
            """SELECT 'revenue' AS kind, r.id, r.date AS event_date, r.branch_id,
                       NULL AS category, NULL AS subcategory,
                       (r.revenue_delivery + r.revenue_pickup) AS amount,
                       NULL AS note,
                       r.created_at, r.created_by,
                       u.username AS created_by_name, b.name AS branch_name,
                       'Выручка ' || (r.orders_delivery + r.orders_pickup) || ' зак.' AS detail
                FROM daily_revenue r
                LEFT JOIN users u ON u.id = r.created_by
                LEFT JOIN branches b ON b.id = r.branch_id"""
        )
    if kind in (None, "expense"):
        parts.append(
            """SELECT 'expense' AS kind, e.id, e.date AS event_date, e.branch_id,
                       'daily_fixed' AS category, NULL AS subcategory,
                       (e.shop_purchase + e.household) AS amount,
                       e.note, e.created_at, e.created_by,
                       u.username AS created_by_name, b.name AS branch_name,
                       'Магазин+хоз/тара (фикс.)' AS detail
                FROM daily_expenses e
                LEFT JOIN users u ON u.id = e.created_by
                LEFT JOIN branches b ON b.id = e.branch_id"""
        )
    if kind in (None, "extra"):
        parts.append(
            """SELECT 'extra' AS kind, x.id, x.date AS event_date, x.branch_id,
                       x.category, x.subcategory, x.amount, x.note,
                       x.created_at, x.created_by,
                       u.username AS created_by_name, b.name AS branch_name,
                       'Доп. расход за день' AS detail
                FROM daily_extra_costs x
                LEFT JOIN users u ON u.id = x.created_by
                LEFT JOIN branches b ON b.id = x.branch_id"""
        )
    if kind in (None, "monthly"):
        parts.append(
            """SELECT 'monthly' AS kind, m.id, m.period AS event_date, m.branch_id,
                       m.category, m.subcategory, m.amount, m.note,
                       m.created_at, m.created_by,
                       u.username AS created_by_name, b.name AS branch_name,
                       'Месячный расход' AS detail
                FROM monthly_costs m
                LEFT JOIN users u ON u.id = m.created_by
                LEFT JOIN branches b ON b.id = m.branch_id"""
        )
    if kind in (None, "salary"):
        parts.append(
            """SELECT 'salary' AS kind, s.id, s.paid_at AS event_date, e.branch_id,
                       e.category, e.full_name AS subcategory, s.amount, s.note,
                       s.created_at, s.created_by,
                       u.username AS created_by_name, b.name AS branch_name,
                       'Выплата ФОТ' AS detail
                FROM salary_payments s
                JOIN employees e ON e.id = s.employee_id
                LEFT JOIN users u ON u.id = s.created_by
                LEFT JOIN branches b ON b.id = e.branch_id"""
        )

    union = " UNION ALL ".join(parts)
    sql = f"SELECT * FROM ({union}) sub"
    where = []
    args: list = []
    if branch_id:
        where.append("branch_id = ?")
        args.append(branch_id)
    if user_id:
        where.append("created_by = ?")
        args.append(user_id)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC LIMIT ?"
    args.append(limit)
    with conn() as c:
        return [dict(r) for r in c.execute(sql, args).fetchall()]
