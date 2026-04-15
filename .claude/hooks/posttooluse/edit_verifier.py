#!/usr/bin/env python3
"""
Edit Verifier PostToolUse Hook

Verifies Write and Edit operations actually persisted correctly to disk.
Blocks when tool claims success but verification fails.

- Write: file must exist and not be empty
- Edit: new_string must be present in file

Records Read observation in tool sequence after successful verification,
so empirical_claims_gate recognizes the file was observed.

Architecture:
- Extends PostToolUseHook base class
- Triggers on Write and Edit tools only
- Deeper verification than ImplementationVerifier:
  - Write: checks file exists AND not empty
  - Edit: checks new_string present, old_string may legitimately remain
"""

import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .base import PostToolUseHook

# Import tool_sequence_manager for recording observations
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))
from tool_sequence_manager import ToolSequenceManager

logger = logging.getLogger(__name__)


def get_excerpt(content: str, anchor: str = "", context_lines: int = 10, max_lines: int = 50) -> str:
    """Extract excerpt from content around an anchor point."""
    lines = content.splitlines()
    total_lines = len(lines)

    if not anchor or anchor not in content:
        return "\n".join(lines[:max_lines])

    anchor_idx = None
    for i, line in enumerate(lines):
        if anchor in line:
            anchor_idx = i
            break

    if anchor_idx is None:
        return "\n".join(lines[:max_lines])

    anchor_lines = anchor.splitlines()
    start_idx = max(0, anchor_idx - context_lines)
    end_idx = min(total_lines, anchor_idx + len(anchor_lines) + context_lines)

    excerpt_lines = lines[start_idx:end_idx]
    if len(excerpt_lines) > max_lines:
        excess = len(excerpt_lines) - max_lines
        trim_start = excess // 2
        trim_end = excess - trim_start
        excerpt_lines = excerpt_lines[trim_start:len(excerpt_lines) - trim_end]

    return "\n".join(excerpt_lines)


def record_observation(file_path: str, session_id: str = "") -> bool:
    """Record a Read observation in the tool sequence."""
    try:
        entry = {
            "name": "Read",
            "file_path": str(file_path),
            "timestamp": datetime.now(UTC).isoformat(),
        }
        return ToolSequenceManager.append(entry, session_id=session_id)
    except Exception:
        return False


def is_failed_operation(tool_response: dict[str, Any]) -> bool:
    """Check if tool response indicates a failed operation."""
    if not tool_response:
        return False
    response_text = (
        tool_response.get("output", "")
        or tool_response.get("result", "")
        or tool_response.get("stdout", "")
        or str(tool_response)
    )
    response_lower = response_text.lower()
    error_indicators = ["error", "failed", "permission denied", "not found"]
    return any(indicator in response_lower for indicator in error_indicators)


def validate_path(file_path: str) -> tuple[bool, str, Path]:
    """Validate file path before verification operations."""
    if not file_path or not isinstance(file_path, str):
        return False, "File path is empty or invalid", Path()

    if file_path in (".", "..") or file_path.endswith("/") or file_path.endswith("\\"):
        return False, f"Path appears to be a directory: {file_path}", Path()

    try:
        path = Path(file_path).resolve()
        if not path.exists():
            return False, f"Path does not exist: {file_path}", Path()
        if not path.is_file():
            if path.is_dir():
                return False, f"Path is a directory, not a file: {file_path}", Path()
            return False, f"Path is not a regular file: {file_path}", Path()
        return True, "", path
    except (OSError, ValueError) as e:
        return False, f"Invalid path '{file_path}': {e}", Path()


def verify_write(file_path: str, expected_content: str) -> tuple[bool, str, str]:
    """Verify Write operation: file must exist, not empty, and match expected content."""
    is_valid, reason, path = validate_path(file_path)
    if not is_valid:
        return False, f"Write verification failed: {reason}", ""

    try:
        actual_content = path.read_text(encoding="utf-8", errors="replace")
    except (PermissionError, OSError, UnicodeDecodeError) as e:
        return False, f"Write verification failed: cannot read file {file_path}: {e}", ""

    if not actual_content or actual_content == "":
        return False, f"Write verification failed: file is empty at {file_path}", ""

    # Deep verification: content must match what was supposed to be written
    # This catches Windows buffer flush failures where old content remains
    # Exception: Claude Code's native memory system appends originSessionId to frontmatter
    # after writes to .claude/projects/*/memory/ — exact match will always fail there.
    if expected_content and actual_content != expected_content:
        return False, f"Write verification failed: content mismatch at {file_path}\nExpected {len(expected_content)} bytes, got {len(actual_content)} bytes", ""

    return True, "Write verification passed", actual_content


