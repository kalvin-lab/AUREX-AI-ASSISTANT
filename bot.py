"""
╔══════════════════════════════════════════════════════════════╗
║  AUREX — bot.py                                             ║
║  Telegram Bot Interface — the entry point of the entire app ║
║                                                              ║
║  Handles:                                                   ║
║    • Text messages → AUREXBrain                             ║
║    • Voice notes   → voice_handler → AUREXBrain             ║
║    • Slash commands → agent_brain.handle_command            ║
║    • Background task result delivery → user chat            ║
║    • Health-check HTTP server (for Render.com keep-alive)   ║
╚══════════════════════════════════════════════════════════════╝
"""

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

from aiohttp import web
from telegram import Update, Bot, constants
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import (
    TELEGRAM_BOT_TOKEN,
    PORT,
    WEBHOOK_URL,
    ALLOW_ALL_USERS,
    ADMIN_USER_ID,
    AUDIO_RESPONSE_ENABLED,
    TEMP_DIR,
    AUREX_BANNER,
    validate_config,
    setup_logging,
)
from memory_manager import MemoryManager
from agent_brain import AUREXBrain, SubAgent
from voice_handler import (
    text_to_speech,
    convert_ogg_to_bytes,
    cleanup_temp_file,
    cleanup_old_temp_files,
)

# ─────────────────────────────────────────────────────────────
# LOGGER SETUP
# ─────────────────────────────────────────────────────────────
logger = setup_logging()


# ════════════════════════════════════════════════════════════════
# GLOBALS (initialized in main)
# ════════════════════════════════════════════════════════════════
memory: MemoryManager
brain: AUREXBrain
sub_agent: SubAgent
bot_app: Application


# ════════════════════════════════════════════════════════════════
# ACCESS CONTROL
# ════════════════════════════════════════════════════════════════

def _is_allowed(user_id: int) -> bool:
    """Check if a user is allowed to use the bot."""
    if ALLOW_ALL_USERS:
        return True
    return user_id == ADMIN_USER_ID


# ════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════

async def _send_typing(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    """Send typing indicator to show AUREX is thinking."""
    try:
        await context.bot.send_chat_action(
            chat_id=chat_id,
            action=constants.ChatAction.TYPING,
        )
    except Exception:
        pass  # Typing indicator is cosmetic, never fail on it


async def _send_response(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    send_audio: bool = False,
    parse_mode: str = "Markdown",
) -> None:
    """
    Send a text (and optionally audio) response to the user.
    Handles long messages by splitting them safely.
    """
    chat_id = update.effective_chat.id
    MAX_LEN = 4000  # Telegram max is 4096; use 4000 for safety

    # ── Split and send long messages ──────────────────────────
    if len(text) > MAX_LEN:
        chunks = _split_message(text, MAX_LEN)
        for i, chunk in enumerate(chunks):
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=chunk,
                    parse_mode=parse_mode,
                )
                if i < len(chunks) - 1:
                    await asyncio.sleep(0.3)  # Small delay between chunks
            except Exception:
                # Retry without parse_mode if Markdown causes issues
                try:
                    await context.bot.send_message(chat_id=chat_id, text=chunk)
                except Exception as e:
                    logger.error(f"Failed to send message chunk: {e}")
    else:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
            )
        except Exception:
            try:
                await context.bot.send_message(chat_id=chat_id, text=text)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")

    # ── Send voice response if requested ──────────────────────
    if send_audio and AUDIO_RESPONSE_ENABLED:
        await _send_audio_response(context, chat_id, text)


async def _send_audio_response(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    text: str,
) -> None:
    """Generate TTS audio and send it as a voice message."""
    audio_path: str | None = None
    try:
        await context.bot.send_chat_action(
            chat_id=chat_id,
            action=constants.ChatAction.RECORD_VOICE,
        )
        audio_path = await text_to_speech(text)

        if audio_path and Path(audio_path).exists():
            with open(audio_path, "rb") as audio_file:
                await context.bot.send_voice(
                    chat_id=chat_id,
                    voice=audio_file,
                    caption="🎤 _AUREX voice response_",
                    parse_mode="Markdown",
                )
            logger.debug(f"Voice response sent to {chat_id}")
        else:
            logger.debug("TTS returned no audio (text too long or disabled).")
    except Exception as e:
        logger.warning(f"Failed to send audio response: {e}")
    finally:
        if audio_path:
            await cleanup_temp_file(audio_path)


