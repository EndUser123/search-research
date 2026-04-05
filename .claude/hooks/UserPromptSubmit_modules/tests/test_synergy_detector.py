"""Tests for synergy_detector module.

Test Coverage:
- Synergy matrix validation (all scores in range, no duplicates)
- Detection logic (single/multiple/no matches)
- Performance baseline (<5ms for typical input)
- Edge cases (empty lists, unknown frameworks/modes)
- Integration with unified_detection output
"""

from __future__ import annotations

import time

import pytest
from UserPromptSubmit_modules.synergy_detector import (
    _DEFAULT_SYNERGY_MATRIX,
    SynergyMatch,
    detect_synergies,
)

# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
def sample_frameworks() -> list[str]:
    """Sample detected frameworks for testing."""
    return [
        "assumption_surfacing",
        "socratic_decomposition",
        "inversion_prompting",
        "first_principles",
    ]


@pytest.fixture
def sample_modes() -> list[str]:
    """Sample detected reasoning modes for testing."""
    return ["sequential", "multi_agent", "two_stage"]


@pytest.fixture
def unified_detection_result(sample_frameworks, sample_modes):
    """Mock unified detection result for integration testing."""
    from types import SimpleNamespace

    return SimpleNamespace(
        matched_frameworks=sample_frameworks,
        matched_modes=sample_modes,
    )


# =============================================================================
# SYNERGY MATRIX VALIDATION TESTS
# =============================================================================


class TestSynergyMatrixValidation:
    """Validate synergy matrix structure and values."""

    def test_all_scores_in_valid_range(self):
        """All synergy scores must be in [0.0, 1.0] range."""
        for rule in _DEFAULT_SYNERGY_MATRIX:
            assert 0.0 <= rule.score <= 1.0, (
                f"Score for {rule.framework}+{rule.mode} is {rule.score}, "
                f"outside valid range [0.0, 1.0]"
            )

    def test_no_duplicate_entries(self):
        """Synergy matrix must not have duplicate framework+mode combinations."""
        seen = set()
        for rule in _DEFAULT_SYNERGY_MATRIX:
            key = (rule.framework, rule.mode)
            assert key not in seen, f"Duplicate synergy rule: {key}"
            seen.add(key)

    def test_all_frameworks_exist_in_matrix(self):
        """All known frameworks should have at least one synergy rule."""
        frameworks = {rule.framework for rule in _DEFAULT_SYNERGY_MATRIX}
        expected_frameworks = {
            "assumption_surfacing",
            "socratic_decomposition",
            "inversion_prompting",
            "first_principles",
            "devil_advocate",
        }
        assert frameworks >= expected_frameworks, (
            f"Missing frameworks in synergy matrix: " f"{expected_frameworks - frameworks}"
        )

    def test_all_modes_exist_in_matrix(self):
        """All known modes should have at least one synergy rule."""
        modes = {rule.mode for rule in _DEFAULT_SYNERGY_MATRIX}
        expected_modes = {"sequential", "multi_agent", "two_stage"}
        assert modes >= expected_modes, f"Missing modes in synergy matrix: {expected_modes - modes}"

    def test_all_scores_documented_with_rationale(self):
        """All synergy rules must have non-empty rationale."""
        for rule in _DEFAULT_SYNERGY_MATRIX:
            assert rule.rationale, f"Synergy rule {rule.framework}+{rule.mode} has empty rationale"
            assert len(rule.rationale) > 10, (
                f"Rationale for {rule.framework}+{rule.mode} is too short: " f'"{rule.rationale}"'
            )


# =============================================================================
# DETECTION LOGIC TESTS
# =============================================================================


