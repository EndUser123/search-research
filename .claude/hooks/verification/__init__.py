"""Verification system for claim grounding.

Phase 2: Shared verification engine and claim detection.
This module provides unified claim and verification abstractions.
"""

from .claims import Claim, classify_claim, extract_claims
from .engine import (
    ToolEventView,
    VerificationStatus,
    VerificationVerdict,
    build_verdicts,
    match_claim_to_events,
)

__all__ = [
    "Claim",
    "classify_claim",
    "extract_claims",
    "VerificationStatus",
    "VerificationVerdict",
    "ToolEventView",
    "build_verdicts",
    "match_claim_to_events",
]