def _split_message(text: str, max_len: int) -> list[str]:
    """Split a long message into chunks at sensible boundaries."""
    if len(text) <= max_len:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break

        # Find good split point: prefer paragraph > sentence > word boundary
        chunk = text[:max_len]
        split_at = (
            chunk.rfind("\n\n") or
            chunk.rfind("\n") or
            chunk.rfind(". ") or
            chunk.rfind(" ")
        )

        if split_at and split_at > max_len // 2:
            chunks.append(text[:split_at].rstrip())
            text = text[split_at:].lstrip()
        else:
            chunks.append(chunk)
            text = text[max_len:]

    return [c for c in chunks if c.strip()]


# ════════════════════════════════════════════════════════════════
# BACKGROUND TASK RESULT CALLBACK
# ════════════════════════════════════════════════════════════════

async def background_result_callback(user_id: int, result: str) -> None:
    """
    Called by SubAgent when a background task (web search etc.) completes.
    Proactively sends the result back to the user.
    """
    try:
        bot: Bot = bot_app.bot
        MAX_LEN = 4000
        header = "✅ **Your background task is complete!**\n\n"
        full_text = header + result

        if len(full_text) > MAX_LEN:
            chunks = _split_message(full_text, MAX_LEN)
            for chunk in chunks:
                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text=chunk,
                        parse_mode="Markdown",
                    )
                    await asyncio.sleep(0.3)
                except Exception:
                    await bot.send_message(chat_id=user_id, text=chunk)
        else:
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=full_text,
                    parse_mode="Markdown",
                )
            except Exception:
                await bot.send_message(chat_id=user_id, text=full_text)

        logger.info(f"Background result delivered to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to deliver background result to {user_id}: {e}")


# ════════════════════════════════════════════════════════════════
# TELEGRAM COMMAND HANDLERS
# ════════════════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    if not _is_allowed(user.id):
        await update.message.reply_text("⛔ Access denied.")
        return

    # Register user in memory
    memory.get_or_create_user(
        user.id, user.username, user.first_name, user.last_name
    )

    response = await brain.handle_command(user.id, "start")
    await _send_response(update, context, response)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    user = update.effective_user
    if not _is_allowed(user.id):
        return

    response = await brain.handle_command(user.id, "help")
    await _send_response(update, context, response)


async def cmd_memory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /memory command."""
    user = update.effective_user
    if not _is_allowed(user.id):
        return

    response = await brain.handle_command(user.id, "memory")
    await _send_response(update, context, response)


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /clear command."""
    user = update.effective_user
    if not _is_allowed(user.id):
        return

    response = await brain.handle_command(user.id, "clear")
    await _send_response(update, context, response)


async def cmd_forget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /forget <fact> command."""
    user = update.effective_user
    if not _is_allowed(user.id):
        return

    args = " ".join(context.args) if context.args else ""
    response = await brain.handle_command(user.id, "forget", args)
    await _send_response(update, context, response)


async def cmd_files(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /files command."""
    user = update.effective_user
    if not _is_allowed(user.id):
        return

    response = await brain.handle_command(user.id, "files")
    await _send_response(update, context, response)


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command (admin only if ADMIN_USER_ID is set)."""
    user = update.effective_user
    if ADMIN_USER_ID and user.id != ADMIN_USER_ID:
        await update.message.reply_text("⛔ This command is for admins only.")
        return

    response = await brain.handle_command(user.id, "stats")
    await _send_response(update, context, response)


# ════════════════════════════════════════════════════════════════
# TEXT MESSAGE HANDLER
# ════════════════════════════════════════════════════════════════

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle all incoming text messages.
    Flow: receive → typing indicator → brain.process_message → send response
    """
    user = update.effective_user
    message = update.message

    # Access control
    if not _is_allowed(user.id):
        await message.reply_text("⛔ Access denied. Contact the bot admin.")
        return

    # Ensure user is registered
    memory.get_or_create_user(
        user.id, user.username, user.first_name, user.last_name
    )

    text = message.text.strip()
    if not text:
        return

    logger.info(f"Text from {user.id} (@{user.username}): '{text[:80]}'")

    # Show typing indicator
    await _send_typing(context, message.chat_id)

    try:
        # Process with AI brain
        response = await brain.process_message(user.id, text, msg_type="text")

        # Send response
        await _send_response(
            update, context,
            response.text,
            send_audio=False,  # Text messages get text responses
        )

    except Exception as e:
        logger.error(f"Text handler error: {e}", exc_info=True)
        await message.reply_text(
            "⚠️ Something went wrong processing your message.\n"
            "Please try again. If the issue persists, use /clear to reset."
        )


