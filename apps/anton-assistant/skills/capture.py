"""
/capture skill — structures raw voice transcript or text into a content idea.
Saves to knowledge-base/transcripts/ and returns structured idea dict.
"""
import re
from datetime import datetime
from pathlib import Path

from loguru import logger

from apps.shared.anthropic_client import ask

VAULT = Path(__file__).parents[3]

CAPTURE_SYSTEM = """
Ты помощник Антона Коваленко (Food Business Academy).
Получаешь сырой голосовой транскрипт или текстовую заметку.
Твоя задача — выделить суть и структурировать.

Верни ТОЛЬКО JSON (без пояснений):
{
  "slug": "kebab-case-slug-max-40-chars",
  "pillar": "💰|⚙️|📣|📖|🔮",
  "core_idea": "1-2 предложения — суть материала",
  "key_points": ["точка 1", "точка 2", "точка 3"],
  "numbers": ["цифры из текста если есть"],
  "recommended_format": "tg-post|short-video|long-video|carousel",
  "platforms": ["telegram", "instagram", "youtube"]
}
"""


async def run(
    *,
    raw_text: str,
    api_key: str,
    source_type: str = "voice",
) -> dict:
    """
    Структурировать сырой контент. Вернуть dict с idea-полями.
    Сохранить транскрипт в knowledge-base/transcripts/.
    """
    import json

    result = await ask(
        api_key=api_key,
        system=CAPTURE_SYSTEM,
        user=raw_text,
        max_tokens=500,
        cache_system=True,
    )

    try:
        raw = result.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
        idea = json.loads(raw)
    except Exception as e:
        logger.warning(f"/capture JSON parse error: {e}")
        idea = {
            "slug": "idea-" + datetime.now().strftime("%Y%m%d-%H%M"),
            "pillar": "📖",
            "core_idea": raw_text[:200],
            "key_points": [],
            "numbers": [],
            "recommended_format": "tg-post",
            "platforms": ["telegram"],
        }

    slug = re.sub(r"[^\w\-]", "", idea.get("slug", "idea"))[:40]
    date_prefix = datetime.now().strftime("%Y-%m-%d")

    # Save as structured transcript
    transcripts_dir = VAULT / "knowledge-base" / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    transcript_file = transcripts_dir / f"{date_prefix}-{slug}.md"

    transcript_file.write_text(
        f"---\n"
        f"date: {date_prefix}\n"
        f"slug: {slug}\n"
        f"source: {source_type}\n"
        f"pillar: {idea.get('pillar', '')}\n"
        f"format: {idea.get('recommended_format', '')}\n"
        f"platforms: {idea.get('platforms', [])}\n"
        f"status: captured\n"
        f"---\n\n"
        f"## Core Idea\n\n{idea.get('core_idea', '')}\n\n"
        f"## Key Points\n\n"
        + "\n".join(f"- {p}" for p in idea.get("key_points", [])) + "\n\n"
        f"## Numbers\n\n"
        + "\n".join(f"- {n}" for n in idea.get("numbers", [])) + "\n\n"
        f"## Raw Source\n\n{raw_text}\n",
        encoding="utf-8",
    )

    idea["transcript_file"] = str(transcript_file)
    logger.info(f"Idea captured: {slug} ({idea.get('pillar')}) → {transcript_file.name}")
    return idea
