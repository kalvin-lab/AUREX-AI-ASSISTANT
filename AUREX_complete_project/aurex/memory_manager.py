"""
╔══════════════════════════════════════════════════════════════╗
║  AUREX — memory_manager.py                                  ║
║  Persistent memory using SQLite (100% local, no cloud cost) ║
║                                                              ║
║  Stores:                                                     ║
║    • User profiles (name, username, preferences)            ║
║    • Conversation history (per user, rolling window)        ║
║    • User facts (key-value facts extracted from chat)       ║
║    • Session metadata (message counts, last active)         ║
╚══════════════════════════════════════════════════════════════╝
"""

import json
import logging
import sqlite3
from datetime import datetime
from typing import Any

from config import MEMORY_DB_PATH, CONVERSATION_HISTORY_LIMIT, MAX_FACTS_PER_USER

logger = logging.getLogger("AUREX.memory")


# ════════════════════════════════════════════════════════════════
# DATABASE SCHEMA
# ════════════════════════════════════════════════════════════════

SCHEMA_SQL = """
-- User profiles table
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    username    TEXT,
    first_name  TEXT,
    last_name   TEXT,
    language    TEXT DEFAULT 'en',
    preferences TEXT DEFAULT '{}',
    msg_count   INTEGER DEFAULT 0,
    created_at  TEXT DEFAULT (datetime('now')),
    last_seen   TEXT DEFAULT (datetime('now'))
);

-- Full conversation history
CREATE TABLE IF NOT EXISTS conversations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    role        TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content     TEXT NOT NULL,
    msg_type    TEXT DEFAULT 'text',  -- text / voice / command
    tokens      INTEGER DEFAULT 0,
    timestamp   TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id, timestamp DESC);

-- Structured user facts (extracted from conversation)
CREATE TABLE IF NOT EXISTS user_facts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    fact_key    TEXT NOT NULL,
    fact_value  TEXT NOT NULL,
    confidence  REAL DEFAULT 1.0,
    source      TEXT DEFAULT 'user',   -- user / inferred
    updated_at  TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, fact_key),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_facts_user ON user_facts(user_id);

-- Background task log (for audit / retry)
CREATE TABLE IF NOT EXISTS task_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER,
    task_type   TEXT,
    task_args   TEXT,
    status      TEXT DEFAULT 'pending',  -- pending / running / done / failed
    result      TEXT,
    started_at  TEXT DEFAULT (datetime('now')),
    finished_at TEXT
);
"""


# ════════════════════════════════════════════════════════════════
# MEMORY MANAGER CLASS
# ════════════════════════════════════════════════════════════════