# ════════════════════════════════════════════════════════════════
# VOICE MESSAGE HANDLER
# ════════════════════════════════════════════════════════════════

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle incoming voice messages (.ogg Opus audio).

    Flow:
    1. Download OGG file from Telegram servers
    2. Read as bytes
    3. Pass to brain.process_voice (Gemini multimodal)
    4. Send text response
    5. Optionally convert response to audio and send back
    """
    user = update.effective_user
    message = update.message

    if not _is_allowed(user.id):
        return

    # Ensure user is registered
    memory.get_or_create_user(
        user.id, user.username, user.first_name, user.last_name
    )

    logger.info(f"Voice note from {user.id} (@{user.username})")

    # Show voice recording indicator
    try:
        await context.bot.send_chat_action(
            chat_id=message.chat_id,
            action=constants.ChatAction.RECORD_VOICE,
        )
    except Exception:
        pass

    # Acknowledge immediately (voice processing takes a moment)
    await message.reply_text("🎤 _Processing your voice message..._", parse_mode="Markdown")

    ogg_path: str | None = None

    try:
        # Download the voice file
        voice_file = await message.voice.get_file()
        ogg_path = str(TEMP_DIR / f"voice_{user.id}_{message.message_id}.ogg")
        await voice_file.download_to_drive(custom_path=ogg_path)

        # Read as bytes
        audio_bytes = await convert_ogg_to_bytes(ogg_path)

        # Show typing while AI processes
        await _send_typing(context, message.chat_id)

        # Process voice with Gemini multimodal
        response = await brain.process_voice(
            user.id,
            audio_bytes,
            mime_type="audio/ogg",
        )

        # Send text response
        await _send_response(
            update, context,
            response.text,
            send_audio=AUDIO_RESPONSE_ENABLED,  # Send audio reply for voice messages
        )

    except Exception as e:
        logger.error(f"Voice handler error: {e}", exc_info=True)
        await message.reply_text(
            "🎤 I couldn't process your voice message.\n\n"
            "Possible reasons:\n"
            "• The audio was too short or silent\n"
            "• Network issue downloading the file\n"
            "• Gemini API temporarily unavailable\n\n"
            "Please try again or send a text message instead."
        )
    finally:
        # Clean up the downloaded OGG file
        if ogg_path:
            await cleanup_temp_file(ogg_path)


# ════════════════════════════════════════════════════════════════
# UNKNOWN MESSAGE HANDLER
# ════════════════════════════════════════════════════════════════

async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unsupported message types (stickers, documents, etc.)."""
    msg = update.message
    if not msg:
        return

    # Check what type was sent
    if msg.sticker:
        await msg.reply_text("😄 Nice sticker! You can send me text or voice messages.")
    elif msg.document:
        await msg.reply_text(
            "📎 I see you sent a file!\n\n"
            "I can't process uploaded files directly yet, but you can:\n"
            "• Tell me what the file contains and I'll help you\n"
            "• Ask me to create files with `/files`"
        )
    elif msg.photo:
        await msg.reply_text(
            "📸 I see an image! Image analysis is coming soon.\n"
            "For now, please describe what you need help with."
        )
    else:
        await msg.reply_text(
            "I can handle **text messages** and **voice notes** right now.\n"
            "Type `/help` to see what I can do!",
            parse_mode="Markdown"
        )


