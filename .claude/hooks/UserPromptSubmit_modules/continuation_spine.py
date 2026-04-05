"""Continuation Spine - Minimal Re-anchoring for Short Affirmatives

When user responds with short affirmative (yes/ok/proceed) to a proposal,
inject minimal re-anchoring spine and suppress other cognitive enhancers.

Design principle: Replace heavy cognitive framework injections with targeted
re-anchoring for continuation turns.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# ---------------------------------------------------------------------------
# Short Affirmative Detector
# ---------------------------------------------------------------------------

_SHORT_AFFIRMATIVE_RE = re.compile(
    r"^\s*(yes|yep|yeah|ok|okay|sure|sounds good|go ahead|proceed|do it|that works|looks good)\s*[.!?]?\s*$",
    re.IGNORECASE,
)


def is_short_affirmative(prompt: str) -> bool:
    """Check if prompt is a short affirmative response.

    Cheap guard: very short messages only (word count <= 6).
    """
    if not prompt:
        return False
    # Word count guard - reject longer messages that have their own intent signal
    if len(prompt.strip().split()) > 6:
        return False
    return bool(_SHORT_AFFIRMATIVE_RE.match(prompt.strip()))


# ---------------------------------------------------------------------------
# Transcript Reader
# ---------------------------------------------------------------------------

def get_last_assistant_message(transcript_path: str) -> str | None:
    """Read last assistant message from transcript JSONL file.

    Args:
        transcript_path: Path to transcript JSONL file

    Returns:
        Last assistant message text, or None if not found
    """
    path = Path(transcript_path)
    if not path.is_file():
        return None

    try:
        # Read whole file once; JSONL is usually small enough
        lines = path.read_text(encoding="utf-8").splitlines()
        for line in reversed(lines):
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("type") == "assistant":
                parts = entry.get("message", {}).get("content", [])
                texts = [p.get("text", "") for p in parts if p.get("type") == "text"]
                msg = "\n".join(t.strip() for t in texts if t.strip())
                if msg:
                    return msg
        return None
    except Exception:
        # Fail open - if we can't read transcript, don't fire spine
        return None


# ---------------------------------------------------------------------------
# Proposal Detector
# ---------------------------------------------------------------------------

_PROPOSAL_MARKERS_RE = re.compile(
    r"\b(I'll|I could|Would you like|We can|Options?:|Option\s+\d+|Step\s+\d+|Here(?:'s| are) (?:a|some) plan|Plan:)",
    re.IGNORECASE,
)


def is_concrete_proposal(text: str) -> bool:
    """Check if text contains a concrete proposal or plan.

    Args:
        text: Text to analyze

    Returns:
        True if text appears to be a proposal/plan, False otherwise
    """
    if not text:
        return False

    # Check for proposal markers
    if _PROPOSAL_MARKERS_RE.search(text):
        return True

    # Fallback: obvious numbered/bulleted plan without explicit markers
    if any(line.strip().startswith(("- ", "* ", "1.", "1)")) for line in text.splitlines()):
        return True

    return False


# ---------------------------------------------------------------------------
# Continuation Spine Hook
# ---------------------------------------------------------------------------

# Cognitive enhancers to suppress when spine fires
_COGNITIVE_ENHANCERS = [
    "assumption_surfacing",
    "outcome_anchoring",
    "inversion_prompting",
    "chestertons_fence",
    "calibrated_confidence",
    "socratic_decomposition",
]

_SPINE_TEXT = "Restate the goal and planned steps before proceeding."


@register_hook("continuation_spine", priority=10.0)
def continuation_spine(context: HookContext) -> HookResult:
    """Inject minimal re-anchoring spine for short affirmative responses to proposals.

    Runs before cognitive enhancers (priority 10.0 vs 11.2-11.8).
    When spine fires, returns dict with suppress signal to prevent redundant injections.
    """
    prompt = context.prompt or ""
    transcript_path = context.data.get("transcript_path", "")

    # Guard: must be short affirmative
    if not is_short_affirmative(prompt):
        return HookResult.empty()

    # Guard: must have last assistant message
    last_assistant = get_last_assistant_message(transcript_path)
    if not last_assistant:
        return HookResult.empty()

    # Guard: last assistant must contain proposal
    if not is_concrete_proposal(last_assistant):
        return HookResult.empty()

    # Fire spine: inject re-anchoring and suppress cognitive enhancers
    return HookResult(
        context={
            "additionalContext": _SPINE_TEXT,
            "suppress": _COGNITIVE_ENHANCERS,
        },
        tokens=len(_SPINE_TEXT) // 4,
        priority=10.0,
    )
