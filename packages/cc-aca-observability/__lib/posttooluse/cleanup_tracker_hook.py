#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook

"""
PostToolUse: Cleanup Tracker Hook

Accumulates tool history to session-scoped file for later analysis
by Stop_cleanup_verifier.py.

This tracks all tool executions during a session for work type detection
and cleanup verification at session end.
"""


class CleanupTrackerHook(PostToolUseHook):
    """
    Track tool usage for cleanup verification.

    Accumulates tool execution data to:
    P:/.claude/state/cleanup_history_{session_id}.json

    Data is read by Stop_cleanup_verifier.py at session end.
    """

    env_var = "CLEANUP_VERIFIER_ENABLED"
    default_enabled = True
    tool_matcher = None  # Track all tools

    def process(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_response: dict[str, Any],
    ) -> dict[str, Any]:
        """Track tool execution to history file."""
        try:
            # Extract session_id from environment or tool input
            session_id = (
                tool_input.get("session_id")
                or tool_input.get("sessionId")
                or tool_input.get("conversation_id")
                or tool_input.get("conversationId")
                or os.environ.get("CLAUDE_SESSION_ID", "")
            ).strip()

            if not session_id:
                # Cannot scope file without session_id
                return {"passed": True, "skipped": True, "reason": "no_session_id"}

            # Sanitize session_id for filename
            safe_session = re.sub(r"[^a-zA-Z0-9_.-]+", "_", session_id)

            # Determine history file path
            state_dir = Path(
                os.environ.get("CLEANUP_TRACKER_DIR", "P:/.claude/state")
            )
            state_dir.mkdir(parents=True, exist_ok=True)

            history_file = state_dir / f"cleanup_history_{safe_session}.json"

            # Load existing history or create new
            if history_file.exists():
                try:
                    history = json.loads(history_file.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    # Corrupted file, start fresh
                    history = {"tools": []}
            else:
                history = {"tools": []}

            # Append current tool execution
            tool_entry = {
                "name": tool_name,
                "input": tool_input,
                "timestamp": datetime.now(UTC).isoformat(),
            }
            history["tools"].append(tool_entry)

            # Write back to file
            history_file.write_text(json.dumps(history, indent=2), encoding="utf-8")

            # Cleanup stale files (> 24 hours)
            self._cleanup_stale_files(state_dir, safe_session)

        except Exception:
            # Silent fail - tracking is best-effort (no stderr per hook policy)
            pass

        return {"passed": True}

    def _cleanup_stale_files(self, state_dir: Path, current_session: str) -> None:
        """Remove cleanup history files older than 24 hours.

        Args:
            state_dir: Directory containing cleanup history files
            current_session: Current session ID (to preserve current file)
        """
        try:
            cutoff_time = datetime.now(UTC).timestamp() - 86400  # 24 hours

            for file_path in state_dir.glob("cleanup_history_*.json"):
                # Skip current session file
                if file_path.name == f"cleanup_history_{current_session}.json":
                    continue

                # Check file age
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink(missing_ok=True)
        except Exception:
            # Cleanup is best-effort
            pass
