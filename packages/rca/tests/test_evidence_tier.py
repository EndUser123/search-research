"""Tests for evidence_tier module.

NOTE: Creating new test file for evidence_tier module which currently has no test coverage.
Task: #988 - Evidence Tiering for rca
"""

import pytest

from rca.evidence_tier import (
    EvidenceSource,
    EvidenceTier,
    EvidenceLedger,
    classify_evidence,
    get_lowest_tier,
    get_confidence_ceiling,
    apply_ceiling,
    format_evidence_summary,
    SOURCE_TYPE_TIERS,
)


class TestEvidenceTier:
    """Tests for EvidenceTier enum."""

    def test_tier_values(self):
        """Test that tier values are sequential integers."""
        assert EvidenceTier.TIER_1 == 1
        assert EvidenceTier.TIER_2 == 2
        assert EvidenceTier.TIER_3 == 3
        assert EvidenceTier.TIER_4 == 4

    def test_tier_comparison(self):
        """Test that tiers can be compared."""
        assert EvidenceTier.TIER_1 < EvidenceTier.TIER_2
        assert EvidenceTier.TIER_2 < EvidenceTier.TIER_3
        assert EvidenceTier.TIER_3 < EvidenceTier.TIER_4


class TestEvidenceSource:
    """Tests for EvidenceSource dataclass."""

    def test_evidence_source_creation(self):
        """Test creating an EvidenceSource."""
        source = EvidenceSource(
            source_type="stack_trace",
            description="Error in main.py",
            tier=EvidenceTier.TIER_2,
        )
        assert source.source_type == "stack_trace"
        assert source.description == "Error in main.py"
        assert source.tier == EvidenceTier.TIER_2

    def test_evidence_source_equality(self):
        """Test EvidenceSource equality."""
        source1 = EvidenceSource("stack_trace", "Error", EvidenceTier.TIER_2)
        source2 = EvidenceSource("stack_trace", "Error", EvidenceTier.TIER_2)
        source3 = EvidenceSource("user_report", "Error", EvidenceTier.TIER_4)

        assert source1 == source2
        assert source1 != source3


class TestClassifyEvidence:
    """Tests for classify_evidence function."""

    def test_classify_tier_1_evidence(self):
        """Test classification of tier 1 evidence sources."""
        tier_1_sources = ["reproduction_script", "failing_test", "debugger_breakpoint"]
        for source_type in tier_1_sources:
            result = classify_evidence(source_type)
            assert isinstance(result, EvidenceSource)
            assert result.source_type == source_type
            assert result.tier == EvidenceTier.TIER_1

    def test_classify_tier_2_evidence(self):
        """Test classification of tier 2 evidence sources."""
        tier_2_sources = ["stack_trace", "assertion_failure", "git_bisect_result"]
        for source_type in tier_2_sources:
            result = classify_evidence(source_type)
            assert isinstance(result, EvidenceSource)
            assert result.source_type == source_type
            assert result.tier == EvidenceTier.TIER_2

    def test_classify_tier_3_evidence(self):
        """Test classification of tier 3 evidence sources."""
        tier_3_sources = ["log_correlation", "timing_analysis", "metric_spike"]
        for source_type in tier_3_sources:
            result = classify_evidence(source_type)
            assert isinstance(result, EvidenceSource)
            assert result.source_type == source_type
            assert result.tier == EvidenceTier.TIER_3

    def test_classify_tier_4_evidence(self):
        """Test classification of tier 4 evidence sources."""
        tier_4_sources = ["user_report", "speculation", "cannot_reproduce"]
        for source_type in tier_4_sources:
            result = classify_evidence(source_type)
            assert isinstance(result, EvidenceSource)
            assert result.source_type == source_type
            assert result.tier == EvidenceTier.TIER_4

    def test_classify_with_description(self):
        """Test classification with description."""
        result = classify_evidence("stack_trace", "Error in function at line 42")
        assert result.description == "Error in function at line 42"

    def test_classify_unknown_source_type(self):
        """Test that unknown source types default to tier 4."""
        result = classify_evidence("unknown_type")
        assert result.tier == EvidenceTier.TIER_4

    def test_classify_case_insensitive(self):
        """Test that source_type matching is case-insensitive."""
        result = classify_evidence("STACK_TRACE")
        assert result.tier == EvidenceTier.TIER_2


