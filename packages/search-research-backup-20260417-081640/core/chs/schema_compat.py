"""CHS Schema Compatibility Layer.

Bridges the gap between old CHS schema (chat_messages, chat_sessions) and
new CHS v2 schema (messages, sessions, turns).

This allows CHS v2 search functions to work with existing chat_history.db
without requiring migration.
"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class SchemaVersion:
    """CHS schema version constants."""

    LEGACY = "legacy"
    V2 = "v2"


class CHSSchemaCompat:
    """Schema compatibility layer for CHS backends."""

    LEGACY_MESSAGES = "chat_messages"
    LEGACY_SESSIONS = "chat_sessions"
    LEGACY_FTS = "message_search"
    V2_MESSAGES = "messages"
    V2_SESSIONS = "sessions"
    V2_TURNS = "turns"
    V2_MESSAGES_FTS = "messages_fts"
    V2_TURNS_FTS = "turns_fts"

    @staticmethod
    def detect_schema_version(db: sqlite3.Connection | str) -> str:
        """Detect which CHS schema version the database uses.

        Args:
            db: Database connection or path string

        Returns:
            Schema version constant: LEGACY, V2, or "unknown"
        """
        if isinstance(db, str):
            db = sqlite3.connect(str(db))
        cursor = db.cursor()
        cursor.execute(
            "\n            SELECT name FROM sqlite_master\n            WHERE type='table' AND name='messages'\n        "
        )
        if cursor.fetchone():
            return SchemaVersion.V2
        cursor.execute(
            "\n            SELECT name FROM sqlite_master\n            WHERE type='table' AND name='chat_messages'\n        "
        )
        if cursor.fetchone():
            return SchemaVersion.LEGACY
        return "unknown"

    @staticmethod
    def get_messages_table(db: sqlite3.Connection) -> str:
        """Get the actual messages table name for the database.

        Args:
            db: Database connection

        Returns:
            Table name to use for messages queries
        """
        version = CHSSchemaCompat.detect_schema_version(db)
        if version == SchemaVersion.V2:
            return CHSSchemaCompat.V2_MESSAGES
        elif version == SchemaVersion.LEGACY:
            return CHSSchemaCompat.LEGACY_MESSAGES
        else:
            return CHSSchemaCompat.LEGACY_MESSAGES

    @staticmethod
    def get_sessions_table(db: sqlite3.Connection) -> str:
        """Get the actual sessions table name for the database.

        Args:
            db: Database connection

        Returns:
            Table name to use for sessions queries
        """
        version = CHSSchemaCompat.detect_schema_version(db)
        if version == SchemaVersion.V2:
            return CHSSchemaCompat.V2_SESSIONS
        elif version == SchemaVersion.LEGACY:
            return CHSSchemaCompat.LEGACY_SESSIONS
        else:
            return CHSSchemaCompat.LEGACY_SESSIONS

    @staticmethod
    def get_fts_table(db: sqlite3.Connection) -> str:
        """Get the actual FTS5 table name for message search.

        Args:
            db: Database connection

        Returns:
            Table name to use for FTS5 queries
        """
        version = CHSSchemaCompat.detect_schema_version(db)
        if version == SchemaVersion.V2:
            return CHSSchemaCompat.V2_MESSAGES_FTS
        elif version == SchemaVersion.LEGACY:
            cursor = db.cursor()
            cursor.execute(
                "\n                SELECT name FROM sqlite_master\n                WHERE type='table' AND name LIKE '%fts%' AND name LIKE '%message%'\n            "
            )
            result = cursor.fetchone()
            if result:
                return result[0]
            return CHSSchemaCompat.LEGACY_FTS
        else:
            return CHSSchemaCompat.LEGACY_FTS

    @staticmethod
    def validate_required_tables(db: sqlite3.Connection) -> dict[str, bool]:
        """Validate that required tables exist for search operations.

        Args:
            db: Database connection

        Returns:
            Dict with table names as keys and existence status as values
        """
        cursor = db.cursor()
        tables_to_check = [
            "chat_messages",
            "chat_sessions",
            "message_search",
            "messages",
            "sessions",
            "turns",
            "messages_fts",
            "turns_fts",
        ]
        cursor.execute("\n            SELECT name FROM sqlite_master WHERE type='table'\n        ")
        existing_tables = {row[0] for row in cursor.fetchall()}
        return {table: table in existing_tables for table in tables_to_check}

    @staticmethod
    def get_schema_health_message(db: sqlite3.Connection | str) -> str | None:
        """Get a user-friendly health message about schema status.

        Args:
            db: Database connection or path string

        Returns:
            Health message or None if schema is valid
        """
        if isinstance(db, str):
            db = sqlite3.connect(str(db))
        validation = CHSSchemaCompat.validate_required_tables(db)
        if validation.get("chat_messages") and validation.get("chat_sessions"):
            version = CHSSchemaCompat.detect_schema_version(db)
            if version == SchemaVersion.LEGACY:
                return None
        if validation.get("messages") and validation.get("sessions"):
            return None
        missing = [t for t, exists in validation.items() if not exists]
        if missing:
            return f"CHS schema incomplete: missing tables {missing}"
        return "CHS schema: unable to determine schema version"
