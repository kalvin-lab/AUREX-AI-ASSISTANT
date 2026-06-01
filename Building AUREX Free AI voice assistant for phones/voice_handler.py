"""
╔══════════════════════════════════════════════════════════════╗
║  AUREX — voice_handler.py                                   ║
║  Speech-to-Text (STT) + Text-to-Speech (TTS) pipelines     ║
║                                                              ║
║  STT Strategy:                                              ║
║    • Primary  → Gemini 1.5 Flash multimodal audio input     ║
║    • (handled directly in agent_brain.process_voice)        ║
║                                                              ║
║  TTS Strategy:                                              ║
║    • Primary  → edge-tts (Microsoft Neural, FREE, offline)  ║
║    • Fallback → gTTS (Google Translate TTS, FREE)           ║
╚══════════════════════════════════════════════════════════════╝
"""

import asyncio
import logging
import os
import tempfile
import uuid
from pathlib import Path

import aiofiles

from config import (
    TEMP_DIR,
    TTS_VOICE,
    TTS_RATE,
    TTS_PITCH,
    TTS_FALLBACK_LANG,
    AUDIO_RESPONSE_ENABLED,
    MAX_VOICE_RESPONSE_CHARS,
)

logger = logging.getLogger("AUREX.voice")


# ════════════════════════════════════════════════════════════════
# TEXT-TO-SPEECH ENGINE
# ════════════════════════════════════════════════════════════════

async def text_to_speech(text: str) -> str | None:
    """
    Convert text to an audio .mp3 file and return the file path.
    Returns None if TTS is disabled or text is too long.

    Strategy:
    1. Strip Markdown formatting (Telegram bolds/italics don't speak well)
    2. Truncate if too long
    3. Try edge-tts (Microsoft Neural voices — best quality)
    4. Fall back to gTTS if edge-tts fails
    """
    if not AUDIO_RESPONSE_ENABLED:
        return None

    # Only convert short responses to audio
    if len(text) > MAX_VOICE_RESPONSE_CHARS:
        logger.debug(f"Text too long for TTS ({len(text)} chars), skipping.")
        return None

    # Clean text for speech
    clean_text = _clean_for_speech(text)
    if not clean_text.strip():
        return None

    # Generate unique output path
    output_path = TEMP_DIR / f"aurex_tts_{uuid.uuid4().hex[:8]}.mp3"

    # Try edge-tts first
    result = await _tts_edge(clean_text, str(output_path))
    if result:
        return result

    # Fallback to gTTS
    result = await _tts_gtts(clean_text, str(output_path))
    if result:
        return result

    logger.warning("All TTS engines failed.")
    return None


def _clean_for_speech(text: str) -> str:
    """
    Remove Markdown formatting and clean text for natural speech.
    """
    import re

    # Remove markdown bold/italic/code
    text = re.sub(r"\*{1,3}(.+?)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,2}(.+?)_{1,2}", r"\1", text)
    text = re.sub(r"`{1,3}(.+?)`{1,3}", r"\1", text, flags=re.DOTALL)

    # Remove markdown headers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    # Replace common symbols with words
    replacements = {
        "→": "to",
        "←": "from",
        "•": ",",
        "–": "-",
        "—": "-",
        "═": "",
        "║": "",
        "╗": "",
        "╚": "",
        "╔": "",
        "╝": "",
        "…": "...",
        "&": "and",
        "@": "at",
        "🔍": "",
        "📺": "",
        "🌐": "",
        "📁": "",
        "✅": "done:",
        "❌": "error:",
        "⚠️": "warning:",
        "💬": "",
        "👤": "",
        "🤖": "",
    }
    for symbol, replacement in replacements.items():
        text = text.replace(symbol, replacement)

    # Remove URLs
    text = re.sub(r"https?://\S+", "a linked URL", text)

    # Remove emojis (simple range removal)
    text = re.sub(
        r"[\U00010000-\U0010ffff\U0001F600-\U0001F64F"
        r"\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
        r"\U0001F1E0-\U0001F1FF]",
        "", text
    )

    # Collapse multiple spaces/newlines
    text = re.sub(r"\n{2,}", ". ", text)
    text = re.sub(r"\n", " ", text)
    text = re.sub(r"\s{2,}", " ", text)

    # Truncate if still very long
    if len(text) > MAX_VOICE_RESPONSE_CHARS:
        text = text[:MAX_VOICE_RESPONSE_CHARS] + "... and so on."

    return text.strip()


async def _tts_edge(text: str, output_path: str) -> str | None:
    """
    Use Microsoft Edge TTS (free, high-quality neural voices).
    Requires: pip install edge-tts
    """
    try:
        import edge_tts

        communicate = edge_tts.Communicate(
            text=text,
            voice=TTS_VOICE,
            rate=TTS_RATE,
            pitch=TTS_PITCH,
        )
        await communicate.save(output_path)

        if Path(output_path).exists() and Path(output_path).stat().st_size > 1000:
            logger.debug(f"edge-tts generated: {output_path}")
            return output_path
        else:
            logger.warning("edge-tts produced empty/tiny file.")
            return None

    except ImportError:
        logger.warning("edge-tts not installed. Install with: pip install edge-tts")
        return None
    except Exception as e:
        logger.warning(f"edge-tts failed: {e}")
        return None


