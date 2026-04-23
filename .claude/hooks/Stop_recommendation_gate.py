#!/usr/bin/env python3
"""
Stop_recommendation_gate.py

Detects when the LLM presents options/choices WITHOUT a recommendation.
Returns a systemMessage advisory so the next response includes one.

Trigger condition: 2+ numbered options + decision-delegation phrase + no recommendation language.
Severity: warn (systemMessage) — not block. Advisory, not enforcement.
"""

from __future__ import annotations
import json
import os

import re
import time
from pathlib import Path

try:
    from __lib import prompt_session_state
except Exception:  # pragma: no cover - fail open if helper unavailable
    prompt_session_state = None

# Any of these signals a recommendation is already present → PASS
RECOMMENDATION_PATTERNS = [
    r"\brecommend\b",
    r"\bmy recommendation\b",
    r"\bgo with\b",
    r"\bbest option\b",
    r"\bbest approach\b",
    r"\boptimal\b",
    r"\bi['\u2019]d (?:choose|pick|suggest|go with)\b",
    r"\bi would (?:choose|pick|suggest|recommend)\b",
    r"\bstart with option\b",
]

# These phrases signal "user must choose" — delegation without guidance
DELEGATION_PATTERNS = [
    r"which (?:would you like|do you prefer|option|approach)",
    r"would you like (?:me to implement|to proceed with|to use|to start|any of)",
    r"want me to (?:implement|proceed|start|use|apply)",
    r"should i (?:proceed|implement|start|use|apply)",
    r"let me know which",
    r"which of these",
    r"do you want (?:me to|to proceed)",
    r"your (?:choice|preference|call|decision)",
    r"choose (?:between|from|which|one)",
    r"pick (?:one|which|the|an option)",
]
QUESTION_PREFIXES = (
    "what ",
    "why ",
    "how ",
    "which ",
    "should ",
    "can ",
    "could ",
    "would ",
    "do ",
)

DIRECTION_PATTERNS = [
    re.compile(r"^\s*(?:yes|yep|yeah|go ahead|proceed|approved|do it|ship it)\s*$", re.IGNORECASE),
    re.compile(
        r"\b(?:go with|proceed with|choose|pick|select|take|use)\s+(?:option\s*)?[a-z0-9]+\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:implement|apply|build|fix|do)\s+(?:it|that|this|option|approach|plan)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:my|the)\s+direction\s+is\b", re.IGNORECASE),
]

STATE_SUBDIR = "stop_recommendation_gate"
STATE_TTL_SECONDS = 14 * 24 * 60 * 60  # 14 days

NEW_BREACH_MESSAGE = (
    "[RECOMMENDATION GATE] You presented multiple options and delegated the decision "
    "without stating a recommendation.\n\n"
    "Rule: When presenting options, ALWAYS include your recommendation with reasoning. "
    "Never make the user ask 'what's your recommendation?'.\n\n"
    "This reminder is now persistent and will fire on every Stop until the user gives explicit direction."
)

PERSISTENT_PENDING_MESSAGE = (
    "[RECOMMENDATION GATE] Recommendation follow-through is still pending.\n\n"
    "Keep giving a clear recommendation with reasoning each turn until the user explicitly provides direction."
)


def _has_option_list(text: str) -> bool:
    """True if 2+ list items found (numbered or bulleted)."""
    numbered = re.findall(r"^\s*\d+\.\s+\S", text, re.MULTILINE)
    if len(numbered) >= 2:
        return True
    bulleted = re.findall(r"^\s*[-*]\s+\S", text, re.MULTILINE)
    return len(bulleted) >= 2


def _has_delegation(text: str) -> bool:
    """True if response delegates the decision to the user."""
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in DELEGATION_PATTERNS)


def _has_recommendation(text: str) -> bool:
    """True if response already contains recommendation language."""
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in RECOMMENDATION_PATTERNS)

def _safe_id(value: str | None) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", (value or "").strip()) or "unknown"


