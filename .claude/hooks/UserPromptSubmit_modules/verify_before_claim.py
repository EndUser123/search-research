"""Verify-before-concluding reminder for existence, ranking, and end-to-end queries.

Fires when the user prompt contains signals that Claude might need to:
  - assert whether something exists or is absent
  - rank or compare approaches
  - make an end-to-end reliability or dependency-chain judgment

The injected reminder is generic enough to avoid brittle prompt coupling,
but specific enough to force decomposition before a confident conclusion.

Conditions to fire (both must be true):
  1. Prompt contains an existence/comparative/end-to-end pattern
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
# Patterns: existence / absence / comparative / end-to-end queries in user prompts
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

_COMPARATIVE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bwhich\s+(method|option|approach|path|workflow)\b", re.IGNORECASE),
    re.compile(r"\b(compare|comparison|vs\.?|versus)\b", re.IGNORECASE),
    re.compile(r"\b(rank|ranking|ranked|reorder this)\b", re.IGNORECASE),
    re.compile(r"\b(best|better|worse|worst)\b", re.IGNORECASE),
    re.compile(r"\bmost\s+(reliable|practical|robust|effective|likely)\b", re.IGNORECASE),
    re.compile(r"\bleast\s+(reliable|practical|robust|effective|likely)\b", re.IGNORECASE),
    re.compile(r"\bhighest[- ]throughput\b", re.IGNORECASE),
    re.compile(r"\bbot[- ]detect(?:ed|ion)\b", re.IGNORECASE),
    re.compile(r"\brate[- ]limit(?:ed|ing)?\b", re.IGNORECASE),
    re.compile(r"\bbypass(?:es|ing)?\b", re.IGNORECASE),
    re.compile(r"\bend[- ]to[- ]end\b", re.IGNORECASE),
    re.compile(r"\bdepends?\s+on\b", re.IGNORECASE),
    re.compile(r"\bdependency\s+chain\b", re.IGNORECASE),
    re.compile(r"\bprerequisite\b", re.IGNORECASE),
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
    "**VERIFY BEFORE CONCLUDING** — This prompt may require an existence, ranking, or "
    "end-to-end judgment. Before answering: "
    "state the decision criterion explicitly; list prerequisite dependencies and "
    "upstream bottlenecks; separate verified facts from inference; and do not rank "
    "a downstream step above a prerequisite without explaining the dependency chain. "
    "Use Read, Glob, Grep, or Bash to verify the critical links first."
)

# ---------------------------------------------------------------------------
# Hook
# ---------------------------------------------------------------------------

def _matches_existence_query(prompt: str) -> bool:
    for pattern in _EXISTENCE_PATTERNS:
        if pattern.search(prompt):
            return True
    for pattern in _COMPARATIVE_PATTERNS:
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
