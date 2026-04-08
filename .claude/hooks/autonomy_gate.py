# P:\.claude\hooks\autonomy_gate.py
"""
Autonomy Gate — Enforcing Execution Directives

Stateless Stop hook that blocks deferral patterns after explicit execution signals.
When user gives autonomous execution signal (e.g., trailing "0"), AI must NOT defer back with
"should I proceed?" or offer path choices. Must either proceed directly or say "cannot comply".

Constitutional compliance:
- Stateless design (no shared mutable state)
- Fail-open default (ambiguous input allows execution)
- Stdlib-only (no external APIs)
- Multi-terminal safe (payload-based evaluation only)
"""

import json
import re
import sys
from difflib import SequenceMatcher
from typing import Any, Dict


def _similar(a: str, b: str) -> float:
    """Calculate sequence similarity ratio between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


# Templates match the specific bad behaviors from the MiniMax transcript.
# User asked "Implement Domain 6a now 0" but AI asked "Should I proceed with Domain 6, or skip to Domain 7?"
DEFER_TEMPLATES = [
    "Should I proceed with Domain",
    "Should I proceed with",
    "Should I proceed",
    "Should we proceed",
    "Should I skip to Domain",
    "Should I skip",
    "skip to Domain",
    "or should I skip",
    "do you want me to proceed",
    "would you like me to",
]

# Regexes to catch common deferral phrasings while staying narrow.
DEFER_PATTERNS = [
    r"\bshould\b.*\bproceed\b",
    r"\bshould\b.*\bskip\b",
    r"\bskip to\b.*\bdomain\b",
    r"\bproceed\b.*\bnext\b",
    r"\bwould you like me to\b",
    r"\bdo you want me to\b",
]

# UNVERIFIED THRESHOLD: Requires calibration data from test corpus of real deferral examples.
# See reasoning_flaws.md: "Arbitrary thresholds - Do not invent constants with no justification."
# Future work: Collect 50+ examples, calculate similarity distribution, set threshold based on data.
SIMILARITY_THRESHOLD = 0.70  # UNVERIFIED - needs calibration


def is_autonomy_signal(user_text: str) -> bool:
    """
    Detect execution signal in user input.

    Current scope: Trailing "0" meaning "execute all".
    Example: "Implement Domain 6a now 0"

    Future expansion: Could add "!!exec", "--yes", etc. as additional signals.
    """
    text = user_text.rstrip()
    if not text:
        return False
    # Treat trailing '0' on its own line or at end as execution directive.
    if text.endswith("0"):
        return True
    return False


def response_defers_decision(response: str) -> bool:
    """
    Returns True if the assistant response looks like it is deferring back to the user
    (asking whether to proceed/skip, offering path choice) instead of executing.

    This is deliberately narrow: we care about *meta* deferral, not normal questions.

    Renamed from draft_defers_decision() to match actual payload field names (assistant_response).
    See adversarial LOGIC-001 finding.
    """
    lower = response.lower()

    # Regex pass
    for pattern in DEFER_PATTERNS:
        if re.search(pattern, lower, flags=re.MULTILINE):
            return True

    # Similarity to known bad templates
    for template in DEFER_TEMPLATES:
        if _similar(response, template) >= SIMILARITY_THRESHOLD:
            return True

    return False


def evaluate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Core pure function: (payload) -> decision dict.

    Expected payload shape (from Stop_router.py:531-534):
    {
      "prompt": "user message text",  # or "user_prompt"
      "assistant_response": "full response text",  # or "response"
      ...other fields...
    }

    Constitutional: Fail-open on ambiguity - if we don't have enough data, allow execution.
    """
    # Use actual payload field names from Stop_router.py (corrected from proposal's "assistant_draft")
    user_prompt = payload.get("prompt", "") or payload.get("user_prompt", "") or ""
    response = payload.get("assistant_response", "") or payload.get("response", "") or ""

    # Fail-open if we don't have enough data
    if not user_prompt or not response:
        return {
            "continue": True,
            "reason": "autonomy_gate: missing user_prompt or response, failing open",
        }

    if not is_autonomy_signal(user_prompt):
        return {
            "continue": True,
            "reason": "autonomy_gate: no autonomy signal in user input",
        }

    if not response_defers_decision(response):
        return {
            "continue": True,
            "reason": "autonomy_gate: no deferral pattern detected in response",
        }

    # Block: this is the specific violation we care about.
    return {
        "continue": False,
        "reason": (
            "Autonomy violation: user issued an execution directive (e.g. '0'), "
            "but response defers back to the user instead of executing."
        ),
    }


def run(data: Dict[str, Any]) -> Dict[str, Any] | None:
    """In-process validator protocol for Stop_router."""
    decision = evaluate(data)
    if decision.get("continue", True):
        return None
    return {
        "block": True,
        "reason": str(decision.get("reason", "")),
        "blocking_hook": "autonomy_gate.py",
    }


def main() -> None:
    """
    Hook entrypoint. Reads a single JSON object from stdin, writes a single JSON object
    to stdout, and exits 0 (pass) or 2 (block) per Stop router conventions.

    Never writes to stderr - Claude Code treats stderr as error output.
    """
    try:
        data = json.load(sys.stdin)
    except Exception:
        # Fail-open on malformed input - don't break user's workflow
        json.dump(
            {
                "continue": True,
                "reason": "autonomy_gate: could not parse stdin JSON, failing open",
            },
            sys.stdout,
        )
        sys.exit(0)

    decision = evaluate(data)

    # Never write to stderr; Claude Code treats it as error
    json.dump(decision, sys.stdout)

    if decision.get("continue", True):
        sys.exit(0)
    else:
        # Exit 2 = intentional block in Stop router ecosystem
        sys.exit(2)


if __name__ == "__main__":
    main()
