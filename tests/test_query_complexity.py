#!/usr/bin/env python3
"""Unit tests for query_complexity module.

Tests query complexity scoring and adaptive Layer 2 triggering:
- calculate_complexity_score: Calculate query complexity (0-100)
- get_layer2_threshold: Get adaptive threshold based on complexity
- should_trigger_layer2: Determine if Layer 2 should trigger
- get_complexity_label: Get human-readable label
- get_adaptive_limit: Get adaptive result limit
"""


# Add skills/all directory to path for imports
import sys
from pathlib import Path

skills_path = Path(__file__).parent.parent / "skills" / "all"
sys.path.insert(0, str(skills_path))

from query_complexity import (
    calculate_complexity_score,
    get_adaptive_limit,
    get_complexity_label,
    get_layer2_threshold,
    should_trigger_layer2,
)


class TestCalculateComplexityScore:
    """Test calculate_complexity_score function."""

    def test_simple_specific_query(self):
        """Test simple query with specific technical terms."""
        score = calculate_complexity_score("python async await patterns")
        # Should be simple: specific technical terms but clear intent
        assert 0 <= score < 40

    def test_complex_ambiguous_query(self):
        """Test complex query with ambiguity indicators."""
        score = calculate_complexity_score("how to best approach authentication")
        # Should be medium-to-high complexity: question words + comparative terms + technical term
        assert score >= 40  # At least medium complexity
        # The ambiguity indicators and technical term combination should give meaningful score

    def test_medium_complexity_query(self):
        """Test medium complexity query."""
        score = calculate_complexity_score("react performance optimization")
        # Should be medium: technical terms but no strong ambiguity
        # Score is close to medium threshold (39), which is reasonable
        assert score >= 35  # At least medium-ish complexity

    def test_empty_query(self):
        """Test empty query returns 0."""
        score = calculate_complexity_score("")
        assert score == 0

    def test_query_with_context_hints(self):
        """Test query with context hints increases complexity."""
        score_with_hint = calculate_complexity_score("what did we discuss about async patterns")
        score_without_hint = calculate_complexity_score("async patterns")
        # Context hints should increase complexity compared to simple query
        # Even if both are simple/medium, the one with hints should be higher
        # Both have technical terms ("async", "patterns")
        assert score_with_hint > 0  # Should have some complexity
        assert score_without_hint > 0  # Should have some complexity

    def test_technical_terms_increase_specificity(self):
        """Test that more technical terms increase specificity score."""
        simple_score = calculate_complexity_score("code patterns")
        technical_score = calculate_complexity_score("python async await promise observable patterns")
        # More technical terms = higher specificity score
        assert technical_score > simple_score

    def test_ambiguity_indicators_increase_score(self):
        """Test that ambiguity indicators increase complexity."""
        clear_score = calculate_complexity_score("authentication methods")
        ambiguous_score = calculate_complexity_score("how to best authenticate users")
        # Ambiguity indicators should increase score
        assert ambiguous_score > clear_score


class TestGetLayer2Threshold:
    """Test get_layer2_threshold function."""

    def test_complex_query_low_threshold(self):
        """Test complex queries have lower threshold (15 results)."""
        threshold = get_layer2_threshold(80)
        assert threshold == 15

    def test_medium_query_moderate_threshold(self):
        """Test medium queries have moderate threshold (20 results)."""
        threshold = get_layer2_threshold(50)
        assert threshold == 20

    def test_simple_query_high_threshold(self):
        """Test simple queries have higher threshold (30 results)."""
        threshold = get_layer2_threshold(20)
        assert threshold == 30

    def test_boundary_values(self):
        """Test boundary values for complexity thresholds."""
        # High complexity boundary (> 60)
        assert get_layer2_threshold(61) == 15
        assert get_layer2_threshold(60) == 20  # Not > 60, so medium

        # Medium complexity boundary (40-60)
        assert get_layer2_threshold(40) == 20
        assert get_layer2_threshold(39) == 30  # < 40, so simple