class TestGetLowestTier:
    """Tests for get_lowest_tier function."""

    def test_get_lowest_tier_single_source(self):
        """Test with a single evidence source."""
        sources = [EvidenceSource("stack_trace", "", EvidenceTier.TIER_2)]
        result = get_lowest_tier(sources)
        assert result == EvidenceTier.TIER_2

    def test_get_lowest_tier_multiple_sources(self):
        """Test with multiple evidence sources."""
        sources = [
            EvidenceSource("stack_trace", "", EvidenceTier.TIER_2),
            EvidenceSource("user_report", "", EvidenceTier.TIER_4),
            EvidenceSource("failing_test", "", EvidenceTier.TIER_1),
        ]
        result = get_lowest_tier(sources)
        # "Lowest tier" = weakest evidence = highest tier number
        assert result == EvidenceTier.TIER_4

    def test_get_lowest_tier_empty_list(self):
        """Test with empty list returns tier 4."""
        result = get_lowest_tier([])
        assert result == EvidenceTier.TIER_4

    def test_get_lowest_tier_all_same_tier(self):
        """Test with all sources at same tier."""
        sources = [
            EvidenceSource("user_report", "", EvidenceTier.TIER_4),
            EvidenceSource("speculation", "", EvidenceTier.TIER_4),
        ]
        result = get_lowest_tier(sources)
        assert result == EvidenceTier.TIER_4

    def test_get_lowest_tier_all_tiers(self):
        """Test with sources at all tiers."""
        sources = [
            EvidenceSource("failing_test", "", EvidenceTier.TIER_1),
            EvidenceSource("stack_trace", "", EvidenceTier.TIER_2),
            EvidenceSource("log_correlation", "", EvidenceTier.TIER_3),
            EvidenceSource("user_report", "", EvidenceTier.TIER_4),
        ]
        result = get_lowest_tier(sources)
        # "Lowest tier" = weakest evidence = highest tier number
        assert result == EvidenceTier.TIER_4


class TestSourceTypeTiers:
    """Tests for SOURCE_TYPE_TIERS constant."""

    def test_all_source_types_have_valid_tiers(self):
        """Test that all source types map to valid tiers."""
        for source_type, tier in SOURCE_TYPE_TIERS.items():
            assert isinstance(source_type, str)
            assert tier in (EvidenceTier.TIER_1, EvidenceTier.TIER_2, EvidenceTier.TIER_3, EvidenceTier.TIER_4)

    def test_source_type_tiers_is_lowercase(self):
        """Test that all source type keys are lowercase."""
        for source_type in SOURCE_TYPE_TIERS:
            assert source_type == source_type.lower()


# New tests for Task #988 enhancements

class TestEvidenceTierConfidenceCeiling:
    """Tests for EvidenceTier confidence_ceiling method."""

    def test_confidence_ceiling_tier_1(self):
        """Test Tier 1 has 95% ceiling."""
        assert EvidenceTier.TIER_1.confidence_ceiling() == 0.95

    def test_confidence_ceiling_tier_2(self):
        """Test Tier 2 has 85% ceiling."""
        assert EvidenceTier.TIER_2.confidence_ceiling() == 0.85

    def test_confidence_ceiling_tier_3(self):
        """Test Tier 3 has 75% ceiling."""
        assert EvidenceTier.TIER_3.confidence_ceiling() == 0.75

    def test_confidence_ceiling_tier_4(self):
        """Test Tier 4 has 50% ceiling."""
        assert EvidenceTier.TIER_4.confidence_ceiling() == 0.50


class TestEvidenceSourceConfidenceCeiling:
    """Tests for EvidenceSource confidence_ceiling property."""

    def test_confidence_ceiling_property(self):
        """Test EvidenceSource has confidence_ceiling property."""
        source = EvidenceSource("failing_test", "Test fails", EvidenceTier.TIER_1)
        assert source.confidence_ceiling == 0.95

    def test_is_unverified_tier_4(self):
        """Test is_unverified returns True for Tier 4."""
        source = EvidenceSource("speculation", "Maybe", EvidenceTier.TIER_4)
        assert source.is_unverified()

    def test_is_not_unverified_tier_1(self):
        """Test is_unverified returns False for Tier 1."""
        source = EvidenceSource("failing_test", "Test fails", EvidenceTier.TIER_1)
        assert not source.is_unverified()

    def test_applies_to_claim_basic(self):
        """Test applies_to_claim with basic keyword matching."""
        source = EvidenceSource("failing_test", "test fails in authentication", EvidenceTier.TIER_1)
        assert source.applies_to_claim("authentication bug")

    def test_applies_to_claim_no_match(self):
        """Test applies_to_claim when no match."""
        source = EvidenceSource("failing_test", "database connection error", EvidenceTier.TIER_1)
        assert not source.applies_to_claim("UI rendering issue")


class TestGetConfidenceCeiling:
    """Tests for get_confidence_ceiling function."""

    def test_single_source_ceiling(self):
        """Test ceiling from single source."""
        sources = [classify_evidence("failing_test", "Test fails")]
        assert get_confidence_ceiling(sources) == 0.95

    def test_mixed_tier_uses_lowest(self):
        """Test that mixed tiers use the lowest tier's ceiling."""
        sources = [
            classify_evidence("failing_test", "Test fails"),
            classify_evidence("speculation", "Maybe race condition"),
        ]
        assert get_confidence_ceiling(sources) == 0.50

    def test_empty_sources_defaults_to_tier_4(self):
        """Test empty sources list defaults to Tier 4 ceiling."""
        assert get_confidence_ceiling([]) == 0.50


