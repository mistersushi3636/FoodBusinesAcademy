import asyncio
import random
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from config import settings
from services.planner_db import (
    get_tasks_for_date, get_overdue_tasks,
    get_pending_reminders_1h, get_pending_reminders_at,
    update_task, get_setting, set_setting,
)


MORNING_GREETINGS = [
    "Антон, доброе утро! ☀️\nШутка дня: владелец суши-ресторана — единственный, у кого бизнес идёт «как по маслу». Правда, на соевом соусе. 🍣\nЯ подготовил ваш план. Хорошего дня!",
    "Антон, доброе утро! 🌅\nГоворят, лучший способ начать день — это хороший завтрак и хороший план. Завтрак за вами, план — за мной. Желаю удачного дня!",
    "Антон, с добрым утром! ☕\nФакт дня: каждое утро продуктивный человек начинает с чашки кофе и списка задач. Кофе у вас, задачи — ниже. Желаю продуктивности!",
    "Доброе утро, Антон! 🚀\nМотивация дня: великие дела начинаются с маленьких шагов. Вот ваши шаги на сегодня. Вперёд!",
    "Антон, доброе утро! 🌞\nПочему рестораторы никогда не опаздывают? Потому что знают: время — деньги, а деньги — это маржа. Ваш план готов, время идёт!",
    "С добрым утром, Антон! 🏆\nСегодня новый день, новые возможности. Я уже всё разложил по полочкам. Ваша задача — выполнить. Желаю боевого настроя!",
    "Антон, доброе утро! 🌤️\nПрограммисты говорят: «Кофе превращается в код». Рестораторы знают: «Кофе превращается в прибыль». Ваши задачи ниже — желаю конвертации! 💰",
    "Доброе утро, Антон! ⚡\nГотов к новому дню? Я уже готов — план составлен, задачи расставлены по приоритетам. Желаю сфокусированного и результативного дня!",
    "Антон, утро добрым бывает тогда, когда есть чёткий план. ✅\nУ вас он есть — ниже. Желаю воплотить всё в жизнь!",
    "С добрым утром! ☀️\nСегодня хороший день чтобы сделать что-то хорошее для FBA. Ваши задачи ждут. Желаю ясности ума и решительности!",
    "Доброе утро, Антон! 🎯\nШутка: бизнесмен приходит к врачу. «Доктор, я устал». «Отпуск?» «Нет, уволю ещё двух менеджеров». Ну а пока — вот ваш план на сегодня!",
    "Антон, доброе утро! 🌿\nЛучший способ предсказать будущее — создать его. Сегодня у вас есть шанс. Вот с чего начать:",
    "С добрым утром, Антон! 💪\nНовый день — новая страница в истории FBA. Я подготовил план. Желаю результатов, которыми будете гордиться!",
    "Доброе утро! 🏅\nВы знаете, что объединяет лучших рестораторов? Они знают свои цифры и выполняют планы. Ваш план на сегодня — ниже. Желаю удачи!",
    "Антон, с добрым утром! 🌸\nКаждое утро — это перезапуск. Вчера осталось вчера. Сегодня — новые задачи и новые победы. Поехали!",
]


def _reminder_keyboard(task_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Понял", callback_data=f"task_done:{task_id}"),
        InlineKeyboardButton(text="⏰ +30 мин", callback_data=f"task_snooze:{task_id}:30"),
    )
    builder.row(
        InlineKeyboardButton(
            text="🔕 Выкл это напоминание", callback_data=f"task_remind_off:{task_id}"
        )
    )
    return builder.as_markup()


