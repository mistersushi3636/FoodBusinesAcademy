"""
V3 Orchestrator — state machine for voice→post→publish→metrics pipeline.
Each task moves through states: captured → drafting → visualizing → reviewing
→ awaiting (Anton) → publishing → learning → done.
"""
import json
from pathlib import Path

from loguru import logger

from config import settings, TRANSCRIPTS_DIR, CONTENT_DRAFTS, DESIGN_BRIEFS_DIR, PLATFORMS
from apps.shared.memory import (
    TaskState, init_db, create_task, update_task, get_task, get_pending_tasks,
)
from apps.shared.anthropic_client import ask
from apps.shared.openai_client import generate_image_to_file, transcribe_audio
from apps.shared.telegram_publisher import post_to_channel, send_semi_auto_draft

DB_PATH = Path(__file__).parent / "fba.db"


def setup() -> None:
    init_db(DB_PATH)


# ─── Entry points ─────────────────────────────────────────────────────────────

async def handle_voice(audio_path: Path) -> int:
    """Transcribe voice, create task, return task_id."""
    logger.info(f"Orchestrator: voice input {audio_path.name}")

    transcript = await transcribe_audio(
        api_key=settings.openai_api_key,
        audio_path=audio_path,
        language="ru",
    )

    ts = audio_path.stem
    transcript_file = TRANSCRIPTS_DIR / f"{ts}.md"
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    transcript_file.write_text(
        f"---\nsource: voice\ndate: {ts}\n---\n\n{transcript}\n",
        encoding="utf-8",
    )

    task_id = create_task(DB_PATH, source_type="voice", source_file=str(transcript_file))
    update_task(DB_PATH, task_id, state=TaskState.DRAFTING, idea_slug=ts)

    await _run_drafts(task_id, transcript)
    return task_id


async def handle_text(text: str, slug: str = "") -> int:
    """Create task from text idea/note."""
    if not slug:
        slug = text[:40].strip().replace(" ", "-").lower()

    task_id = create_task(DB_PATH, source_type="text")
    update_task(DB_PATH, task_id, state=TaskState.DRAFTING, idea_slug=slug)

    await _run_drafts(task_id, text)
    return task_id


async def handle_approve(task_id: int, platform: str) -> None:
    """Anton approved a draft — publish it."""
    task = get_task(DB_PATH, task_id)
    if not task:
        logger.warning(f"Task {task_id} not found")
        return

    update_task(DB_PATH, task_id, state=TaskState.PUBLISHING)
    await _publish(task_id, task, platform)


async def handle_cancel(task_id: int) -> None:
    update_task(DB_PATH, task_id, state=TaskState.CANCELLED)
    logger.info(f"Task {task_id} cancelled by Anton")


# ─── Pipeline steps ──────────────────────────────────────────────────────────

