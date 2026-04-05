"""Verification claims module.

Provides Claim dataclass and extract_claims() function for detecting
and representing verification claims in LLM responses.

FIELD ALIGNMENT (from RawClaim in hypothesis_as_fact_detector.py):
- RawClaim.text → Claim.text (same)
- RawClaim.subject_entity → Claim.targets[0] (rename+list wrapper)
- RawClaim.claim_type → Claim.type (rename)
- RawClaim.confidence → Claim.confidence (same)
- RawClaim.has_hedge → Claim.has_hedge (same)
- RawClaim.risk_domain → Claim.risk_domain (same)

This alignment ensures Phase 2 is a rename+move operation, not a redesign.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import List

from anti_sycophancy.hypothesis_as_fact_detector import (
    HypothesisAsFactDetector,
    RawClaim,
)


@dataclass
class Claim:
    """Verification claim with targets and metadata.

    This is the Phase 2 unified claim representation that replaces
    RawClaim from Phase 1. Field alignment ensures smooth migration.
    """

    id: str
    text: str
    targets: List[str]
    type: str
    confidence: float
    risk_domain: str
    has_hedge: bool


def extract_claims(response_text: str) -> List[Claim]:
    """Extract verification claims from response text.

    This function wraps the Phase 1 HypothesisAsFactDetector and converts
    RawClaim objects to Phase 2 Claim objects with aligned fields.

    Args:
        response_text: The LLM response text to analyze

    Returns:
        List of Claim objects representing detected claims

    Examples:
        >>> text = "Package has no skill/ directory"
        >>> claims = extract_claims(text)
        >>> assert len(claims) > 0
        >>> assert claims[0].type == "ABSENCE"
    """
    detector = HypothesisAsFactDetector()
    raw_claims: List[RawClaim] = detector.detect_claims(response_text)

    # Convert RawClaim to Claim with field alignment
    claims: List[Claim] = []
    for raw in raw_claims:
        claim = _raw_claim_to_claim(raw)
        if claim:
            claims.append(claim)

    return claims


def _raw_claim_to_claim(raw: RawClaim) -> Claim | None:
    """Convert RawClaim to Claim with field alignment.

    Field mapping:
    - text → text (same)
    - subject_entity → targets[0] (rename+list wrapper)
    - claim_type → type (rename, strip "entity_" prefix)
    - confidence → confidence (same)
    - has_hedge → has_hedge (same)
    - risk_domain → risk_domain (same)

    Args:
        raw: RawClaim object from Phase 1 detector

    Returns:
        Claim object with aligned fields, or None if conversion fails
    """
    try:
        # Generate unique ID for claim
        claim_id = str(uuid.uuid4())

        # Map claim_type: "entity_absence" → "ABSENCE", "rule" → "RULE", etc.
        claim_type = raw.claim_type
        if claim_type.startswith("entity_"):
            claim_type = claim_type.replace("entity_", "").upper()
        else:
            claim_type = claim_type.upper()

        # Wrap subject_entity in targets list (RawClaim has single string)
        targets = [raw.subject_entity] if raw.subject_entity else []

        return Claim(
            id=claim_id,
            text=raw.text,
            targets=targets,
            type=claim_type,
            confidence=raw.confidence,
            risk_domain=raw.risk_domain,
            has_hedge=raw.has_hedge,
        )
    except (AttributeError, ValueError):
        # Fail gracefully on malformed RawClaim
        return None
