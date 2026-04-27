"""
OpenAI client: DALL-E 3 image generation + Whisper API transcription.
Replaces local whisper (too heavy for 1GB RAM server).
"""
import base64
from pathlib import Path

import httpx
from loguru import logger
from openai import AsyncOpenAI

_client: AsyncOpenAI | None = None


def get_client(api_key: str) -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=api_key)
    return _client


# ─── DALL-E 3 ────────────────────────────────────────────────────────────────

async def generate_image(
    *,
    api_key: str,
    prompt: str,
    size: str = "1024x1024",
    quality: str = "standard",
    style: str = "vivid",
) -> bytes:
    """
    Generate image with DALL-E 3. Returns raw image bytes.
    size options: "1024x1024" | "1024x1792" | "1792x1024"
    quality: "standard" (~$0.04) | "hd" (~$0.08)
    """
    client = get_client(api_key)
    logger.info(f"DALL-E 3: size={size} quality={quality} prompt={prompt[:80]}...")

    response = await client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=size,
        quality=quality,
        style=style,
        response_format="b64_json",
        n=1,
    )

    b64 = response.data[0].b64_json
    revised = response.data[0].revised_prompt
    logger.debug(f"DALL-E revised prompt: {revised[:100] if revised else 'N/A'}")

    return base64.b64decode(b64)


async def generate_image_to_file(
    *,
    api_key: str,
    prompt: str,
    output_path: Path,
    size: str = "1024x1024",
    quality: str = "standard",
) -> Path:
    """Generate image and save to file. Returns path."""
    image_bytes = await generate_image(
        api_key=api_key,
        prompt=prompt,
        size=size,
        quality=quality,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image_bytes)
    logger.info(f"Image saved: {output_path} ({len(image_bytes)//1024} KB)")
    return output_path


# ─── Whisper API ─────────────────────────────────────────────────────────────

async def transcribe_audio(
    *,
    api_key: str,
    audio_path: Path,
    language: str = "ru",
) -> str:
    """
    Transcribe voice file via Whisper API. ~$0.006/min.
    Supports: mp3, mp4, mpeg, mpga, m4a, wav, webm, ogg.
    Telegram voice = ogg/opus — works fine.
    """
    client = get_client(api_key)
    file_size_kb = audio_path.stat().st_size // 1024
    logger.info(f"Whisper API: {audio_path.name} ({file_size_kb} KB) lang={language}")

    with open(audio_path, "rb") as f:
        transcript = await client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language=language,
            response_format="text",
        )

    text = transcript.strip() if isinstance(transcript, str) else transcript.text.strip()
    logger.info(f"Transcribed: {len(text)} chars")
    return text