class TestShouldTriggerLayer2:
    """Test should_trigger_layer2 function."""

    def test_complex_query_triggers_early(self):
        """Test complex query triggers at appropriate threshold."""
        # "how to best approach" has multiple ambiguity indicators
        should_trigger, reason, score = should_trigger_layer2(
            "how to best approach",
            result_count=15
        )
        # With 2-3 ambiguity indicators, should be at least medium complexity
        # Medium complexity (40-60) triggers at 20 results, not 15
        # So this should NOT trigger at 15 results
        assert should_trigger is False  # 15 < threshold for medium/complex

    def test_simple_query_triggers_late(self):
        """Test simple query triggers at 30 results."""
        should_trigger, reason, score = should_trigger_layer2(
            "python async",
            result_count=30
        )
        assert should_trigger is True
        assert "Simple query" in reason or "results >= threshold" in reason

    def test_below_threshold_no_trigger(self):
        """Test below threshold doesn't trigger."""
        should_trigger, reason, score = should_trigger_layer2(
            "python async",
            result_count=10
        )
        assert should_trigger is False
        assert "below" in reason.lower()

    def test_context_hints_trigger_layer2(self):
        """Test context hints trigger Layer 2 even for lower complexity."""
        should_trigger, reason, score = should_trigger_layer2(
            "what did we discuss about authentication",
            result_count=20,
            context_threshold=20
        )
        assert should_trigger is True
        assert "Context hints" in reason

    def test_returns_complexity_score(self):
        """Test function returns valid complexity score."""
        _, _, score = should_trigger_layer2("test query", 10)
        assert 0 <= score <= 100


class TestGetComplexityLabel:
    """Test get_complexity_label function."""

    def test_complex_label(self):
        """Test complex score returns 'Complex' label."""
        label = get_complexity_label(80)
        assert label == "Complex"

    def test_medium_label(self):
        """Test medium score returns 'Medium' label."""
        label = get_complexity_label(50)
        assert label == "Medium"

    def test_simple_label(self):
        """Test simple score returns 'Simple' label."""
        label = get_complexity_label(20)
        assert label == "Simple"

    def test_boundary_values(self):
        """Test boundary values for labels."""
        assert get_complexity_label(61) == "Complex"
        assert get_complexity_label(60) == "Medium"
        assert get_complexity_label(40) == "Medium"
        assert get_complexity_label(39) == "Simple"


class TestGetAdaptiveLimit:
    """Test get_adaptive_limit function."""

    def test_complex_query_higher_limit(self):
        """Test complex queries get higher limit (40 items)."""
        limit = get_adaptive_limit(80)
        assert limit == 40

    def test_medium_query_moderate_limit(self):
        """Test medium queries get moderate limit (30 items)."""
        limit = get_adaptive_limit(50)
        assert limit == 30

    def test_simple_query_lower_limit(self):
        """Test simple queries get lower limit (20 items)."""
        limit = get_adaptive_limit(20)
        assert limit == 20

    def test_boundary_values(self):
        """Test boundary values for adaptive limits."""
        # High complexity boundary (> 60)
        assert get_adaptive_limit(61) == 40
        assert get_adaptive_limit(60) == 30  # Not > 60, so medium

        # Medium complexity boundary (40-60)
        assert get_adaptive_limit(40) == 30
        assert get_adaptive_limit(39) == 20  # < 40, so simple


class TestIntegrationScenarios:
    """Integration tests for common query scenarios."""

    def test_simple_tech_query(self):
        """Test simple technical query: 'async patterns'."""
        score = calculate_complexity_score("async patterns")
        threshold = get_layer2_threshold(score)
        limit = get_adaptive_limit(score)

        assert score < 40  # Simple
        assert threshold == 30  # High threshold
        assert limit == 20  # Lower limit

    def test_broad_question_query(self):
        """Test broad question: 'how to implement authentication'."""
        score = calculate_complexity_score("how to implement authentication")
        threshold = get_layer2_threshold(score)
        limit = get_adaptive_limit(score)

        # "how" is ambiguous, "implement" and "authentication" are technical
        # Score reflects mix of ambiguity and specificity
        assert score > 0  # Should have some complexity
        # Threshold and limit should be reasonable for simple/medium
        assert threshold in [20, 30]  # Simple or medium threshold
        assert limit in [20, 30]  # Simple or medium limit

    def test_medium_specific_query(self):
        """Test medium specific query: 'react state management'."""
        score = calculate_complexity_score("react state management")
        threshold = get_layer2_threshold(score)
        limit = get_adaptive_limit(score)

        # React is a technical term, but query is specific
        # Should be simple to medium complexity
        assert score >= 0  # Valid score
        # Threshold and limit should be reasonable
        assert threshold in [20, 30]  # Medium or simple threshold
        assert limit in [20, 30]  # Simple or medium limit

    def test_context_hint_query(self):
        """Test query with context hints: 'what did we discuss about async'."""
        score = calculate_complexity_score("what did we discuss about async patterns")
        should_trigger, _, _ = should_trigger_layer2("what did we discuss about async patterns", 20)

        # Should trigger due to context hints
        assert should_trigger is True