async def _tts_gtts(text: str, output_path: str) -> str | None:
    """
    Fallback TTS using Google Translate TTS (gTTS).
    Requires: pip install gTTS
    """
    try:
        from gtts import gTTS
        import io

        def _generate():
            tts = gTTS(text=text, lang=TTS_FALLBACK_LANG, slow=False)
            tts.save(output_path)

        await asyncio.to_thread(_generate)

        if Path(output_path).exists() and Path(output_path).stat().st_size > 1000:
            logger.debug(f"gTTS generated: {output_path}")
            return output_path
        return None

    except ImportError:
        logger.warning("gTTS not installed. Install with: pip install gTTS")
        return None
    except Exception as e:
        logger.warning(f"gTTS failed: {e}")
        return None


# ════════════════════════════════════════════════════════════════
# AUDIO FORMAT CONVERSION
# ════════════════════════════════════════════════════════════════

async def convert_ogg_to_bytes(ogg_path: str) -> bytes:
    """
    Read an OGG audio file and return raw bytes.
    Telegram voice messages come as .ogg (Opus codec).
    """
    async with aiofiles.open(ogg_path, "rb") as f:
        return await f.read()


async def convert_audio_if_needed(input_path: str, target_format: str = "mp3") -> str:
    """
    Convert audio file to target format using pydub.
    Returns path to converted file (or original if conversion fails).
    """
    if input_path.endswith(f".{target_format}"):
        return input_path

    output_path = input_path.rsplit(".", 1)[0] + f".{target_format}"

    try:
        from pydub import AudioSegment
        import io

        def _convert():
            audio = AudioSegment.from_file(input_path)
            audio.export(output_path, format=target_format)

        await asyncio.to_thread(_convert)

        if Path(output_path).exists():
            return output_path
    except ImportError:
        logger.warning("pydub not installed. Using original file format.")
    except Exception as e:
        logger.warning(f"Audio conversion failed: {e}")

    return input_path  # Return original if conversion fails


# ════════════════════════════════════════════════════════════════
# CLEANUP UTILITIES
# ════════════════════════════════════════════════════════════════

async def cleanup_temp_file(file_path: str) -> None:
    """Safely delete a temporary audio file."""
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            logger.debug(f"Temp file cleaned up: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to clean up temp file {file_path}: {e}")


async def cleanup_old_temp_files(max_age_minutes: int = 10) -> int:
    """Delete temp audio files older than max_age_minutes. Returns count deleted."""
    import time

    deleted = 0
    now = time.time()
    cutoff = now - (max_age_minutes * 60)

    try:
        for f in TEMP_DIR.iterdir():
            if f.is_file() and f.name.startswith("aurex_tts_"):
                if f.stat().st_mtime < cutoff:
                    f.unlink()
                    deleted += 1
    except Exception as e:
        logger.warning(f"Cleanup error: {e}")

    if deleted > 0:
        logger.info(f"Cleaned up {deleted} old temp audio files.")
    return deleted


# ════════════════════════════════════════════════════════════════
# VOICE LISTING UTILITY (for user help)
# ════════════════════════════════════════════════════════════════

AVAILABLE_VOICES = {
    "en-US-AriaNeural":    "🇺🇸 US English — Aria (Female, Warm)",
    "en-US-GuyNeural":     "🇺🇸 US English — Guy (Male, Professional)",
    "en-US-JennyNeural":   "🇺🇸 US English — Jenny (Female, Friendly)",
    "en-GB-SoniaNeural":   "🇬🇧 British English — Sonia (Female, Elegant)",
    "en-GB-RyanNeural":    "🇬🇧 British English — Ryan (Male, Casual)",
    "en-AU-NatashaNeural": "🇦🇺 Australian English — Natasha (Female)",
    "en-IN-NeerjaNeural":  "🇮🇳 Indian English — Neerja (Female)",
    "fr-FR-DeniseNeural":  "🇫🇷 French — Denise (Female)",
    "de-DE-KatjaNeural":   "🇩🇪 German — Katja (Female)",
    "es-ES-ElviraNeural":  "🇪🇸 Spanish — Elvira (Female)",
    "ja-JP-NanamiNeural":  "🇯🇵 Japanese — Nanami (Female)",
    "zh-CN-XiaoxiaoNeural":"🇨🇳 Chinese — Xiaoxiao (Female)",
    "ar-SA-ZariyahNeural": "🇸🇦 Arabic — Zariyah (Female)",
    "hi-IN-SwaraNeural":   "🇮🇳 Hindi — Swara (Female)",
    "ur-PK-UzmaNeural":    "🇵🇰 Urdu — Uzma (Female)",
}

def get_voice_list_text() -> str:
    """Return formatted list of available TTS voices."""
    lines = ["🎙️ **Available AUREX Voice Options:**\n"]
    for voice_id, description in AVAILABLE_VOICES.items():
        current = " ✅ _(current)_" if voice_id == TTS_VOICE else ""
        lines.append(f"• `{voice_id}` — {description}{current}")
    lines.append(
        "\n_To change voice, update `TTS_VOICE` in `.env` or `config.py`_"
    )
    return "\n".join(lines)