class MemoryManager:
    """
    Thread-safe SQLite memory manager for AUREX.
    
    All methods are synchronous (use asyncio.to_thread if needed
    from async code — SQLite handles concurrency fine for this scale).
    """

    def __init__(self, db_path: str = MEMORY_DB_PATH):
        self.db_path = db_path
        self._init_db()
        logger.info(f"Memory Manager initialized → {db_path}")

    # ─────────────────────────────────────────────────────────
    # PRIVATE: DATABASE INIT
    # ─────────────────────────────────────────────────────────

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._connect() as conn:
            conn.executescript(SCHEMA_SQL)
        logger.debug("Database schema initialized.")

    def _connect(self) -> sqlite3.Connection:
        """Return a new database connection with row factory."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")   # Better concurrent writes
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    # ─────────────────────────────────────────────────────────
    # USER PROFILE MANAGEMENT
    # ─────────────────────────────────────────────────────────

    def get_or_create_user(
        self,
        user_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Get existing user or create a new profile.
        Updates last_seen and username on every call.
        """
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()

            if row is None:
                # New user
                conn.execute(
                    """INSERT INTO users (user_id, username, first_name, last_name)
                       VALUES (?, ?, ?, ?)""",
                    (user_id, username, first_name, last_name),
                )
                logger.info(f"New user registered: {user_id} (@{username})")
                return {
                    "user_id": user_id,
                    "username": username,
                    "first_name": first_name or "User",
                    "last_name": last_name,
                    "language": "en",
                    "preferences": {},
                    "msg_count": 0,
                    "is_new": True,
                }
            else:
                # Returning user — update last_seen
                conn.execute(
                    """UPDATE users
                       SET last_seen = datetime('now'),
                           username  = COALESCE(?, username)
                       WHERE user_id = ?""",
                    (username, user_id),
                )
                prefs = json.loads(row["preferences"] or "{}")
                return {
                    "user_id": row["user_id"],
                    "username": row["username"] or username,
                    "first_name": row["first_name"] or first_name or "User",
                    "last_name": row["last_name"],
                    "language": row["language"],
                    "preferences": prefs,
                    "msg_count": row["msg_count"],
                    "is_new": False,
                }

    def update_preferences(self, user_id: int, preferences: dict) -> None:
        """Update user preferences dict (merged, not replaced)."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT preferences FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            existing = json.loads(row["preferences"] or "{}") if row else {}
            existing.update(preferences)
            conn.execute(
                "UPDATE users SET preferences = ? WHERE user_id = ?",
                (json.dumps(existing), user_id),
            )

    def increment_message_count(self, user_id: int) -> None:
        """Increment the total message count for a user."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET msg_count = msg_count + 1 WHERE user_id = ?",
                (user_id,),
            )

    # ─────────────────────────────────────────────────────────
    # CONVERSATION HISTORY
    # ─────────────────────────────────────────────────────────

    def add_message(
        self,
        user_id: int,
        role: str,
        content: str,
        msg_type: str = "text",
    ) -> int:
        """
        Add a message to conversation history.
        Returns the new message ID.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO conversations (user_id, role, content, msg_type)
                   VALUES (?, ?, ?, ?)""",
                (user_id, role, content, msg_type),
            )
            # Also update message count
            if role == "user":
                conn.execute(
                    "UPDATE users SET msg_count = msg_count + 1 WHERE user_id = ?",
                    (user_id,),
                )
            return cursor.lastrowid

    def get_history(
        self,
        user_id: int,
        limit: int = CONVERSATION_HISTORY_LIMIT,
    ) -> list[dict[str, str]]:
        """
        Get the most recent N conversation turns for a user.
        Returns list of {role, content} dicts, oldest-first.
        """
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT role, content, msg_type, timestamp
                   FROM conversations
                   WHERE user_id = ?
                   ORDER BY timestamp DESC
                   LIMIT ?""",
                (user_id, limit),
            ).fetchall()

        # Return oldest-first for proper chronological context
        result = [
            {
                "role": row["role"],
                "content": row["content"],
                "msg_type": row["msg_type"],
                "timestamp": row["timestamp"],
            }
            for row in reversed(rows)
        ]
        return result

    def get_history_formatted(
        self,
        user_id: int,
        limit: int = CONVERSATION_HISTORY_LIMIT,
    ) -> str:
        """
        Get conversation history as a formatted string for prompt injection.
        """
        history = self.get_history(user_id, limit)
        if not history:
            return "No previous conversation."

        lines = []
        for msg in history:
            role_label = "👤 USER" if msg["role"] == "user" else "🤖 AUREX"
            # Truncate very long messages in history to save tokens
            content = msg["content"]
            if len(content) > 400:
                content = content[:400] + "... [truncated]"
            lines.append(f"{role_label}: {content}")

        return "\n".join(lines)

    def clear_history(self, user_id: int) -> int:
        """Delete all conversation history for a user. Returns rows deleted."""
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM conversations WHERE user_id = ?", (user_id,)
            )
            return cursor.rowcount

    # ─────────────────────────────────────────────────────────
    # USER FACTS (Persistent knowledge about users)
    # ─────────────────────────────────────────────────────────

    def save_fact(
        self,
        user_id: int,
        key: str,
        value: str,
        source: str = "user",
    ) -> None:
        """
        Save or update a key-value fact about a user.
        Examples: name=John, city=London, language=Spanish
        """
        key = key.strip().lower().replace(" ", "_")
        value = value.strip()

        with self._connect() as conn:
            conn.execute(
                """INSERT INTO user_facts (user_id, fact_key, fact_value, source, updated_at)
                   VALUES (?, ?, ?, ?, datetime('now'))
                   ON CONFLICT(user_id, fact_key) DO UPDATE SET
                       fact_value = excluded.fact_value,
                       source     = excluded.source,
                       updated_at = datetime('now')""",
                (user_id, key, value, source),
            )
        logger.debug(f"Fact saved for user {user_id}: {key} = {value}")

    def get_facts(self, user_id: int) -> dict[str, str]:
        """Get all saved facts for a user as a dict."""
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT fact_key, fact_value
                   FROM user_facts
                   WHERE user_id = ?
                   ORDER BY updated_at DESC
                   LIMIT ?""",
                (user_id, MAX_FACTS_PER_USER),
            ).fetchall()
        return {row["fact_key"]: row["fact_value"] for row in rows}

    def get_facts_formatted(self, user_id: int) -> str:
        """Return facts as a readable string for prompt injection."""
        facts = self.get_facts(user_id)
        if not facts:
            return "No facts saved yet."
        return ", ".join(f"{k}={v}" for k, v in facts.items())

    def delete_fact(self, user_id: int, key: str) -> bool:
        """Delete a specific fact. Returns True if deleted."""
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM user_facts WHERE user_id = ? AND fact_key = ?",
                (user_id, key.lower()),
            )
        return cursor.rowcount > 0

    # ─────────────────────────────────────────────────────────
    # TASK LOG (Background sub-agent audit trail)
    # ─────────────────────────────────────────────────────────

    def log_task_start(
        self, user_id: int, task_type: str, task_args: dict
    ) -> int:
        """Log the start of a background task. Returns task log ID."""
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO task_log (user_id, task_type, task_args, status)
                   VALUES (?, ?, ?, 'running')""",
                (user_id, task_type, json.dumps(task_args)),
            )
        return cursor.lastrowid

    def log_task_done(
        self, task_id: int, result: str, status: str = "done"
    ) -> None:
        """Update task log when a background task finishes."""
        with self._connect() as conn:
            conn.execute(
                """UPDATE task_log
                   SET status = ?, result = ?, finished_at = datetime('now')
                   WHERE id = ?""",
                (status, result[:2000], task_id),
            )

    # ─────────────────────────────────────────────────────────
    # ANALYTICS / ADMIN
    # ─────────────────────────────────────────────────────────

    def get_stats(self) -> dict[str, Any]:
        """Get overall bot statistics."""
        with self._connect() as conn:
            total_users = conn.execute(
                "SELECT COUNT(*) as c FROM users"
            ).fetchone()["c"]
            total_msgs = conn.execute(
                "SELECT COUNT(*) as c FROM conversations"
            ).fetchone()["c"]
            active_today = conn.execute(
                """SELECT COUNT(DISTINCT user_id) as c FROM users
                   WHERE last_seen >= date('now')"""
            ).fetchone()["c"]
            total_tasks = conn.execute(
                "SELECT COUNT(*) as c FROM task_log"
            ).fetchone()["c"]

        return {
            "total_users": total_users,
            "total_messages": total_msgs,
            "active_today": active_today,
            "background_tasks": total_tasks,
            "db_path": self.db_path,
        }

    def get_user_summary(self, user_id: int) -> dict[str, Any]:
        """Get a summary of a specific user's data."""
        with self._connect() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            if not user:
                return {}
            facts = self.get_facts(user_id)
            msg_count_row = conn.execute(
                "SELECT COUNT(*) as c FROM conversations WHERE user_id = ?",
                (user_id,),
            ).fetchone()

        return {
            "user_id": user["user_id"],
            "first_name": user["first_name"],
            "username": user["username"],
            "language": user["language"],
            "total_messages": msg_count_row["c"],
            "facts": facts,
            "created_at": user["created_at"],
            "last_seen": user["last_seen"],
        }
