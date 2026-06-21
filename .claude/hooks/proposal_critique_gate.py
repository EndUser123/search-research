#!/usr/bin/env python3
"""proposal_critique_gate.py — block a proposal presented with NO self-critique.

WHY (measured 2026-06-20, session b2014a6e): across the user's transcripts, 53%
of the turns where the user had to send a "please critically review" reminder
were proposals I made with ZERO self-critique markers. The user's interventions
are a request for a self-review PASS by default, not a quality judgment — so this
gate is a PRESENCE check: a proposal/recommendation turn must also contain at
least one named failure mode / falsification, or it is blocked before the user
sees it.

SCOPE (deliberate):
  - Catches the ZERO-critique bucket (the measured 53%).
  - Does NOT judge critique quality/depth — a shallow-but-present critique passes.
    Catching "shallow critique that misses the fatal flaw" needs a quality layer
    that the same session measured as non-discriminating (LLM adequacy ≈0), so it
    is intentionally out of scope here. This gate raises the floor, nothing more.

This is a quality-class Stop gate: turn-mode suppression (control/exploration/
trivial) and the regen circuit breaker are applied by Stop.py around it, so it
cannot livelock or nag on non-analytical turns.

Disable: PROPOSAL_CRITIQUE_GATE_ENABLED=false
Per-turn bypass: include --skip-critique-gate in the prompt.
"""
from __future__ import annotations

import os
import re

ENABLED = os.environ.get("PROPOSAL_CRITIQUE_GATE_ENABLED", "true").lower() == "true"
BYPASS_TOKEN = "--skip-critique-gate"
_MIN_LEN = 200  # below this, treat as trivial (not a substantive proposal)

# A proposal/recommendation is being made. High-signal recommendation framing —
# deliberately NOT bare "should" (too noisy); FP cost here is low (just asks for a
# critique sentence) but we still avoid flooding every instructional answer.
_PROPOSAL = re.compile(
    r"\bI\s+recommend\b"
    r"|\bmy\s+recommendation\b"
    r"|\bI'?d\s+recommend\b"
    r"|\bI\s+propose\b"
    r"|\bmy\s+proposal\b"
    r"|\bI\s+suggest\s+(?:we|you|that)\b"
    r"|\bthe\s+fix\s+is\b"
    r"|\bthe\s+solution\s+is\b"
    r"|\bthe\s+best\s+(?:option|approach|choice|fix|path)\s+(?:is|would\s+be)\b"
    r"|\brecommended\s+(?:option|approach|fix)\b"
    r"|\bOption\s+[A-Z0-9]\b",
    re.IGNORECASE,
)

# At least one of these must be present for the proposal to pass — a named failure
# mode, a falsification condition, or an explicit downside/risk of the proposal.
_CRITIQUE = re.compile(
    r"would\s+be\s+wrong\s+if"
    r"|\bwrong\s+if\b"
    r"|falsif"
    r"|failure\s+mode"
    r"|fails?\s+(?:when|if)\b"
    r"|could\s+(?:fail|break|misfire|backfire|regress)"
    r"|counter-?example"
    r"|the\s+(?:main\s+)?(?:risk|flaw|weakness|catch|downside|trade-?off|limitation|drawback)"
    r"|\brisk:"
    r"|\bcaveat"
    r"|gameable"
    r"|false\s+positive"
    r"|this\s+(?:might|may|could)\s+not"
    r"|wouldn'?t\s+(?:catch|work|help)"
    r"|\bFP\b",
    re.IGNORECASE,
)

# Vacuous "critique" filler that satisfies _CRITIQUE without saying anything —
# "Risk: none", "no caveats", "risk: low", "no real downside". External review
# (2026-06-21) flagged these as a Goodhart bypass. detect() strips these and
# re-checks: if removing them eliminates ALL critique signal, the critique was hollow.
_VACUOUS = re.compile(
    r"(?:the\s+)?(?:main\s+)?(?:risk|caveat|downside|trade-?offs?|drawback|flaw|weakness|limitation)s?"
    r"\s*(?:[:\-]|is|are|=)?\s*"
    r"(?:none|n/?a|nil|nothing|minimal|negligible|low|not\s+applicable|none\s+known|unknown)\b"
    r"|no\s+(?:real\s+|significant\s+|major\s+|known\s+|obvious\s+)?"
    r"(?:risks?|caveats?|downsides?|trade-?offs?|drawbacks?|flaws?|weakness(?:es)?|limitations?)\b",
    re.IGNORECASE,
)

_BLOCK_MSG = (
    "Proposal/recommendation presented without a self-critique. Before showing a "
    "proposal, include at least one NAMED failure mode and a falsification "
    "condition — e.g. \"This would be wrong if ___\" plus the concrete signal that "
    "would disconfirm it, or the main risk/downside of the recommended option. "
    "Add the self-critique, then present. "
    "(disable: PROPOSAL_CRITIQUE_GATE_ENABLED=false; one-turn bypass: --skip-critique-gate)"
)


def detect(response_text: str, prompt: str = "") -> dict | None:
    """Return a block dict when a proposal lacks any self-critique, else None."""
    if not ENABLED:
        return None
    text = response_text or ""
    # Bypass is sourced ONLY from the user prompt — NEVER the assistant response.
    # External review (2026-06-21, glm-5.2 + M3 consensus): a response-text bypass
    # let a turn self-unblock by emitting the token, defeating the gate's purpose.
    if BYPASS_TOKEN in (prompt or ""):
        return None
    if len(text) < _MIN_LEN:
        return None
    if not _PROPOSAL.search(text):
        return None  # no proposal → gate does not apply
    if _CRITIQUE.search(text):
        # Goodhart guard: strip vacuous filler ("Risk: none", "no caveats") and
        # re-check. If removing it eliminates all critique signal, the critique
        # was hollow → block anyway.
        if _CRITIQUE.search(_VACUOUS.sub(" ", text)):
            return None  # genuine (non-vacuous) self-critique present → pass
    return {"decision": "block", "reason": _BLOCK_MSG}


def _extract_response_and_prompt(data: dict) -> tuple[str, str]:
    """Pull the assistant response + user prompt from a Stop payload.

    Mirrors _run_semantic_critic's extraction: prefer transcript, fall back to
    flat fields.
    """
    response_text = ""
    user_prompt = ""
    if isinstance(data.get("transcript"), list):
        for msg in reversed(data["transcript"]):
            content = msg.get("content", "") if isinstance(msg, dict) else ""
            if not isinstance(content, str):
                continue
            if msg.get("role") == "assistant" and not response_text:
                response_text = content
            elif msg.get("role") == "user" and not user_prompt:
                user_prompt = content
    if not response_text:
        response_text = data.get("response", data.get("raw_response", "")) or ""
    if not user_prompt:
        user_prompt = data.get("user_prompt", data.get("prompt", "")) or ""
    return response_text, user_prompt


def run(data: dict) -> dict | None:
    response_text, user_prompt = _extract_response_and_prompt(data)
    return detect(response_text, user_prompt)


if __name__ == "__main__":
    import json
    import sys

    try:
        print(json.dumps(run(json.loads(sys.stdin.read()))))
    except json.JSONDecodeError:
        print(json.dumps(None))
