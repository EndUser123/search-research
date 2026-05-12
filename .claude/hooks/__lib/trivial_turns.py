#!/usr/bin/env python3
"""
trivial_turns - Detect trivial/low-stakes exchanges for gate softening.

Used by Stop gates (epistemic contract, reasoning quality) to skip enforcement
on turns where format nagging is inappropriate and the response carries no
epistemic weight.

Signals:
  1. Turn mode "control" → primary switch (already suppressed in GATE_CLASSES)
  2. Bare numeric/boolean response ("4", "true", "yes") + simple prompt → trivial
  3. Pure acknowledgement < 80 chars ("ok", "done", "thanks") → trivial
  4. Explicit smoke test patterns in prompt → trivial
  5. Contract context: if a contract is active and user is completing it,
     NOT trivial (normal enforcement applies)

Contract completions are NOT trivial — they carry epistemic weight.
"""
from __future__ import annotations

import re
import os
from typing import Literal

# Type alias for clarity
TurnMode = Literal[
    "control", "exploration", "analysis", "plan", "execution-report", "final-answer", "meta"
]


# === Detection signals ===

_I = re.IGNORECASE

# Numeric / boolean lone responses
_NUMERIC_RESPONSE_RE = re.compile(r'^\s*[\d.]+\s*$')
_BOOL_RESPONSE_RE = re.compile(r'^\s*(?:true|false|yes|no|y|n|on|off)\s*$', _I)

# Bare acknowledgement < 80 chars (no format, no analysis)
_SHORT_ACK_RE = re.compile(
    r'^\s*(?:ok|okay|done|thanks?|sure|yep|yeah|sounds good|'
    r'agreed|perfect|great|cool|alright|lgtm|ack|acknowledged|'
    r'ty|thx|cheers|noted|got\s+it|understood|makes\s+sense)\s*$', _I
)

# Smoke test / model-identity patterns in user prompt
_SMOKE_TEST_RE = re.compile(
    r'(?:'
    r'test\s+(?:m27|glm|claude|haiku|opus|sonnet)|'
    r'prove\s+(?:you\'?re?|this\s+is)|'
    r'confirm\s+(?:you\s+can|this\s+works)|'
    r'smoke\s+test|'
    r'health\s+check|'
    r'^ping\b|'
    r'are\s+you\s+there|'
    r'can\s+you\s+hear\s+me|'
    r'model\s+check|'
    r'llm\s+check'
    r')\b',
    _I
)

# Responses with epistemic structure → NOT trivial
_EPISTEMIC_STRUCTURE_RE = re.compile(
    r'\[[\s]*(?:FACT|INFERENCE|RECOMMENDATION|CONCLUSION|UNKNOWN)|'
    r'(?:^|\n)\s*\*\s|\d+\.\s+[A-Z]'  # [FACT]/[INFERENCE], section headers, numbered lists
)


def is_trivial_exchange(
    context: dict,
    response: str,
    turn_mode: TurnMode | None = None,
    contract_active: bool = False,
) -> tuple[bool, str]:
    """
    Detect whether the current exchange is trivial enough to skip quality gates.

    Args:
        context: Stop hook data dict (user_prompt, response, etc.)
        response: The assistant's response string
        turn_mode: Optional turn mode (classified externally)
        contract_active: True if a task contract is currently active

    Returns:
        (is_trivial: bool, reason: str) — reason explains why it is/isn't trivial
    """
    if not response or not response.strip():
        return False, "empty response"

    user_prompt = context.get("user_prompt") or context.get("prompt") or ""
    prompt_words = len(user_prompt.split())

    # --- Signal 1: Turn mode "control" ---
    # This is the primary switch. Quality gates are already suppressed for control
    # in GATE_CLASSES, but we add a double-layer here for belt-and-suspenders.
    if turn_mode == "control":
        return True, "control_mode"

    # --- Signal 5: Contract completion → NOT trivial ---
    # Completing a contract (even with a short response) carries epistemic weight.
    if contract_active:
        return False, "contract_active"

    # --- Signal 2: Bare numeric response ---
    if _NUMERIC_RESPONSE_RE.match(response) or _BOOL_RESPONSE_RE.match(response):
        if prompt_words < 15:
            return True, "bare_numeric"
        return True, "bare_numeric_simple_prompt"

    # --- Signal 3: Short acknowledgement ---
    stripped = response.strip()
    if len(stripped) < 80 and _SHORT_ACK_RE.match(stripped):
        # Double-check: no epistemic structure present
        if not _EPISTEMIC_STRUCTURE_RE.search(response):
            # Belt-and-suspenders: only skip if the PROMPT was also trivial.
            # "done" in response to "fix the bug in Stop.py" carries epistemic weight.
            if prompt_words < 15:
                return True, "short_ack"

    # --- Signal 4: Smoke test pattern in prompt (only at start, ~80 chars) ---
    if _SMOKE_TEST_RE.search(user_prompt[:80]):
        return True, "smoke_test"

    # Sampled non-trivial telemetry: provides tuning baseline for future heuristic work
    # Log every non-trivial decision so precision/recall can be measured
    try:
        log_non_trivial_classification("generic", "not_trivial", turn_mode, response)
    except Exception:
        pass

    return False, "not_trivial"


