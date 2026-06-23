#!/usr/bin/env python3
"""PostToolUse hook: Record observed facts from tool outputs into terminal-scoped state.

Input: JSON on stdin with tool_name, tool_input, tool_output fields.
Output: exit 0 always (non-blocking).
"""
from __future__ import annotations



# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P

def _normalize_stdout(data: dict) -> dict:
    """Normalize hook output to Claude Code Zod-valid schema."""
    if data.get('decision') == 'allow':
        return {'decision': 'approve'}
    if data.get('decision') == 'block':
        return {'decision': 'block', 'reason': data.get('reason', '')}
    if 'allow' in data:
        if data['allow'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'continue' in data:
        if data['continue'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'ok' in data:
        return {'decision': 'approve'}
    return data


_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


import json
import sys
from pathlib import Path

# Add src to path

from state import detect_terminal_id
from fact_extraction import extract_from_tool_output
from provenance import record_observation


def main() -> None:
    try:
        hook_input = json.load(sys.stdin)

        tool_name = hook_input.get("tool_name", "")
        tool_input = hook_input.get("tool_input", "")
        tool_output = hook_input.get("tool_output", "")

        if tool_name not in ("Read", "Bash", "Grep", "read_file", "bash_command", "grep"):
            sys.exit(0)

        terminal_id = detect_terminal_id()
        file_path = tool_input if tool_name in ("Read", "read_file") else ""
        facts = extract_from_tool_output(tool_name, tool_input, tool_output, file_path)

        for fact in facts:
            record_observation(fact, terminal_id)

        sys.exit(0)

    except Exception as e:
        print(f"PostToolUse error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