def verify_edit(file_path: str, old_string: str, new_string: str) -> tuple[bool, str, str]:
    """Verify Edit operation: new_string must be present in file."""
    if not old_string or not new_string:
        return True, "Edit verification skipped: missing old/new string payload", ""

    if not file_path:
        return True, "Edit verification skipped: missing file path payload", ""

    is_valid, reason, path = validate_path(file_path)
    if not is_valid:
        return True, f"Edit verification skipped: {reason}", ""

    try:
        actual_content = path.read_text(encoding="utf-8", errors="replace")
    except (PermissionError, OSError, UnicodeDecodeError) as e:
        return True, f"Edit verification skipped: cannot read file {file_path}: {e}", ""

    if new_string not in actual_content:
        return False, f"Edit verification failed: new_string not found in {file_path}", ""

    # old_string may legitimately remain if it appears multiple times
    if old_string in actual_content:
        return True, "Edit verification passed (partial replacement detected)", actual_content

    return True, "Edit verification passed", actual_content


class EditVerifier(PostToolUseHook):
    """
    Verifies Write/Edit operations actually persisted correctly to disk.

    Environment Variables:
        EDIT_VERIFIER_ENABLED: "true" (default) or "false" to disable

    Configuration:
        env_var: "EDIT_VERIFIER_ENABLED"
        default_enabled: True
        tool_matcher: {"Write", "Edit"} - Only verifies write operations
    """

    env_var = "EDIT_VERIFIER_ENABLED"
    default_enabled = True
    tool_matcher = {"Write", "Edit"}

    def process(
        self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Verify Write or Edit operation persisted correctly.

        Args:
            tool_name: "Write" or "Edit"
            tool_input: Tool input dict with file_path, content, old_string, new_string
            tool_response: Tool response dict

        Returns:
            dict with:
                - passed: bool - True if verification passed
                - injection: str | None - Context message with verification excerpt
                - metadata: dict - Additional diagnostic info
        """
        # Skip failed operations
        if is_failed_operation(tool_response):
            return {"passed": True, "metadata": {"reason": "failed_operation"}}

        file_path = (
            tool_input.get("file_path")
            or tool_input.get("filePath")
            or tool_input.get("target_file")
            or tool_input.get("path")
            or ""
        )

        if tool_name == "Write":
            content = tool_input.get("content", "")
            success, reason, actual_content = verify_write(file_path, content)
            if success:
                record_observation(file_path, "")
                excerpt = get_excerpt(actual_content, "", max_lines=50)
                return {
                    "passed": True,
                    "injection": f"Verified {file_path}:\n```\n{excerpt}\n```",
                    "metadata": {
                        "file_path": file_path,
                        "verified": True,
                        "reason": "write_verified",
                    },
                }
            else:
                return {
                    "decision": "block",
                    "injection": f"WRITE VERIFICATION FAILED: {file_path}\n{reason}",
                    "metadata": {
                        "file_path": file_path,
                        "verified": False,
                        "reason": reason,
                    },
                }

        elif tool_name == "Edit":
            old_string = tool_input.get("old_string", "")
            new_string = tool_input.get("new_string", "")
            success, reason, actual_content = verify_edit(file_path, old_string, new_string)
            if success:
                if not file_path or not actual_content:
                    return {"passed": True, "metadata": {"reason": "empty_verification"}}
                record_observation(file_path, "")
                excerpt = get_excerpt(actual_content, new_string, context_lines=10, max_lines=50)
                return {
                    "passed": True,
                    "injection": f"Verified {file_path}:\n```\n{excerpt}\n```",
                    "metadata": {
                        "file_path": file_path,
                        "verified": True,
                        "reason": "edit_verified",
                    },
                }
            else:
                return {
                    "decision": "block",
                    "injection": f"EDIT VERIFICATION FAILED: {file_path}\n{reason}",
                    "metadata": {
                        "file_path": file_path,
                        "verified": False,
                        "reason": reason,
                    },
                }

        # Should not reach here due to tool_matcher, but guard anyway
        return {"passed": True, "metadata": {"reason": "tool_not_matched"}}
