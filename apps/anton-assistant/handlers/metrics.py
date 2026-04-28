"""
Metrics handler V3.
/metrics → шаблон немедленно.
Авто-детект: Anton присылает заполненный шаблон → парсит + сохраняет в дашборд.
"""
import json
import sys
from datetime import date, timedelta

from aiogram import Bot, Router, F
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger

from config import settings

router = Router(name="metrics")

_VAULT = settings.vault_path
_PROJECT_DB = _VAULT / "apps" / "dashboard" / "projects" / "fba-2-0.db"

TEMPLATE = """\
📊 МЕТРИКИ НЕДЕЛИ
{week_range}

Заполни и отправь обратно 👇

TELEGRAM (@Food_Busines_Academy)
Подписчиков всего:
Прирост за неделю:
Просмотры на пост (среднее):
Реакции на пост (среднее):
Постов опубликовано:
Лидов в бот:

INSTAGRAM
Подписчиков всего:
Прирост за неделю:
Охват на пост (среднее):
Лайки (среднее):
Сохранения (среднее):
Постов/Reels опубликовано:

YOUTUBE
Подписчиков всего:
Прирост за неделю:
Просмотров за неделю:
Видео/Shorts опубликовано:

БИЗНЕС
Обращений / заявок:
Консультаций проведено:

Лучший контент недели:
Главный вывод: \
"""


def _week_range() -> str:
    today = date.today()
    mon = today - timedelta(days=today.weekday())
    sun = mon + timedelta(days=6)
    return f"{mon.strftime('%d.%m')} — {sun.strftime('%d.%m.%Y')}"


def _week_start() -> str:
    today = date.today()
    return (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")


def _week_end() -> str:
    today = date.today()
    return (today - timedelta(days=today.weekday()) + timedelta(days=6)).strftime("%Y-%m-%d")


def _is_filled_metrics(text: str) -> bool:
    return sum(1 for k in ["TELEGRAM", "INSTAGRAM", "YOUTUBE", "Подписчиков"] if k in text) >= 3


async def send_metrics_template(bot: Bot) -> None:
    """Вызывается таймером каждое воскресенье 20:00."""
    await bot.send_message(settings.anton_chat_id, TEMPLATE.format(week_range=_week_range()))
    logger.info("Metrics template sent")


@router.message(Command("metrics"))
async def cmd_metrics(message: Message) -> None:
    if message.from_user.id != settings.anton_chat_id:
        return
    await message.answer(TEMPLATE.format(week_range=_week_range()))


@router.message(F.text)
async def receive_filled_metrics(message: Message) -> None:
    if message.from_user.id != settings.anton_chat_id:
        return
    if not message.text or not _is_filled_metrics(message.text):
        return

    await message.answer("📊 Получил метрики! Анализирую (~10 сек)...")
    try:
        dash_dir = str(_VAULT / "apps" / "dashboard")
        if dash_dir not in sys.path:
            sys.path.insert(0, dash_dir)

        from apps.shared.anthropic_client import ask
        import db as dash_db

        raw_json = await ask(
            api_key=settings.anthropic_api_key,
            system="Ты парсер данных. Возвращаешь только валидный JSON без пояснений.",
            user=(
                "Извлеки метрики из текста и верни ТОЛЬКО валидный JSON:\n"
                '{"telegram":{"subscribers_total":0,"subscribers_growth":0,"views_avg":0,'
                '"reactions_avg":0,"posts_count":0,"leads_count":0},'
                '"instagram":{"subscribers_total":0,"subscribers_growth":0,"reach_avg":0,'
                '"likes_avg":0,"saves_avg":0,"posts_count":0},'
                '"youtube":{"subscribers_total":0,"subscribers_growth":0,'
                '"views_week":0,"videos_count":0},'
                '"business":{"inquiries":0,"consultations":0},'
                '"extra":{"best_content":"","main_insight":""}}\n\n'
                f"Текст:\n{message.text}\n\nЕсли не указано — 0 или пустая строка. ТОЛЬКО JSON."
            ),
            max_tokens=600,
        )

        clean = raw_json.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        data = json.loads(clean)

        _PROJECT_DB.parent.mkdir(parents=True, exist_ok=True)
        dash_db.init_project_db(_PROJECT_DB)
        dash_db.save_metrics(_PROJECT_DB, _week_start(), data)

        lines = []
        for platform, fields in dash_db.METRICS_FIELDS.items():
            pdata = data.get(platform, {})
            lines.append(f"\n{dash_db.PLATFORM_LABELS[platform]}:")
            for key, label in fields:
                lines.append(f"  {label}: {pdata.get(key, '—')}")
        extra = data.get("extra", {})
        if extra.get("best_content"):
            lines.append(f"\nЛучший контент: {extra['best_content']}")
        if extra.get("main_insight"):
            lines.append(f"Главный вывод: {extra['main_insight']}")

        analysis = await ask(
            api_key=settings.anthropic_api_key,
            system="Ты стратегический аналитик контента для ресторанного бизнеса.",
            user=(
                f"Проанализируй метрики за неделю {_week_start()} для Food Business Academy:"
                + "\n".join(lines)
                + "\n\nНапиши анализ (~200 слов):\n"
                "1. Оценка недели (1–10)\n2. Достижения (2–3)\n"
                "3. Проблемные зоны (2–3)\n4. Три действия на следующую неделю"
            ),
            max_tokens=1200,
        )

        dash_db.save_report(_PROJECT_DB, _week_start(), _week_end(), "week", data, analysis)

        await message.answer(
            f"✅ <b>Метрики сохранены!</b>\n\n"
            f"<b>Анализ:</b>\n{analysis[:1800]}\n\n"
            f"📊 https://mistersushi36.pro/p/fba-2-0/reports"
        )
        logger.info(f"Metrics saved for week {_week_start()}")

    except json.JSONDecodeError as e:
        await message.answer(f"⚠️ Не смог распарсить: {e}\nПопробуй ещё раз.")
        logger.error(f"Metrics JSON error: {e}")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {e}")
        logger.error(f"Metrics error: {e}", exc_info=True)
