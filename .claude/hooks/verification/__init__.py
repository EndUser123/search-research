"""Verification system for claim grounding.

Phase 2: Shared verification engine and claim detection.
This module provides unified claim and verification abstractions.
"""

from .claims import Claim, extract_claims
from .engine import (
    ToolEventView,
    VerificationStatus,
    VerificationVerdict,
    build_verdicts,
    match_claim_to_events,
)

__all__ = [
    "Claim",
    "extract_claims",
    "VerificationStatus",
    "VerificationVerdict",
    "ToolEventView",
    "build_verdicts",
    "match_claim_to_events",
]
