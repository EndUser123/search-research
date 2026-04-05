#!/usr/bin/env python3
from __future__ import annotations

"""
Change Verification Reminder Hook
==================================

Tracks file changes after Write/Edit operations.
Silent tracking only - no ASCII box output (disabled for performance).

Problem: CC makes code changes, assumes they're correct, and moves on.
When errors occur later, CC blames external factors instead of checking its own work.

Solution: Track all changes for potential verification (now silent).

Extracted from PostToolUse_change_verification.py for in-process execution.
"""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Import base class
from posttooluse.base import PostToolUseHook


class ChangeVerification(PostToolUseHook):
    """Tracks file changes for verification (silent mode)."""

    env_var = "CHANGE_VERIFICATION_ENABLED"
    default_enabled = True

    # Skip verification for these file types
    SKIP_EXTENSIONS = {".md", ".txt", ".rst", ".log", ".gitignore"}

    def __init__(self):
        super().__init__()
        self.hooks_dir = Path(__file__).resolve().parent.parent
        # Instance isolation: use current working directory hash
        self._instance_id = hashlib.md5(str(Path.cwd()).encode()).hexdigest()[:8]
        # State file is shared, but filtering happens in UserPromptSubmit_verification_reminder.py
        self.session_file = self.hooks_dir / "session_data" / "pending_verifications.json"
        self.session_file.parent.mkdir(parents=True, exist_ok=True)

    def process(self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]) -> dict[str, Any]:
        """
        Track file changes (silent - no injection).

        Returns dict with tracking status (no injection since ASCII box is disabled).
        """
        result = {
            "ok": True,
            "passed": True,
            "tracked": False,
            "injection": None,
        }

        # Only track Write/Edit operations
        if tool_name not in ("Write", "Edit"):
            return result

        # Check if the operation succeeded
        tool_response_str = str(tool_response)
        if any(err in tool_response_str.lower() for err in ["error", "failed", "denied", "not found"]):
            return result

        file_path = self._extract_file_path(tool_input, tool_response)
        if not file_path:
            return result

        # Track the change
        self._save_pending_verification({
            "file": file_path,
            "tool": tool_name,
            "timestamp": datetime.now(UTC).isoformat(),
            "needs_verification": Path(file_path).suffix.lower() not in self.SKIP_EXTENSIONS,
        })

        result["tracked"] = True
        result["file_modified"] = file_path

        # ASCII box disabled - silent tracking only
        # (Tracking still recorded to session_data/pending_verifications.json)

        return result

    def _extract_file_path(self, tool_input: dict[str, Any], tool_response: dict[str, Any]) -> str | None:
        """Extract file path from tool input/response."""
        if isinstance(tool_input, dict):
            path = (
                tool_input.get("file_path") or
                tool_input.get("path") or
                tool_input.get("filePath") or
                tool_input.get("target")
            )
            if path:
                return path

        # Try other fields
        if isinstance(tool_response, dict):
            return tool_response.get("file_path") or tool_response.get("path")

        return None

    def _save_pending_verification(self, change: dict) -> None:
        """Save a pending verification to session file."""
        try:
            pending = self._load_pending_verifications()
            pending.append(change)
            # Keep only last 10
            pending = pending[-10:]
            self.session_file.write_text(json.dumps(pending, indent=2), encoding='utf-8')
        except Exception:
            pass  # Don't fail if tracking fails

    def _load_pending_verifications(self) -> list[dict]:
        """Load pending verifications from session file."""
        try:
            if self.session_file.exists():
                return json.loads(self.session_file.read_text(encoding='utf-8'))
        except Exception:
            pass
        return []
