#!/usr/bin/env python3
"""
Error Attribution Tracker - PostToolUse Hook
=============================================

PHASE 1: Warning + Logging (advisory)
PHASE 2: Stop gate if logs show poor self-correction (not yet implemented)

When tool output contains error messages with identifiable sources,
inject prominent attribution and log for compliance auditing.

Integration: Registered in posttooluse/__init__.py create_registry()
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook

# Preserve patched globals across importlib.reload() in tests.
if "detect_terminal_id" not in globals():
    try:
        from __lib.terminal_detection import detect_terminal_id
    except ImportError:
        detect_terminal_id = None

LOG_FILE = Path("P:/.claude/logs/error_attribution.jsonl")
STATE_FILE = globals().get(
    "STATE_FILE",
    Path("P:/.claude/hooks/state/error_attribution.json"),
)

# Patterns to extract error source from tool output
ERROR_SOURCE_PATTERNS = [
    # Hook file in brackets: [python .claude/hooks/skill_enforcement_gate.py]
    # or shorthand [python skill_enforcement_gate.py]
    (r"\[python (?:\.claude/hooks/)?(\w+\.py)\]", "hook_file"),
    # Hook event prefix: PreToolUse:Bash hook error - capture full "PreToolUse:Bash"
    (r"((?:Pre|Post)ToolUse:\w+) hook (?:error|denied)", "hook_event"),
    # Skill enforcement specific
    (r'⛔ Use Skill\(skill=[\'"](\w+)[\'"]\)', "skill_enforcement"),
    # Generic Python exception with file
    (r'File "([^"]+\.py)", line \d+', "python_exception"),
]

# Patterns to exclude from error attribution (historical data files)
EXCLUDED_PATTERNS = [
    "session_ledger.json",
    "/data/session_",
    "/logs/",
    "/.claude/data/",
    "/CHANGELOG.md",
    "/CHANGELOG",
    ".md:",
    '.md"',
]


class ErrorAttributionTracker(PostToolUseHook):
    """
    Track error sources and inject attribution to prevent confabulation.

    When tool output contains errors with identifiable sources,
    prominently inject the source so LLM references it correctly.

    TEMPORARILY DISABLED due to false positive bug being debugged.
    """

    env_var = "ERROR_ATTRIBUTION_ENABLED"
    default_enabled = False  # Disabled until fix is verified

    def __init__(self):
        """Initialize the tracker with terminal ID detection."""
        super().__init__()
        try:
            self.terminal_id = detect_terminal_id()
        except (ImportError, TypeError):
            self.terminal_id = None

        # Initialize terminal-specific state file
        if self.terminal_id:
            safe_terminal = re.sub(r"[^a-zA-Z0-9_.-]+", "_", self.terminal_id)
            self.STATE_FILE = STATE_FILE.with_name(
                f"{STATE_FILE.stem}_{safe_terminal}{STATE_FILE.suffix}"
            )
        else:
            self.STATE_FILE = STATE_FILE

    def process(
        self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]
    ) -> dict[str, Any]:
        """Process tool output for error attribution."""

        # Skip attribution for Read/Edit of hook files - never actual errors
        file_path = tool_input.get("file_path", "")
        if tool_name in ("Read", "Edit", "Grep") and "/hooks/" in file_path:
            return {"passed": True}

        # Early return for excluded files (historical data)
        if self._is_excluded_file(file_path):
            return {"passed": True, "skipped": True, "reason": "historical_data"}

        # Convert response to string for pattern matching
        if isinstance(tool_response, str):
            output = tool_response
        elif isinstance(tool_response, dict):
            output = tool_response.get("output", "") or tool_response.get("error", "")
            if not output:
                output = json.dumps(tool_response)
        else:
            output = str(tool_response)

        if not output:
            return {"passed": True}

        # Filter out context-entry lines (⎿ prefix) - these are historical messages, not current errors
        lines = output.strip().split("\n") if output.strip() else []
        non_context_lines = [l for l in lines if l.strip() and not l.strip().startswith("⎿")]

        # If ALL lines are context entries, no actual error occurred
        if not non_context_lines:
            return {"passed": True}

        # Fast path: check for error indicators in non-context lines only
        # Use patterns that match actual errors, not code/docs containing "error"
        filtered_output = "\n".join(non_context_lines)
        error_patterns = [
            "Traceback",
            "Exception",
            "Error:",
            "ERROR:",
            "⛔",
            "denied",
            "blocked",
            "failed",
            "Exit code",
            "stderr:",
            "fatal",
            "FATAL",
            "hook error",
        ]
        # Also check for Python traceback pattern: File "...", line XX
        has_traceback = bool(re.search(r'File\s+"[^"]+",\s+line\s+\d+', filtered_output))

        if not any(ind in filtered_output for ind in error_patterns) and not has_traceback:
            return {"passed": True}

        # Extract error source from FILTERED output only (not full content)
        # This prevents false positives from code/docs containing error patterns
        tool_timestamp = tool_response.get("timestamp") if isinstance(tool_response, dict) else None
        error_info = self._extract_error_source(filtered_output, tool_timestamp)
        if not error_info:
            return {"passed": True}

        # Log for auditing
        self._log_attribution(error_info, tool_name)

        # Write state for potential Stop gate
        self._write_state(error_info)

        # Build injection
        injection = self._build_injection(error_info)

        return {
            "passed": True,
            "injection": injection,
            "metadata": {
                "error_source": error_info["source"],
                "source_type": error_info["source_type"],
            },
        }

    def _is_excluded_file(self, file_path: str) -> bool:
        """Check if file path matches any excluded pattern.

        Args:
            file_path: File path to check against exclusion patterns

        Returns:
            True if file path matches any excluded pattern, False otherwise
        """
        if not file_path:
            return False

        for pattern in EXCLUDED_PATTERNS:
            if pattern in file_path:
                return True
        return False

    def _extract_error_source(self, output: str, tool_timestamp: float = None) -> dict | None:
        """Extract error attribution from tool output.

        Args:
            output: Tool output string to search for error patterns
            tool_timestamp: Optional timestamp from tool response. If None, uses current time.

        Returns:
            dict with error source info if recent error found, None otherwise
        """
        current_time = tool_timestamp if tool_timestamp is not None else time.time()

        for pattern, source_type in ERROR_SOURCE_PATTERNS:
            if match := re.search(pattern, output):
                # Look for timestamp in context around the pattern match
                # Find the timestamp closest to the pattern (before or after)
                context_start = max(0, match.start() - 200)
                context_end = min(len(output), match.end() + 100)
                context = output[context_start:context_end]

                # Find all timestamps in context and pick the one closest to the pattern
                ts_matches = list(re.finditer(r'"timestamp":\s*(\d+\.?\d*)', context))
                if ts_matches:
                    # Find the timestamp closest to the pattern match position
                    pattern_pos_in_context = match.start() - context_start
                    closest_ts = None
                    closest_dist = float("inf")

                    for ts_m in ts_matches:
                        ts_pos = ts_m.start()
                        dist = abs(ts_pos - pattern_pos_in_context)
                        if dist < closest_dist:
                            closest_dist = dist
                            closest_ts = float(ts_m.group(1))

                    if closest_ts is not None:
                        age = current_time - closest_ts
                        if age > 10:  # Older than 10 seconds
                            continue  # Skip to next pattern

                # All patterns now use single capture group
                source = match.group(1)
                return {
                    "source": source,
                    "source_type": source_type,
                    "pattern_matched": pattern,
                    "context": output[:300],
                }
        return None

    def _log_attribution(self, error_info: dict, tool_name: str) -> None:
        """Log error attribution for auditing."""
        try:
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            entry = {
                "timestamp": time.time(),
                "tool_name": tool_name,
                "source": error_info["source"],
                "source_type": error_info["source_type"],
                "context": error_info["context"][:150],
            }
            with open(LOG_FILE, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass  # Non-critical

    def _write_state(self, error_info: dict) -> None:
        """Write state for potential Stop gate validation."""
        try:
            self.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            state = {
                "source": error_info["source"],
                "source_type": error_info["source_type"],
                "timestamp": time.time(),
                "expires_at": time.time() + 120,  # Valid for 2 minutes
                "terminal_id": self.terminal_id,
            }
            self.STATE_FILE.write_text(json.dumps(state))
        except Exception:
            pass  # Non-critical

    def _build_injection(self, error_info: dict) -> str:
        """Build prominent error source injection."""
        source = error_info["source"]
        return f"""
┌─────────────────────────────────────────────────────────┐
│ ⚠️  ERROR SOURCE: {source:<38} │
│ Reference this source when explaining what went wrong.  │
└─────────────────────────────────────────────────────────┘
""".strip()
