"""Shared detector for recommendation/optimality prompts and response compliance.

Single source of truth for two related questions:

1. ``is_recommendation_request(prompt)`` -- did the user ask for a recommendation,
   the "best"/"optimal" approach, or the highest-ROI action? Used by the
   UserPromptSubmit advisory injector (recommendation_rubric_injector.py) to remind
   the model to compare options, and by the Stop-side shadow recorder
   (Stop_recommendation_compliance.py) to decide whether a turn is in scope.

2. ``assess_compliance(response)`` -- did the response actually name >=2 options and a
   selection criterion? Used by the shadow recorder to log whether the
   recommendation followed the rubric.

Scoring overlaps conceptually with the epistemic plugin's
``verification/recommendation_rubric.py`` (assess_recommendation), but this module is
intentionally self-contained: coupling a local hook to a plugin-internal path/version
is more fragile than a small, stable, documented regex set. Keep the two in rough sync
if the rubric definition changes.
"""

from __future__ import annotations

import re

__all__ = ["is_recommendation_request", "assess_compliance"]

# ---------------------------------------------------------------------------
# Prompt-side: is the user asking for a recommendation / "best" / "optimal"?
# ---------------------------------------------------------------------------

_REQUEST_PATTERNS = [
    r"\bis\s+(?:that|this|it)\s+(?:the\s+)?optimal\b",
    r"\boptimal\s+(?:solution|approach|way|fix|design|choice|path)\b",
    r"\b(?:the\s+)?best\s+(?:way|approach|option|solution|choice|path|design)\b",
    r"\bwhat'?s?\s+the\s+best\b",
    r"\bhighest[\s-]roi\b",
    r"\bnext\s+highest\b",
    r"\bwhat\s+do\s+you\s+recommend\b",
    r"\bwhat\s+would\s+you\s+recommend\b",
    r"\byour\s+recommendation\b",
    r"\bwhich\s+(?:option|approach|one|path|design)\b",
    r"\bshould\s+(?:we|i)\s+\w+",
    r"\bwhat'?s?\s+the\s+(?:right|better|correct)\s+(?:way|approach|option)\b",
]

_COMPILED_REQUEST = [re.compile(p, re.IGNORECASE) for p in _REQUEST_PATTERNS]


def is_recommendation_request(prompt: str) -> bool:
    """Return True if the prompt asks for a recommendation / optimal / best option."""
    if not prompt:
        return False
    return any(rx.search(prompt) for rx in _COMPILED_REQUEST)


# ---------------------------------------------------------------------------
# Response-side: did the recommendation name >=2 options AND a selection criterion?
# ---------------------------------------------------------------------------

_OPTIONS_PATTERN = re.compile(
    r"\b(?:alternativ|option\s|another\s+(?:option|approach)|instead|either\b|"
    r"versus\b|vs\.?\b|or\s+you\s+could|two\s+(?:paths|options)|"
    r"option\s+a\b|option\s+1\b|trade-?off\s+between)",
    re.IGNORECASE,
)

_CRITERION_PATTERN = re.compile(
    r"\b(?:criteri|axis|optimi[sz]e|optimizing|trade-?off|reversibilit|"
    r"per\s+unit|lower\s+(?:risk|cost)|highest\s+roi|because\b|in\s+order\s+to|"
    r"selection\s+criterion|on\s+that\s+axis|the\s+metric)\b",
    re.IGNORECASE,
)


def assess_compliance(response: str) -> dict[str, bool]:
    """Score a response for recommendation-rubric compliance (advisory only).

    Returns a dict with ``has_options``, ``has_criterion``, and ``compliant``
    (both present). Heuristic and noisy by design -- meant for trend measurement
    across many turns, not per-turn judgement.
    """
    text = response or ""
    has_options = bool(_OPTIONS_PATTERN.search(text))
    has_criterion = bool(_CRITERION_PATTERN.search(text))
    return {
        "has_options": has_options,
        "has_criterion": has_criterion,
        "compliant": has_options and has_criterion,
    }