async def _run_drafts(task_id: int, raw_content: str) -> None:
    """Draft for all 3 platforms + generate image, then ask Anton to approve."""
    from skills.draft import run as draft
    from skills.visual import run as visual
    from skills.critique import run as critique

    task = get_task(DB_PATH, task_id)
    slug = task["idea_slug"] or str(task_id)
    CONTENT_DRAFTS.mkdir(parents=True, exist_ok=True)

    drafts: dict[str, str] = {}

    # Draft for each platform
    for platform in PLATFORMS:
        logger.info(f"Drafting for {platform} ...")
        draft_text = await draft(
            content=raw_content,
            platform=platform,
            api_key=settings.anthropic_api_key,
        )
        draft_file = CONTENT_DRAFTS / f"{slug}-{platform}.md"
        draft_file.write_text(draft_text, encoding="utf-8")
        drafts[platform] = draft_text
        logger.info(f"Draft saved: {draft_file}")

    update_task(DB_PATH, task_id,
                draft_tg=str(CONTENT_DRAFTS / f"{slug}-telegram.md"),
                draft_ig=str(CONTENT_DRAFTS / f"{slug}-instagram.md"),
                draft_yt=str(CONTENT_DRAFTS / f"{slug}-youtube.md"),
                state=TaskState.VISUALIZING)

    # Generate image based on TG draft
    try:
        image_path, image_prompt = await visual(
            draft_text=drafts.get("telegram", raw_content[:500]),
            slug=slug,
            api_key_anthropic=settings.anthropic_api_key,
            api_key_openai=settings.openai_api_key,
        )
        update_task(DB_PATH, task_id, image_path=str(image_path), state=TaskState.REVIEWING)
    except Exception as e:
        logger.warning(f"Visual generation failed (skipping): {e}")
        image_path = None
        update_task(DB_PATH, task_id, state=TaskState.REVIEWING)

    # Critique TG draft
    tg_draft = drafts.get("telegram", "")
    critique_result = await critique(
        draft_text=tg_draft,
        platform="telegram",
        api_key=settings.anthropic_api_key,
    )

    # If critique suggests major fixes, apply them
    if "[NEEDS_EDIT]" in critique_result:
        tg_draft = await draft(
            content=raw_content,
            platform="telegram",
            api_key=settings.anthropic_api_key,
            feedback=critique_result,
        )
        draft_file = CONTENT_DRAFTS / f"{slug}-telegram.md"
        draft_file.write_text(tg_draft, encoding="utf-8")
        update_task(DB_PATH, task_id, draft_tg=str(draft_file))

    update_task(DB_PATH, task_id, state=TaskState.AWAITING)
    await _send_for_approval(task_id, drafts, image_path)


async def _send_for_approval(
    task_id: int,
    drafts: dict[str, str],
    image_path: Path | None,
) -> None:
    """Send all drafts to Anton in Telegram for approval."""
    tg_draft = drafts.get("telegram", "")

    # TG draft first (most important, auto-publish candidate)
    await send_semi_auto_draft(
        bot_token=settings.bot_token,
        anton_chat_id=settings.anton_chat_id,
        platform="telegram",
        draft_text=(
            f"📋 <b>Черновик для TG</b> (task #{task_id}):\n\n{tg_draft}"
        ),
        image_path=image_path,
        task_id=task_id,
        extra_instructions="Нажми ✅ чтобы опубликовать в канал автоматически.",
    )

    # IG + YT drafts (semi-auto: Anton copies and posts manually)
    for platform in ["instagram", "youtube"]:
        draft_text = drafts.get(platform, "")
        if not draft_text:
            continue
        await send_semi_auto_draft(
            bot_token=settings.bot_token,
            anton_chat_id=settings.anton_chat_id,
            platform=platform,
            draft_text=draft_text,
            image_path=image_path if platform == "instagram" else None,
            task_id=task_id,
            extra_instructions=(
                "Semi-auto: скопируй текст → опубликуй в приложении → нажми ✅"
            ),
        )


async def _publish(task_id: int, task: dict, platform: str) -> None:
    """Publish approved draft."""
    if platform == "telegram":
        draft_path = Path(task["draft_tg"]) if task.get("draft_tg") else None
        if not draft_path or not draft_path.exists():
            logger.error(f"TG draft not found for task {task_id}")
            update_task(DB_PATH, task_id, state=TaskState.FAILED)
            return

        # Strip frontmatter from draft file
        raw = draft_path.read_text(encoding="utf-8")
        text = raw.split("---\n\n", 1)[-1] if "---\n\n" in raw else raw

        image_path = Path(task["image_path"]) if task.get("image_path") else None
        result = await post_to_channel(
            bot_token=settings.bot_token,
            channel_id=settings.tg_channel_id,
            text=text,
            image_path=image_path,
        )
        if result.get("ok"):
            update_task(DB_PATH, task_id, state=TaskState.DONE,
                        meta=json.dumps({"published_msg_id": result["result"]["message_id"]}))
            logger.info(f"Task {task_id} DONE — published to TG")
        else:
            update_task(DB_PATH, task_id, state=TaskState.FAILED)

    else:
        # IG / YT: Anton publishes manually, we just mark done
        update_task(DB_PATH, task_id, state=TaskState.DONE,
                    meta=json.dumps({"published_manually": platform}))
        logger.info(f"Task {task_id} DONE — {platform} marked as manually published")
