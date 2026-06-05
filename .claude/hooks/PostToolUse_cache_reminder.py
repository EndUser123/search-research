#!/usr/bin/env python3
"""PostToolUse Cache Reminder - Design #2 implementation.

After writing a plugin source file, emit advisory to run bump + reload.
Key requirements:
- Match Write only (not Edit/MultiEdit)
- Resolve plugin name via .claude-plugin/plugin.json parent lookup
- Fire on packages/*/** EXCEPT cache/ and local .claude/hooks/
- Session-scoped plugin-warned set for deduplication
- Fallback to UNKNOWN on extraction failure
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Module-level session state persists across hook invocations
_SESSION_WARNED_PLUGINS: dict[str, bool] = {}


def _resolve_plugin_name(file_path: str) -> str:
    """Resolve plugin name from file path via .claude-plugin/plugin.json parent lookup."""
    try:
        resolved = Path(file_path).resolve()
    except (OSError, ValueError):
        return "UNKNOWN"

    current = resolved.parent
    packages_root = Path("P:/packages")

    for _ in range(20):
        plugin_json = current / ".claude-plugin" / "plugin.json"
        if plugin_json.exists():
            return current.name
        try:
            current.resolve().relative_to(packages_root.resolve())
        except ValueError:
            break
        if current.parent == current:
            break
        current = current.parent

    return "UNKNOWN"


def _is_plugin_source_path(file_path: str) -> bool:
    """Check if file_path is a plugin source file (not cache, not local hooks)."""
    try:
        resolved = Path(file_path).resolve()
        resolved_str = str(resolved)
    except (OSError, ValueError):
        return False

    normalized = resolved_str.replace("\\", "/")

    # Exclude cache paths
    if "/cache/" in normalized:
        return False

    # Exclude local hooks
    claude_hooks = Path("P:/.claude/hooks").resolve()
    try:
        resolved.relative_to(claude_hooks)
        return False
    except ValueError:
        pass

    # Must be under packages/*
    packages_str = str(Path("P:/packages").resolve()).replace("\\", "/")
    if not normalized.startswith(packages_str + "/"):
        return False

    # Extract plugin name
    rest = normalized[len(packages_str) + 1:]
    plugin_name = rest.split("/")[0]

    # Exclude cache directory itself
    if plugin_name == "cache":
        return False

    return bool(plugin_name)


def main() -> None:
    """PostToolUse hook entry point."""
    global _SESSION_WARNED_PLUGINS

    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({}))
        return

    tool_name = input_data.get("name", "")
    tool_input = input_data.get("tool_input", {})
    tool_response = input_data.get("response", {})

    if tool_name != "Write":
        print(json.dumps({}))
        return

    file_path = (
        tool_input.get("path", "")
        or tool_response.get("path", "")
        or os.environ.get("CLAUDE_TOOL_WRITE_FILE", "")
    )

    if not file_path or not _is_plugin_source_path(file_path):
        print(json.dumps({}))
        return

    plugin_name = _resolve_plugin_name(file_path)
    already_warned = _SESSION_WARNED_PLUGINS.get(plugin_name, False)
    _SESSION_WARNED_PLUGINS[plugin_name] = True

    if plugin_name == "UNKNOWN":
        msg = (
            "Edit to plugin source: plugin name could not be resolved from path.\n"
            "  Run: plugin-audit-and-fix.py --bump UNKNOWN + /reload-plugins"
        )
        print(msg)
        print(json.dumps({"plugin": "UNKNOWN", "file": file_path, "suppressed": False}))
        return

    suppress_marker = " [already warned]" if already_warned else ""
    msg = (
        f"Edit to plugin source{suppress_marker}: {file_path}\n"
        f"  Plugin: {plugin_name}\n"
        f"  The running system loads from cache/{plugin_name}/... Run:\n"
        f"    plugin-audit-and-fix.py --bump {plugin_name} + /reload-plugins\n"
        f"  to activate."
    )
    print(msg)
    print(json.dumps({
        "plugin": plugin_name,
        "file": file_path,
        "suppressed": already_warned,
    }))


if __name__ == "__main__":
    main()
