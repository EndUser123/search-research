"""stop_block_log — shared Stop-block diagnostic logging.

Extracted verbatim from cc-aca-authority/__lib/router.py so every subprocess
router can record blocks to the same stop_blocks.jsonl without duplicating the
implementation.

Public API:
    _extract_block_ctx(event, input_data) -> dict
    _log_stop_block(hook_name, reason, child_stderr, ctx) -> None

The leading underscore is intentional: these are internal helpers shared
across routers, not a public API contract.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

_LIB = Path(__file__).resolve().parent
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
from file_lock import _LOCK_FAILURES, append_jsonl_safe


def _diag_dir() -> Path:
    """Resolve the global diagnostics directory (flat-file block logs live here)."""
    env = os.environ.get("CC_DIAGNOSTICS_DIR")
    if env:
        return Path(env)
    return Path("P:/.claude/hooks/logs/diagnostics")


def _response_fingerprint(transcript_path: str, fallback: bytes) -> str:
    """Hash the last assistant message so a block can be tied to the exact response.

    Falls back to hashing the raw Stop payload when the transcript is unreadable,
    which still yields a stable per-turn fingerprint.
    """
    try:
        if transcript_path and Path(transcript_path).exists():
            last_text = ""
            with open(transcript_path, "r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    msg = obj.get("message") if isinstance(obj, dict) else None
                    role = (obj.get("role") if isinstance(obj, dict) else None) or (
                        msg.get("role") if isinstance(msg, dict) else None
                    )
                    if obj.get("type") == "assistant" or role == "assistant":
                        content = (msg or obj).get("content")
                        if isinstance(content, list):
                            parts = [
                                p.get("text", "")
                                for p in content
                                if isinstance(p, dict) and p.get("type") == "text"
                            ]
                            text = "".join(parts)
                        else:
                            text = str(content or "")
                        if text:
                            last_text = text
            if last_text:
                return hashlib.sha256(last_text.encode("utf-8", "replace")).hexdigest()[:16]
    except Exception:
        pass
    return hashlib.sha256(fallback).hexdigest()[:16]


def _extract_block_ctx(event: str, input_data: bytes) -> dict:
    """Build the per-turn context attached to a block-log row."""
    ctx = {
        "event": event,
        "session_id": "",
        "terminal_id": "",
        "transcript_path": "",
        "response_hash": "",
    }
    try:
        payload = json.loads(input_data.decode("utf-8", "replace"))
        if isinstance(payload, dict):
            ctx["session_id"] = str(payload.get("session_id") or "")
            ctx["transcript_path"] = str(payload.get("transcript_path") or "")
            ctx["terminal_id"] = str(
                payload.get("terminal_id") or payload.get("cwd") or ""
            )
    except Exception:
        pass
    ctx["response_hash"] = _response_fingerprint(ctx["transcript_path"], input_data)
    return ctx


def _log_stop_block(
    hook_name: str, reason: str, child_stderr: str, ctx: dict | None
) -> None:
    """Append one diagnosable row per Stop block to stop_blocks.jsonl.

    This is the record that makes "Blocked by hook" attributable: it names the
    gate, the reason, the best-available matched text, and a response fingerprint.
    Only Stop blocks are logged here; PreToolUse blocks have their own canonical
    log (pretooluse_blocks.jsonl). Fail-open: logging never affects the block.
    """
    if not ctx or ctx.get("event") != "Stop":
        return
    try:
        row = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event": "Stop",
            "gate_name": hook_name,
            "reason": (reason or "")[:1000],
            "matched_span": ((child_stderr or reason) or "").strip()[:300],
            "response_hash": ctx.get("response_hash", ""),
            "session_id": ctx.get("session_id", ""),
            "terminal_id": ctx.get("terminal_id", ""),
            "transcript_path": ctx.get("transcript_path", ""),
        }
        diag = _diag_dir()
        diag.mkdir(parents=True, exist_ok=True)
        append_jsonl_safe(diag / "stop_blocks.jsonl", row, ensure_ascii=False)
    except _LOCK_FAILURES:
        # append_jsonl_safe already wrote a dropped-trace sidecar; this is
        # defense-in-depth so a future helper change can't crash the block path.
        pass
