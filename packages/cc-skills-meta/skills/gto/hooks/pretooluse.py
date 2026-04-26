#!/usr/bin/env python3
"""GTO PreToolUse hook — optional gates during GTO runs.

Claude Code hook protocol: reads JSON from stdin, outputs JSON to stdout.

During GTO runs, this hook can:
- Warn if tool usage might conflict with artifact generation
- Block destructive operations during active analysis
"""
from __future__ import annotations

import json
import sys

from .common import is_gto_active, read_state, write_hook_output

# Tools that should be warned about during active GTO runs
WARN_TOOLS = {"Bash"}

# Commands that could interfere with GTO artifact generation
BLOCK_PATTERNS = ["rm -rf", "git reset --hard", "git checkout --"]


def run(data: dict) -> dict | None:
    """In-process hook entry point."""
    if not is_gto_active():
        return None

    state = read_state()
    if state.get("phase") != "running":
        return None

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if tool_name not in WARN_TOOLS:
        return None

    # Check for destructive commands
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        for pattern in BLOCK_PATTERNS:
            if pattern in command:
                return {
                    "decision": "block",
                    "reason": f"GTO: blocking destructive command during active run: '{pattern}'",
                }

    return None


def main() -> None:
    """CLI entry point."""
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        data = {}

    result = run(data)
    if result is not None:
        write_hook_output(result)
        if result.get("decision") == "block":
            sys.exit(2)
    else:
        write_hook_output({"decision": "allow"})
    sys.exit(0)


if __name__ == "__main__":
    main()