# ════════════════════════════════════════════════════════════════
# ERROR HANDLER
# ════════════════════════════════════════════════════════════════

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler for telegram-python-bot."""
    logger.error(f"Telegram error: {context.error}", exc_info=context.error)

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ An unexpected error occurred. Please try again.\n"
                "If the problem persists, use /clear to reset your session."
            )
        except Exception:
            pass


# ════════════════════════════════════════════════════════════════
# HEALTH CHECK HTTP SERVER (for Render.com / HuggingFace keep-alive)
# ════════════════════════════════════════════════════════════════

async def health_check(request: web.Request) -> web.Response:
    """HTTP health check endpoint."""
    stats = memory.get_stats()
    return web.json_response({
        "status": "healthy",
        "service": "AUREX Telegram Bot",
        "version": "1.0.0",
        "users": stats["total_users"],
        "messages": stats["total_messages"],
        "uptime": "running",
    })


async def start_health_server() -> None:
    """Start the health-check HTTP server."""
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"Health check server running on port {PORT}")


# ════════════════════════════════════════════════════════════════
# PERIODIC CLEANUP TASK
# ════════════════════════════════════════════════════════════════

async def periodic_cleanup() -> None:
    """Run every 10 minutes: clean up old temp audio files."""
    while True:
        await asyncio.sleep(600)  # 10 minutes
        try:
            deleted = await cleanup_old_temp_files(max_age_minutes=10)
            if deleted > 0:
                logger.debug(f"Periodic cleanup: deleted {deleted} temp files")
        except Exception as e:
            logger.warning(f"Periodic cleanup failed: {e}")


# ════════════════════════════════════════════════════════════════
# APPLICATION SETUP & MAIN
# ════════════════════════════════════════════════════════════════

async def post_init(application: Application) -> None:
    """Called after bot is initialized — set up commands menu."""
    commands = [
        ("start",  "Welcome & quick intro"),
        ("help",   "Show all commands & tips"),
        ("memory", "View your profile & saved facts"),
        ("clear",  "Clear conversation history"),
        ("forget", "Delete a specific saved fact"),
        ("files",  "List files in your workspace"),
        ("stats",  "Bot usage statistics"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands menu registered.")


def create_application() -> Application:
    """Build and configure the Telegram application."""
    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # ── Slash command handlers ─────────────────────────────────
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("help",   cmd_help))
    app.add_handler(CommandHandler("memory", cmd_memory))
    app.add_handler(CommandHandler("clear",  cmd_clear))
    app.add_handler(CommandHandler("forget", cmd_forget, has_args=False))
    app.add_handler(CommandHandler("files",  cmd_files))
    app.add_handler(CommandHandler("stats",  cmd_stats))

    # ── Message handlers ───────────────────────────────────────
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(
        ~filters.TEXT & ~filters.VOICE & ~filters.COMMAND,
        handle_unknown
    ))

    # ── Global error handler ───────────────────────────────────
    app.add_error_handler(error_handler)

    return app


async def main() -> None:
    """
    Main entry point.
    Uses the PTB low-level API (initialize/start/updater.start_polling)
    instead of run_polling() to avoid the 'event loop already running'
    conflict on Windows with Python 3.11+.
    """
    global memory, brain, sub_agent, bot_app

    # ── Validate config ────────────────────────────────────────
    if not validate_config():
        sys.exit(1)

    print(AUREX_BANNER)
    logger.info("Starting AUREX...")

    # ── Initialize components ──────────────────────────────────
    memory = MemoryManager()
    sub_agent = SubAgent()

    brain = AUREXBrain(
        memory=memory,
        sub_agent=sub_agent,
        result_callback=background_result_callback,
    )

    # Start background SubAgent worker
    await sub_agent.start()

    # ── Build Telegram app ─────────────────────────────────────
    bot_app = create_application()

    # ── Start health check + cleanup as background tasks ───────
    asyncio.create_task(start_health_server())
    asyncio.create_task(periodic_cleanup())

    # ── Log startup info ───────────────────────────────────────
    me = await bot_app.bot.get_me()
    logger.info(f"Bot: @{me.username} ({me.first_name})")
    logger.info(f"Mode: {'Webhook' if WEBHOOK_URL else 'Long Polling'}")
    logger.info(f"Audio responses: {'ON' if AUDIO_RESPONSE_ENABLED else 'OFF'}")
    logger.info("AUREX is running! Send /start on Telegram.")

    # ── LOW-LEVEL start (avoids run_polling event loop conflict) ─
    # run_polling() creates its own loop internally — crashes when
    # asyncio.run() already owns the loop (Python 3.11 / Windows).
    # Solution: manually initialize, start polling, and await forever.
    await bot_app.initialize()
    await bot_app.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )
    await bot_app.start()

    # Keep running until Ctrl+C
    try:
        await asyncio.Event().wait()   # blocks here forever
    finally:
        logger.info("Shutting down AUREX...")
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()
        await sub_agent.stop()


# ════════════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("AUREX stopped by user (Ctrl+C)")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
