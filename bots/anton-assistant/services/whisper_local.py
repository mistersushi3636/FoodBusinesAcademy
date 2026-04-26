import asyncio
from pathlib import Path

import av
import numpy as np
from loguru import logger

from config import settings


_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        logger.info(f"Loading Whisper model: {settings.whisper_model} ({settings.whisper_compute_type})")
        _model = WhisperModel(
            settings.whisper_model,
            device="cpu",
            compute_type=settings.whisper_compute_type,
        )
        logger.info("Whisper model loaded.")
    return _model


def _decode_audio(audio_path: Path, target_sr: int = 16000) -> np.ndarray:
    """Decode any audio format to float32 mono PCM using pyav (bundled ffmpeg)."""
    container = av.open(str(audio_path))
    resampler = av.AudioResampler(format="fltp", layout="mono", rate=target_sr)
    chunks = []
    for frame in container.decode(audio=0):
        for resampled in resampler.resample(frame):
            chunks.append(resampled.to_ndarray()[0])
    # flush resampler
    for resampled in resampler.resample(None):
        chunks.append(resampled.to_ndarray()[0])
    container.close()
    return np.concatenate(chunks).astype(np.float32)


def _transcribe_sync(audio_path: Path, language: str = "ru") -> str:
    audio = _decode_audio(audio_path)
    model = _get_model()
    segments, info = model.transcribe(
        audio,
        language=language,
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )
    text_parts = [seg.text for seg in segments]
    text = " ".join(text_parts).strip()
    logger.info(f"Transcribed {audio_path.name}: {len(text)} chars (lang: {info.language})")
    return text


async def transcribe(audio_path: Path, language: str = "ru") -> str:
    """Async wrapper — runs sync Whisper in thread pool."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _transcribe_sync, audio_path, language)
