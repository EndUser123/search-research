"""TDD Tests for CHS Reindex Tool Role Ingestion.

Tests that tool role messages are ingested from history.jsonl.
"""

from __future__ import annotations


class TestToolRoleIngestion:
    """Tests for tool role message ingestion."""

    def test_tool_role_is_ingested(self) -> None:
        """Tool messages should be ingested, not skipped.

        The schema supports 'tool' role (schema.sql line 44).
        But reindex_from_jsonl.py line 356 only ingests user/assistant/system.
        """
        import json
        import sqlite3
        import tempfile
        from pathlib import Path

        from core.chs.scripts.reindex_from_jsonl import HistoryReindexer

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            jsonl_path = Path(tmp) / "history.jsonl"

            # Write a session with tool message
            tool_entry = {
                "sessionId": "test-session-1",
                "uuid": "tool-msg-001",
                "type": "tool",
                "timestamp": 1700000000000,
                "message": {
                    "role": "tool",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "call_abc",
                            "content": "result: success",
                        }
                    ],
                },
            }
            jsonl_path.write_text(json.dumps(tool_entry) + "\n")

            # Run reindex
            with HistoryReindexer(db_path) as reindexer:
                reindexer.reindex(jsonl_path)

            # Check tool message was ingested
            conn = sqlite3.connect(str(db_path))
            cursor = conn.execute("SELECT role, content FROM messages")
            rows = cursor.fetchall()
            conn.close()

            roles = [r[0] for r in rows]
            contents = [r[1] for r in rows]

            # The tool message should have been ingested
            assert "tool" in roles, (
                f"Tool role not ingested. Found roles: {roles}. Contents: {contents[:2]}..."
            )
