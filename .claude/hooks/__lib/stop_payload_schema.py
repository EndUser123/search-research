"""Frozen Stop-payload field set and factory functions.

Field set verified against live Stop payload 2026-07-02 on Claude Code
2.1.199.  On CC upgrade, re-verify against the hooks reference
(code.claude.com/docs/en/hooks) before trusting.
"""

STOP_PAYLOAD_KEYS = frozenset({
    "session_id",
    "transcript_path",
    "hook_event_name",
    "stop_hook_active",
    "last_assistant_message",
    "cwd",
    "effort",
    "permission_mode",
    "background_tasks",
    "session_crons",
    "terminal_id",
    "output_text",
    "response",
})


def make_stop_payload(transcript_path: str, **overrides) -> dict:
    """Build a dict matching the real Stop payload shape.

    Unknown override keys raise ValueError.
    """
    unknown = set(overrides) - STOP_PAYLOAD_KEYS
    if unknown:
        raise ValueError(
            f"Unknown stop payload key(s): {', '.join(sorted(unknown))}"
        )
    payload = {
        "session_id": "test-session",
        "transcript_path": transcript_path,
        "hook_event_name": "Stop",
        "stop_hook_active": False,
        "last_assistant_message": "",
        "cwd": "P:/",
        "terminal_id": "test",
        "output_text": "",
        "response": "",
        "permission_mode": "default",
        "effort": {"level": "high"},
        "background_tasks": [],
        "session_crons": [],
    }
    payload.update(overrides)
    return payload


def make_transcript_line(role: str, text: str, is_meta: bool = False) -> dict:
    """Build a transcript JSONL entry for a simple text message."""
    entry = {
        "type": role,
        "message": {
            "role": role,
            "content": [{"type": "text", "text": text}],
        },
    }
    if is_meta:
        entry["isMeta"] = True
    return entry


def make_tool_result_line(content: str, tool_use_id: str = "t1") -> dict:
    """Build a transcript JSONL entry for a tool_result."""
    return {
        "type": "user",
        "message": {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": tool_use_id, "content": content}],
        },
    }
