#!/usr/bin/env python3
"""Migrate Claude Code sessions to SQLite database.
Reads compressed session files and stores them in the dedicated chat history database.
"""

import argparse
import gzip
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add CSF NIP paths
csf_nip_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(csf_nip_root))
sys.path.insert(0, str(csf_nip_root / "src"))
sys.path.insert(0, str(csf_nip_root / "src" / "lib"))

from chat_history_db import ChatHistoryDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SessionMigrator:
    """Migrates Claude Code session files to SQLite database."""

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize the migrator.

        Args:
            db_path: Path to SQLite database. Uses default if not provided.
        """
        self.db = ChatHistoryDB(db_path)

    def migrate_from_directory(self, session_dir: Path,
                              pattern: str = "*.json.gz",
                              limit: int | None = None) -> dict[str, int]:
        """Migrate all session files from a directory.

        Args:
            session_dir: Directory containing session files.
            pattern: File pattern to match.
            limit: Maximum number of sessions to migrate.

        Returns:
            Dictionary with migration statistics.
        """
        session_files = list(session_dir.glob(pattern))
        if limit:
            session_files = session_files[:limit]

        stats = {
            "files_processed": 0,
            "sessions_migrated": 0,
            "messages_migrated": 0,
            "errors": 0
        }

        logger.info(f"Starting migration from {session_dir}")
        logger.info(f"Found {len(session_files)} session files to process")

        for session_file in session_files:
            try:
                session_data = self._read_session_file(session_file)
                if session_data:
                    self._migrate_session(session_data)
                    stats["sessions_migrated"] += 1
                    stats["messages_migrated"] += len(session_data.get("messages", []))

                stats["files_processed"] += 1

                if stats["files_processed"] % 10 == 0:
                    logger.info(f"Processed {stats['files_processed']} files, "
                               f"{stats['sessions_migrated']} sessions migrated")

            except Exception as e:
                logger.error(f"Error processing {session_file}: {e}")
                stats["errors"] += 1

        logger.info(f"Migration complete: {stats['sessions_migrated']} sessions, "
                   f"{stats['messages_migrated']} messages migrated")
        return stats

    def migrate_from_claude_code(self, claude_dir: Path | None = None) -> dict[str, int]:
        """Migrate from standard Claude Code session storage.

        Args:
            claude_dir: Claude Code directory. Defaults to ~/.claude.

        Returns:
            Dictionary with migration statistics.
        """
        if claude_dir is None:
            claude_dir = Path.home() / ".claude"

        session_dir = claude_dir / "session_storage"
        if not session_dir.exists():
            raise FileNotFoundError(f"Session directory not found: {session_dir}")

        # Try both JSON and msgpack formats
        json_dir = session_dir / "json"
        msgpack_dir = session_dir / "msgpack"

        total_stats = {
            "files_processed": 0,
            "sessions_migrated": 0,
            "messages_migrated": 0,
            "errors": 0
        }

        # Migrate JSON files
        if json_dir.exists():
            logger.info("Migrating JSON session files...")
            json_stats = self.migrate_from_directory(json_dir, "*.json.gz")
            for key, value in json_stats.items():
                total_stats[key] += value

        # Migrate msgpack files
        if msgpack_dir.exists():
            logger.info("Migrating msgpack session files...")
            msgpack_stats = self.migrate_from_directory(msgpack_dir, "*.msgpack.gz")
            for key, value in msgpack_stats.items():
                total_stats[key] += value

        return total_stats

    def _read_session_file(self, session_file: Path) -> dict | None:
        """Read and parse a session file.

        Args:
            session_file: Path to the session file.

        Returns:
            Parsed session data or None if invalid.
        """
        try:
            with gzip.open(session_file, 'rt', encoding='utf-8') as f:
                data = json.load(f)

            # Extract session ID from filename if not in data
            if 'session_id' not in data:
                session_id = session_file.stem.split('.')[0]
                data['session_id'] = session_id

            # Validate session structure
            if not self._validate_session(data):
                logger.warning(f"Invalid session structure in {session_file}")
                return None

            return data

        except Exception as e:
            logger.error(f"Failed to read {session_file}: {e}")
            return None

    def _validate_session(self, session_data: dict) -> bool:
        """Validate session data structure.

        Args:
            session_data: Session data to validate.

        Returns:
            True if valid, False otherwise.
        """
        if not isinstance(session_data, dict):
            return False

        # Check for messages
        messages = session_data.get('messages', [])
        if not isinstance(messages, list):
            return False

        # Basic message validation
        for message in messages:
            if not isinstance(message, dict):
                return False
            if 'role' not in message or 'content' not in message:
                return False

        return True

    def _migrate_session(self, session_data: dict) -> str:
        """Migrate a single session to the database.

        Args:
            session_data: Session data to migrate.

        Returns:
            Session ID of the migrated session.
        """
        # Transform session data to expected format
        transformed_session = {
            "session_id": session_data.get("session_id"),
            "model": self._extract_model(session_data),
            "metadata": {
                "original_format": "claude_code",
                "migration_date": datetime.now().isoformat(),
                "source_file": session_data.get("source_file", "unknown")
            },
            "messages": self._transform_messages(session_data.get("messages", []))
        }

        return self.db.store_session(transformed_session)

    def _extract_model(self, session_data: dict) -> str:
        """Extract model information from session data.

        Args:
            session_data: Session data.

        Returns:
            Model name string.
        """
        # Try different common fields for model information
        for field in ["model", "model_name", "llm_model", "claude_model"]:
            if field in session_data:
                return session_data[field]

        # Check messages for model usage
        messages = session_data.get("messages", [])
        for message in messages:
            if message.get("role") == "assistant":
                metadata = message.get("metadata", {})
                if "model" in metadata:
                    return metadata["model"]

        return "claude-unknown"

    def _transform_messages(self, messages: list[dict]) -> list[dict]:
        """Transform messages to expected format.

        Args:
            messages: Original messages list.

        Returns:
            Transformed messages list.
        """
        transformed = []
        for message in messages:
            transformed_message = {
                "role": message.get("role", "unknown"),
                "content": message.get("content", ""),
                "timestamp": message.get("timestamp", datetime.now().isoformat()),
                "token_count": message.get("token_count", 0),
                "tool_calls": message.get("tool_calls", []),
                "metadata": {
                    "original_format": "claude_code",
                    **message.get("metadata", {})
                }
            }
            transformed.append(transformed_message)

        return transformed


def main():
    """CLI interface for session migration."""
    parser = argparse.ArgumentParser(
        description="Migrate Claude Code sessions to SQLite database"
    )
    parser.add_argument(
        "--source", "-s",
        help="Source directory containing session files"
    )
    parser.add_argument(
        "--claude-code", "-c",
        action="store_true",
        help="Migrate from standard Claude Code session directory"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        help="Limit number of sessions to migrate"
    )
    parser.add_argument(
        "--db-path", "-d",
        help="Custom database path"
    )
    parser.add_argument(
        "--pattern", "-p",
        default="*.json.gz",
        help="File pattern to match (default: *.json.gz)"
    )
    parser.add_argument(
        "--stats", "--stat",
        action="store_true",
        help="Show database statistics after migration"
    )

    args = parser.parse_args()

    # Initialize migrator
    db_path = Path(args.db_path) if args.db_path else None
    migrator = SessionMigrator(db_path)

    if not args.source and not args.claude_code:
        parser.error("Either --source or --claude-code must be specified")

    try:
        # Perform migration
        if args.claude_code:
            stats = migrator.migrate_from_claude_code()
        else:
            source_path = Path(args.source)
            if not source_path.exists():
                raise FileNotFoundError(f"Source directory not found: {source_path}")
            stats = migrator.migrate_from_directory(source_path, args.pattern, args.limit)

        # Show results
        print("\n📊 Migration Results:")
        print(f"Files processed: {stats['files_processed']}")
        print(f"Sessions migrated: {stats['sessions_migrated']}")
        print(f"Messages migrated: {stats['messages_migrated']}")
        print(f"Errors: {stats['errors']}")

        if args.stats:
            print("\n📈 Database Statistics:")
            db_stats = migrator.db.get_stats()
            for key, value in db_stats.items():
                print(f"{key}: {value}")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
