"""
RCA Specialist Integration with Error Signature Matching

This module bridges the RCA Specialist subagent with the error signature
matching and CKS pattern registry.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

# Import error signature system
try:
    from ..error_signature import (
        ErrorSignature,
        extract_signature,
    )
except ImportError:
    # Fallback for standalone usage
    from rca.error_signature import (
        ErrorSignature,
        extract_signature,
    )

# import CKS pattern registry
try:
    from .cks_pattern_integration import (
        CKSPatternRegistry,
        get_cks_pattern_registry,
    )
except ImportError:
    # Fallback for standalone usage
    from rca.integration.cks_pattern_integration import (
        CKSPatternRegistry,
        get_cks_pattern_registry,
    )

logger = logging.getLogger(__name__)


@dataclass
class SignatureAnalysisResult:
    """Result of error signature analysis."""

    signature: ErrorSignature | None = None
    pattern_name: str = ""
    error_type: str = ""
    confidence: float = 0.0
    match_source: str = ""
    suggested_fix: str = ""
    fix_template: str = ""
    code_diff: str = ""
    times_seen: int = 0
    locations_seen: list[str] = field(default_factory=list)
    verified: bool = False
    semantic_matches: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_name": self.pattern_name,
            "error_type": self.error_type,
            "confidence": self.confidence,
            "match_source": self.match_source,
            "suggested_fix": self.suggested_fix,
            "fix_template": self.fix_template,
            "code_diff": self.code_diff,
            "times_seen": self.times_seen,
            "locations_seen": self.locations_seen,
            "verified": self.verified,
            "semantic_matches_count": len(self.semantic_matches),
        }

    @property
    def has_match(self) -> bool:
        """Whether a pattern match was found."""
        return self.signature is not None and self.confidence > 0.5

    @property
    def has_verified_fix(self) -> bool:
        """Whether a verified fix exists."""
        return self.verified and self.times_seen > 0


class RCASpecialistSignatureBridge:
    """Bridge between RCA Specialist and Error Signature/CKS systems."""

    def __init__(self, cks_registry: CKSPatternRegistry | None = None) -> None:
        self._cks_registry = cks_registry or get_cks_pattern_registry()

    def analyze(
        self,
        error_message: str,
        code_context: str = "",
        location: str = "",
        include_semantic: bool = True,
    ) -> SignatureAnalysisResult:
        """Analyze an error using signature matching and CKS lookup."""
        result = SignatureAnalysisResult()

        signature = extract_signature(error_message)
        if not signature:
            result.match_source = "none"
            return result

        result.signature = signature
        result.pattern_name = signature.pattern_name
        result.error_type = signature.error_type

        if self._cks_registry:
            try:
                from ..error_signature import match_to_pattern
            except ImportError:
                from rca.error_signature import match_to_pattern

            cks_match = self._cks_registry.lookup(error_message)
            if cks_match:
                result.confidence = cks_match.get("confidence", 0.7)
                result.match_source = cks_match.get("source", "cks")
                result.suggested_fix = cks_match.get("fix_description", "")
                result.fix_template = cks_match.get("fix_template", "")
                result.code_diff = cks_match.get("code_diff", "")
                result.times_seen = cks_match.get("applied_count", 0)
                result.locations_seen = cks_match.get("locations_seen", [])
                result.verified = cks_match.get("verified", False)

                if not result.suggested_fix:
                    result.suggested_fix = signature.fix_template
                    result.fix_template = signature.fix_template

                if include_semantic:
                    result.semantic_matches = self._cks_registry.lookup_semantic(
                        error_message, limit=5
                    )
            else:
                result.match_source = "template"
                result.confidence = 0.7
                result.suggested_fix = signature.fix_template
                result.fix_template = signature.fix_template
        else:
            result.match_source = "template"
            result.confidence = 0.7
            result.suggested_fix = signature.fix_template
            result.fix_template = signature.fix_template

        return result

    def register_fix(
        self,
        error_message: str,
        fix_description: str,
        fix_template: str = "",
        code_diff: str = "",
        location: str = "",
        verified: bool = False,
    ) -> bool:
        """Register a successful fix in CKS."""
        if not self._cks_registry:
            logger.warning("CKS registry not available")
            return False

        return self._cks_registry.register_fix(
            error_message=error_message,
            fix_description=fix_description,
            fix_template=fix_template,
            code_diff=code_diff,
            location=location,
            verified=verified,
        )

    def get_similar_patterns(self, error_message: str, limit: int = 5):
        """Get similar patterns from CKS."""
        if not self._cks_registry:
            return []
        return self._cks_registry.lookup_semantic(error_message, limit=limit)

    def get_pattern_stats(self) -> dict:
        """Get statistics about registered patterns."""
        if not self._cks_registry:
            return {"available": False}
        return self._cks_registry.get_stats()


def analyze_error_with_signatures(
    error_message: str,
    code_context: str = "",
    location: str = "",
) -> SignatureAnalysisResult:
    """Quick analysis of an error with signature matching."""
    bridge = RCASpecialistSignatureBridge()
    return bridge.analyze(error_message, code_context, location)


def register_fix_from_rca(
    error_message: str,
    fix_description: str,
    location: str = "",
    verified: bool = True,
) -> bool:
    """Register a fix discovered during RCA."""
    bridge = RCASpecialistSignatureBridge()
    return bridge.register_fix(
        error_message=error_message,
        fix_description=fix_description,
        location=location,
        verified=verified,
    )


def get_fix_suggestions_for_rca(error_message: str) -> dict:
    """Get fix suggestions for RCA analysis."""
    bridge = RCASpecialistSignatureBridge()
    analysis = bridge.analyze(error_message)

    response = {
        "has_match": analysis.has_match,
        "confidence": analysis.confidence,
        "suggestions": [],
        "evidence": [],
    }

    if analysis.has_match:
        response["suggestions"].append(
            {
                "pattern": analysis.pattern_name,
                "fix": analysis.suggested_fix,
                "source": analysis.match_source,
                "verified": analysis.verified,
                "times_seen": analysis.times_seen,
            }
        )

        if analysis.locations_seen:
            response["evidence"] = [
                {"location": loc, "pattern": analysis.pattern_name}
                for loc in analysis.locations_seen[:3]
            ]

        for match in analysis.semantic_matches[:3]:
            response["suggestions"].append(
                {
                    "pattern": match.get("pattern_name"),
                    "fix": match.get("fix_description"),
                    "source": "semantic",
                    "similarity": match.get("similarity", 0),
                }
            )

    return response
