"""Shared transcript_path JSONL reader for Stop hooks.

Claude Code Stop hook input does NOT include transcript_entries.
Use this module to parse transcript_path JSONL instead.

Usage:
    entries = read_transcript(data)  # list of dicts with role, type, text
    user_messages = [e for e in entries if e["role"] == "user"]
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_transcript(data: dict[str, Any]) -> list[dict[str, str]]:
    """Parse transcript_path JSONL into a flat list of entries.

    Each entry has:
        role: "user" | "assistant" | "system"
        type: "message" | "system-reminder" | "tool_result" | "tool_use"
        text: extracted text content (empty string if none found)
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

    entries: list[dict[str, str]] = []

    for line in content.strip().splitlines():
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            continue

        role = raw.get("role", "")
        msg_type = raw.get("type", "")
        message = raw.get("message", raw)
        message_content = message.get("content", raw.get("content", []))

        is_assistant = (
            (msg_type == "message" and role == "assistant")
            or msg_type == "assistant"
            or role == "assistant"
        )
        is_user = role == "user" or (msg_type == "message" and role == "user")

        if is_assistant:
            if isinstance(message_content, list):
                for block in message_content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_use":
                        entries.append({
                            "role": "assistant",
                            "type": "tool_use",
                            "text": "",
                            "name": block.get("name", ""),
                            "input": block.get("input", {}),
                        })
                    elif block.get("type") == "text":
                        entries.append({
                            "role": "assistant",
                            "type": "text",
                            "text": block.get("text", ""),
                        })
            elif isinstance(message_content, str) and message_content.strip():
                entries.append({
                    "role": "assistant",
                    "type": "text",
                    "text": message_content,
                })

        elif is_user:
            is_tool_result = msg_type == "tool_result" or (
                isinstance(message_content, list)
                and any(
                    isinstance(b, dict) and b.get("type") == "tool_result"
                    for b in message_content
                )
            )

            if is_tool_result:
                entries.append({"role": "user", "type": "tool_result", "text": ""})
            elif msg_type == "system-reminder":
                entries.append({"role": "system", "type": "system-reminder", "text": ""})
            else:
                text = ""
                if isinstance(message_content, list):
                    text = " ".join(
                        b.get("text", "")
                        for b in message_content
                        if isinstance(b, dict) and b.get("type") == "text"
                    )
                elif isinstance(message_content, str):
                    text = message_content
                entries.append({
                    "role": "user",
                    "type": "message",
                    "text": text.strip(),
                })

    return entries


def get_user_messages(data: dict[str, Any]) -> list[str]:
    """Return all real user message texts from transcript, in order."""
    return [
        e["text"]
        for e in read_transcript(data)
        if e["role"] == "user" and e["type"] == "message" and e.get("text")
    ]


def get_latest_user_text(data: dict[str, Any]) -> str:
    """Return the most recent user message text, or empty string."""
    messages = get_user_messages(data)
    return messages[-1] if messages else ""


def get_assistant_tool_uses(data: dict[str, Any]) -> list[dict]:
    """Return all assistant tool_use blocks from transcript."""
    return [
        e for e in read_transcript(data)
        if e.get("role") == "assistant" and e.get("type") == "tool_use"
    ]
