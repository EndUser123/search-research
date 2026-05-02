"""Advisory-only recommendation quality assessment.

Separates recommendation quality from factual verification.
This module never blocks — it produces advisory metadata only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

__all__ = [
    "RecommendationAssessment",
    "assess_recommendation",
]

# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------

_GOAL_PATTERN = re.compile(
    r"\b(?:goal|objective|purpose|aim|target)\b.*\b(?:is|are|to)\b",
    re.IGNORECASE,
)

_ASSUMPTION_PATTERN = re.compile(
    r"\b(?:assuming|assumption|if|provided that|given that|suppose)\b",
    re.IGNORECASE,
)

_TRADEOFF_PATTERN = re.compile(
    r"\b(?:trade-?off|downside|drawback|cost|sacrifice|at the expense of)\b",
    re.IGNORECASE,
)

_ALTERNATIVE_PATTERN = re.compile(
    r"\b(?:alternative|instead|or you could|another option|other approach)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Data structure
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RecommendationAssessment:
    """Quality assessment for a recommendation claim."""

    claim_id: str | int
    has_goal: bool
    has_assumptions: bool
    has_tradeoffs: bool
    has_downside: bool
    has_alternative_not_chosen: bool
    notes: str


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def assess_recommendation(claim: Any) -> RecommendationAssessment:
    """Assess recommendation quality (advisory only, never blocking).

    Checks whether a recommendation claim includes:
    - A stated goal or objective
    - Explicit assumptions
    - Acknowledged tradeoffs/downsides
    - Alternatives not chosen

    Args:
        claim: Claim object with .id and .text attributes, or a raw string.
    """
    claim_id = getattr(claim, "id", "")
    text = getattr(claim, "text", str(claim))

    has_goal = bool(_GOAL_PATTERN.search(text))
    has_assumptions = bool(_ASSUMPTION_PATTERN.search(text))
    has_tradeoffs = bool(_TRADEOFF_PATTERN.search(text))
    has_downside = has_tradeoffs  # Same detector for now
    has_alt = bool(_ALTERNATIVE_PATTERN.search(text))

    quality_parts: list[str] = []
    if has_goal:
        quality_parts.append("states goal")
    if has_assumptions:
        quality_parts.append("names assumptions")
    if has_tradeoffs:
        quality_parts.append("acknowledges tradeoffs")
    if has_alt:
        quality_parts.append("considers alternatives")

    if not quality_parts:
        notes = "recommendation lacks goal, assumptions, tradeoffs, or alternatives"
    else:
        notes = "; ".join(quality_parts)

    return RecommendationAssessment(
        claim_id=claim_id,
        has_goal=has_goal,
        has_assumptions=has_assumptions,
        has_tradeoffs=has_tradeoffs,
        has_downside=has_downside,
        has_alternative_not_chosen=has_alt,
        notes=notes,
    )