def _resolve_session_id(data: dict | None) -> str:
    payload = data or {}
    return (
        str(
            payload.get("session_id")
            or payload.get("sessionId")
            or payload.get("CLAUDE_SESSION_ID")
            or os.environ.get("CLAUDE_SESSION_ID", "")
        )
        .strip()
    )


def _resolve_terminal_id(data: dict | None) -> str:
    payload = data or {}
    return (
        str(
            payload.get("terminal_id")
            or payload.get("terminalId")
            or payload.get("CLAUDE_TERMINAL_ID")
            or os.environ.get("CLAUDE_TERMINAL_ID", "")
        )
        .strip()
    )


def _state_path(data: dict | None) -> Path | None:
    session_id = _resolve_session_id(data)
    if not session_id:
        return None
    terminal_id = _resolve_terminal_id(data) or "terminal_unknown"
    base = Path(os.environ.get("CSF_STATE_DIR", "P:/.claude/state"))
    return base / STATE_SUBDIR / f"recommendation_pending_{_safe_id(session_id)}_{_safe_id(terminal_id)}.json"


def _load_pending_state(path: Path | None) -> dict:
    if path is None or not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _write_pending_state(path: Path | None) -> None:
    if path is None:
        return
    payload = {"pending": True, "updated_at": int(time.time())}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")
    except OSError:
        return


def _clear_pending_state(path: Path | None) -> None:
    if path is None:
        return
    try:
        if path.exists():
            path.unlink()
    except OSError:
        return


def _pending_active(state: dict) -> bool:
    if not state.get("pending"):
        return False
    updated_at = int(state.get("updated_at", 0))
    if not updated_at:
        return False
    return (int(time.time()) - updated_at) <= STATE_TTL_SECONDS


def _extract_latest_user_text(data: dict | None) -> str:
    payload = data or {}
    for key in ("user_prompt", "prompt", "message", "last_user_message"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    if prompt_session_state is not None:
        try:
            prompt, status = prompt_session_state.read_latest_prompt(payload)
            if status == "ok" and prompt.strip():
                return prompt.strip()
        except Exception:
            pass

    entries = payload.get("transcript_entries")
    if not isinstance(entries, list):
        entries = payload.get("transcript")
    if isinstance(entries, list):
        for entry in reversed(entries):
            if not isinstance(entry, dict):
                continue
            if str(entry.get("type", "")).lower() == "user":
                msg = entry.get("message")
                if isinstance(msg, dict):
                    content = msg.get("content")
                    if isinstance(content, str) and content.strip():
                        return content.strip()
                text = entry.get("text")
                if isinstance(text, str) and text.strip():
                    return text.strip()
    return ""


def _is_question_like(text: str) -> bool:
    normalized = " ".join(text.lower().split())
    return normalized.endswith("?") or normalized.startswith(QUESTION_PREFIXES)


def _has_user_direction(text: str) -> bool:
    if not text.strip():
        return False
    normalized = " ".join(text.lower().split())
    if _is_question_like(normalized):
        return bool(DIRECTION_PATTERNS[0].search(normalized))
    return any(pattern.search(normalized) for pattern in DIRECTION_PATTERNS)


def check_recommendation(response: str, data: dict | None = None) -> dict | None:
    """
    Check for options-without-recommendation pattern and persist reminder state.

    Returns:
        dict with 'systemMessage' if violation detected, else None.
    """
    state_file = _state_path(data)
    state = _load_pending_state(state_file)
    pending = _pending_active(state)

    if state and not pending:
        _clear_pending_state(state_file)

    latest_user_text = _extract_latest_user_text(data)
    if pending and _has_user_direction(latest_user_text):
        _clear_pending_state(state_file)
        pending = False

    has_breach = bool(
        response
        and len(response) >= 80
        and _has_option_list(response)
        and _has_delegation(response)
        and not _has_recommendation(response)
    )

    if has_breach:
        _write_pending_state(state_file)
        return {"systemMessage": NEW_BREACH_MESSAGE}

    if pending:
        return {"systemMessage": PERSISTENT_PENDING_MESSAGE}

    return None