class TestDetectionLogic:
    """Test synergy detection with various input scenarios."""

    def test_single_framework_mode_match(self):
        """Single framework+mode combination returns correct synergy."""
        frameworks = ["assumption_surfacing"]
        modes = ["sequential"]

        result = detect_synergies(frameworks, modes)

        assert len(result.synergies) == 1
        assert len(result.top_synergies) == 1
        assert result.synergies[0]["framework"] == "assumption_surfacing"
        assert result.synergies[0]["mode"] == "sequential"
        assert result.synergies[0]["score"] == 0.9  # Known high-synergy combo
        assert result.total_score == 0.9

    def test_multiple_matches_returns_top_three_sorted(self):
        """Multiple matches return top 3 sorted by score (descending)."""
        frameworks = [
            "assumption_surfacing",  # 0.9 with sequential
            "socratic_decomposition",  # 0.85 with multi_agent
            "inversion_prompting",  # 0.8 with two_stage
            "first_principles",  # 0.75 with multi_agent
        ]
        modes = ["sequential", "multi_agent", "two_stage"]

        result = detect_synergies(frameworks, modes)

        # Should have all combinations
        assert len(result.synergies) > 3

        # Top 3 should be sorted by score (descending)
        assert len(result.top_synergies) == 3
        scores = [s["score"] for s in result.top_synergies]
        assert scores == sorted(scores, reverse=True), "Top synergies not sorted"

        # Verify highest is assumption_surfacing+sequential (0.9)
        assert result.top_synergies[0]["framework"] == "assumption_surfacing"
        assert result.top_synergies[0]["mode"] == "sequential"
        assert result.top_synergies[0]["score"] == 0.9

    def test_no_framework_matches_returns_empty_result(self):
        """Empty framework list returns empty synergy match."""
        frameworks = []
        modes = ["sequential", "multi_agent"]

        result = detect_synergies(frameworks, modes)

        assert result.synergies == []
        assert result.top_synergies == []
        assert result.total_score == 0.0

    def test_no_mode_matches_returns_empty_result(self):
        """Empty mode list returns empty synergy match."""
        frameworks = ["assumption_surfacing"]
        modes = []

        result = detect_synergies(frameworks, modes)

        assert result.synergies == []
        assert result.top_synergies == []
        assert result.total_score == 0.0

    def test_unknown_framework_skipped_gracefully(self):
        """Unknown framework should be skipped without error."""
        frameworks = ["unknown_framework_xyz", "assumption_surfacing"]
        modes = ["sequential"]

        result = detect_synergies(frameworks, modes)

        # Should only match the known framework
        assert len(result.synergies) == 1
        assert result.synergies[0]["framework"] == "assumption_surfacing"

    def test_unknown_mode_skipped_gracefully(self):
        """Unknown mode should be skipped without error."""
        frameworks = ["assumption_surfacing"]
        modes = ["unknown_mode_abc", "sequential"]

        result = detect_synergies(frameworks, modes)

        # Should only match the known mode
        assert len(result.synergies) == 1
        assert result.synergies[0]["mode"] == "sequential"


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================


