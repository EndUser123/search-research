#!/usr/bin/env python3
"""Tests for behavioral_protocol.py - Evidence tier and confidence ceiling logic.

Tests the CLAUDE.md v8.0 Evidence Tier contracts:
- Tier 1: 95% ceiling - Execution artifacts, logs, test output
- Tier 2: 85% ceiling - Official docs, specs, peer-reviewed
- Tier 3: 75% ceiling - Static analysis, logical derivation
- Tier 4: 50% ceiling - Comments, unverified claims
"""

from __future__ import annotations

from __lib.behavioral_protocol import (
    EVIDENCE_TIERS,
    EvidenceTier,
    calculate_confidence_ceiling,
    format_confidence_label,
    get_evidence_tier,
    requires_high_stakes_evidence,
    should_flag_unverified,
)


class TestEvidenceTierEnum:
    """Test EvidenceTier enum values."""

    def test_tier_values(self) -> None:
        """Evidence tiers should be 1-4."""
        assert EvidenceTier.TIER_1 == 1
        assert EvidenceTier.TIER_2 == 2
        assert EvidenceTier.TIER_3 == 3
        assert EvidenceTier.TIER_4 == 4


class TestConfidenceCeilings:
    """Test confidence ceiling definitions."""

    def test_tier_1_ceiling(self) -> None:
        """Tier 1 should have 95% ceiling."""
        tier = EVIDENCE_TIERS[EvidenceTier.TIER_1]
        assert tier.ceiling == 0.95
        assert "execution" in tier.sources.lower()

    def test_tier_2_ceiling(self) -> None:
        """Tier 2 should have 85% ceiling."""
        tier = EVIDENCE_TIERS[EvidenceTier.TIER_2]
        assert tier.ceiling == 0.85
        assert "official" in tier.sources.lower()

    def test_tier_3_ceiling(self) -> None:
        """Tier 3 should have 75% ceiling."""
        tier = EVIDENCE_TIERS[EvidenceTier.TIER_3]
        assert tier.ceiling == 0.75
        assert "static" in tier.sources.lower()

    def test_tier_4_ceiling(self) -> None:
        """Tier 4 should have 50% ceiling."""
        tier = EVIDENCE_TIERS[EvidenceTier.TIER_4]
        assert tier.ceiling == 0.50
        assert "unverified" in tier.sources.lower()


class TestCalculateConfidenceCeiling:
    """Test confidence ceiling calculation rules."""

    def test_single_tier_1(self) -> None:
        """Single Tier 1 should return 95%."""
        assert calculate_confidence_ceiling([EvidenceTier.TIER_1]) == 0.95

    def test_single_tier_2(self) -> None:
        """Single Tier 2 should return 85%."""
        assert calculate_confidence_ceiling([EvidenceTier.TIER_2]) == 0.85

    def test_single_tier_3(self) -> None:
        """Single Tier 3 should return 75%."""
        assert calculate_confidence_ceiling([EvidenceTier.TIER_3]) == 0.75

    def test_single_tier_4(self) -> None:
        """Single Tier 4 should return 50%."""
        assert calculate_confidence_ceiling([EvidenceTier.TIER_4]) == 0.50

    def test_mixed_tiers_lowest_wins(self) -> None:
        """Mixed tiers should use lowest (most conservative) ceiling."""
        # Tier 1 + Tier 4 = Tier 4 ceiling (50%)
        assert calculate_confidence_ceiling([
            EvidenceTier.TIER_1,
            EvidenceTier.TIER_4
        ]) == 0.50

        # Tier 2 + Tier 3 = Tier 3 ceiling (75%)
        assert calculate_confidence_ceiling([
            EvidenceTier.TIER_2,
            EvidenceTier.TIER_3
        ]) == 0.75

    def test_empty_tiers(self) -> None:
        """Empty tier list should return 1.0 (no restriction)."""
        assert calculate_confidence_ceiling([]) == 1.0

    def test_duplicate_tiers(self) -> None:
        """Duplicate tiers should not affect ceiling."""
        assert calculate_confidence_ceiling([
            EvidenceTier.TIER_1,
            EvidenceTier.TIER_1,
            EvidenceTier.TIER_1
        ]) == 0.95