def log_trivial_skip(gate_name: str, reason: str, turn_mode: TurnMode, response: str) -> None:
    """Log a trivial exchange skip to diagnostics."""
    try:
        import logging
        logger = logging.getLogger(f"trivial_turns.{gate_name}")
        logger.info(
            f"[{gate_name}] SKIP — trivial_exchange reason={reason} "
            f"turn_mode={turn_mode} response_len={len(response)}"
        )
    except Exception:
        pass  # Fail open


def log_non_trivial_classification(
    gate_name: str, reason: str, turn_mode: TurnMode | None, response: str
) -> None:
    """Log a non-trivial classification for tuning baseline.

    Sampled telemetry: logs every decision with reason so future heuristic
    tuning can be evidence-based rather than anecdotal.
    """
    try:
        import logging
        logger = logging.getLogger(f"trivial_turns.{gate_name}")
        logger.info(
            f"[{gate_name}] NON_TRIVIAL — reason={reason} "
            f"turn_mode={turn_mode} response_len={len(response)}"
        )
    except Exception:
        pass  # Fail open


# === Self-test ===
if __name__ == "__main__":
    cases = [
        # (context, response, turn_mode, contract_active, expected_trivial, expected_reason)
        # Numeric answers
        ({"user_prompt": "what is 2+2"}, "4", None, False, True, "bare_numeric"),
        ({"user_prompt": "how many items"}, "42", None, False, True, "bare_numeric"),
        ({"user_prompt": "count the files"}, "17", None, False, True, "bare_numeric"),
        # Control mode
        ({"user_prompt": "stop"}, "understood", "control", False, True, "control_mode"),
        ({"user_prompt": "actually fix it"}, "done", "control", False, True, "control_mode"),
        # Short acknowledgements
        ({"user_prompt": "does this work"}, "yes", None, False, True, "bare_numeric"),  # bool wins over ack
        ({"user_prompt": "is it done"}, "done", None, False, True, "short_ack"),
        ({"user_prompt": "okay proceed"}, "ok", None, False, True, "short_ack"),
        # Smoke tests
        ({"user_prompt": "test m27"}, "I am working correctly.", None, False, True, "smoke_test"),
        ({"user_prompt": "are you there"}, "yes, I am here", None, False, True, "smoke_test"),
        # Contract active → NOT trivial
        ({"user_prompt": "finish the task"}, "done", None, True, False, "contract_active"),
        # Non-trivial: long response with format
        ({"user_prompt": "explain why"}, "[FACT]\n- evidence here", None, False, False, "not_trivial"),
        # Non-trivial: short but not an ack pattern (prompt must be substantial)
        ({"user_prompt": "fix the bug in Stop.py carefully"}, "done", None, False, True, "short_ack"),  # 5 words < 15
        # Non-trivial: "done" to a complex substantive request (prompt ≥ 15 words)
        ({"user_prompt": "Analyze and fix the concurrency bug in the task scheduler where race conditions cause duplicate execution"}, "done", None, False, False, "not_trivial"),
        # Non-trivial: response too long
        ({"user_prompt": "thanks"}, "you're welcome, let me know if you need anything else!", None, False, False, "not_trivial"),
    ]

    failed = 0
    for ctx, resp, mode, active, expected, expected_reason in cases:
        result, reason = is_trivial_exchange(ctx, resp, mode, active)
        status = "✓" if result == expected and reason == expected_reason else "✗"
        if result != expected or reason != expected_reason:
            failed += 1
            print(f"{status} response={resp!r:30s} expected={expected}/{expected_reason} got={result}/{reason}")
        else:
            print(f"{status} {resp!r:30s} → trivial={result} ({reason})")

    print(f"\n{'All passed' if failed == 0 else f'{failed} FAILED'}")