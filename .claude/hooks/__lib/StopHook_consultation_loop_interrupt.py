"""StopHook_consultation_loop_interrupt.py - Detect consultation loops and log to CKS.

At session end (any stop):
1. Reads transcript from Stop event payload
2. Scans for consultation loop pattern: directive -> LLM question -> user repeat -> LLM question
3. If loop detected (counter >= 2): writes sanitized pattern entry to CKS queue
4. Outputs advisory block message (NOT blocking stop)

Feature-gated by CONSULTATION_LOOP_INTERRUPT_ENABLED.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Final

# Feature flag
_ENABLED: Final = os.environ.get("CONSULTATION_LOOP_INTERRUPT_ENABLED", "").lower() in (
    "1",
    "true",
    "yes",
)

# Detection patterns
DIRECTIVE_PATTERNS: Final[list[re.Pattern]] = [
    re.compile(r"(?i)\b(?:consider all|implement|do|execute|start|begin|proceed)\b"),
    re.compile(r"(?i)\b(?:save the? |write an? )\b"),
    re.compile(r"(?i)\b(?:which (?:should |has )?(?:we|i) )\b"),
]

QUESTION_RESPONSE_PATTERNS: Final[list[re.Pattern]] = [
    re.compile(r"\?\s*$"),
    re.compile(r"which (?:would you|do you|should I|should we|i)\b"),
]

# CKS CLI path
CKS_CLI_PATH: Final = "P:/__csf/src/cks/cks_cli.py"

# State file for per-session counter (terminal_id + session_id scoped)
_STATE_DIR: Final = Path(__file__).resolve().parent.parent / "state"


def _get_state_file(terminal_id: str, session_id: str) -> Path:
    """Get path to consultation loop state file."""
    safe_terminal = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(terminal_id))
    safe_session = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(session_id))
    return _STATE_DIR / f"consultation_loop_{safe_terminal}_{safe_session}.json"


def _load_state(terminal_id: str, session_id: str) -> dict:
    """Load consultation loop state for session."""
    state_file = _get_state_file(terminal_id, session_id)
    if state_file.exists():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "consecutive_question_responses": 0,
        "in_question_sequence": False,
        "last_directive": None,
        "injected_directives": [],  # Rate limiting: directives already injected this session
    }


def _save_state(terminal_id: str, session_id: str, state: dict) -> None:
    """Save consultation loop state for session."""
    state_file = _get_state_file(terminal_id, session_id)
    try:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass  # Fail open - state save errors don't block stop


def _extract_terminal_id(data: dict) -> str:
    """Extract terminal_id from hook data."""
    terminal = data.get("terminal_id", "")
    if terminal:
        return str(terminal)
    session = data.get("session", {})
    if isinstance(session, dict):
        terminal = session.get("terminal_id", "")
        if terminal:
            return str(terminal)
    return os.environ.get("CLAUDE_TERMINAL_ID", "")


def _extract_session_id(data: dict) -> str:
    """Extract session_id from hook data."""
    session = data.get("session_id", "")
    if session:
        return str(session)
    session_obj = data.get("session")
    if isinstance(session_obj, dict):
        for key in ("id", "session_id", "sessionId"):
            val = session_obj.get(key)
            if val:
                return str(val)
    return ""


def _extract_transcript(data: dict) -> list[dict]:
    """Extract transcript from hook data."""
    transcript = data.get("transcript", [])
    if isinstance(transcript, list):
        return transcript
    handoff = data.get("handoff_envelope", {})
    if isinstance(handoff, dict):
        transcript = handoff.get("transcript", [])
        if isinstance(transcript, list):
            return transcript
    return []


def _is_directive(text: str) -> bool:
    """Check if text matches directive patterns."""
    if not text:
        return False
    return any(pattern.search(text) for pattern in DIRECTIVE_PATTERNS)


def _is_question_response(text: str) -> bool:
    """Check if text matches question response patterns."""
    if not text:
        return False
    return any(pattern.search(text) for pattern in QUESTION_RESPONSE_PATTERNS)


def _get_last_directive_and_questions(transcript: list[dict]) -> tuple[str | None, int]:
    """Scan transcript for last directive and consecutive question responses after it.

    Returns:
        Tuple of (last_directive_text, consecutive_question_count)
    """
    last_directive: str | None = None
    question_count = 0

    for entry in transcript:
        role = entry.get("role", "")
        content = entry.get("content", "")
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
                elif isinstance(part, str):
                    text_parts.append(part)
            content = " ".join(text_parts)
        elif not isinstance(content, str):
            content = ""

        if role == "user":
            # User message - check if it's a directive
            if _is_directive(content):
                # New directive or repeat - track it
                last_directive = content
            elif question_count > 0:
                # Non-directive user message after questions - reset
                question_count = 0
                last_directive = None

        elif role == "assistant":
            if last_directive is not None and _is_question_response(content):
                question_count += 1
            elif not _is_question_response(content):
                # LLM gave non-question response - reset counter
                question_count = 0
                last_directive = None

    return last_directive, question_count


def _write_cks_queue(pattern_entry: dict) -> None:
    """Write pattern entry to CKS queue for async ingestion.

    CKS ingestion happens via subprocess CLI - NOT via MCP from Stop hook.
    """
    queue_dir = Path(__file__).resolve().parent.parent / "state" / "cks_queue"
    try:
        queue_dir.mkdir(parents=True, exist_ok=True)
        queue_file = queue_dir / f"consultation_loop_{int(time.time() * 1000)}.json"
        queue_file.write_text(json.dumps(pattern_entry, ensure_ascii=False), encoding="utf-8")

        # Trigger CKS ingestion via subprocess CLI
        command = [sys.executable, CKS_CLI_PATH, "add", "--file", str(queue_file)]
        subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        # Fail open - CKS errors don't block stop
        pass


def run(data: dict) -> dict:
    """Main entry point for Stop router.

    Args:
        data: Stop hook payload with transcript and session info.

    Returns:
        dict with 'allow' (bool) and 'reason' (str).
    """
    if not _ENABLED:
        return {"allow": True, "reason": "Consultation loop interrupt disabled"}

    try:
        terminal_id = _extract_terminal_id(data)
        session_id = _extract_session_id(data)
        if not terminal_id or not session_id:
            return {"allow": True, "reason": "No terminal_id or session_id available"}

        transcript = _extract_transcript(data)
        if not transcript:
            return {"allow": True, "reason": "No transcript available"}

        state = _load_state(terminal_id, session_id)
        injected_directives: list[str] = state.get("injected_directives", [])

        last_directive, question_count = _get_last_directive_and_questions(transcript)

        if question_count >= 2:
            # Loop definitively detected - log to CKS
            directive_text = last_directive or ""
            sanitized_directive = directive_text[:200] if directive_text else ""

            pattern_entry = {
                "type": "pattern",
                "title": "Consultation Loop: directive misinterpreted as question",
                "content": (
                    "User gave directive, LLM asked clarifying questions, "
                    "user repeated directive, LLM asked again. "
                    "Pattern indicates LLM needs to recognize delegation signals."
                ),
                "evidence": [
                    sanitized_directive,
                    question_count,
                    0,  # duration not tracked per-session
                ],
                "tags": ["consultation-loop", "delegation-signal", "llm-behavior"],
            }
            _write_cks_queue(pattern_entry)

            # Advisory output - NOT blocking
            # Rate limit: only show once per directive per session
            if sanitized_directive and sanitized_directive not in injected_directives:
                injected_directives.append(sanitized_directive)
                state["injected_directives"] = injected_directives
                _save_state(terminal_id, session_id, state)

                advisory = """
CONSULTATION LOOP DETECTED

You appear to be repeating a directive that the LLM answered with questions.
The LLM should recognize this as a delegation signal and proceed with ranked execution.
Pattern logged to CKS for calibration.
"""
                print(advisory, file=sys.stdout)

        return {"allow": True, "reason": "Consultation loop check complete"}

    except Exception as exc:
        # Fail open - errors don't block stop
        return {"allow": True, "reason": f"Consultation loop interrupt error: {exc}"}
