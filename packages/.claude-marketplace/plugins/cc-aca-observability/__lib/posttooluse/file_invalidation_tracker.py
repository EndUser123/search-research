#!/usr/bin/env python3
"""
PostToolUse_file_invalidation_tracker.py - File Invalidation Tracking
=====================================================================

Phase 4 of LLM Behavioral Integrity system.

Tracks file modifications via Edit/Write tools and marks them as
invalidated in the evidence_store file_metadata table.

This invalidation is consulted by the cross_validator stop hook to
detect when source documents have been modified after a claim was made.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook

# Ensure hooks dir is on path for evidence_store import
_hooks_dir = Path(__file__).resolve().parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))


class FileInvalidationTrackerHook(PostToolUseHook):
    """Track file modifications and mark them as invalidated."""

    env_var = "FILE_INVALIDATION_TRACKER_ENABLED"
    default_enabled = True
    # Only trigger on Edit and Write tools
    tool_matcher = {"Edit", "Write"}

    def process(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_response: dict[str, Any],
    ) -> dict[str, Any]:
        """Extract file path and mark it as invalidated."""
        file_path = tool_input.get("file_path", "")
        if not file_path:
            return {"passed": True, "skipped": True, "reason": "no_file_path"}

        session_id = (
            tool_input.get("session_id")
            or tool_input.get("sessionId")
            or os.environ.get("CLAUDE_SESSION_ID", "")
        ).strip()

        terminal_id = (
            tool_input.get("terminal_id")
            or tool_input.get("terminalId")
            or os.environ.get("CLAUDE_TERMINAL_ID", "")
        ).strip()

        try:
            from cc_diagnostic_logger import log_hook_invocation
            from evidence_store import mark_file_invalidated

            success = mark_file_invalidated(
                path=file_path,
                session_id=session_id,
                terminal_id=terminal_id,
            )
            try:
                log_hook_invocation(
                    hook_name="file_invalidation_tracker",
                    event_type="file_invalidation",
                    action="invalidated" if success else "failed",
                    reason=f"File: {file_path}",
                )
            except Exception:
                pass
            return {
                "passed": True,
                "invalidated": success,
                "file_path": file_path,
            }
        except Exception:
            # Fail open — do not block tool execution
            return {"passed": True, "skipped": True, "reason": "evidence_store_error"}
