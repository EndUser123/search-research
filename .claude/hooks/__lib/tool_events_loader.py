"""Load tool_events from transcript_path for Stop hooks.

Stop hook input does NOT include tool_events field.
This module loads tool events from transcript_path JSONL.

Usage:
    from __lib.tool_events_loader import load_tool_events_from_transcript

    tool_events = load_tool_events_from_transcript(data)
    # Returns list[dict] with standard event schema:
    # {
    #   "name": "Edit|Write|Bash|Skill|...",
    #   "input": {...},
    #   "command": "...",  # for Bash tools
    #   "file_path": "...",  # for Edit/Write tools
    # }
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_tool_events_from_transcript(data: dict[str, Any]) -> list[dict]:
    """Load tool events from transcript_path JSONL.

    Converts transcript tool_use blocks to standard event schema.

    Args:
        data: Stop hook input dict with transcript_path field

    Returns:
        List of event dicts with standard schema:
        - name: tool name
        - input: tool input dict
        - command: command string (for Bash tools)
        - file_path: file path string (for Edit/Write tools)
    """
    transcript_path = data.get("transcript_path", "")
    if not transcript_path:
        return []

    try:
        path = Path(transcript_path)
        if not path.exists():
            return []
        content = path.read_text(encoding="utf-8")
    except OSError:
        return []

    events: list[dict] = []

    for line in content.strip().splitlines():
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg = raw.get("message", raw)
        content_blocks = msg.get("content", raw.get("content", []))

        if not isinstance(content_blocks, list):
            continue

        for block in content_blocks:
            if not isinstance(block, dict):
                continue
            if block.get("type") != "tool_use":
                continue

            tool_name = block.get("name", "")
            tool_input = block.get("input", {})

            event: dict = {
                "name": tool_name,
                "input": tool_input,
            }

            # Extract tool-specific fields
            if tool_name == "Bash":
                event["command"] = tool_input.get("command", "")
            elif tool_name in ("Edit", "Write"):
                # Support both flat and nested input formats
                event["file_path"] = (
                    tool_input.get("file_path", "")
                    or tool_input.get("input", {}).get("file_path", "")
                )
            elif tool_name == "Skill":
                event["skill"] = tool_input.get("skill", "")

            events.append(event)

    return events


def _extract_file_path(event: dict) -> str:
    """Extract file path from event (flat or nested format)."""
    path = event.get("file_path", "")
    if path:
        return str(path)
    inp = event.get("input", {})
    if isinstance(inp, dict):
        path = inp.get("file_path", "")
        if path:
            return str(path)
    return ""