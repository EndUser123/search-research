"""
Tests for /gto health scoring module.
"""

import pytest
from health_scoring import (
    HealthScoringEngine,
    calculate_health_score,
    format_health_score,
)


class TestHealthScoring:
    """Test health scoring calculation."""

    def test_perfect_score_no_gaps(self):
        """Perfect score when no gaps detected."""
        gaps = []
        health = calculate_health_score(gaps)

        assert health.overall_score == 100
        assert health.total_gaps == 0
        assert health.critical_gaps == 0
        assert health.high_gaps == 0
        assert "Excellent health" in health.recommendation

    def test_critical_gap_impact(self):
        """Critical gaps significantly impact score."""
        gaps = [
            {"type": "test failure", "severity": "critical"},
        ]
        health = calculate_health_score(gaps)

        # Should deduct 20 points from one category
        assert health.overall_score < 100
        assert health.overall_score >= 70  # But not catastrophic
        assert health.critical_gaps == 1
        assert "immediate attention" in format_health_score(health)

    def test_multiple_critical_gaps(self):
        """Multiple critical gaps drive score down significantly."""
        gaps = [
            {"type": "test failure", "severity": "critical"},
            {"type": "missing tests", "severity": "critical"},
            {"type": "import error", "severity": "critical"},
        ]
        health = calculate_health_score(gaps)

        # Should significantly impact score (but not catastrophic if only in one category)
        # Tests category (30% weight) takes the hit: 2 test gaps = -40 points → 60/100
        # Code quality (15% weight) takes the hit: 1 import error = -20 points → 80/100
        # Overall: (60*0.3) + (100*0.2) + (100*0.2) + (100*0.15) + (80*0.15) = 85
        assert health.overall_score < 95  # Definitely impacted
        assert health.critical_gaps == 3

    def test_high_gap_impact(self):
        """High gaps moderately impact score."""
        gaps = [
            {"type": "missing docs", "severity": "high"},
        ]
        health = calculate_health_score(gaps)

        # Should deduct 10 points
        assert health.overall_score < 100
        assert health.overall_score >= 85
        assert health.high_gaps == 1

    def test_mixed_severity_gaps(self):
        """Mixed severity gaps calculate correctly."""
        gaps = [
            {"type": "test failure", "severity": "critical"},
            {"type": "missing docs", "severity": "high"},
            {"type": "style issue", "severity": "low"},
        ]
        health = calculate_health_score(gaps)

        # Critical (-20) + High (-10) + Low (-2) = -32 deduction
        # Weighted average across categories
        assert health.overall_score < 100
        assert health.overall_score > 50  # Should still be passable
        assert health.critical_gaps == 1
        assert health.high_gaps == 1

    def test_category_breakdown(self):
        """Category scores are calculated correctly."""
        gaps = [
            {"type": "missing test", "severity": "high"},
            {"type": "failing test", "severity": "critical"},
            {"type": "outdated README", "severity": "medium"},
            {"type": "uncommitted changes", "severity": "high"},
        ]
        health = calculate_health_score(gaps)

        # Should have categories with gaps
        categories_with_gaps = [cat for cat in health.categories if cat.gap_count > 0]

        assert len(categories_with_gaps) >= 2  # At least tests and documentation
        assert any(cat.gap_count > 0 for cat in health.categories)

    def test_category_floor(self):
        """Category scores floor at 0 (can't go negative)."""
        # Create enough critical gaps to drive a category negative
        gaps = [
            {"type": "test failure", "severity": "critical"},
            {"type": "test failure 2", "severity": "critical"},
            {"type": "test failure 3", "severity": "critical"},
            {"type": "test failure 4", "severity": "critical"},
            {"type": "test failure 5", "severity": "critical"},
        ]
        health = calculate_health_score(gaps)

        # Tests category should floor at 0
        test_category = next(
            (cat for cat in health.categories if "test" in cat.name.lower()),
            None,
        )
        assert test_category is not None
        assert test_category.score == 0

    def test_format_health_score(self):
        """Health score formatting is readable."""
        gaps = [
            {"type": "missing test", "severity": "high"},
            {"type": "style issue", "severity": "low"},
        ]
        health = calculate_health_score(gaps)
        formatted = format_health_score(health)

        # Check required sections are present
        assert "**Project Health:" in formatted
        assert "**Category Breakdown:**" in formatted
        assert "**Recommendation**:" in formatted
        assert "weight:" in formatted

    def test_recommendation_levels(self):
        """Recommendations match score ranges."""
        # Excellent health (90-100)
        health_excellent = calculate_health_score([])
        assert (
            "Excellent" in health_excellent.recommendation
            or "no immediate" in health_excellent.recommendation
        )

        # Good health (80-89)
        gaps_good = [{"type": "style issue", "severity": "low"}]
        health_good = calculate_health_score(gaps_good)
        assert health_good.overall_score >= 80
        assert health_good.overall_score < 100

        # Poor health (< 60) - needs LOTS of critical gaps across multiple categories
        # With weighted average, need many gaps to drive score below 60
        gaps_poor = [
            # Tests category (30% weight): 5 critical = -100 points → floors at 0
            {"type": "test failure", "severity": "critical"},
            {"type": "test failure 2", "severity": "critical"},
            {"type": "test failure 3", "severity": "critical"},
            {"type": "test failure 4", "severity": "critical"},
            {"type": "test failure 5", "severity": "critical"},
            # Documentation (20% weight): 4 critical = -80 points → floors at 20
            {"type": "missing docs", "severity": "critical"},
            {"type": "outdated README", "severity": "critical"},
            {"type": "incomplete SKILL.md", "severity": "critical"},
            {"type": "missing CLAUDE.md", "severity": "critical"},
        ]
        health_poor = calculate_health_score(gaps_poor)
        # Score should be: (0*0.3) + (20*0.2) + (100*0.2) + (100*0.15) + (100*0.15) = 0 + 4 + 20 + 15 + 15 = 54
        assert health_poor.overall_score < 60
        assert "focus on" in health_poor.recommendation.lower()

    def test_urgency_indicators(self):
        """Urgency indicators appear for critical/high gaps."""
        # Critical gaps show urgency
        gaps_critical = [
            {"type": "import error", "severity": "critical"},
        ]
        health_critical = calculate_health_score(gaps_critical)
        formatted_critical = format_health_score(health_critical)

        assert "⚠️" in formatted_critical
        assert "critical" in formatted_critical.lower()

        # High gaps show urgency
        gaps_high = [
            {"type": "missing docs", "severity": "high"},
        ]
        health_high = calculate_health_score(gaps_high)
        formatted_high = format_health_score(health_high)

        assert "⚡" in formatted_high
        assert "high-severity" in formatted_high.lower()

    def test_weight_distribution(self):
        """Category weights sum to 1.0."""
        engine = HealthScoringEngine()
        total_weight = sum(engine.CATEGORY_WEIGHTS.values())

        assert total_weight == pytest.approx(1.0)

    def test_categorization_by_keywords(self):
        """Gaps are categorized by type keywords."""
        engine = HealthScoringEngine()

        # Test category
        test_gap = {"type": "test coverage missing", "severity": "high"}
        categorized = engine._categorize_gaps([test_gap])
        assert len(categorized["tests"]) == 1
        assert len(categorized["documentation"]) == 0

        # Documentation category
        doc_gap = {"type": "outdated README", "severity": "medium"}
        categorized = engine._categorize_gaps([doc_gap])
        assert len(categorized["documentation"]) == 1

        # Git category
        git_gap = {"type": "uncommitted changes", "severity": "high"}
        categorized = engine._categorize_gaps([git_gap])
        assert len(categorized["git"]) == 1

        # Dependencies category
        dep_gap = {"type": "outdated package", "severity": "medium"}
        categorized = engine._categorize_gaps([dep_gap])
        assert len(categorized["dependencies"]) == 1

        # Code quality category
        quality_gap = {"type": "ruff linting issue", "severity": "low"}
        categorized = engine._categorize_gaps([quality_gap])
        assert len(categorized["code_quality"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
