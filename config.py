"""
╔══════════════════════════════════════════════════════════════╗
║  AUREX — config.py                                          ║
║  Centralized configuration and environment management       ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────
# Load .env file
# ─────────────────────────────────────────────────────────────
load_dotenv()

# ─────────────────────────────────────────────────────────────
# BASE DIRECTORIES
# ─────────────────────────────────────────────────────────────
BASE_DIR: Path = Path(__file__).parent.resolve()
WORKSPACE_DIR: Path = BASE_DIR / "workspace"
TEMP_DIR: Path = BASE_DIR / "temp"
LOG_DIR: Path = BASE_DIR / "logs"

# Ensure directories exist on import
WORKSPACE_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────────
# API CREDENTIALS  (raise early if missing)
# ─────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

def validate_config() -> bool:
    """Validate required environment variables are set."""
    errors = []
    if not TELEGRAM_BOT_TOKEN:
        errors.append("❌ TELEGRAM_BOT_TOKEN is not set in .env")
    if not GEMINI_API_KEY:
        errors.append("❌ GEMINI_API_KEY is not set in .env")
    
    if errors:
        print("\n" + "═" * 60)
        print("  AUREX Configuration Error")
        print("═" * 60)
        for err in errors:
            print(f"  {err}")
        print("\n  Please copy .env.example → .env and fill in your keys.")
        print("  Get Gemini key FREE at: https://aistudio.google.com/app/apikey")
        print("  Get Telegram token from: @BotFather on Telegram")
        print("═" * 60 + "\n")
        return False
    return True


# ─────────────────────────────────────────────────────────────
# GEMINI MODEL SETTINGS
# ─────────────────────────────────────────────────────────────
GEMINI_MODEL: str = "gemini-1.5-flash"          # Free, fast, multimodal
GEMINI_MAX_OUTPUT_TOKENS: int = 2048
GEMINI_TEMPERATURE: float = 0.7
GEMINI_SAFETY_THRESHOLD: str = "BLOCK_ONLY_HIGH" # Less restrictive for general use

# ─────────────────────────────────────────────────────────────
# MEMORY / DATABASE SETTINGS
# ─────────────────────────────────────────────────────────────
MEMORY_DB_PATH: str = str(BASE_DIR / "aurex_memory.db")
CONVERSATION_HISTORY_LIMIT: int = 20   # Number of past turns to include
MAX_FACTS_PER_USER: int = 50           # Max stored facts per user

# ─────────────────────────────────────────────────────────────
# BOT BEHAVIOR SETTINGS
# ─────────────────────────────────────────────────────────────
AUDIO_RESPONSE_ENABLED: bool = os.getenv("AUDIO_RESPONSE", "true").lower() == "true"
MAX_VOICE_RESPONSE_CHARS: int = 600     # Only generate audio if response < this length
MAX_TG_MESSAGE_LENGTH: int = 4000       # Telegram limit is 4096 chars
TYPING_DELAY_THRESHOLD: int = 100       # Show typing indicator for messages > this long

# ─────────────────────────────────────────────────────────────
# SERVER SETTINGS (for health-check keep-alive)
# ─────────────────────────────────────────────────────────────
PORT: int = int(os.getenv("PORT", 8080))
WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "").rstrip("/")

# ─────────────────────────────────────────────────────────────
# ACCESS CONTROL
# ─────────────────────────────────────────────────────────────
ADMIN_USER_ID: int = int(os.getenv("ADMIN_USER_ID", 0))
ALLOW_ALL_USERS: bool = ADMIN_USER_ID == 0  # If no admin set, allow everyone

# ─────────────────────────────────────────────────────────────
# LOGGING SETUP
# ─────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

def setup_logging() -> logging.Logger:
    """Configure application logging with colors and file output."""
    try:
        import colorlog
        handler = colorlog.StreamHandler()
        handler.setFormatter(colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s [%(levelname)s] %(name)s: %(message)s%(reset)s",
            datefmt="%H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            }
        ))
    except ImportError:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S"
        ))
    
    # File handler
    file_handler = logging.FileHandler(LOG_DIR / "aurex.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.addHandler(file_handler)
    
    # Suppress noisy third-party loggers
    for noisy in ["httpx", "httpcore", "telegram.ext", "urllib3"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)
    
    return logging.getLogger("AUREX")


# ─────────────────────────────────────────────────────────────
# TTS VOICE SETTINGS
# ─────────────────────────────────────────────────────────────
TTS_VOICE: str = "en-US-AriaNeural"         # Edge TTS voice (free, high quality)
TTS_RATE: str = "+10%"                       # Speech rate (+/- %)
TTS_PITCH: str = "+0Hz"                      # Voice pitch
TTS_FALLBACK_LANG: str = "en"               # gTTS fallback language

# Available Edge TTS voices (all free):
# en-US-AriaNeural   → Female, warm, expressive
# en-US-GuyNeural    → Male, professional
# en-US-JennyNeural  → Female, friendly
# en-GB-SoniaNeural  → British female
# Change TTS_VOICE above to use different voices

# ─────────────────────────────────────────────────────────────
# PLAYWRIGHT BROWSER SETTINGS
# ─────────────────────────────────────────────────────────────
BROWSER_TIMEOUT_MS: int = 30_000    # 30 second page load timeout
BROWSER_HEADLESS: bool = True
BROWSER_ARGS: list = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--no-first-run",
    "--disable-extensions",
]

# ─────────────────────────────────────────────────────────────
# AUREX PERSONALITY CONSTANTS
# ─────────────────────────────────────────────────────────────
AUREX_VERSION: str = "1.0.0"
AUREX_TAGLINE: str = "Advanced Universal Reasoning & Execution Assistant"
AUREX_BANNER: str = f"""
╔══════════════════════════════════════════╗
║   🤖 A U R E X  v{AUREX_VERSION}                     ║
║   {AUREX_TAGLINE[:42]}  ║
║   Powered by Google Gemini 1.5 Flash     ║
╚══════════════════════════════════════════╝"""
