"""
/learn skill — analyses metrics input and appends insights to patterns/learnings.md.
Called after Anton provides weekly metrics.
"""
from datetime import datetime
from pathlib import Path

from loguru import logger

from apps.shared.anthropic_client import ask
from apps.shared.memory import append_learning

VAULT = Path(__file__).parents[3]

ANALYST_SYSTEM = """
Ты аналитик контента Food Business Academy.
Анализируешь метрики и выявляешь паттерны.

Формат ответа — ТОЛЬКО JSON-массив объектов, без пояснений:
[
  {
    "platform": "telegram|instagram|youtube",
    "pillar": "💰|⚙️|📣|📖|🔮",
    "worked": "что именно сработало (хук/структура/формат/время)",
    "metric": "конкретные цифры",
    "hypothesis": "почему, по твоей версии",
    "apply": "как использовать в будущих постах"
  }
]

Если данных мало — верни пустой массив: []
"""


async def run(
    *,
    metrics_text: str,
    week: str,
    api_key: str,
) -> list[dict]:
    """
    Parse metrics, extract learnings, append to patterns/learnings.md.
    Returns list of extracted learning dicts.
    """
    import json

    if not week:
        week = datetime.now().strftime("%Y-W%V")

    logger.info(f"Running /learn for {week}")

    result = await ask(
        api_key=api_key,
        system=ANALYST_SYSTEM,
        user=f"Метрики за {week}:\n\n{metrics_text}",
        max_tokens=1000,
        cache_system=True,
    )

    # Parse JSON
    try:
        raw = result.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
        learnings = json.loads(raw)
    except Exception as e:
        logger.warning(f"/learn JSON parse error: {e} — raw: {result[:200]}")
        return []

    # Append each learning to patterns/learnings.md
    learnings_path = VAULT / "patterns" / "learnings.md"
    for item in learnings:
        try:
            append_learning(
                learnings_path=learnings_path,
                week=week,
                platform=item.get("platform", "?"),
                pillar=item.get("pillar", "?"),
                worked=item.get("worked", ""),
                metric=item.get("metric", ""),
                hypothesis=item.get("hypothesis", ""),
                apply=item.get("apply", ""),
            )
        except Exception as e:
            logger.warning(f"append_learning failed: {e}")

    # Save raw metrics file
    metrics_dir = VAULT / "analytics" / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    metrics_file = metrics_dir / f"{week}.md"
    metrics_file.write_text(
        f"---\nweek: {week}\nrecorded: {datetime.utcnow().isoformat()}\n---\n\n{metrics_text}",
        encoding="utf-8",
    )
    logger.info(f"Metrics saved: {metrics_file}, {len(learnings)} learnings extracted")
    return learnings
