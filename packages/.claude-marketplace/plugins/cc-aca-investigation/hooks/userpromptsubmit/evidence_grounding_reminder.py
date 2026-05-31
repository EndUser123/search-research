from __future__ import annotations
# --- plugin bootstrap ---
import sys
from pathlib import Path
_l = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in sys.path: sys.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

"""Evidence Grounding Reminder — conditional epistemic priming for UserPromptSubmit.

Fires every N turns (default: 5) with a rotated lightweight reminder to prime
evidence-grounded language before generation. Designed to avoid habituation
through rotation and frequency control.

Configuration:
  EVIDENCE_GROUNDING_ENABLED     Enable/disable (default: true)
  EVIDENCE_GROUNDING_FREQUENCY  Fire every N turns (default: 5)
"""


import os
import threading
from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

ENABLED = os.environ.get("EVIDENCE_GROUNDING_ENABLED", "true").lower() in ("1", "true", "yes")
FREQUENCY = max(1, int(os.environ.get("EVIDENCE_GROUNDING_FREQUENCY", "5")))

# Rotated variants — each under 30 tokens to avoid habituation
VARIANTS = [
    "Evidence-grounded responses are more credible.",
    "Cite [Tier N]: for causal claims.",
    "Attribute outcomes to observable events.",
    "Use hedging language when not directly evidenced.",
]

# Thread-safe turn counter per session
_counter_lock = threading.Lock()
_counters: dict[str, int] = {}


def _get_counter(session_id: str) -> int:
    with _counter_lock:
        return _counters.get(session_id, 0)


def _inc_counter(session_id: str) -> int:
    with _counter_lock:
        n = _counters.get(session_id, 0) + 1
        _counters[session_id] = n
        return n


def _advance(session_id: str) -> int:
    """Return the turn number for this session, incrementing atomically."""
    return _inc_counter(session_id)


@register_hook("evidence_grounding_reminder", priority=11.5)
def evidence_grounding_reminder(context: HookContext) -> HookResult:
    """Inject a rotated, lightweight epistemic reminder every N turns.

    Priority 11.5 — after cognitive_enhancers (11.0) but before
    verify_before_claim (12.0).
    """
    if not ENABLED:
        return HookResult.empty()

    session_id = str(context.session_id or "default")
    turn = _advance(session_id)

    # Fire every FREQUENCY turns
    if turn % FREQUENCY != 0:
        return HookResult.empty()

    # Rotate through variants
    variant_idx = (turn // FREQUENCY) % len(VARIANTS)
    variant = VARIANTS[variant_idx]

    return HookResult(context=variant, tokens=len(variant) // 4)
