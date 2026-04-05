"""Verify-before-claiming reminder for existence/absence queries.

Fires when the user prompt contains signals that Claude might need to
assert whether a file, hook, feature, or resource exists or is absent.

The injected reminder is generic (not context-specific) to avoid
brittleness and injection fatigue.

Conditions to fire (both must be true):
  1. Prompt contains an existence-query pattern
  2. Cooldown window has elapsed since last injection for this session

Configuration:
  VERIFY_BEFORE_CLAIM_ENABLED           Enable/disable hook (default: true)
  VERIFY_BEFORE_CLAIM_COOLDOWN_SECS     Min seconds between injections
                                        per session (default: 120)
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

from .base import HookContext, HookResult
from .registry import register_hook

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ENABLED = os.environ.get("VERIFY_BEFORE_CLAIM_ENABLED", "true").lower() in ("1", "true", "yes")
COOLDOWN_SECS = int(os.environ.get("VERIFY_BEFORE_CLAIM_COOLDOWN_SECS", "120"))

_STATE_DIR = Path(__file__).resolve().parent.parent / "session_data"

# ---------------------------------------------------------------------------
# Patterns: existence / absence queries in user prompts
# ---------------------------------------------------------------------------

# Each group covers a distinct signal that the response may involve an
# existence or absence judgment.
_EXISTENCE_PATTERNS: list[re.Pattern[str]] = [
    # Direct existence questions
    re.compile(r"\bis\s+there\s+(a|an|any)\b", re.IGNORECASE),
    re.compile(r"\bare\s+there\s+(any|some)\b", re.IGNORECASE),
    re.compile(r"\bdo\s+we\s+have\s+(a|an|any)?\b", re.IGNORECASE),
    re.compile(r"\bdoes\s+\w+\s+exist\b", re.IGNORECASE),
    re.compile(r"\bexist[s]?\b.*\?", re.IGNORECASE),

    # Locating a resource
    re.compile(r"\bwhere\s+is\s+the\b", re.IGNORECASE),
    re.compile(r"\bwhere'?s\s+the\b", re.IGNORECASE),
    re.compile(r"\bwhich\s+(file|hook|module|class|function|script|config)\b", re.IGNORECASE),

    # Implementation / existence checks
    re.compile(r"\bimplemented\b", re.IGNORECASE),           # "is the feature implemented?"
    re.compile(r"\bbeen\s+(added|created|implemented|written)\b", re.IGNORECASE),
    re.compile(r"\bdoes\s+the\s+(hook|system|code|file|module)\b", re.IGNORECASE),

    # Gap / audit framing
    re.compile(r"\bwhat'?s?\s+missing\b", re.IGNORECASE),
    re.compile(r"\bwhy\s+\S*n'?t\b", re.IGNORECASE),        # "why doesn't / why isn't / why won't"
    re.compile(r"\bwhy\s+does\s+not\b", re.IGNORECASE),
    re.compile(r"\bcheck\s+if\b", re.IGNORECASE),
    re.compile(r"\bverify\s+(?:that|if|whether)\b", re.IGNORECASE),
    re.compile(r"\bsee\s+if\b", re.IGNORECASE),
    re.compile(r"\bconfirm\s+(?:that|if|whether)\b", re.IGNORECASE),

    # User suspects something is absent
    re.compile(r"\b(missing|absent|lacking)\b.*\?", re.IGNORECASE),
    re.compile(r"\bno\s+(hook|file|test|config|handler|module)\s+for\b", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# Cooldown state
# ---------------------------------------------------------------------------

def _safe_id(value: str | None) -> str:
    """Sanitise session/terminal id for use in a filename."""
    if not value:
        return "unknown"
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value.strip())


def _cooldown_path(session_id: str | None, terminal_id: str | None) -> Path:
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    key = f"{_safe_id(session_id)}__{_safe_id(terminal_id)}"
    return _STATE_DIR / f"verify_before_claim_cooldown_{key}.json"


def _is_on_cooldown(session_id: str | None, terminal_id: str | None) -> bool:
    """Return True if we fired recently enough to suppress this injection."""
    if COOLDOWN_SECS <= 0:
        return False
    path = _cooldown_path(session_id, terminal_id)
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        last_fired = float(data.get("last_fired", 0))
        return (time.time() - last_fired) < COOLDOWN_SECS
    except Exception:
        return False


def _record_fired(session_id: str | None, terminal_id: str | None) -> None:
    """Write a timestamp so the next call can check the cooldown."""
    path = _cooldown_path(session_id, terminal_id)
    try:
        path.write_text(
            json.dumps({"last_fired": time.time()}),
            encoding="utf-8",
        )
    except Exception:
        pass  # Never block on state write failure


# ---------------------------------------------------------------------------
# Reminder text
# ---------------------------------------------------------------------------

_REMINDER = (
    "**VERIFY BEFORE CLAIMING** — If your response involves asserting that a "
    "file, hook, feature, or resource *does* or *does not* exist: use Read, "
    "Glob, Grep, or Bash (ls/find) to verify *before* making the claim. "
    "The Stop hook will block unverified absence claims, costing an extra turn."
)

# ---------------------------------------------------------------------------
# Hook
# ---------------------------------------------------------------------------

def _matches_existence_query(prompt: str) -> bool:
    for pattern in _EXISTENCE_PATTERNS:
        if pattern.search(prompt):
            return True
    return False


@register_hook("verify_before_claim", priority=12.0)
def verify_before_claim(context: HookContext) -> HookResult:
    """Inject a verify-before-claiming reminder on existence-query turns.

    Priority 12.0 — fires after critical gates (< 10.0) but before
    heavy context injectors (>= 15.0).
    """
    if not ENABLED:
        return HookResult.empty()

    if not _matches_existence_query(context.prompt):
        return HookResult.empty()

    if _is_on_cooldown(context.session_id, context.terminal_id):
        return HookResult.empty()

    _record_fired(context.session_id, context.terminal_id)
    return HookResult(context=_REMINDER, tokens=len(_REMINDER) // 4)
