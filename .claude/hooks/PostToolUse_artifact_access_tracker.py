"""
.. deprecated::
   Canonical source moved to
   ``cc-aca-observability/__lib/posttooluse/artifact_access_tracker.py``.

   This file is now a compatibility shim that delegates to the plugin-owned
   implementation.  All behavior changes land in the canonical module.
   Do not add new consumers of this path.

Re-exported symbols:
   track_tool_use(session_id, terminal_id, tool_name, tool_input)
   _extract_file_paths(tool_name, tool_input)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Resolve the plugin __lib/ directory relative to this file's location
# in the project tree: P:/.claude/hooks/ → P:/packages/.claude-marketplace/plugins/cc-aca-observability/__lib/
_hooks_root = Path(__file__).resolve().parent
_project_root = _hooks_root.parent.parent  # P:\
_plugin_lib = _project_root / "packages" / ".claude-marketplace" / "plugins" / "cc-aca-observability" / "__lib"

if _plugin_lib.exists() and str(_plugin_lib) not in sys.path:
    sys.path.insert(0, str(_plugin_lib))

from posttooluse.artifact_access_tracker import (
    _extract_file_paths,  # noqa: F401 — re-exported for existing consumers
    track_tool_use,       # noqa: F401 — re-exported for existing consumers
)

__all__ = [
    "_extract_file_paths",
    "track_tool_use",
]

# Standalone entry point preserved for backward compatibility
if __name__ == "__main__":
    data = json.loads(sys.stdin.read())

    session_id = data.get("session_id", "")
    terminal_id = data.get("terminal_id", "") or os.environ.get("CLAUDE_TERMINAL_ID", "")
    tool_name = data.get("name", "") or data.get("tool_name", "")
    tool_input = data.get("input", {}) or data.get("tool_input", {})

    if tool_name:
        track_tool_use(session_id, terminal_id, tool_name, tool_input)

    print("{}")
    sys.exit(0)
