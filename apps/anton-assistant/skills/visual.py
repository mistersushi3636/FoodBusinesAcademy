"""
/visual skill — generates DALL-E prompt from draft + creates image.
Returns (image_path, prompt).
"""
import re
from datetime import datetime
from pathlib import Path

from loguru import logger

from apps.shared.anthropic_client import ask
from apps.shared.openai_client import generate_image_to_file

VAULT = Path(__file__).parents[3]

DESIGN_SYSTEM_PROMPT = """
Ты генерируешь DALL-E 3 промпт для поста Food Business Academy.
Стиль: фотореализм + ресторанная/food-тематика. Тёплые цвета, профессиональный свет.
Никаких людей с читаемым текстом. Никаких логотипов. Никакого текста на картинке.
Формат ответа: ТОЛЬКО промпт на английском языке, без пояснений.
"""


async def run(
    *,
    draft_text: str,
    slug: str,
    api_key_anthropic: str,
    api_key_openai: str,
    size: str = "1024x1024",
    quality: str = "standard",
) -> tuple[Path, str]:
    """
    1. Ask Claude to generate DALL-E prompt from draft text.
    2. Generate image with DALL-E 3.
    3. Save to design-system/briefs/{slug}.png.
    Returns (image_path, prompt).
    """
    # Step 1: Generate DALL-E prompt
    prompt = await ask(
        api_key=api_key_anthropic,
        system=DESIGN_SYSTEM_PROMPT,
        user=f"Пост:\n\n{draft_text[:800]}\n\nСгенерируй DALL-E промпт для этого поста.",
        max_tokens=300,
        cache_system=True,
    )
    prompt = prompt.strip().strip('"')
    logger.info(f"DALL-E prompt: {prompt[:100]}...")

    # Step 2: Generate image
    output_dir = VAULT / "design-system" / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)

    date_prefix = datetime.now().strftime("%Y-%m-%d")
    safe_slug = re.sub(r"[^\w\-]", "", slug)[:40]
    image_path = output_dir / f"{date_prefix}-{safe_slug}.png"

    await generate_image_to_file(
        api_key=api_key_openai,
        prompt=prompt,
        output_path=image_path,
        size=size,
        quality=quality,
    )

    # Step 3: Save brief alongside image
    brief_path = output_dir / f"{date_prefix}-{safe_slug}-brief.md"
    brief_path.write_text(
        f"---\nslug: {safe_slug}\ndate: {date_prefix}\n---\n\n"
        f"## DALL-E prompt\n\n{prompt}\n\n## Image\n\n![](./{image_path.name})\n",
        encoding="utf-8",
    )

    return image_path, prompt