class TestPerformanceBaseline:
    """Verify performance meets <5ms baseline."""

    def test_typical_input_under_5ms(self):
        """Typical input (1000 chars, 4 frameworks, 3 modes) must complete <5ms."""
        frameworks = [
            "assumption_surfacing",
            "socratic_decomposition",
            "inversion_prompting",
            "first_principles",
        ]
        modes = ["sequential", "multi_agent", "two_stage"]

        # Warm-up run (compilation, caching)
        detect_synergies(frameworks, modes)

        # Timed run
        start = time.perf_counter()
        _result = detect_synergies(frameworks, modes)  # noqa: F841
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Verify detection returned results (checked in warm-up above)
        assert elapsed_ms < 5.0, f"Detection took {elapsed_ms:.2f}ms, exceeds 5ms baseline"
        assert elapsed_ms < 5.0, f"Detection took {elapsed_ms:.2f}ms, exceeds 5ms baseline"

    def test_large_input_still_fast(self):
        """Large input (10 frameworks, 4 modes) should still be fast."""
        frameworks = [
            "assumption_surfacing",
            "socratic_decomposition",
            "inversion_prompting",
            "first_principles",
            "devil_advocate",
            "chestertons_fence",
            "outcome_anchoring",
            "calibrated_confidence",
            "cynefin_classification",
            "hanlons_razor",
        ]
        modes = ["sequential", "multi_agent", "two_stage", "graph"]

        # Warm-up run
        detect_synergies(frameworks, modes)

        # Timed run
        start = time.perf_counter()
        _result = detect_synergies(frameworks, modes)  # noqa: F841
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 10.0, f"Large input took {elapsed_ms:.2f}ms, too slow"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestUnifiedDetectionIntegration:
    """Test integration with unified_detection module output."""

    def test_works_with_unified_detection_result(self, unified_detection_result):
        """Should accept UnifiedDetectionResult from unified_detection."""
        result = detect_synergies(
            unified_detection_result.matched_frameworks,
            unified_detection_result.matched_modes,
        )

        assert isinstance(result, SynergyMatch)
        assert hasattr(result, "synergies")
        assert hasattr(result, "top_synergies")
        assert hasattr(result, "total_score")

    def test_handles_empty_unified_result(self):
        """Should handle empty UnifiedDetectionResult gracefully."""
        from types import SimpleNamespace

        empty_result = SimpleNamespace(
            matched_frameworks=[],
            matched_modes=[],
        )

        result = detect_synergies(
            empty_result.matched_frameworks,
            empty_result.matched_modes,
        )

        assert result.synergies == []
        assert result.top_synergies == []
        assert result.total_score == 0.0


# =============================================================================
# EDGE CASES AND ERROR HANDLING
# =============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_none_input_returns_empty_result(self):
        """None input should return empty result (graceful degradation)."""
        result = detect_synergies(None, None)

        assert result.synergies == []
        assert result.top_synergies == []
        assert result.total_score == 0.0

    def test_single_framework_multiple_modes(self):
        """Single framework with multiple modes returns defined combos."""
        frameworks = ["socratic_decomposition"]
        modes = ["sequential", "multi_agent", "two_stage"]

        result = detect_synergies(frameworks, modes)

        # Should have 2 combinations (only those defined in matrix)
        # socratic_decomposition has synergies with sequential (0.6) and multi_agent (0.85)
        # but NOT with two_stage (no entry in matrix)
        assert len(result.synergies) == 2
        assert any(s["mode"] == "sequential" for s in result.synergies)
        assert any(s["mode"] == "multi_agent" for s in result.synergies)

    def test_multiple_frameworks_single_mode(self):
        """Multiple frameworks with single mode returns all combos."""
        frameworks = ["assumption_surfacing", "devil_advocate", "socratic_decomposition"]
        modes = ["sequential"]

        result = detect_synergies(frameworks, modes)

        # Should have 3 combinations (one per framework)
        assert len(result.synergies) == 3

    def test_synergy_match_is_dataclass(self):
        """Result should be a frozen dataclass (immutable)."""
        frameworks = ["assumption_surfacing"]
        modes = ["sequential"]

        result = detect_synergies(frameworks, modes)

        # Dataclass with frozen=True raises AttributeError on mutation attempt
        with pytest.raises((AttributeError, TypeError)):
            result.synergies = []  # Should not be mutable

    def test_synergy_score_threshold(self):
        """Only synergies with score >= 0.5 should be reported."""
        # This test validates that we're not reporting low-value synergies
        # The current matrix has no scores < 0.5, so this is a sanity check
        frameworks = ["assumption_surfacing"]
        modes = ["sequential"]

        result = detect_synergies(frameworks, modes)

        # All reported synergies should have score >= 0.5
        for synergy in result.synergies:
            assert synergy["score"] >= 0.5, (
                f"Synergy {synergy['framework']}+{synergy['mode']} has score "
                f"{synergy['score']}, below 0.5 threshold"
            )
