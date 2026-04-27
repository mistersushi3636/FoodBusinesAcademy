"""
/plan skill — weekly cycle: reads metrics → competitor ideas → builds 30-day content plan.
Called by systemd timer every Monday 11:00.
"""
import glob
from datetime import datetime, timedelta
from pathlib import Path

from loguru import logger

from apps.shared.anthropic_client import ask
from apps.shared.telegram_publisher import send_semi_auto_draft

VAULT = Path(__file__).parents[3]

PLANNER_SYSTEM = """
Ты контент-маркетолог Food Business Academy.
Задача: анализировать метрики прошлой недели и строить стратегический 30-дневный контент-план.

Пиллары (доля):
- 💰 Деньги (30%) — маржа, юнит-экономика, чеки
- ⚙️ Операционка (20%) — найм, КПИ, регламенты
- 📣 Маркетинг (20%) — трафик, акции, упаковка
- 📖 Кейсы (20%) — свои истории, ошибки, успехи
- 🔮 Тренды (10%) — F&B новости, инструменты

Форматы: TG-пост (1200 знаков), Reels-сценарий (60 сек), YouTube (5-10 мин).
Платформы: Telegram (2-3/нед), Instagram (3-4/нед), YouTube (1/нед).

Правила A/B тестирования на первую неделю:
- Для каждой темы недели 1 — два хука: A (эмоциональный), B (экспертный/цифры).
- Антон выбирает по реакции аудитории через 24 ч.

Self-critique ОБЯЗАТЕЛЕН: пройди план 3 раза (стратегия / тон / реалистичность).
Формат ответа: структурированный markdown-план.
"""


def _load_latest_metrics() -> str:
    metrics_dir = VAULT / "analytics" / "metrics"
    if not metrics_dir.exists():
        return "Метрики за прошлую неделю: нет данных."

    files = sorted(metrics_dir.glob("*.md"), reverse=True)
    if not files:
        return "Метрики за прошлую неделю: нет данных."

    latest = files[0]
    logger.info(f"Loading metrics: {latest.name}")
    return latest.read_text(encoding="utf-8")


def _load_learnings() -> str:
    lf = VAULT / "patterns" / "learnings.md"
    if not lf.exists():
        return ""
    content = lf.read_text(encoding="utf-8")
    if "## 20" not in content:
        return ""
    return content


async def run(
    *,
    api_key: str,
    bot_token: str,
    anton_chat_id: int,
) -> str:
    """Build 30-day plan and notify Anton via Telegram."""
    week = datetime.now().strftime("%Y-W%V")
    logger.info(f"Running /plan for week {week}")

    metrics = _load_latest_metrics()
    learnings = _load_learnings()

    user_parts = [
        f"## Неделя: {week}",
        f"## Метрики прошлой недели\n\n{metrics}",
    ]
    if learnings:
        user_parts.append(f"## Паттерны (что зашло)\n\n{learnings}")

    user_parts.append(
        "Построй 30-дневный контент-план. Неделя 1 — с A/B вариантами. "
        "Добавь self-critique (стратегия / тон / реалистичность). "
        "Выдай финальный план в формате markdown."
    )

    plan_text = await ask(
        api_key=api_key,
        system=PLANNER_SYSTEM,
        user="\n\n".join(user_parts),
        max_tokens=3000,
        cache_system=True,
    )

    # Save plan
    plans_dir = VAULT / "content" / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    plan_file = plans_dir / f"{week}-plan.md"
    plan_file.write_text(
        f"---\nweek: {week}\nstatus: draft\ngenerated: {datetime.utcnow().isoformat()}\n---\n\n{plan_text}",
        encoding="utf-8",
    )
    logger.info(f"Plan saved: {plan_file}")

    # Notify Anton
    summary = plan_text[:1500] + "\n\n[...полный план в content/plans/]" if len(plan_text) > 1500 else plan_text
    await send_semi_auto_draft(
        bot_token=bot_token,
        anton_chat_id=anton_chat_id,
        platform="plan",
        draft_text=(
            f"📅 <b>Контент-план {week} готов</b>\n\n"
            f"{summary}"
        ),
        extra_instructions="Ответь «ок» или напиши правки.",
    )

    return plan_text