def _format_morning_plan(tasks: list, overdue: list) -> str:
    now = datetime.now()
    date_str = now.strftime("%d %B %Y")
    greeting = random.choice(MORNING_GREETINGS)

    lines = [greeting, "", f"📅 <b>Расписание на {date_str}</b>", ""]

    if overdue:
        lines.append("🔴 <b>Просроченные:</b>")
        for t in overdue[:5]:
            lines.append(f"  • [{t['task_date']}] {t['title']}")
        lines.append("")

    important = [t for t in tasks if t["is_important"]]
    regular = [t for t in tasks if not t["is_important"]]
    timed = sorted([t for t in regular if t.get("task_time")], key=lambda x: x["task_time"])
    untimed = [t for t in regular if not t.get("task_time")]

    if important:
        lines.append("⭐ <b>ВАЖНЫЕ:</b>")
        for t in sorted(important, key=lambda x: x.get("task_time") or "99:99"):
            tm = f"🕐 {t['task_time']} — " if t.get("task_time") else ""
            lines.append(f"  ⭐ {tm}{t['title']}")
        lines.append("")

    if timed:
        lines.append("⏰ <b>По времени:</b>")
        for t in timed:
            lines.append(f"  🕐 {t['task_time']} — {t['title']}")
        lines.append("")

    if untimed:
        lines.append("📌 <b>Без времени:</b>")
        for t in untimed:
            lines.append(f"  • {t['title']}")
        lines.append("")

    total = len(tasks)
    imp_count = len(important)
    suffix = f" ({imp_count} важных)" if imp_count else ""
    lines.append(f"📊 Итого: {total} задач{suffix}")

    tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    return "\n".join(lines)


async def _run_scheduler(bot: Bot) -> None:
    while True:
        try:
            now = datetime.now()

            # Global notifications check
            notif_enabled = await get_setting("notifications_enabled", "1")

            if notif_enabled == "1":
                today = now.strftime("%Y-%m-%d")
                now_time = now.strftime("%H:%M")

                # 1h reminders: tasks due in ~60 min
                one_hour = (now + timedelta(hours=1)).strftime("%H:%M")
                tasks_1h = await get_pending_reminders_1h(today, one_hour)
                for task in tasks_1h:
                    try:
                        await bot.send_message(
                            chat_id=settings.anton_chat_id,
                            text=(
                                f"🔔 <b>Через 1 час:</b> {task['title']}\n"
                                f"⏰ {task['task_time']}"
                                + (" ⭐" if task["is_important"] else "")
                            ),
                            reply_markup=_reminder_keyboard(task["id"]),
                        )
                        await update_task(task["id"], reminded_1h=1)
                        logger.info(f"Sent 1h reminder for task {task['id']}")
                    except Exception as e:
                        logger.error(f"1h reminder send failed: {e}")

                # At-time reminders
                tasks_at = await get_pending_reminders_at(today, now_time)
                for task in tasks_at:
                    try:
                        await bot.send_message(
                            chat_id=settings.anton_chat_id,
                            text=(
                                f"⏰ <b>Сейчас:</b> {task['title']}"
                                + (" ⭐" if task["is_important"] else "")
                            ),
                            reply_markup=_reminder_keyboard(task["id"]),
                        )
                        await update_task(task["id"], reminded_at=1)
                        logger.info(f"Sent at-time reminder for task {task['id']}")
                    except Exception as e:
                        logger.error(f"At-time reminder send failed: {e}")

            # Morning plan at 10:00
            if now.hour == 10 and now.minute == 0:
                last_plan = await get_setting("last_morning_plan", "")
                today_str = now.strftime("%Y-%m-%d")
                if last_plan != today_str:
                    try:
                        tasks = await get_tasks_for_date(today_str)
                        overdue = await get_overdue_tasks(today_str)
                        text = _format_morning_plan(tasks, overdue)
                        await bot.send_message(
                            chat_id=settings.anton_chat_id,
                            text=text[:4000],
                        )
                        await set_setting("last_morning_plan", today_str)
                        logger.info("Sent morning plan")
                    except Exception as e:
                        logger.error(f"Morning plan failed: {e}")

        except Exception as e:
            logger.error(f"Scheduler error: {e}")

        await asyncio.sleep(60)


def setup_task_scheduler(bot: Bot) -> None:
    asyncio.create_task(_run_scheduler(bot))
    logger.info("Task scheduler started")
