"""Verification system for claim grounding.

Phase 2: Shared verification engine and claim detection.
This module provides unified claim and verification abstractions.
"""

from .claims import Claim, classify_claim, extract_claims
from .engine import (
    EnrichedVerdict,
    ToolEventView,
    VerificationStatus,
    VerificationVerdict,
    analyze_silent_verdicts,
    build_verdicts,
    match_claim_to_events,
    micro_fallback_verify,
)

__all__ = [
    "Claim",
    "EnrichedVerdict",
    "classify_claim",
    "extract_claims",
    "VerificationStatus",
    "VerificationVerdict",
    "ToolEventView",
    "analyze_silent_verdicts",
    "build_verdicts",
    "match_claim_to_events",
    "micro_fallback_verify",
]
