"""Evidence Tier - classifies evidence sources and enforces confidence ceilings.

Per the evidence-tiers constitutional framework:
- Tier 1 (95% ceiling): Execution artifacts, logs, test output
- Tier 2 (85% ceiling): Official docs, specs, peer-reviewed sources
- Tier 3 (75% ceiling): Static analysis, logical derivation
- Tier 4 (50% ceiling): Comments, unverified claims, speculation

Confidence cannot exceed the evidence tier ceiling.
Mixed tiers: ceiling = lowest tier used.
Tier 4 alone: flag as [UNVERIFIED].
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import IntEnum
from typing import Any

# CKS integration - optional, graceful fallback if not available
CKS_AVAILABLE = False
try:
    from cks.unified import ingest_pattern

    CKS_AVAILABLE = True
except ImportError:
    try:
        # Fallback for development environment
        from search_research.cks.unified import ingest_pattern

        CKS_AVAILABLE = True
    except ImportError:
        ingest_pattern = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class EvidenceTier(IntEnum):
    """Evidence quality tiers with confidence ceilings.

    Per /evidence-tiers constitutional framework:
    - TIER_1: 95% ceiling - Direct execution evidence
    - TIER_2: 85% ceiling - Authoritative sources
    - TIER_3: 75% ceiling - Derived/analytical evidence
    - TIER_4: 50% ceiling - Unverified/speculation
    """

    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3
    TIER_4 = 4

    def confidence_ceiling(self) -> float:
        """Get the maximum confidence allowed for this tier."""
        return {
            EvidenceTier.TIER_1: 0.95,
            EvidenceTier.TIER_2: 0.85,
            EvidenceTier.TIER_3: 0.75,
            EvidenceTier.TIER_4: 0.50,
        }[self]

    def is_unverified(self) -> bool:
        """Check if this tier represents unverified evidence."""
        return self == EvidenceTier.TIER_4


@dataclass
class EvidenceSource:
    """A piece of evidence with its tier classification.

    Attributes:
        source_type: The type/category of evidence source.
        description: Human-readable description of the evidence.
        tier: The evidence tier (1-4).
        citation: Optional reference/citation for the evidence.
        timestamp: When this evidence was collected (ISO format).
    """

    source_type: str
    description: str
    tier: EvidenceTier
    citation: str = ""
    timestamp: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def confidence_ceiling(self) -> float:
        """Get the maximum confidence allowed by this evidence source."""
        return self.tier.confidence_ceiling()

    def is_unverified(self) -> bool:
        """Check if this evidence is unverified (Tier 4)."""
        return self.tier == EvidenceTier.TIER_4

    def applies_to_claim(self, claim: str) -> bool:
        """Check if this evidence is relevant to a specific claim.

        A basic implementation - can be overridden for more sophisticated
        relevance checking.

        Args:
            claim: The claim/hypothesis to check relevance against.

        Returns:
            True if evidence appears relevant to the claim.
        """
        # Simple keyword matching - case-insensitive
        claim_lower = claim.lower()
        desc_lower = self.description.lower()

        # Extract key terms from description (remove common words)
        common_words = {"the", "a", "an", "is", "was", "at", "on", "in", "to", "for"}
        desc_terms = [w for w in desc_lower.split() if w not in common_words and len(w) > 2]

        # Check if any significant term appears in the claim
        return any(term in claim_lower for term in desc_terms)


# Source type to tier mapping
# Per /evidence-tiers framework:
# - Tier 1: Direct execution (repro scripts, test output, debugger)
# - Tier 2: Authoritative (stack traces, assertions, git bisect)
# - Tier 3: Analytical (logs, timing, metrics)
# - Tier 4: Unverified (reports, speculation, unreproducible issues)
SOURCE_TYPE_TIERS: dict[str, EvidenceTier] = {
    # Tier 1: Direct execution evidence
    "reproduction_script": EvidenceTier.TIER_1,
    "failing_test": EvidenceTier.TIER_1,
    "debugger_breakpoint": EvidenceTier.TIER_1,
    "test_output": EvidenceTier.TIER_1,
    "execution_log": EvidenceTier.TIER_1,
    # Tier 2: Authoritative sources
    "stack_trace": EvidenceTier.TIER_2,
    "assertion_failure": EvidenceTier.TIER_2,
    "git_bisect_result": EvidenceTier.TIER_2,
    "official_documentation": EvidenceTier.TIER_2,
    "specification": EvidenceTier.TIER_2,
    # Tier 3: Analytical evidence
    "log_correlation": EvidenceTier.TIER_3,
    "timing_analysis": EvidenceTier.TIER_3,
    "metric_spike": EvidenceTier.TIER_3,
    "static_analysis": EvidenceTier.TIER_3,
    "code_trace": EvidenceTier.TIER_3,
    # Tier 4: Unverified evidence
    "user_report": EvidenceTier.TIER_4,
    "speculation": EvidenceTier.TIER_4,
    "cannot_reproduce": EvidenceTier.TIER_4,
    "heuristic": EvidenceTier.TIER_4,
    "assumption": EvidenceTier.TIER_4,
}


def classify_evidence(
    source_type: str,
    description: str = "",
    citation: str = "",
    timestamp: str = "",
) -> EvidenceSource:
    """Classify an evidence source by type and determine its tier.

    Args:
        source_type: The type of evidence (e.g., "stack_trace", "failing_test").
        description: Human-readable description of the evidence.
        citation: Optional reference/citation for the evidence.
        timestamp: When the evidence was collected (ISO format string).

    Returns:
        An EvidenceSource with the appropriate tier assigned.

    Examples:
        >>> from rca import classify_evidence
        >>> ev = classify_evidence("stack_trace", "Error in main.py line 42")
        >>> ev.tier
        <EvidenceTier.TIER_2: 2>
        >>> ev.confidence_ceiling
        0.85
    """
    tier = SOURCE_TYPE_TIERS.get(source_type.lower(), EvidenceTier.TIER_4)
    return EvidenceSource(
        source_type=source_type,
        description=description,
        tier=tier,
        citation=citation,
        timestamp=timestamp,
    )


def get_lowest_tier(evidence_sources: list[EvidenceSource]) -> EvidenceTier:
    """Get the lowest (weakest) tier from a list of evidence sources.

    When using multiple evidence sources, the confidence ceiling
    is determined by the weakest tier.

    Args:
        evidence_sources: List of evidence sources to evaluate.

    Returns:
        The lowest (weakest) tier among the sources, or TIER_4 if empty.

    Examples:
        >>> from rca import classify_evidence, get_lowest_tier
        >>> sources = [
        ...     classify_evidence("failing_test", "Test fails consistently"),
        ...     classify_evidence("user_report", "User said it broke"),
        ... ]
        >>> get_lowest_tier(sources)
        <EvidenceTier.TIER_4: 4>
    """
    if not evidence_sources:
        return EvidenceTier.TIER_4
    # "Lowest tier" means weakest evidence, which is the highest tier number
    # TIER_4 is weaker than TIER_1, so we use max() to get the weakest
    return max((e.tier for e in evidence_sources), default=EvidenceTier.TIER_4)


def get_confidence_ceiling(evidence_sources: list[EvidenceSource]) -> float:
    """Calculate the maximum confidence allowed based on evidence tiers.

    Per /evidence-tiers: "Mixed tiers: ceiling = lowest tier used"

    Args:
        evidence_sources: List of evidence sources to evaluate.

    Returns:
        The confidence ceiling (0.0 to 1.0).

    Examples:
        >>> from rca import classify_evidence, get_confidence_ceiling
        >>> sources = [classify_evidence("failing_test", "Test fails")]
        >>> get_confidence_ceiling(sources)
        0.95
    """
    lowest_tier = get_lowest_tier(evidence_sources)
    return lowest_tier.confidence_ceiling()


def apply_ceiling(confidence: float, evidence_sources: list[EvidenceSource]) -> float:
    """Apply evidence tier ceiling to a confidence value.

    Args:
        confidence: The proposed confidence level (0.0 to 1.0).
        evidence_sources: List of evidence sources supporting the claim.

    Returns:
        The confidence capped at the evidence tier ceiling.

    Examples:
        >>> from rca import classify_evidence, apply_ceiling
        >>> sources = [classify_evidence("speculation", "I think it's X")]
        >>> apply_ceiling(0.9, sources)
        0.5
    """
    ceiling = get_confidence_ceiling(evidence_sources)
    return min(confidence, ceiling)


def format_evidence_summary(evidence_sources: list[EvidenceSource]) -> str:
    """Format a human-readable summary of evidence with tiers.

    Args:
        evidence_sources: List of evidence sources to summarize.

    Returns:
        A formatted string showing evidence types and their tiers.

    Examples:
        >>> from rca import classify_evidence, format_evidence_summary
        >>> sources = [
        ...     classify_evidence("failing_test", "Test fails"),
        ...     classify_evidence("speculation", "Maybe race condition"),
        ... ]
        >>> print(format_evidence_summary(sources))
    """
    if not evidence_sources:
        return "[No evidence - TIER_4 ceiling applies]"

    lines = ["Evidence Summary:"]
    for i, ev in enumerate(evidence_sources, 1):
        unverified_tag = " [UNVERIFIED]" if ev.is_unverified() else ""
        lines.append(f"  {i}. [{ev.tier.name}] {ev.source_type}: {ev.description}{unverified_tag}")

    lowest = get_lowest_tier(evidence_sources)
    ceiling = get_confidence_ceiling(evidence_sources)
    lines.append(f"\nOverall ceiling: {ceiling * 100:.0f}% (based on {lowest.name})")

    if lowest == EvidenceTier.TIER_4:
        lines.append("⚠️  WARNING: Tier 4 evidence - conclusions are unverified")

    return "\n".join(lines)


@dataclass
class EvidenceLedger:
    """Accumulates and tracks evidence for an RCA investigation.

    The ledger maintains all evidence sources collected during an investigation
    and provides methods to query confidence ceilings and evidence summaries.

    Attributes:
        sources: List of evidence sources collected.
        claim: The primary claim/hypothesis being investigated.
    """

    sources: list[EvidenceSource] = field(default_factory=list)
    claim: str = ""

    def add_evidence(self, source: EvidenceSource) -> None:
        """Add an evidence source to the ledger.

        Args:
            source: The evidence source to add.
        """
        self.sources.append(source)

    def add_classified(
        self,
        source_type: str,
        description: str,
        citation: str = "",
        timestamp: str = "",
    ) -> EvidenceSource:
        """Classify and add evidence in one step.

        Args:
            source_type: The type of evidence.
            description: Description of the evidence.
            citation: Optional citation/reference.
            timestamp: Optional timestamp.

        Returns:
            The created EvidenceSource.
        """
        source = classify_evidence(source_type, description, citation, timestamp)
        self.add_evidence(source)
        return source

    def confidence_ceiling(self) -> float:
        """Get the confidence ceiling based on all evidence in the ledger."""
        return get_confidence_ceiling(self.sources)

    def lowest_tier(self) -> EvidenceTier:
        """Get the lowest evidence tier in the ledger."""
        return get_lowest_tier(self.sources)

    def is_unverified(self) -> bool:
        """Check if the ledger contains only Tier 4 evidence."""
        return self.lowest_tier() == EvidenceTier.TIER_4

    def summary(self) -> str:
        """Get a formatted summary of the evidence ledger."""
        claim_display = self.claim if self.claim else "(unnamed claim)"
        lines = [f"Evidence Ledger for: {claim_display}"]
        lines.append(f"Total sources: {len(self.sources)}")
        lines.append(f"Lowest tier: {self.lowest_tier().name}")
        lines.append(f"Confidence ceiling: {self.confidence_ceiling() * 100:.0f}%")

        if self.sources:
            lines.append("\nEvidence sources:")
            for i, ev in enumerate(self.sources, 1):
                tier_tag = f"[{ev.tier.name}]"
                unverified = " [UNVERIFIED]" if ev.is_unverified() else ""
                lines.append(f"  {i}. {tier_tag} {ev.source_type}: {ev.description}{unverified}")
        else:
            lines.append("\nNo evidence collected.")

        if self.is_unverified():
            lines.append("\n⚠️  WARNING: Only Tier 4 evidence - conclusions are UNVERIFIED")

        return "\n".join(lines)

    def filter_by_tier(self, tier: EvidenceTier) -> list[EvidenceSource]:
        """Get all evidence sources of a specific tier.

        Args:
            tier: The tier to filter by.

        Returns:
            List of evidence sources at the specified tier.
        """
        return [e for e in self.sources if e.tier == tier]

    def count_by_tier(self) -> dict[EvidenceTier, int]:
        """Count evidence sources by tier.

        Returns:
            Dictionary mapping tier to count of sources at that tier.
        """
        counts = {
            EvidenceTier.TIER_1: 0,
            EvidenceTier.TIER_2: 0,
            EvidenceTier.TIER_3: 0,
            EvidenceTier.TIER_4: 0,
        }
        for ev in self.sources:
            counts[ev.tier] += 1
        return counts

    def store_to_cks(
        self,
        outcome: str = "unknown",
        root_cause: str = "",
        fix_applied: str = "",
        verification_method: str = "",
    ) -> str | None:
        """Store this evidence ledger to CKS as a pattern with automatic embedding.

        This enables:
        - Semantic search across RCA investigations
        - Finding similar past investigations
        - Learning from verified root causes and fixes

        Args:
            outcome: Investigation outcome (resolved/failed/partial/unknown)
            root_cause: Identified root cause (if known)
            fix_applied: What fix was applied (if any)
            verification_method: How the fix was verified

        Returns:
            CKS entry ID if successful, None otherwise

        Example:
            >>> ledger = EvidenceLedger(claim="Database timeout on queries")
            >>> ledger.add_classified("stack_trace", "Timeout at db.py:42")
            >>> entry_id = ledger.store_to_cks(
            ...     outcome="resolved",
            ...     root_cause="Missing connection pool timeout",
            ...     fix_applied="Added connect_timeout=5 to connection pool",
            ...     verification_method="pytest test_db_timeout.py -v"
            ... )
        """
        if not CKS_AVAILABLE:
            logger.warning("CKS not available - cannot store evidence ledger")
            return None

        if not self.sources:
            logger.warning("No evidence to store - skipping CKS ingestion")
            return None

        try:
            # Build title from claim
            claim_display = self.claim if self.claim else "RCA Investigation"
            title = f"RCA: {claim_display[:100]}"

            # Build content with full evidence details
            content_parts = [
                f"## Investigation: {claim_display}",
                f"**Outcome**: {outcome}",
                f"**Confidence Ceiling**: {self.confidence_ceiling() * 100:.0f}% (based on {self.lowest_tier().name})",
                "",
            ]

            if root_cause:
                content_parts.extend(
                    [
                        f"**Root Cause**: {root_cause}",
                        "",
                    ]
                )

            if fix_applied:
                content_parts.extend(
                    [
                        f"**Fix Applied**: {fix_applied}",
                        "",
                    ]
                )

            if verification_method:
                content_parts.extend(
                    [
                        f"**Verification**: {verification_method}",
                        "",
                    ]
                )

            # Add evidence summary
            content_parts.extend(
                [
                    "## Evidence Collected",
                    f"Total sources: {len(self.sources)}",
                    "",
                ]
            )

            for i, ev in enumerate(self.sources, 1):
                tier_tag = f"[{ev.tier.name}]"
                content_parts.append(f"{i}. {tier_tag} **{ev.source_type}**: {ev.description}")
                if ev.citation:
                    content_parts.append(f"   Citation: {ev.citation}")
                if ev.timestamp:
                    content_parts.append(f"   Timestamp: {ev.timestamp}")

            # Add tier breakdown
            counts = self.count_by_tier()
            content_parts.extend(
                [
                    "",
                    "## Evidence Tier Breakdown",
                    f"- Tier 1 (95% ceiling): {counts[EvidenceTier.TIER_1]} sources",
                    f"- Tier 2 (85% ceiling): {counts[EvidenceTier.TIER_2]} sources",
                    f"- Tier 3 (75% ceiling): {counts[EvidenceTier.TIER_3]} sources",
                    f"- Tier 4 (50% ceiling): {counts[EvidenceTier.TIER_4]} sources",
                ]
            )

            if self.is_unverified():
                content_parts.append(
                    "\n⚠️ **WARNING**: Only Tier 4 evidence - conclusions are UNVERIFIED"
                )

            content = "\n".join(content_parts)

            # Build metadata for structured querying
            # Note: 'entry_type' key is renamed to 'rca_entry_type' to avoid conflict
            # with CKS ingest_pattern's entry_type parameter
            metadata = {
                "rca_outcome": outcome,
                "confidence_ceiling": f"{self.confidence_ceiling() * 100:.0f}%",
                "lowest_tier": self.lowest_tier().name,
                "evidence_count": len(self.sources),
                "tier_1_count": counts[EvidenceTier.TIER_1],
                "tier_2_count": counts[EvidenceTier.TIER_2],
                "tier_3_count": counts[EvidenceTier.TIER_3],
                "tier_4_count": counts[EvidenceTier.TIER_4],
                "ingested_at": datetime.now(tz=UTC).isoformat(),
                "rca_entry_type": "rca_investigation",  # Renamed to avoid conflict
            }

            if root_cause:
                metadata["root_cause"] = root_cause
            if fix_applied:
                metadata["fix_applied"] = fix_applied
            if verification_method:
                metadata["verification_method"] = verification_method

            # Use source_chunk for better semantic matching
            # Combine claim + root cause + fix for semantic embedding
            source_chunk_parts = [claim_display]
            if root_cause:
                source_chunk_parts.append(root_cause)
            if fix_applied:
                source_chunk_parts.append(fix_applied)
            source_chunk = " | ".join(source_chunk_parts)

            # Store in CKS as a pattern with automatic embedding
            entry_id = ingest_pattern(
                title=title,
                content=content,
                source_chunk=source_chunk,
                entry_type="pattern",  # Use pattern type for RCA findings
                **metadata,
            )

            if entry_id:
                logger.info("Stored evidence ledger to CKS: %s", entry_id)
            else:
                logger.warning("CKS ingestion returned empty entry_id")

            return entry_id

        except Exception as e:
            logger.exception("Failed to store evidence ledger to CKS: %s", e)
            return None


def store_rca_finding(
    claim: str,
    outcome: str,
    root_cause: str = "",
    fix_applied: str = "",
    verification_method: str = "",
    evidence_sources: list[EvidenceSource] | None = None,
) -> str | None:
    """Convenience function to store an RCA finding directly to CKS.

    This creates an EvidenceLedger, populates it, and stores to CKS in one call.

    Args:
        claim: The problem/claim investigated
        outcome: Investigation outcome (resolved/failed/partial/unknown)
        root_cause: Identified root cause (if known)
        fix_applied: What fix was applied (if any)
        verification_method: How the fix was verified
        evidence_sources: Optional list of evidence sources

    Returns:
        CKS entry ID if successful, None otherwise

    Example:
        >>> from rca import store_rca_finding, classify_evidence
        >>>
        >>> entry_id = store_rca_finding(
        ...     claim="Database connection timeout",
        ...     outcome="resolved",
        ...     root_cause="Missing connection pool timeout configuration",
        ...     fix_applied="Added connect_timeout=5 to database config",
        ...     verification_method="pytest test_db_timeout.py -v",
        ...     evidence_sources=[
        ...         classify_evidence("stack_trace", "TimeoutError at db.py:42"),
        ...         classify_evidence("log_correlation", "Timeouts correlate with high load"),
        ...     ],
        ... )
    """
    ledger = EvidenceLedger(claim=claim)
    if evidence_sources:
        for source in evidence_sources:
            ledger.add_evidence(source)
    return ledger.store_to_cks(
        outcome=outcome,
        root_cause=root_cause,
        fix_applied=fix_applied,
        verification_method=verification_method,
    )
