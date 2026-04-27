import asyncio
from pathlib import Path
from loguru import logger

from config import settings


async def run_claude_skill(skill_name: str, prompt: str, timeout: int = 300) -> str:
    """Run a Claude Code skill in headless mode and return output.

    Note: requires Claude CLI installed at settings.claude_cli_path.
    Used to invoke /idea-curator skill from the bot.
    """
    full_prompt = f"/{skill_name} {prompt}"
    logger.info(f"Calling Claude CLI: {skill_name}")

    process = await asyncio.create_subprocess_exec(
        settings.claude_cli_path,
        "-p",
        full_prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(settings.vault_path),
    )

    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        logger.error(f"Claude CLI timeout after {timeout}s for skill {skill_name}")
        return "⚠️ Анализ занял слишком много времени. Попробуй ещё раз позже."

    if process.returncode != 0:
        logger.error(f"Claude CLI failed: {stderr.decode()[:500]}")
        return f"⚠️ Ошибка анализа. Проверь Claude Code: {stderr.decode()[:200]}"

    return stdout.decode("utf-8", errors="replace").strip()


async def ask_claude(prompt: str, timeout: int = 60) -> str:
    """Send a raw prompt to Claude CLI and return the text response."""
    process = await asyncio.create_subprocess_exec(
        settings.claude_cli_path,
        "-p", prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(settings.vault_path),
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        return ""
    if process.returncode != 0:
        logger.error(f"ask_claude failed: {stderr.decode()[:300]}")
        return ""
    return stdout.decode("utf-8", errors="replace").strip()


async def analyze_idea_via_claude(idea_path: Path) -> str:
    """Trigger /idea-curator skill on a specific idea file."""
    relative_path = idea_path.relative_to(settings.vault_path)
    return await run_claude_skill("idea-curator", f"проанализируй идею в файле {relative_path}")


async def build_plan_via_claude(idea_path: Path) -> str:
    """Trigger plan building for a refined idea."""
    relative_path = idea_path.relative_to(settings.vault_path)
    return await run_claude_skill("idea-curator", f"построй план реализации для идеи в файле {relative_path}")
