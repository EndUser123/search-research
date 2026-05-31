#!/usr/bin/env python3
"""PostToolUse hook: Record observed facts from tool outputs into terminal-scoped state.

Input: JSON on stdin with tool_name, tool_input, tool_output fields.
Output: exit 0 always (non-blocking).
"""
from __future__ import annotations


# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---




# --- plugin bootstrap ---
import sys
from pathlib import Path


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
