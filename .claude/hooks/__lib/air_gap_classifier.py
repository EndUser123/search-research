#!/usr/bin/env python3
"""
AIR Gap Classifier: Detects Silent Pivot, Hallucinated, and Unjustified Revert gaps.

This module provides gap classification logic for the AIR Auditor framework.
It correlates user directives with agent actions and git diffs to identify
behavioral gaps.

Run: PreToolUse (capture directive context) + PostToolUse (classify gaps)
Timeout: 5 seconds
Exit Codes:
  - 0: Always allow (classification never blocks)

Author: Claude Code
Date: 2026-03-26
Related: temporal-honking-bubble.md (AIR Auditor plan CHANGE-003)
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add hooks lib to path
# Add hooks lib to path
# air_gap_classifier.py is in P:/.claude/hooks/__lib/
# so we need to go up one level to find the hooks directory
hooks_dir = Path(__file__).resolve().parent.parent  # P:/.claude/hooks/
hooks_lib = hooks_dir / "__lib"
sys.path.insert(0, str(hooks_lib))

from pre_tool_use_logic import resolve_session_id

# State file paths
STATE_DIR = Path("P:/") / ".claude" / "state"
AIR_GAPS_KEY = "air_gap_context"

# Gap type definitions
GAP_TYPES = ["silent_pivot", "hallucinated", "unjustified_revert"]


def _get_session_id(data: dict | None = None) -> str:
    """Get session ID from hook data or environment."""
    if data:
        session_id = resolve_session_id(data)
        if session_id:
            return session_id
    return os.environ.get("CLAUDE_SESSION_ID", "default")


def _get_terminal_id() -> str:
    """Get terminal ID from environment."""
    return os.environ.get("CLAUDE_TERMINAL_ID", "default")


def _get_transcript_path() -> str | None:
    """Get transcript path from hook data if available."""
    # Transcript path is available in some hook contexts
    # via session metadata
    return None


def _capture_git_diff(cwd: str) -> dict:
    """Capture git diff --stat summary for modified files.

    Returns:
        dict with keys:
            - line_count: total lines changed
            - files_changed: number of files changed
            - raw: raw diff stat output
            - timestamp: ISO timestamp of capture
    """
    try:
        # Get diff stat summary
        result = subprocess.run(
            ["git", "diff", "--stat", "--stat-width", "200"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5.0,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )

        # Parse line count from diff
        lines = result.stdout.strip().split("\n")
        total_lines = 0
        for line in lines:
            if "file" in line.lower() and "changed" in line.lower():
                # e.g., "3 files changed, 10 insertions(+), 5 deletions(-)"
                parts = line.split(",")
                for part in parts:
                    part = part.strip()
                    if "insertion" in part:
                        try:
                            total_lines += int(part.split()[0])
                        except (ValueError, IndexError):
                            pass
                    if "deletion" in part:
                        try:
                            total_lines += int(part.split()[0])
                        except (ValueError, IndexError):
                            pass

        return {
            "line_count": total_lines,
            "files_changed": len([l for l in lines if l.strip() and "changed" in l.lower()]),
            "raw": result.stdout,
            "timestamp": datetime.now().isoformat(),
        }
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        return {
            "line_count": 0,
            "files_changed": 0,
            "raw": "",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }


def _get_cwd(tool_input: dict) -> str:
    """Get working directory from tool input."""
    return tool_input.get("cwd", "") or os.getcwd()


def classify_gap(
    directive: str | None,
    action: str,
    git_diff: dict,
) -> dict | None:
    """Classify a gap based on directive, action, and git diff.

    Args:
        directive: The user directive that prompted the action (None if missing)
        action: Description of the agent action taken
        git_diff: Dict with line_count, files_changed, raw output

    Returns:
        dict with gap classification or None if no gap detected:
            {
                "type": "silent_pivot" | "hallucinated" | "unjustified_revert",
                "directive": directive or "none",
                "action": action,
                "evidence": str,
                "timestamp": ISO timestamp
            }
    """
    line_count = git_diff.get("line_count", 0)
    raw_output = git_diff.get("raw", "")
    timestamp = git_diff.get("timestamp", datetime.now().isoformat())

    # Hallucinated: Directive exists but no meaningful diff
    if directive and line_count < 5:
        return {
            "type": "hallucinated",
            "directive": directive,
            "action": action,
            "evidence": f"Directive '{directive}' but only {line_count} lines changed",
            "timestamp": timestamp,
        }

    # Silent Pivot: Action exists but no directive in window
    if not directive and line_count >= 5:
        return {
            "type": "silent_pivot",
            "directive": "none",
            "action": action,
            "evidence": f"Action '{action}' taken without explicit directive, {line_count} lines changed",
            "timestamp": timestamp,
        }

    # Unjustified Revert: Detect revert without technical evidence
    if "revert" in action.lower() or "revert" in raw_output.lower():
        # Check for technical justification in commit/message
        has_technical_evidence = any(
            keyword in raw_output.lower()
            for keyword in ["bug", "fix", "error", "crash", "fail", "break", "issue"]
        )
        if not has_technical_evidence:
            return {
                "type": "unjustified_revert",
                "directive": directive or "none",
                "action": action,
                "evidence": "Revert without technical justification in commit message",
                "timestamp": timestamp,
            }

    return None


def store_gap(session_id: str, gap: dict) -> bool:
    """Store classified gap to state file.

    Args:
        session_id: Session identifier
        gap: Gap classification dict

    Returns:
        True if stored successfully, False otherwise
    """
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        state_file = STATE_DIR / f"air_gaps_{session_id}.json"

        # Load existing gaps or create new
        existing = []
        if state_file.exists():
            try:
                existing = json.loads(state_file.read_text(encoding="utf-8"))
                if not isinstance(existing, list):
                    existing = []
            except (json.JSONDecodeError, OSError):
                existing = []

        # Append new gap
        existing.append(gap)

        # Write with owner-only permissions (0o600)
        state_file.write_text(json.dumps(existing, indent=2), encoding="utf-8")

        # Set permissions on Windows (no-op if not supported)
        try:
            os.chmod(state_file, 0o600)
        except OSError:
            pass  # Windows may not support chmod

        return True
    except OSError:
        return False


def load_gaps(session_id: str) -> list:
    """Load all classified gaps for a session.

    Args:
        session_id: Session identifier

    Returns:
        List of gap classifications
    """
    try:
        state_file = STATE_DIR / f"air_gaps_{session_id}.json"
        if state_file.exists():
            return json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass
    return []


def capture_directive_context(
    data: dict,
    tool_name: str,
    tool_input: dict,
) -> dict | None:
    """Capture directive context at PreToolUse time.

    Args:
        data: Hook data dictionary
        tool_name: Name of tool being executed
        tool_input: Tool input dictionary

    Returns:
        Context dict with directive and action info, or None
    """
    session_id = _get_session_id(data)
    terminal_id = _get_terminal_id()
    cwd = _get_cwd(tool_input)

    # Extract action description from tool
    action = f"{tool_name}"
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        action = f"Bash: {command[:100]}"
    elif tool_name == "Edit":
        action = f"Edit: {tool_input.get('file_path', 'unknown')}"
    elif tool_name == "Write":
        action = f"Write: {tool_input.get('file_path', 'unknown')}"

    return {
        "session_id": session_id,
        "terminal_id": terminal_id,
        "tool_name": tool_name,
        "action": action,
        "cwd": cwd,
        "timestamp": datetime.now().isoformat(),
    }


def classify_and_store(
    data: dict,
    tool_name: str,
    tool_input: dict,
    git_diff: dict,
) -> dict | None:
    """Classify gap and store result.

    This is called at PostToolUse time with the git diff.

    Args:
        data: Hook data dictionary
        tool_name: Name of tool that was executed
        tool_input: Tool input dictionary
        git_diff: Git diff capture from PostToolUse

    Returns:
        Gap classification dict or None
    """
    session_id = _get_session_id(data)

    # Extract action description
    action = f"{tool_name}"
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        action = f"Bash: {command[:100]}"

    # NOTE: directive detection from transcript requires transcript parsing
    # which is expensive. For now, we classify based on available context.
    # The directive field is populated from the stored context if available.
    directive = None  # Would require transcript parsing

    # Classify the gap
    gap = classify_gap(directive, action, git_diff)

    if gap:
        store_gap(session_id, gap)

    return gap
