from pathlib import Path
from typing import Any

import aiofiles
import frontmatter


async def write_markdown(path: Path, metadata: dict[str, Any], content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    post = frontmatter.Post(content, **metadata)
    text = frontmatter.dumps(post)
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(text)


async def read_markdown(path: Path) -> tuple[dict[str, Any], str]:
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        text = await f.read()
    post = frontmatter.loads(text)
    return dict(post.metadata), post.content


async def update_metadata(path: Path, **updates: Any) -> None:
    metadata, content = await read_markdown(path)
    metadata.update(updates)
    await write_markdown(path, metadata, content)


def list_idea_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(
        [p for p in directory.glob("*.md") if not p.name.startswith("README")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
