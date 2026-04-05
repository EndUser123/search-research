#!/usr/bin/env python3
"""Behavioral Protocol for Truth & Evidence Hooks Modernization.

Defines evidence tier taxonomy, confidence ceiling protocol, and behavioral
contracts for enforcing CLAUDE.md v8.0 constitutional rules.

Source: CLAUDE.md v8.0 Evidence Tiers (lines 22-36)
Plan: plan-20260207-consolidated-truth-evidence-behavioral-modernization.md

Evidence Tier Taxonomy:
    Tier 1: 95% ceiling - Execution artifacts, logs, test output
    Tier 2: 85% ceiling - Official docs, specs, peer-reviewed
    Tier 3: 75% ceiling - Static analysis, logical derivation
    Tier 4: 50% ceiling - Comments, unverified claims

Rules:
    - High-stakes requires Tier 1/2
    - Mixed tiers: ceiling = lowest tier used
    - Tier 4 alone: flag as [UNVERIFIED]
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


class EvidenceTier(IntEnum):
    """Evidence tier levels with confidence ceilings.

    Source: CLAUDE.md v8.0 lines 22-36
    """
    TIER_1 = 1  # Execution artifacts, logs, test output
    TIER_2 = 2  # Official docs, specs, peer-reviewed
    TIER_3 = 3  # Static analysis, logical derivation
    TIER_4 = 4  # Comments, unverified claims


@dataclass(frozen=True)
class ConfidenceCeiling:
    """Confidence ceiling for an evidence tier.

    Attributes:
        tier: Evidence tier level (1-4)
        ceiling: Maximum confidence allowed (0.0-1.0)
        sources: Description of acceptable sources
        use_case: Typical use case for this tier
    """
    tier: EvidenceTier
    ceiling: float
    sources: str
    use_case: str

    def __post_init__(self) -> None:
        """Validate ceiling is between 0 and 1."""
        if not 0.0 <= self.ceiling <= 1.0:
            raise ValueError(f"Confidence ceiling must be 0.0-1.0, got {self.ceiling}")


# Evidence tier definitions (from CLAUDE.md v8.0)
EVIDENCE_TIERS: dict[EvidenceTier, ConfidenceCeiling] = {
    EvidenceTier.TIER_1: ConfidenceCeiling(
        tier=EvidenceTier.TIER_1,
        ceiling=0.95,
        sources="Execution artifacts, logs, test output",
        use_case="High-stakes enforcement"
    ),
    EvidenceTier.TIER_2: ConfidenceCeiling(
        tier=EvidenceTier.TIER_2,
        ceiling=0.85,
        sources="Official docs, specs, peer-reviewed",
        use_case="Technical decisions"
    ),
    EvidenceTier.TIER_3: ConfidenceCeiling(
        tier=EvidenceTier.TIER_3,
        ceiling=0.75,
        sources="Static analysis, logical derivation",
        use_case="Architecture analysis"
    ),
    EvidenceTier.TIER_4: ConfidenceCeiling(
        tier=EvidenceTier.TIER_4,
        ceiling=0.50,
        sources="Comments, unverified claims",
        use_case="Flag as [UNVERIFIED]"
    ),
}


def calculate_confidence_ceiling(tiers: Iterable[EvidenceTier]) -> float:
    """Calculate confidence ceiling from evidence tiers.

    Rules:
    - Mixed tiers: ceiling = lowest quality tier used (most conservative)
    - Single tier: use that tier's ceiling
    - Empty: return 1.0 (no restriction)

    Note: Higher tier numbers = lower quality (TIER_4 is worst quality)
    So we use max() to find the lowest quality tier.

    Args:
        tiers: Iterable of evidence tiers used

    Returns:
        Confidence ceiling (0.0-1.0)

    Examples:
        >>> calculate_confidence_ceiling([EvidenceTier.TIER_1])
        0.95
        >>> calculate_confidence_ceiling([EvidenceTier.TIER_1, EvidenceTier.TIER_4])
        0.5  # Lowest quality tier wins (TIER_4)
        >>> calculate_confidence_ceiling([])
        1.0
    """
    tier_list = list(tiers)
    if not tier_list:
        return 1.0

    # Use lowest quality tier (highest tier number, most conservative)
    lowest_quality_tier = max(tier_list)
    return EVIDENCE_TIERS[lowest_quality_tier].ceiling


def get_evidence_tier(source_type: str) -> EvidenceTier | None:
    """Map source type to evidence tier.

    Args:
        source_type: Description of evidence source

    Returns:
        Corresponding evidence tier, or None if unrecognized

    Examples:
        >>> get_evidence_tier("test output")
        <EvidenceTier.TIER_1: 1>
        >>> get_evidence_tier("official documentation")
        <EvidenceTier.TIER_2: 2>
        >>> get_evidence_tier("code comment")
        <EvidenceTier.TIER_4: 4>
        >>> get_evidence_tier("unknown")
        None
    """
    source_lower = source_type.lower()

    # Check in order: most specific to least specific to avoid false matches

    # Tier 4: Unverified or weak sources (check first to avoid overlap)
    if any(kw in source_lower for kw in (
        "comment", "unverified", "anecdotal", "hearsay",
        "opinion", "speculation"
    )):
        return EvidenceTier.TIER_4

    # Tier 3: Derived analysis
    if any(kw in source_lower for kw in (
        "static analysis", "logical derivation", "code review",
        "architecture analysis", "pattern matching"
    )):
        return EvidenceTier.TIER_3

    # Tier 2: Authoritative sources
    if any(kw in source_lower for kw in (
        "official doc", "specification", "peer-reviewed", "api doc",
        "documentation", "reference", "standard"
    )):
        return EvidenceTier.TIER_2

    # Tier 1: Direct execution evidence
    if any(kw in source_lower for kw in (
        "test output", "execution artifact", "log", "run output",
        "command result", "terminal output"
    )):
        return EvidenceTier.TIER_1

    return None


def requires_high_stakes_evidence(tiers: Iterable[EvidenceTier]) -> bool:
    """Check if high-stakes enforcement requires Tier 1/2 evidence.

    Args:
        tiers: Evidence tiers being used

    Returns:
        True if high-stakes and not using Tier 1/2

    Examples:
        >>> requires_high_stakes_evidence([EvidenceTier.TIER_1])
        False
        >>> requires_high_stakes_evidence([EvidenceTier.TIER_3, EvidenceTier.TIER_4])
        True
    """
    tier_list = list(tiers)
    if not tier_list:
        return False

    # High-stakes requires Tier 1 or 2 (lower tier numbers are better)
    # If all tiers are 3 or higher, we lack high-quality evidence
    return all(t >= EvidenceTier.TIER_3 for t in tier_list)


def should_flag_unverified(tiers: Iterable[EvidenceTier]) -> bool:
    """Check if claim should be flagged as [UNVERIFIED].

    Rule: Tier 4 alone (no other tiers) = flag as unverified.

    Args:
        tiers: Evidence tiers being used

    Returns:
        True if should flag as [UNVERIFIED]

    Examples:
        >>> should_flag_unverified([EvidenceTier.TIER_4])
        True
        >>> should_flag_unverified([EvidenceTier.TIER_1, EvidenceTier.TIER_4])
        False
    """
    tier_list = list(tiers)
    return len(tier_list) == 1 and tier_list[0] == EvidenceTier.TIER_4


def format_confidence_label(tiers: Iterable[EvidenceTier], confidence: float) -> str:
    """Format confidence with tier-based label.

    Args:
        tiers: Evidence tiers used
        confidence: Calculated confidence value

    Returns:
        Formatted label with confidence percentage

    Examples:
        >>> format_confidence_label([EvidenceTier.TIER_1], 0.90)
        '90% [Tier 1: Execution artifacts]'
        >>> format_confidence_label([EvidenceTier.TIER_4], 0.50)
        '50% [UNVERIFIED]'
    """
    tier_list = list(tiers)

    if should_flag_unverified(tier_list):
        return f"{confidence:.0%} [UNVERIFIED]"

    if tier_list:
        # Show highest quality tier (lowest tier number)
        best_tier = min(tier_list)
        tier_info = EVIDENCE_TIERS[best_tier]
        return f"{confidence:.0%} [Tier {best_tier}: {tier_info.sources}]"

    return f"{confidence:.0%}"