class TestGetEvidenceTier:
    """Test source type to evidence tier mapping."""

    def test_tier_1_execution_artifacts(self) -> None:
        """Execution artifacts should map to Tier 1."""
        assert get_evidence_tier("test output") == EvidenceTier.TIER_1
        assert get_evidence_tier("execution artifact") == EvidenceTier.TIER_1
        assert get_evidence_tier("log file") == EvidenceTier.TIER_1
        assert get_evidence_tier("command result") == EvidenceTier.TIER_1

    def test_tier_2_authoritative_sources(self) -> None:
        """Authoritative sources should map to Tier 2."""
        assert get_evidence_tier("official documentation") == EvidenceTier.TIER_2
        assert get_evidence_tier("specification") == EvidenceTier.TIER_2
        assert get_evidence_tier("peer-reviewed paper") == EvidenceTier.TIER_2
        assert get_evidence_tier("API docs") == EvidenceTier.TIER_2

    def test_tier_3_derived_analysis(self) -> None:
        """Derived analysis should map to Tier 3."""
        assert get_evidence_tier("static analysis") == EvidenceTier.TIER_3
        assert get_evidence_tier("logical derivation") == EvidenceTier.TIER_3
        assert get_evidence_tier("code review") == EvidenceTier.TIER_3
        assert get_evidence_tier("architecture analysis") == EvidenceTier.TIER_3

    def test_tier_4_unverified_sources(self) -> None:
        """Unverified sources should map to Tier 4."""
        assert get_evidence_tier("code comment") == EvidenceTier.TIER_4
        assert get_evidence_tier("unverified claim") == EvidenceTier.TIER_4
        assert get_evidence_tier("anecdotal") == EvidenceTier.TIER_4
        assert get_evidence_tier("opinion") == EvidenceTier.TIER_4

    def test_unknown_source(self) -> None:
        """Unknown source types should return None."""
        assert get_evidence_tier("unknown") is None
        assert get_evidence_tier("random text") is None


class TestRequiresHighStakesEvidence:
    """Test high-stakes evidence requirements."""

    def test_tier_1_sufficient(self) -> None:
        """Tier 1 alone should not require high-stakes warning."""
        assert not requires_high_stakes_evidence([EvidenceTier.TIER_1])

    def test_tier_2_sufficient(self) -> None:
        """Tier 2 alone should not require high-stakes warning."""
        assert not requires_high_stakes_evidence([EvidenceTier.TIER_2])

    def test_tier_1_and_2_sufficient(self) -> None:
        """Tier 1 + 2 should not require high-stakes warning."""
        assert not requires_high_stakes_evidence([
            EvidenceTier.TIER_1,
            EvidenceTier.TIER_2
        ])

    def test_tier_3_insufficient(self) -> None:
        """Tier 3 alone should trigger high-stakes warning."""
        assert requires_high_stakes_evidence([EvidenceTier.TIER_3])

    def test_tier_4_insufficient(self) -> None:
        """Tier 4 alone should trigger high-stakes warning."""
        assert requires_high_stakes_evidence([EvidenceTier.TIER_4])

    def test_tier_3_and_4_insufficient(self) -> None:
        """Tier 3 + 4 should trigger high-stakes warning."""
        assert requires_high_stakes_evidence([
            EvidenceTier.TIER_3,
            EvidenceTier.TIER_4
        ])

    def test_empty_no_warning(self) -> None:
        """Empty tier list should not trigger warning."""
        assert not requires_high_stakes_evidence([])


class TestShouldFlagUnverified:
    """Test [UNVERIFIED] flagging rules."""

    def test_tier_4_alone_flags(self) -> None:
        """Tier 4 alone should be flagged as [UNVERIFIED]."""
        assert should_flag_unverified([EvidenceTier.TIER_4])

    def test_tier_1_with_4_no_flag(self) -> None:
        """Tier 1 + Tier 4 should NOT be flagged (mixed evidence)."""
        assert not should_flag_unverified([
            EvidenceTier.TIER_1,
            EvidenceTier.TIER_4
        ])

    def test_tier_1_alone_no_flag(self) -> None:
        """Tier 1 alone should NOT be flagged."""
        assert not should_flag_unverified([EvidenceTier.TIER_1])

    def test_empty_no_flag(self) -> None:
        """Empty tier list should NOT be flagged."""
        assert not should_flag_unverified([])


class TestFormatConfidenceLabel:
    """Test confidence label formatting."""

    def test_unverified_label(self) -> None:
        """Tier 4 alone should show [UNVERIFIED] label."""
        label = format_confidence_label([EvidenceTier.TIER_4], 0.50)
        assert "[UNVERIFIED]" in label
        assert "50%" in label

    def test_tier_1_label(self) -> None:
        """Tier 1 should show source description."""
        label = format_confidence_label([EvidenceTier.TIER_1], 0.90)
        assert "90%" in label
        assert "Tier 1" in label

    def test_tier_2_label(self) -> None:
        """Tier 2 should show source description."""
        label = format_confidence_label([EvidenceTier.TIER_2], 0.80)
        assert "80%" in label
        assert "Tier 2" in label

    def test_empty_tiers_label(self) -> None:
        """Empty tiers should show confidence without tier info."""
        label = format_confidence_label([], 0.75)
        assert label == "75%"

    def test_mixed_tiers_shows_lowest(self) -> None:
        """Mixed tiers should show lowest tier in label."""
        # Tier 1 + Tier 4 = show Tier 4 ceiling
        label = format_confidence_label([
            EvidenceTier.TIER_1,
            EvidenceTier.TIER_4
        ], 0.50)
        # Should NOT show [UNVERIFIED] because mixed evidence
        assert "[UNVERIFIED]" not in label
        assert "50%" in label
