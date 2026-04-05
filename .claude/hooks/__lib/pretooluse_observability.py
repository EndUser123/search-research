from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path


def truncate_text(value: object, limit: int = 2000) -> str:
    text = "" if value is None else str(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def safe_id(value: object) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(value or ""))


def resolve_session_id(data: dict) -> str:
    session_obj = data.get("session")
    if isinstance(session_obj, dict):
        for key in ("id", "session_id", "sessionId"):
            value = session_obj.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    for key in ("session_id", "sessionId", "CLAUDE_SESSION_ID"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def resolve_terminal_id(data: dict) -> str:
    for key in ("terminal_id", "terminalId", "CLAUDE_TERMINAL_ID"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def extract_tool_fields(tool_input: object) -> dict[str, str]:
    payload = tool_input if isinstance(tool_input, dict) else {}
    command = truncate_text(payload.get("command", ""), 1000)
    prompt = truncate_text(payload.get("prompt", ""), 1000)
    file_path = truncate_text(
        payload.get("file_path") or payload.get("path") or "",
        500,
    )
    return {
        "command": command,
        "prompt": prompt,
        "file_path": file_path,
        "tool_input_preview": truncate_text(
            command or prompt or file_path or json.dumps(payload, ensure_ascii=False),
            1000,
        ),
    }


def append_jsonl(log_path: Path, entry: dict) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def build_pretooluse_block_entry(
    data: dict,
    *,
    blocking_hook: str,
    reason: object,
    event_kind: str,
    source_hook: str | None = None,
    child_exit_code: int | None = None,
    raw_stdout: object = "",
    raw_stderr: object = "",
    artifact_path: str = "",
    active_turn_id: str = "",
) -> dict:
    tool_name = str(data.get("tool_name", "") or "")
    tool_fields = extract_tool_fields(data.get("tool_input"))
    session_id = resolve_session_id(data)
    terminal_id = resolve_terminal_id(data)

    return {
        "schema": "pretooluse_block",
        "version": 2,
        "event_id": str(uuid.uuid4()),
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "event_kind": event_kind,
        "tool_name": tool_name,
        "blocking_hook": blocking_hook,
        "source_hook": source_hook or blocking_hook,
        "child_exit_code": child_exit_code,
        "session_id": session_id,
        "terminal_id": terminal_id,
        "prompt_id": str(data.get("prompt_id", "") or ""),
        "cwd": str(data.get("cwd", "") or ""),
        "active_turn_id": active_turn_id,
        "artifact_path": artifact_path,
        "reason": truncate_text(reason, 4000),
        "reason_preview": truncate_text(reason, 300),
        "raw_stdout_preview": truncate_text(raw_stdout, 1200),
        "raw_stderr_preview": truncate_text(raw_stderr, 1200),
        **tool_fields,
    }


def extract_runner_input_metadata(payload_text: str) -> dict[str, str]:
    try:
        payload = json.loads(payload_text) if payload_text.strip() else {}
    except json.JSONDecodeError:
        payload = {}

    tool_fields = extract_tool_fields(payload.get("tool_input"))
    return {
        "session_id": resolve_session_id(payload),
        "terminal_id": resolve_terminal_id(payload),
        "prompt_id": str(payload.get("prompt_id", "") or ""),
        "tool_name": str(payload.get("tool_name", "") or ""),
        "cwd": str(payload.get("cwd", "") or ""),
        **tool_fields,
    }
