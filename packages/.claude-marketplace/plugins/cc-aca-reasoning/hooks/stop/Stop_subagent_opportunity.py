"""Stop_subagent_opportunity - Stop hook advisory.

Surfaces delegation opportunity advisory if task completed without Agent tool
but multiple file operations were performed. Advisory only - never blocks.

This complements the UserPromptSubmit delegation_prospector which fires BEFORE
tool execution. This hook fires AFTER task completion to identify missed
opportunities when the main agent did the work directly instead of delegating.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

# Telemetry log path
_LOG_DIR = Path("P:/") / ".claude" / "logs" / "diagnostics"
_LOG_FILE = _LOG_DIR / "subagent_opportunity.jsonl"

# Advisory threshold: number of file operations before surfacing advisory
_OPPORTUNITY_THRESHOLD = 3

# Sanitize path components to prevent traversal attacks (SEC-001 fix)
_SAFE_ID_RE = re.compile(r"[^a-zA-Z0-9_.-]")


def _safe_id(value: str) -> str:
    """Strip anything unsafe from a path component."""
    return _SAFE_ID_RE.sub("", value)


def _get_terminal_id(data: dict) -> str:
    return (data.get("terminal_id") or data.get("terminalId") or data.get("CLAUDE_TERMINAL_ID") or os.environ.get("CLAUDE_TERMINAL_ID") or "default")


def _get_session_id(data: dict) -> str:
    return (data.get("session_id") or data.get("sessionId") or os.environ.get("CLAUDE_SESSION_ID") or "unknown")


def _load_session_opportunities(session_id: str, terminal_id: str) -> dict:
    """Load session-level opportunity tracking state."""
    state_file = _LOG_DIR / f"opportunity_session_{_safe_id(terminal_id)}_{_safe_id(session_id)}.json"
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"count": 0, "last_advisory_ts": None}


def _save_session_opportunities(session_id: str, terminal_id: str, state: dict) -> None:
    """Save session-level opportunity tracking state."""
    state_file = _LOG_DIR / f"opportunity_session_{_safe_id(terminal_id)}_{_safe_id(session_id)}.json"
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except OSError as e:
        import warnings
        warnings.warn(f"Stop_subagent_opportunity: failed to save session state: {e}")


def _log_opportunity_event(event_type: str, terminal_id: str, session_id: str, details: dict) -> None:
    """Log subagent opportunity event."""
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "event": event_type,
            "terminal_id": terminal_id,
            "session_id": session_id,
            **details,
        }
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def _count_file_operations(data: dict) -> int:
    """Count Edit/Write operations from tool_events."""
    tool_events = data.get("tool_events", [])
    if not isinstance(tool_events, list):
        return 0
    count = 0
    for event in tool_events:
        name = event.get("name", "")
        if name in ("Edit", "Write", "MultiEdit"):
            count += 1
    return count


def _agent_was_used(data: dict) -> bool:
    """Check if Agent tool was used in this turn."""
    tool_events = data.get("tool_events", [])
    if not isinstance(tool_events, list):
        return False
    for event in tool_events:
        if event.get("name") == "Agent":
            return True
    return False


def run(data: dict) -> dict | None:
    """Check for delegation opportunity and return advisory.

    Args:
        data: Stop hook input with session_id, terminal_id, tool_events, etc.

    Returns:
        Dict with systemMessage or None (allows stop to proceed)
    """
    terminal_id = _get_terminal_id(data)
    session_id = _get_session_id(data)

    # Skip if Agent tool was already used - no missed opportunity
    if _agent_was_used(data):
        _log_opportunity_event(
            event_type="agent_used",
            terminal_id=terminal_id,
            session_id=session_id,
            details={"result": "delegation occurred"},
        )
        return None

    # Load session opportunity state
    session_state = _load_session_opportunities(session_id, terminal_id)

    # Check if advisory was recently shown (within this session)
    if session_state.get("last_advisory_ts"):
        return None

    # Count file operations
    file_op_count = _count_file_operations(data)

    # Log opportunity detection
    _log_opportunity_event(
        event_type="opportunity_detected" if file_op_count >= _OPPORTUNITY_THRESHOLD else "below_threshold",
        terminal_id=terminal_id,
        session_id=session_id,
        details={
            "file_ops": file_op_count,
            "threshold": _OPPORTUNITY_THRESHOLD,
            "files_touched": _get_touched_files(data),
        },
    )

    # Only surface advisory if threshold exceeded
    if file_op_count < _OPPORTUNITY_THRESHOLD:
        return None

    # Mark advisory as shown
    session_state["count"] = session_state.get("count", 0) + 1
    session_state["last_advisory_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    _save_session_opportunities(session_id, terminal_id, session_state)

    # Return advisory in systemMessage format
    advisory_text = """
[DELEGATION OPPORTUNITY NOTED]

This task involved multiple file operations without subagent delegation.
Consider using Agent tool for multi-surface verification tasks.

Benefits:
  - Parallel verification reduces total time
  - Each subagent returns focused, verified findings
  - Main context stays clear for synthesis
""".strip()

    return {"systemMessage": "\n\n" + advisory_text}


def _get_touched_files(data: dict) -> list[str]:
    """Extract file paths from tool events."""
    tool_events = data.get("tool_events", [])
    if not isinstance(tool_events, list):
        return []
    files = []
    for event in tool_events:
        name = event.get("name", "")
        if name in ("Edit", "Write", "MultiEdit"):
            file_path = event.get("file_path", "") or event.get("path", "")
            if file_path:
                files.append(Path(file_path).name)
    return files[:10]


if __name__ == "__main__":
    import sys
    input_data = json.load(sys.stdin)
    result = run(input_data)
    if result:
        print(json.dumps(result))
    sys.exit(0)