class TestApplyCeiling:
    """Tests for apply_ceiling function."""

    def test_apply_ceiling_below_threshold(self):
        """Test confidence below ceiling is unchanged."""
        sources = [classify_evidence("speculation", "Maybe")]
        assert apply_ceiling(0.4, sources) == 0.4

    def test_apply_ceiling_above_threshold(self):
        """Test confidence above ceiling is capped."""
        sources = [classify_evidence("speculation", "Maybe")]
        assert apply_ceiling(0.9, sources) == 0.5

    def test_apply_ceiling_at_threshold(self):
        """Test confidence at ceiling is unchanged."""
        sources = [classify_evidence("failing_test", "Test fails")]
        assert apply_ceiling(0.95, sources) == 0.95


class TestFormatEvidenceSummary:
    """Tests for format_evidence_summary function."""

    def test_format_empty_evidence(self):
        """Test formatting with no evidence."""
        summary = format_evidence_summary([])
        assert "No evidence" in summary

    def test_format_single_evidence(self):
        """Test formatting single evidence source."""
        sources = [classify_evidence("failing_test", "Test fails")]
        summary = format_evidence_summary(sources)
        assert "TIER_1" in summary
        assert "95%" in summary

    def test_format_mixed_tiers(self):
        """Test formatting with mixed tiers."""
        sources = [
            classify_evidence("failing_test", "Test fails"),
            classify_evidence("speculation", "Maybe"),
        ]
        summary = format_evidence_summary(sources)
        assert "TIER_1" in summary
        assert "TIER_4" in summary
        assert "50%" in summary  # Lowest tier ceiling

    def test_format_unverified_warning(self):
        """Test unverified warning appears for Tier 4 only."""
        sources = [classify_evidence("speculation", "Maybe")]
        summary = format_evidence_summary(sources)
        assert "UNVERIFIED" in summary
        assert "WARNING" in summary


class TestEvidenceLedger:
    """Tests for EvidenceLedger class."""

    def test_ledger_creation(self):
        """Test creating an evidence ledger."""
        ledger = EvidenceLedger(claim="Database timeout")
        assert ledger.claim == "Database timeout"
        assert len(ledger.sources) == 0

    def test_ledger_add_evidence(self):
        """Test adding evidence to ledger."""
        ledger = EvidenceLedger()
        source = classify_evidence("failing_test", "Test fails")
        ledger.add_evidence(source)
        assert len(ledger.sources) == 1

    def test_ledger_add_classified(self):
        """Test add_classified method."""
        ledger = EvidenceLedger()
        source = ledger.add_classified("stack_trace", "Error in main.py")
        assert len(ledger.sources) == 1
        assert source.source_type == "stack_trace"

    def test_ledger_confidence_ceiling(self):
        """Test ledger confidence ceiling calculation."""
        ledger = EvidenceLedger()
        ledger.add_classified("failing_test", "Test fails")
        assert ledger.confidence_ceiling() == 0.95

    def test_ledger_lowest_tier(self):
        """Test ledger lowest tier tracking."""
        ledger = EvidenceLedger()
        ledger.add_classified("failing_test", "Test fails")
        ledger.add_classified("speculation", "Maybe")
        assert ledger.lowest_tier() == EvidenceTier.TIER_4

    def test_ledger_is_unverified(self):
        """Test is_unverified detection."""
        ledger = EvidenceLedger()
        assert ledger.is_unverified()  # Empty means unverified

        ledger.add_classified("failing_test", "Test fails")
        assert not ledger.is_unverified()

        ledger.add_classified("speculation", "Maybe")
        assert ledger.is_unverified()  # Now has Tier 4

    def test_ledger_summary(self):
        """Test ledger summary formatting."""
        ledger = EvidenceLedger(claim="Database timeout")
        ledger.add_classified("failing_test", "Test fails")
        summary = ledger.summary()
        assert "Database timeout" in summary
        assert "TIER_1" in summary
        assert "95%" in summary

    def test_ledger_filter_by_tier(self):
        """Test filtering evidence by tier."""
        ledger = EvidenceLedger()
        ledger.add_classified("failing_test", "Test fails")
        ledger.add_classified("speculation", "Maybe")

        tier_1 = ledger.filter_by_tier(EvidenceTier.TIER_1)
        tier_4 = ledger.filter_by_tier(EvidenceTier.TIER_4)

        assert len(tier_1) == 1
        assert len(tier_4) == 1

    def test_ledger_count_by_tier(self):
        """Test counting evidence by tier."""
        ledger = EvidenceLedger()
        ledger.add_classified("failing_test", "Test fails")
        ledger.add_classified("stack_trace", "Error in main.py")
        ledger.add_classified("speculation", "Maybe")

        counts = ledger.count_by_tier()
        # failing_test is TIER_1, stack_trace is TIER_2, speculation is TIER_4
        assert counts[EvidenceTier.TIER_1] == 1
        assert counts[EvidenceTier.TIER_2] == 1
        assert counts[EvidenceTier.TIER_4] == 1
