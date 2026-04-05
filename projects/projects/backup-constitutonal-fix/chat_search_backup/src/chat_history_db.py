#!/usr/bin/env python3
"""Chat History SQLite Database Manager
Dedicated SQLite database for storing Claude Code chat sessions with proper schema.
"""

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add CSF NIP paths for integration
csf_nip_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(csf_nip_root))
sys.path.insert(0, str(csf_nip_root / "src"))
sys.path.insert(0, str(csf_nip_root / "src" / "lib"))


class ChatHistoryDB:
    """Dedicated SQLite database for chat history storage and retrieval."""

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize the chat history database.

        Args:
            db_path: Path to SQLite database file. Defaults to CSF NIP data directory.
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent.parent / ".data" / "chat_history.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()

    def _init_database(self) -> None:
        """Initialize database schema for chat history."""
        with sqlite3.connect(self.db_path) as conn:
            # Chat sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id TEXT PRIMARY KEY,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    message_count INTEGER DEFAULT 0,
                    model_used TEXT,
                    total_tokens INTEGER DEFAULT 0,
                    metadata TEXT DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Chat messages table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    message_index INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    token_count INTEGER DEFAULT 0,
                    tool_calls TEXT DEFAULT '[]',
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id),
                    UNIQUE(session_id, message_index)
                )
            """)

            # Search index for fast content retrieval
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS message_search USING fts5(
                    session_id,
                    role,
                    content,
                    timestamp
                )
            """)

            # Indexes for performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session_time
                ON chat_messages(session_id, timestamp)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_start_time
                ON chat_sessions(start_time)
            """)

            conn.commit()

    def store_session(self, session_data: dict[str, Any]) -> str:
        """Store a complete chat session in the database.

        Args:
            session_data: Dictionary containing session information and messages.

        Returns:
            Session ID of the stored session.
        """
        session_id = session_data.get("session_id", self._generate_session_id())

        with sqlite3.connect(self.db_path) as conn:
            # Extract session metadata
            messages = session_data.get("messages", [])
            start_time = self._parse_timestamp(messages[0].get("timestamp") if messages else None)
            end_time = self._parse_timestamp(messages[-1].get("timestamp") if messages else None)

            # Insert session
            conn.execute("""
                INSERT OR REPLACE INTO chat_sessions
                (session_id, start_time, end_time, message_count, model_used, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                start_time,
                end_time,
                len(messages),
                session_data.get("model", "unknown"),
                json.dumps(session_data.get("metadata", {}))
            ))

            # Insert messages
            for idx, message in enumerate(messages):
                self._store_message(conn, session_id, idx, message)

            # Update search index - populate for all messages in this session
            conn.execute("""
                INSERT OR REPLACE INTO message_search (session_id, role, content, timestamp)
                SELECT session_id, role, content, timestamp FROM chat_messages
                WHERE session_id = ?
            """, (session_id,))

            conn.commit()

        return session_id

    def _store_message(self, conn: sqlite3.Connection, session_id: str,
                      message_index: int, message: dict[str, Any]) -> None:
        """Store a single message in the database."""
        conn.execute("""
            INSERT OR REPLACE INTO chat_messages
            (session_id, message_index, role, content, timestamp,
             token_count, tool_calls, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            message_index,
            message.get("role", "unknown"),
            message.get("content", ""),
            self._parse_timestamp(message.get("timestamp")),
            message.get("token_count", 0),
            json.dumps(message.get("tool_calls", [])),
            json.dumps(message.get("metadata", {}))
        ))

    def search_messages(self, query: str, limit: int = 50,
                       session_filter: str | None = None) -> list[dict[str, Any]]:
        """Search for messages matching the query.

        Args:
            query: Search query text.
            limit: Maximum number of results to return.
            session_filter: Optional session ID to filter by.

        Returns:
            List of matching message dictionaries.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Use LIKE queries for robust search (can be upgraded to FTS later)
            sql = """
                SELECT m.*, s.start_time as session_start_time
                FROM chat_messages m
                JOIN chat_sessions s ON m.session_id = s.session_id
                WHERE m.content LIKE ?
            """
            params = [f"%{query}%"]

            if session_filter:
                sql += " AND m.session_id = ?"
                params.append(session_filter)

            sql += " ORDER BY m.timestamp DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Retrieve a complete chat session by ID.

        Args:
            session_id: Session ID to retrieve.

        Returns:
            Session dictionary with messages, or None if not found.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get session info
            cursor = conn.execute("""
                SELECT * FROM chat_sessions WHERE session_id = ?
            """, (session_id,))
            session_row = cursor.fetchone()

            if not session_row:
                return None

            # Get messages
            cursor = conn.execute("""
                SELECT * FROM chat_messages
                WHERE session_id = ?
                ORDER BY message_index
            """, (session_id,))
            message_rows = cursor.fetchall()

            return {
                "session": dict(session_row),
                "messages": [dict(row) for row in message_rows]
            }

    def get_recent_sessions(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get the most recent chat sessions.

        Args:
            limit: Maximum number of sessions to return.

        Returns:
            List of session dictionaries.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM chat_sessions
                ORDER BY start_time DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> dict[str, Any]:
        """Get database statistics.

        Returns:
            Dictionary with database statistics.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM chat_sessions")
            session_count = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM chat_messages")
            message_count = cursor.fetchone()[0]

            cursor = conn.execute("""
                SELECT SUM(total_tokens) FROM chat_sessions WHERE total_tokens > 0
            """)
            total_tokens = cursor.fetchone()[0] or 0

            return {
                "sessions": session_count,
                "messages": message_count,
                "total_tokens": total_tokens,
                "db_path": str(self.db_path),
                "db_size_mb": self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
            }

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        import uuid
        return str(uuid.uuid4())[:8]

    def _parse_timestamp(self, timestamp: Any) -> str:
        """Parse and normalize timestamp."""
        if isinstance(timestamp, str):
            return timestamp
        elif isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp).isoformat()
        else:
            return datetime.now().isoformat()


def main():
    """CLI interface for the chat history database."""
    import argparse

    parser = argparse.ArgumentParser(description="Chat History SQLite Database Manager")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument("--sessions", action="store_true", help="List recent sessions")
    parser.add_argument("--search", help="Search messages")
    parser.add_argument("--session", help="Get specific session")
    parser.add_argument("--migrate", help="Migrate from Claude session files")
    parser.add_argument("--limit", type=int, default=20, help="Result limit")

    args = parser.parse_args()

    db = ChatHistoryDB()

    if args.stats:
        stats = db.get_stats()
        print("📊 Chat History Database Statistics")
        print(f"Sessions: {stats['sessions']:,}")
        print(f"Messages: {stats['messages']:,}")
        print(f"Total Tokens: {stats['total_tokens']:,}")
        print(f"Database Size: {stats['db_size_mb']:.2f} MB")
        print(f"Path: {stats['db_path']}")

    elif args.sessions:
        sessions = db.get_recent_sessions(args.limit)
        print(f"📝 Recent {len(sessions)} Sessions:")
        for session in sessions:
            print(f"  {session['session_id']}: {session['start_time']} "
                  f"({session['message_count']} messages)")

    elif args.search:
        results = db.search_messages(args.search, args.limit)
        print(f"🔍 Search Results for '{args.search}' ({len(results)} found):")
        for result in results:
            print(f"  {result['timestamp']} [{result['role']}]: "
                  f"{result['content'][:100]}...")

    elif args.session:
        session = db.get_session(args.session)
        if session:
            print(f"💬 Session {args.session}:")
            print(f"  Start: {session['session']['start_time']}")
            print(f"  Messages: {len(session['messages'])}")
            for msg in session['messages'][:5]:  # Show first 5 messages
                print(f"  {msg['timestamp']} [{msg['role']}]: {msg['content'][:80]}...")
        else:
            print(f"❌ Session {args.session} not found")

    elif args.migrate:
        print(f"🔄 Migration from {args.migrate} not implemented yet")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
