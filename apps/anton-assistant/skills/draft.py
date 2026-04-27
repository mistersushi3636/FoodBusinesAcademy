"""
/draft skill — turns raw content into a platform-formatted post.
Reads brand/tone-of-voice.md, brand/examples/, and platform format-rules.md as context.
"""
from pathlib import Path

from loguru import logger

from apps.shared.anthropic_client import ask

VAULT = Path(__file__).parents[3]  # FoodBusinesAcademy/


def _load_context(platform: str) -> str:
    """Load brand + platform rules as cached system context."""
    parts: list[str] = []

    tone_file = VAULT / "brand" / "tone-of-voice.md"
    if tone_file.exists():
        parts.append(f"## ГОЛОС БРЕНДА (tone-of-voice)\n\n{tone_file.read_text(encoding='utf-8')}")

    audience_file = VAULT / "brand" / "audience.md"
    if audience_file.exists():
        parts.append(f"## АУДИТОРИЯ\n\n{audience_file.read_text(encoding='utf-8')}")

    # Real post examples (up to 5)
    examples_dir = VAULT / "brand" / "examples"
    if examples_dir.exists():
        examples = []
        for f in sorted(examples_dir.glob("*.md"))[:5]:
            if f.name != "README.md":
                examples.append(f.read_text(encoding="utf-8"))
        if examples:
            parts.append(f"## ПРИМЕРЫ РЕАЛЬНЫХ ПОСТОВ АНТОНА\n\n" + "\n\n---\n\n".join(examples))

    # Platform format rules
    rules_file = VAULT / "platforms" / platform / "format-rules.md"
    if rules_file.exists():
        parts.append(f"## ПРАВИЛА ФОРМАТА ({platform.upper()})\n\n{rules_file.read_text(encoding='utf-8')}")

    # Learnings (what worked / didn't)
    learnings_file = VAULT / "patterns" / "learnings.md"
    if learnings_file.exists():
        learnings = learnings_file.read_text(encoding="utf-8")
        if "## 20" in learnings:  # has actual entries
            parts.append(f"## ЧТО ЗАШЛО (паттерны)\n\n{learnings}")

    return "\n\n---\n\n".join(parts)


async def run(
    *,
    content: str,
    platform: str,
    api_key: str,
    feedback: str = "",
) -> str:
    """
    Generate a post for the given platform.
    content: raw voice transcript or idea text
    feedback: optional critique from /critique skill (triggers rewrite)
    """
    system = _load_context(platform)

    rewrite_note = ""
    if feedback:
        rewrite_note = f"\n\n## ПРАВКИ ОТ РЕДАКТОРА\n\n{feedback}\n\nПереработай пост с учётом этих правок."

    user = f"""Напиши пост для {platform.upper()} на основе этого материала:

---
{content}
---
{rewrite_note}

Верни ТОЛЬКО текст поста — без пояснений, без «вот твой пост» и без markdown-обёртки.
Пост должен быть на русском языке в голосе Антона."""

    logger.info(f"Drafting for {platform} ({len(content)} chars input)")
    result = await ask(
        api_key=api_key,
        system=system,
        user=user,
        max_tokens=1500,
        cache_system=True,
    )
    return result.strip()
