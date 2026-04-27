"""
/critique skill — reviews a draft for tone, facts, length. Returns feedback.
Tags [NEEDS_EDIT] if orchestrator should trigger a rewrite.
"""
from pathlib import Path

from apps.shared.anthropic_client import ask

VAULT = Path(__file__).parents[3]

CRITIQUE_SYSTEM = """
Ты редактор контента Food Business Academy. Проверяешь посты Антона Коваленко.

Критерии проверки:
1. ТОНАЛЬНОСТЬ — соответствует ли голосу Антона (прямой, конкретный, без воды, без инфоцыганщины)?
2. ФАКТЫ — есть ли конкретные цифры? Нет ли выдуманных чисел?
3. ДЛИНА — укладывается ли в норму платформы?
4. СТРУКТУРА — есть ли хук, контекст, вывод, вопрос?
5. CTA — есть ли призыв к действию?

Если пост хорош — ответь: [OK] + 1-2 строки что понравилось.
Если нужны правки — ответь: [NEEDS_EDIT] + конкретный список правок (что изменить, не как именно).

Никаких длинных рассуждений. Только вердикт и список.
"""

PLATFORM_LIMITS = {
    "telegram":  (700, 1200),
    "instagram": (400, 2200),
    "youtube":   (200, 500),    # for captions / scripts intro
}


async def run(
    *,
    draft_text: str,
    platform: str,
    api_key: str,
) -> str:
    """Returns critique string. Contains [NEEDS_EDIT] if rewrite needed."""
    min_len, max_len = PLATFORM_LIMITS.get(platform, (300, 1500))
    char_count = len(draft_text)
    length_note = ""
    if char_count < min_len:
        length_note = f"\n⚠️ СЛИШКОМ КОРОТКИЙ: {char_count} знаков (минимум {min_len})"
    elif char_count > max_len:
        length_note = f"\n⚠️ СЛИШКОМ ДЛИННЫЙ: {char_count} знаков (максимум {max_len})"

    user = (
        f"Платформа: {platform.upper()}{length_note}\n\n"
        f"Пост:\n\n{draft_text}"
    )

    result = await ask(
        api_key=api_key,
        system=CRITIQUE_SYSTEM,
        user=user,
        max_tokens=600,
        cache_system=True,
    )
    return result.strip()
