#!/usr/bin/env python3
"""Extract real Claude Code sessions from compressed files and migrate to SQLite."""

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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RealSessionExtractor:
    """Extract and migrate real Claude Code sessions."""

    def __init__(self):
        self.db = ChatHistoryDB()
        self.session_storage_path = Path(r"P:\.claude\session_storage")
        self.processed_sessions = 0
        self.processed_messages = 0
        self.errors = 0

    def extract_and_migrate_sessions(self, limit=None):
        """Extract and migrate real Claude Code sessions.

        Args:
            limit: Maximum number of sessions to process (None for all)
        """
        logger.info("Starting real Claude Code session extraction and migration")

        # Check both JSON and msgpack directories
        json_dir = self.session_storage_path / "json"
        msgpack_dir = self.session_storage_path / "msgpack"

        session_files = []

        # Collect JSON session files
        if json_dir.exists():
            json_files = list(json_dir.glob("*.json.gz"))
            session_files.extend([("json", f) for f in json_files])
            logger.info(f"Found {len(json_files)} JSON session files")

        # Collect msgpack session files
        if msgpack_dir.exists():
            msgpack_files = list(msgpack_dir.glob("*.msgpack.gz"))
            session_files.extend([("msgpack", f) for f in msgpack_files])
            logger.info(f"Found {len(msgpack_files)} msgpack session files")

        if not session_files:
            logger.warning("No session files found")
            return

        # Apply limit if specified
        if limit:
            session_files = session_files[:limit]

        logger.info(f"Processing {len(session_files)} session files")

        for file_type, session_file in session_files:
            try:
                self._process_session_file(session_file, file_type)
                self.processed_sessions += 1

                if self.processed_sessions % 10 == 0:
                    logger.info(f"Processed {self.processed_sessions} sessions, {self.processed_messages} messages")

            except Exception as e:
                logger.error(f"Error processing {session_file}: {e}")
                self.errors += 1

        logger.info(f"Migration complete: {self.processed_sessions} sessions, {self.processed_messages} messages, {self.errors} errors")

    def _process_session_file(self, session_file: Path, file_type: str):
        """Process a single session file."""
        try:
            # Read compressed file
            with gzip.open(session_file, 'rt', encoding='utf-8') if file_type == "json" else gzip.open(session_file, 'rb') as f:
                if file_type == "json":
                    data = json.load(f)
                else:
                    # For msgpack, we'd need msgpack library, skip for now
                    logger.warning(f"Skipping msgpack file {session_file} - msgpack support not implemented")
                    return

            # Validate and extract session data
            if not self._is_valid_session(data):
                logger.warning(f"Invalid session data in {session_file}")
                return

            # Extract session ID from filename if not present
            session_id = data.get('session_id', session_file.stem.split('.')[0])

            # Check if this looks like a real conversation session
            if not self._is_real_conversation_session(data):
                logger.debug(f"Skipping {session_id} - not a conversation session")
                return

            # Convert to expected format
            converted_session = self._convert_session_format(data, session_id, session_file.name)

            # Store in database
            stored_id = self.db.store_session(converted_session)
            message_count = len(converted_session.get('messages', []))
            self.processed_messages += message_count

            logger.debug(f"Migrated session {stored_id} with {message_count} messages")

        except Exception as e:
            logger.error(f"Failed to process {session_file}: {e}")
            raise

    def _is_valid_session(self, data: dict) -> bool:
        """Validate session data structure."""
        if not isinstance(data, dict):
            return False

        # Look for conversation indicators
        has_conversation_indicators = (
            'messages' in data or
            'conversation' in data or
            'chat_history' in data or
            any(key in data for key in ['user', 'assistant', 'tool_call', 'content'])
        )

        return has_conversation_indicators

    def _is_real_conversation_session(self, data: dict) -> bool:
        """Check if this is a real conversation session with messages."""
        # Look for actual message content
        messages = data.get('messages', [])

        if not messages:
            return False

        # Check if messages have actual content
        for message in messages:
            if isinstance(message, dict):
                content = message.get('content', '')
                if content and len(str(content).strip()) > 10:
                    return True

        return False

    def _convert_session_format(self, data: dict, session_id: str, source_file: str) -> dict:
        """Convert session data to expected format."""
        # Extract messages in various possible formats
        messages = []

        # Try different message formats
        if 'messages' in data and isinstance(data['messages'], list):
            for msg in data['messages']:
                if isinstance(msg, dict) and self._has_message_content(msg):
                    converted_msg = self._convert_message_format(msg, source_file)
                    if converted_msg:
                        messages.append(converted_msg)

        # If no messages found in standard format, try to extract from conversation
        if not messages and 'conversation' in data:
            conversation = data['conversation']
            if isinstance(conversation, list):
                for item in conversation:
                    if isinstance(item, dict) and self._has_message_content(item):
                        converted_msg = self._convert_message_format(item, source_file)
                        if converted_msg:
                            messages.append(converted_msg)

        # Create session metadata
        session_metadata = {
            'session_id': session_id,
            'model': self._extract_model_info(data),
            'start_time': data.get('start_time', datetime.now().isoformat()),
            'end_time': data.get('end_time', datetime.now().isoformat()),
            'working_directory': data.get('working_directory', ''),
            'status': data.get('status', 'completed'),
            'type': data.get('type', 'claude_code_session'),
            'metadata': {
                'source_format': 'claude_code_compressed',
                'source_file': source_file,
                'migration_date': datetime.now().isoformat(),
                'original_session_type': data.get('type', 'unknown')
            },
            'messages': messages
        }

        return session_metadata

    def _has_message_content(self, message: dict) -> bool:
        """Check if message has actual content."""
        content = message.get('content', '')
        if not content:
            return False

        # Check if content is substantial
        if isinstance(content, str):
            return len(content.strip()) > 5

        return bool(content)

    def _convert_message_format(self, message: dict, source_file: str) -> dict:
        """Convert individual message to expected format."""
        # Extract content and role
        content = message.get('content', '')
        role = message.get('role', message.get('type', 'unknown'))

        # Handle different content types
        if isinstance(content, list):
            # Content might be a list of content blocks
            content_text = ""
            for block in content:
                if isinstance(block, dict) and 'text' in block:
                    content_text += block['text']
                elif isinstance(block, str):
                    content_text += block
            content = content_text
        elif not isinstance(content, str):
            content = str(content)

        # Skip if no meaningful content
        if not content.strip():
            return None

        # Create timestamp
        timestamp = message.get('timestamp', datetime.now().isoformat())

        converted_message = {
            'role': role,
            'content': content.strip(),
            'timestamp': timestamp,
            'token_count': len(content.split()) + 5,  # Rough estimate
            'metadata': {
                'source_file': source_file,
                'original_role': role,
                'message_type': 'extracted_from_claude_code',
                'has_tool_calls': 'tool_calls' in message or 'tool_use' in message
            }
        }

        return converted_message

    def _extract_model_info(self, data: dict) -> str:
        """Extract model information from session data."""
        # Try different possible model fields
        for field in ['model', 'model_name', 'llm_model', 'claude_model']:
            if field in data and data[field]:
                return data[field]

        # Check in metadata
        metadata = data.get('metadata', {})
        if isinstance(metadata, dict):
            for field in ['model', 'model_name', 'llm_model', 'claude_model']:
                if field in metadata and metadata[field]:
                    return metadata[field]

        # Look in messages for model info
        messages = data.get('messages', [])
        for message in messages:
            if isinstance(message, dict):
                msg_metadata = message.get('metadata', {})
                if isinstance(msg_metadata, dict) and 'model' in msg_metadata:
                    return msg_metadata['model']

        return "claude-unknown"

    def get_migration_stats(self) -> dict:
        """Get migration statistics."""
        return {
            'processed_sessions': self.processed_sessions,
            'processed_messages': self.processed_messages,
            'errors': self.errors,
            'avg_messages_per_session': self.processed_messages / max(self.processed_sessions, 1)
        }


def main():
    """Main extraction and migration function."""
    extractor = RealSessionExtractor()

    print("🔍 Extracting Real Claude Code Sessions")
    print("=" * 50)

    # Process first 50 session files to start with
    extractor.extract_and_migrate_sessions(limit=50)

    # Show results
    stats = extractor.get_migration_stats()
    print("\n📊 Migration Results:")
    print(f"   Sessions Processed: {stats['processed_sessions']}")
    print(f"   Messages Migrated: {stats['processed_messages']}")
    print(f"   Errors: {stats['errors']}")
    print(f"   Avg Messages/Session: {stats['avg_messages_per_session']:.1f}")

    # Show database stats
    print("\n📈 Database Statistics:")
    db = ChatHistoryDB()
    db_stats = db.get_stats()
    print(f"   Total Sessions: {db_stats['sessions']}")
    print(f"   Total Messages: {db_stats['messages']}")
    print(f"   Database Size: {db_stats['db_size_mb']:.2f} MB")


if __name__ == "__main__":
    main()
