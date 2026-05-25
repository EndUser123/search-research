#!/usr/bin/env python3
"""
Veridical integrity gate -- behavioral sycophancy detection via external LLM.

Detects epistemic integrity violations that regex-based detectors miss:
- Agreeing with user premise before verifying
- Backfilling evidence after premature agreement
- Oscillating positions based on user tone rather than new evidence
- Misinterpreting tool outputs to validate user assumptions

This module is imported by Stop_semantic_critic.py and called before the
diagnostic scope gate, using its own agreement-pattern scope gate and
per-session cap.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

VERIDICAL_GATE_CAP: int = int(os.environ.get("VERIDICAL_GATE_CAP", "5"))
VERIDICAL_TIMEOUT_SEC: int = int(os.environ.get("VERIDICAL_TIMEOUT_SEC", "15"))
VERIDICAL_CIRCUIT_BREAKER_LIMIT: int = int(
    os.environ.get("VERIDICAL_CIRCUIT_BREAKER_LIMIT", "3")
)
VERIDICAL_COOLDOWN_SEC: int = int(os.environ.get("VERIDICAL_COOLDOWN_SEC", "300"))

_VERIDICAL_COUNTS: dict[str, int] = {}

# ---------------------------------------------------------------------------
# Agreement patterns (scope gate)
# ---------------------------------------------------------------------------

_B = "\\b"

_VERIDICAL_AGREEMENT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(_B + r"you're\s+right" + _B, re.IGNORECASE),
    re.compile(_B + r"you are\s+right" + _B, re.IGNORECASE),
    re.compile(_B + r"that's\s+correct" + _B, re.IGNORECASE),
    re.compile(_B + r"exactly" + _B, re.IGNORECASE),
    re.compile(_B + r"agreed?" + _B, re.IGNORECASE),
    re.compile(_B + r"I\s+agree" + _B, re.IGNORECASE),
    re.compile(_B + r"good\s+point" + _B, re.IGNORECASE),
    re.compile(_B + r"fair\s+enough" + _B, re.IGNORECASE),
    re.compile(_B + r"yes,\s+that'?s?" + _B, re.IGNORECASE),
    re.compile(_B + r"I\s+see\s+your\s+point" + _B, re.IGNORECASE),
    re.compile(_B + r"that\s+makes\s+sense" + _B, re.IGNORECASE),
    re.compile(_B + r"absolutely" + _B, re.IGNORECASE),
    re.compile(_B + r"you're\s+absolutely" + _B, re.IGNORECASE),
    re.compile(_B + r"I\s+stand\s+corrected" + _B, re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# Prompt loader
# ---------------------------------------------------------------------------

_PROMPT_CACHE: Optional[str] = None


def _load_prompt() -> str:
    global _PROMPT_CACHE
    if _PROMPT_CACHE is not None:
        return _PROMPT_CACHE
    prompt_path = Path(__file__).parent / "veridical_prompt.txt"
    try:
        _PROMPT_CACHE = prompt_path.read_text(encoding="utf-8").strip()
    except OSError:
        _logger.warning("veridical gate: prompt file not found at %s", prompt_path)
        _PROMPT_CACHE = ""
    return _PROMPT_CACHE


# ---------------------------------------------------------------------------
# Scope gate -- does the response contain agreement language?
# ---------------------------------------------------------------------------


def _has_agreement_pattern(response: str) -> bool:
    if not response:
        return False
    return any(p.search(response) for p in _VERIDICAL_AGREEMENT_PATTERNS)


# ---------------------------------------------------------------------------
# Transcript builder
# ---------------------------------------------------------------------------


def _build_transcript(tool_events: list[dict], response: str) -> str:
    """Build a concise transcript from the last 6 tool events + response."""
    lines: list[str] = []
    recent = tool_events[-6:] if len(tool_events) > 6 else tool_events
    for ev in recent:
        name = ev.get("name", "")
        inp = ev.get("input", {})
        if isinstance(inp, dict):
            summary = json.dumps(inp, default=str)[:200]
        else:
            summary = str(inp)[:200]
        lines.append(f"[tool:{name}] {summary}")
    if response:
        lines.append(f"[response] {response[:500]}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# LLM response parser
# ---------------------------------------------------------------------------

_TICKS = chr(96) + chr(96) + chr(96)


def _parse_llm_response(raw: str) -> Optional[dict]:
    """Strip code fences and parse JSON from LLM response."""
    text = raw.strip()
    # Strip code fences
    if text.startswith(_TICKS):
        # Remove opening fence (with optional language tag)
        first_newline = text.index("\n") if "\n" in text else len(text)
        text = text[first_newline + 1 :]
        if text.endswith(_TICKS):
            text = text[: -len(_TICKS)]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        _logger.debug("veridical gate: failed to parse LLM response: %s", text[:200])
        return None


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------

_CIRCUIT_FAILURES: dict[str, list[float]] = {}


def _circuit_open(session_id: str) -> bool:
    """Return True if the circuit breaker is open for this session."""
    failures = _CIRCUIT_FAILURES.get(session_id, [])
    now = time.monotonic()
    # Expire old failures outside cooldown window
    failures = [t for t in failures if now - t < VERIDICAL_COOLDOWN_SEC]
    _CIRCUIT_FAILURES[session_id] = failures
    return len(failures) >= VERIDICAL_CIRCUIT_BREAKER_LIMIT


def _record_failure(session_id: str) -> None:
    failures = _CIRCUIT_FAILURES.get(session_id, [])
    failures.append(time.monotonic())
    _CIRCUIT_FAILURES[session_id] = failures


# ---------------------------------------------------------------------------
# Per-session cap
# ---------------------------------------------------------------------------


def _check_cap(session_id: str) -> bool:
    """Return True if the session has reached its invocation cap."""
    return _VERIDICAL_COUNTS.get(session_id, 0) >= VERIDICAL_GATE_CAP


def _increment_cap(session_id: str) -> None:
    _VERIDICAL_COUNTS[session_id] = _VERIDICAL_COUNTS.get(session_id, 0) + 1


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

_BF_AGENT_PATH = Path(r"P:\packages\cc-skills-architect\skills\bf\bf_agent.py")


def check_veridical_integrity(
    response_text: str,
    transcript: str,
    session_key: str,
    mistral_api_key: str = "",
) -> Optional[dict]:
    """Main entry point for veridical integrity checking.

    Returns None to allow (no opinion), or a dict with allow/reason.
    Called by Stop_semantic_critic.py before the diagnostic scope gate.
    """
    # Missing input -- nothing to check
    if not response_text or not response_text.strip():
        return None

    # Scope gate: skip if no agreement language detected
    if not _has_agreement_pattern(response_text):
        return None

    # Per-session cap reached
    if _check_cap(session_key):
        _logger.debug("veridical gate: cap reached for session %s", session_key)
        return None

    # Circuit breaker open
    if _circuit_open(session_key):
        _logger.debug("veridical gate: circuit open for session %s", session_key)
        return None

    # Load prompt template
    system_prompt = _load_prompt()
    if not system_prompt:
        _logger.warning("veridical gate: empty prompt, skipping")
        return None

    # Build the user payload for the LLM
    user_payload = json.dumps(
        {
            "response_to_audit": response_text[:1500],
            "conversation_context": (transcript or "")[:3000],
        },
        default=str,
    )

    # Call Mistral via bf_agent.py subprocess with --stdin
    try:
        import subprocess

        cmd = [
            sys.executable,
            str(_BF_AGENT_PATH),
            "--stdin",
            "--model",
            "mistral-large-latest",
            "--timeout",
            str(VERIDICAL_TIMEOUT_SEC),
        ]
        stdin_payload = json.dumps(
            {
                "system": system_prompt,
                "user": user_payload,
                "api_key": mistral_api_key,
            }
        )

        _logger.debug(
            "veridical gate: calling bf_agent for session %s", session_key
        )
        result = subprocess.run(
            cmd,
            input=stdin_payload,
            capture_output=True,
            text=True,
            timeout=VERIDICAL_TIMEOUT_SEC + 5,
        )

        if result.returncode != 0:
            _logger.warning(
                "veridical gate: bf_agent exited %d: %s",
                result.returncode,
                result.stderr[:200],
            )
            _record_failure(session_key)
            return None

        parsed = _parse_llm_response(result.stdout)
        if parsed is None:
            _logger.debug("veridical gate: could not parse LLM response")
            _record_failure(session_key)
            return None

        _increment_cap(session_key)

        if parsed.get("ok") is False:
            reason = parsed.get("reason", "behavioral sycophancy detected")
            return {"allow": False, "reason": f"veridical_gate: {reason}"}

        # LLM said ok or unsure -- allow
        return None

    except subprocess.TimeoutExpired:
        _logger.warning("veridical gate: bf_agent timed out for session %s", session_key)
        _record_failure(session_key)
        return None
    except Exception as exc:
        _logger.warning(
            "veridical gate: fail-open on exception for session %s: %s",
            session_key,
            exc,
        )
        return None
