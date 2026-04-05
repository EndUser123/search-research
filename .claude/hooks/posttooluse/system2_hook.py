#!/usr/bin/env python3
from __future__ import annotations

"""
System 2 Debugging Prompt - In-process adapter.

Detects errors in tool output and provides debugging guidance.
Writes diagnostic messages to stderr (not additionalContext).
Absorbed from PostToolUse_system2.py.

Original matcher: .* (all tools)
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Final

from posttooluse.base import PostToolUseHook

# Debug mode: Only write diagnostic stderr when enabled
# Set environment variable SYSTEM2_DEBUG=1 to enable diagnostic output
SYSTEM2_DEBUG = os.environ.get("SYSTEM2_DEBUG", "0") == "1"

_hooks_dir = Path(__file__).resolve().parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))

# Add atomic_write to path
_csf_nip_src = _hooks_dir.parent.parent / "__csf" / "src" / "core"
if str(_csf_nip_src) not in sys.path:
    sys.path.insert(0, str(_csf_nip_src))

SESSION_STATE_FILE = _hooks_dir / ".state" / "debug_session_state.json"

ERROR_PATTERNS: Final = [
    (r"(?i)command not found", "command_not_found"),
    (r"(?i)is not recognized as an", "command_not_found"),
    (r"(?i)exit code (?:[1-9]|\d{2,})", "nonzero_exit"),
    (r"(?i)traceback\s*\(most\s*recent", "python_exception"),
    (r"(?i)error:", "generic_error"),
    (r"(?i)failed", "generic_failed"),
    (r"(?i)exception:", "exception"),
]

WINDOWS_TOOL_ALTERNATIVES: Final = {
    "sqlite3": 'python -c "import sqlite3; conn = sqlite3.connect(...)"',
    "sed": "python re module (re.sub, re.findall)",
    "grep": "Select-String (PowerShell) or python re module",
    "awk": "python str.split() and list comprehensions",
    "find": "Path.glob() or pathlib.Path.rglob()",
    "xargs": "python subprocess.run() with list comprehension",
}

CAUSAL_GRAPHS: Final = {
    "command_not_found": [
        {"cause_id": "unix_tool_not_available", "description": "Unix tool not available on Windows",
         "base_probability": 0.85, "adjusted_probability": 0.85},
        {"cause_id": "tool_not_installed", "description": "Tool not installed on system",
         "base_probability": 0.10, "adjusted_probability": 0.10},
        {"cause_id": "wrong_syntax", "description": "Command syntax incorrect",
         "base_probability": 0.05, "adjusted_probability": 0.05},
    ],
    "import_error": [
        {"cause_id": "module_not_installed", "description": "Third-party module not installed",
         "base_probability": 0.80, "adjusted_probability": 0.80},
    ],
    "python_exception": [
        {"cause_id": "null_pointer", "description": "Variable is None when accessed",
         "base_probability": 0.60, "adjusted_probability": 0.60},
        {"cause_id": "type_mismatch", "description": "Wrong type for operation",
         "base_probability": 0.25, "adjusted_probability": 0.25},
    ],
}


def _get_tool_output(data: dict) -> str:
    """Extract tool output from hook data."""
    for key in ["tool_response", "output", "content", "result"]:
        if key not in data:
            continue
        val = data[key]
        if isinstance(val, dict):
            parts = []
            for field in ["stdout", "stderr", "output", "error", "content"]:
                if field in val and val[field]:
                    parts.append(str(val[field]))
            return " ".join(parts) if parts else ""
        return str(val) if val else ""
    return ""


def _detect_error_patterns(output: str) -> list[str]:
    return [name for pattern, name in ERROR_PATTERNS if re.search(pattern, output)]


def _classify_error_with_confidence(output: str) -> tuple[str, str, float]:
    output_lower = output.lower()
    if "command not found" in output_lower or "is not recognized" in output_lower:
        error_type = "command_not_found"
    elif "modulenotfounderror" in output_lower or "importerror" in output_lower:
        error_type = "import_error"
    elif "traceback" in output_lower:
        error_type = "python_exception"
    else:
        error_type = "generic_error"

    if error_type in CAUSAL_GRAPHS:
        causes = CAUSAL_GRAPHS[error_type]
        top_cause = max(causes, key=lambda x: x["adjusted_probability"])
        return error_type, top_cause["cause_id"], top_cause["adjusted_probability"]
    return error_type, "unknown", 0.5


def _classify_severity(output: str) -> str:
    output_lower = output.lower()
    if re.search(r"exit code [1-9]", output_lower):
        return "CRITICAL"
    if "error:" in output_lower and "warning:" not in output_lower:
        return "CRITICAL"
    if "traceback" in output_lower or "exception" in output_lower:
        return "CRITICAL"
    if "command not found" in output_lower or "is not recognized" in output_lower:
        return "CRITICAL"
    if "warning:" in output_lower:
        return "WARNING"
    return "IGNORE"


class System2Hook(PostToolUseHook):
    """Detects errors and provides System 2 debugging guidance via stderr."""

    tool_matcher = None  # All tools

    def process(self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]) -> dict[str, Any]:
        # Build a data dict compatible with _get_tool_output
        data = {"tool_response": tool_response}
        output = _get_tool_output(data)

        if not output:
            return {"passed": True}

        command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""

        # Check for Windows tool not found
        output_lower = output.lower()
        if "command not found" in output_lower or "is not recognized" in output_lower:
            for tool in WINDOWS_TOOL_ALTERNATIVES:
                if tool in output_lower:
                    alt = WINDOWS_TOOL_ALTERNATIVES[tool]
                    if SYSTEM2_DEBUG:
                        sys.stderr.write(f"\n{'=' * 64}\n  WINDOWS Tool Not Available: {tool}\n{'=' * 64}\n")
                        sys.stderr.write(f"Python alternative: {alt}\n{'=' * 64}\n")
                        sys.stderr.flush()
                    return {"passed": True}

        if not _detect_error_patterns(output):
            return {"passed": True}

        error_type, cause_id, confidence = _classify_error_with_confidence(output)
        severity = _classify_severity(output)

        if SYSTEM2_DEBUG:
            if confidence > 0.7:
                sys.stderr.write(f"\n{'=' * 64}\n  HIGH-CONFIDENCE ANALYSIS: {error_type}\n{'=' * 64}\n")
                sys.stderr.write(f"Confidence: {confidence * 100:.0f}%\n")
                sys.stderr.write("For deeper investigation: /debug --react\n")
                sys.stderr.write(f"{'=' * 64}\n")
            else:
                sys.stderr.write(f"\n{'=' * 64}\n  Error Detected - Confidence Below Threshold\n{'=' * 64}\n")
                sys.stderr.write(f"Error Type: {error_type}, Confidence: {confidence * 100:.0f}%\n")
                sys.stderr.write(f"{'=' * 64}\n")
            sys.stderr.flush()

        # Write session state for CRITICAL errors
        if severity == "CRITICAL":
            try:
                from utils.atomic_write import atomic_write_json
                SESSION_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
                state = {}
                if SESSION_STATE_FILE.exists():
                    state = json.loads(SESSION_STATE_FILE.read_text())
                state["last_error"] = {
                    "tool": tool_name, "command": command, "error_type": error_type,
                    "confidence": confidence, "severity": severity,
                }
                state["timestamp"] = datetime.now().isoformat()
                history = state.get("command_history", [])
                if command:
                    history = [h for h in history if h != command][-4:]
                    history.append(command)
                    state["command_history"] = history
                atomic_write_json(SESSION_STATE_FILE, state, indent=2)
            except Exception:
                pass

        return {"passed": True}
