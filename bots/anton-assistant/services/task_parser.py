import json
import re
from datetime import datetime
from typing import Dict, Any, Optional

from loguru import logger


IMPORTANT_KEYWORDS = [
    "важно", "важный", "важная", "важное", "важные",
    "срочно", "срочный", "срочная", "срочное",
    "критично", "критический", "горит", "asap", "must",
]


def _is_important(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in IMPORTANT_KEYWORDS)


async def parse_task_from_text(text: str) -> Dict[str, Any]:
    """
    Parse Russian natural language task via Claude.
    Falls back to raw text if Claude fails.
    """
    from services.claude_cli import ask_claude

    now = datetime.now()
    current_dt = now.strftime("%Y-%m-%d %H:%M")
    today = now.strftime("%Y-%m-%d")

    prompt = (
        f"Сегодня: {current_dt}\n\n"
        f'Пользователь говорит: "{text}"\n\n'
        "Извлеки задачу. Верни только JSON (без комментариев):\n"
        '{\n'
        '  "title": "краткое название без даты и времени",\n'
        '  "task_date": "YYYY-MM-DD или null",\n'
        '  "task_time": "HH:MM или null",\n'
        '  "recurring": "daily/weekly/weekday/null"\n'
        '}\n\n'
        "Правила:\n"
        "- title: суть задачи, без лишних слов\n"
        "- task_date: вычисли от текущей даты (завтра, в пятницу, через 3 дня)\n"
        "- task_time: переводи в 24ч (в три = 15:00, утром = 09:00, вечером = 19:00)\n"
        "- если дата/время не упомянуты — null\n"
        "Только JSON."
    )

    try:
        result = await ask_claude(prompt, timeout=25)
        m = re.search(r"\{[^{}]+\}", result, re.DOTALL)
        if m:
            data = json.loads(m.group())
            return {
                "title": (data.get("title") or text[:100]).strip(),
                "task_date": data.get("task_date") or None,
                "task_time": data.get("task_time") or None,
                "is_important": _is_important(text),
                "recurring": data.get("recurring") or None,
            }
    except Exception as e:
        logger.error(f"task_parser: Claude failed: {e}")

    return {
        "title": text[:200].strip(),
        "task_date": None,
        "task_time": None,
        "is_important": _is_important(text),
        "recurring": None,
    }


async def parse_edit_command(command: str, task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse voice edit command like 'перенеси на завтра в три'.
    Returns dict of fields to update, or None if unclear.
    """
    from services.claude_cli import ask_claude

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    prompt = (
        f"Сегодня: {now}\n"
        f"Задача: {task['title']} (дата: {task.get('task_date')}, время: {task.get('task_time')})\n"
        f'Команда: "{command}"\n\n'
        "Что нужно изменить в задаче? Верни только JSON:\n"
        '{\n'
        '  "action": "reschedule/rename/delete/done/none",\n'
        '  "task_date": "YYYY-MM-DD или null (не менять)",\n'
        '  "task_time": "HH:MM или null (не менять)",\n'
        '  "title": "новое название или null (не менять)"\n'
        '}\n'
        "Только JSON."
    )

    try:
        result = await ask_claude(prompt, timeout=25)
        m = re.search(r"\{[^{}]+\}", result, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception as e:
        logger.error(f"parse_edit_command failed: {e}")
    return None
