"""Conflict Arbiter - Resolves conflicts between cognitive and reasoning systems.

This module implements precedence rules when cognitive framework guidance
and reasoning mode guidance push in different directions.

Precedence Rules:
1. Fast mode (#fast): Caps cognitive enhancers to 1-2 lightweight frameworks
2. High-confidence override: High-confidence mode selections (confidence >= 3) override low-confidence cognitive selections (confidence < 2)
3. Token budget cap: Total injection tokens limited to configurable maximum (default: 500)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from UserPromptSubmit_modules.cognitive_enhancers import Enhancer


@dataclass(frozen=True)
class ArbiterResult:
    """Result from conflict arbitration.

    Attributes:
        enhancers: Adjusted list of cognitive enhancers (may be reduced or empty)
        mode_selection: Adjusted reasoning mode (may be None if overridden)
        reasoning_confidence: Confidence of reasoning mode selection (0-4)
        token_budget_applied: Whether token budget cap was applied
        rationale: Human-readable explanation of arbitration decisions
    """

    enhancers: list[Enhancer]
    mode_selection: str | None
    reasoning_confidence: int
    token_budget_applied: bool
    rationale: str


# Lightweight cognitive frameworks (can be used in fast mode)
_LIGHTWEIGHT_ENHANCERS = {
    "assumption_surfacing",
    "outcome_anchoring",
}


def resolve_conflict(
    enhancers: list[Enhancer],
    mode_selection: str | None,
    reasoning_confidence: int,
    prompt_mode: str | None,
    token_limit: int = 500,
) -> ArbiterResult:
    """Resolve conflicts between cognitive and reasoning systems.

    Args:
        enhancers: Selected cognitive enhancers from cognitive frameworks hook
        mode_selection: Selected reasoning mode (or None if not selected)
        reasoning_confidence: Confidence of reasoning mode selection (0-4)
        prompt_mode: User-specified mode override (#fast, #deep, #rca, or None)
        token_limit: Maximum tokens to allow for combined injections

    Returns:
        ArbiterResult with adjusted enhancers, mode selection, and rationale
    """
    # Start with original selections
    adjusted_enhancers = list(enhancers)
    adjusted_mode = mode_selection
    rationale_parts = []

    # Rule 1: Fast mode caps cognitive enhancers
    if prompt_mode == "fast":
        # Filter to lightweight enhancers only
        adjusted_enhancers = [
            e for e in enhancers if e.name in _LIGHTWEIGHT_ENHANCERS
        ]
        # Cap at 2
        adjusted_enhancers = adjusted_enhancers[:2]

        if len(adjusted_enhancers) < len(enhancers):
            removed = len(enhancers) - len(adjusted_enhancers)
            rationale_parts.append(
                f"Fast mode: Removed {removed} cognitive enhancer(s), kept lightweight frameworks only"
            )

    # Rule 2: High-confidence reasoning mode overrides low-confidence cognitive selections
    # (Reasoning confidence >= 3 AND cognitive confidence is low)
    # Note: Cognitive confidence is implicit in number of enhancers selected
    # (more enhancers = higher confidence, but we don't have explicit confidence score)
    if mode_selection and reasoning_confidence >= 3:
        # High-confidence reasoning overrides cognitive
        # Keep only 1-2 essential cognitive enhancers
        if len(adjusted_enhancers) > 2:
            adjusted_enhancers = adjusted_enhancers[:2]
            rationale_parts.append(
                f"High-confidence reasoning mode ({mode_selection}, confidence={reasoning_confidence}): "
                f"Reduced cognitive enhancers to {len(adjusted_enhancers)}"
            )

    # Rule 3: Token budget cap (estimate tokens for both injections)
    # Estimate: each enhancer ~100 tokens, reasoning mode ~50 tokens
    estimated_tokens = len(adjusted_enhancers) * 100 + (50 if mode_selection else 0)

    if estimated_tokens > token_limit:
        # Need to reduce cognitive enhancers
        max_enhancers = (token_limit - (50 if mode_selection else 0)) // 100
        if max_enhancers < 0:
            max_enhancers = 0

        if len(adjusted_enhancers) > max_enhancers:
            adjusted_enhancers = adjusted_enhancers[:max_enhancers]
            rationale_parts.append(
                f"Token budget cap: Reduced to {max_enhancers} cognitive enhancer(s) "
                f"to stay under {token_limit} token limit"
            )

    # Build rationale
    rationale = " | ".join(rationale_parts) if rationale_parts else "No conflicts detected"

    return ArbiterResult(
        enhancers=adjusted_enhancers,
        mode_selection=adjusted_mode,
        reasoning_confidence=reasoning_confidence,
        token_budget_applied=estimated_tokens > token_limit,
        rationale=rationale,
    )
