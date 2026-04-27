from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from config import IDEAS_INCOMING, IDEA_STATUSES, METRICS_DIR
from utils.markdown import write_markdown, read_markdown
from utils.slug import slugify, timestamp_slug


async def save_new_idea(text: str, source: str = "telegram") -> Path:
    """Save a fresh idea from Anton to ideas-bot/incoming/."""
    title_line = text.strip().split("\n")[0][:80]
    slug = slugify(title_line)
    filename = f"{timestamp_slug()}-{slug}.md"
    path = IDEAS_INCOMING / filename

    metadata = {
        "type": "idea",
        "status": "incoming",
        "source": source,
        "created": datetime.now().isoformat(),
        "title": title_line,
        "tags": [],
    }

    content = f"""## Описание

{text}

## История диалогов

- {datetime.now().strftime('%Y-%m-%d %H:%M')} — идея получена через {source}

## Анализ idea-curator

_(агент заполнит после анализа)_

## План реализации

_(заполняется после согласования с Антоном)_
"""

    await write_markdown(path, metadata, content)
    return path


async def move_idea(path: Path, new_status: str) -> Path:
    """Move idea file to a new status folder."""
    target_dir = next((p for s, _, p in IDEA_STATUSES if s == new_status), None)
    if not target_dir:
        raise ValueError(f"Unknown status: {new_status}")
    target_dir.mkdir(parents=True, exist_ok=True)
    new_path = target_dir / path.name

    metadata, content = await read_markdown(path)
    metadata["status"] = new_status
    metadata["updated"] = datetime.now().isoformat()
    await write_markdown(new_path, metadata, content)
    path.unlink()
    return new_path


async def append_to_idea(path: Path, section_header: str, text: str) -> None:
    """Append text under a section header in idea file."""
    metadata, content = await read_markdown(path)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    addition = f"\n- {timestamp} — {text}"
    if section_header in content:
        content = content.replace(section_header, section_header + addition, 1)
    else:
        content += f"\n\n{section_header}\n{addition}\n"
    metadata["updated"] = datetime.now().isoformat()
    await write_markdown(path, metadata, content)


async def find_idea_by_slug(slug: str) -> Optional[Path]:
    for status, _, directory in IDEA_STATUSES:
        if not directory.exists():
            continue
        for path in directory.glob("*.md"):
            if path.stem == slug:
                return path
    return None


async def save_metrics_entry(week_id: str, content: str) -> Path:
    """Save metrics entry to analytics/metrics/YYYY-WW.md."""
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    path = METRICS_DIR / f"{week_id}.md"

    if path.exists():
        existing_meta, existing_content = await read_markdown(path)
        merged_content = existing_content + f"\n\n## Дополнение {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n{content}"
        existing_meta["updated"] = datetime.now().isoformat()
        existing_meta["status"] = "complete"
        await write_markdown(path, existing_meta, merged_content)
    else:
        metadata = {
            "week": week_id,
            "status": "complete",
            "created": datetime.now().isoformat(),
            "source": "telegram-bot",
        }
        await write_markdown(path, metadata, content)
    return path
