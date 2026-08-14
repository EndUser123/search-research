#!/usr/bin/env python3
"""Unit tests for adaptive_limits module.

Tests adaptive result limits and token estimation:
- get_adaptive_limit: Get adaptive limit based on complexity
- estimate_tokens: Estimate token usage for results
- check_token_limit: Check if within safe token limits
- get_adaptive_config: Get complete adaptive configuration
- recommend_layer2_limit: Recommend maximum results for Layer 2
"""


# Add skills/all directory to path for imports
import sys
from pathlib import Path

skills_path = Path(__file__).parent.parent / "skills" / "all"
sys.path.insert(0, str(skills_path))

from adaptive_limits import (
    check_token_limit,
    estimate_tokens,
    get_adaptive_config,
    get_adaptive_limit,
    recommend_layer2_limit,
)


class TestGetAdaptiveLimit:
    """Test get_adaptive_limit function."""

    def test_simple_query_lower_limit(self):
        """Test simple queries get lower limit (20 items)."""
        limit = get_adaptive_limit(20)
        assert limit == 20

    def test_medium_query_moderate_limit(self):
        """Test medium queries get moderate limit (30 items)."""
        limit = get_adaptive_limit(50)
        assert limit == 30

    def test_complex_query_higher_limit(self):
        """Test complex queries get higher limit (40 items)."""
        limit = get_adaptive_limit(80)
        assert limit == 40

    def test_boundary_values(self):
        """Test boundary values for adaptive limits."""
        # High complexity boundary (> 60)
        assert get_adaptive_limit(61) == 40
        assert get_adaptive_limit(60) == 30  # Not > 60, so medium

        # Medium complexity boundary (40-60)
        assert get_adaptive_limit(40) == 30
        assert get_adaptive_limit(39) == 20  # < 40, so simple


class TestEstimateTokens:
    """Test estimate_tokens function."""

    def test_basic_estimation(self):
        """Test basic token estimation."""
        tokens = estimate_tokens(result_count=10, avg_content_length=300)
        # 10 results * (300 chars / 4 chars per token) = 750 content tokens
        # 10 results * 30 metadata tokens = 300 metadata tokens
        # Total: ~1050 tokens
        assert 1000 <= tokens <= 1100

    def test_no_metadata(self):
        """Test estimation without metadata."""
        tokens_with_metadata = estimate_tokens(result_count=10, has_metadata=True)
        tokens_without_metadata = estimate_tokens(result_count=10, has_metadata=False)

        # Without metadata should be significantly less
        assert tokens_without_metadata < tokens_with_metadata

    def test_larger_content(self):
        """Test estimation with larger content."""
        tokens_small = estimate_tokens(result_count=10, avg_content_length=200)
        tokens_large = estimate_tokens(result_count=10, avg_content_length=500)

        # Larger content should have more tokens
        assert tokens_large > tokens_small

    def test_more_results(self):
        """Test estimation scales with result count."""
        tokens_10 = estimate_tokens(result_count=10)
        tokens_20 = estimate_tokens(result_count=20)

        # 20 results should have roughly 2x tokens of 10 results
        assert tokens_20 > tokens_10
        assert abs(tokens_20 - 2 * tokens_10) < 100  # Within reasonable range


class TestCheckTokenLimit:
    """Test check_token_limit function."""

    def test_within_limit(self):
        """Test check when within safe limit."""
        result = check_token_limit(result_count=10, avg_content_length=300, limit=8000)
        assert result["within_limit"] is True
        assert result["estimated_tokens"] < 8000
        assert result["warning"] is None

    def test_approaching_limit(self):
        """Test check when approaching limit."""
        # Large result count should approach limit
        result = check_token_limit(result_count=50, avg_content_length=300, limit=8000)
        # 50 results * (75 + 30) tokens = ~5250 tokens, still under limit
        # But let's test with even more
        result = check_token_limit(result_count=60, avg_content_length=400, limit=8000)

        if result["estimated_tokens"] > 7000:
            assert "Approaching" in result["warning"] or "Over" in result["warning"]

    def test_over_limit(self):
        """Test check when over limit."""
        result = check_token_limit(result_count=100, avg_content_length=500, limit=8000)
        # 100 results * (125 + 30) = ~15500 tokens, definitely over
        assert result["within_limit"] is False
        assert "Over" in result["warning"] or "exceed" in result["warning"].lower()

    def test_custom_limit(self):
        """Test check with custom limit."""
        result = check_token_limit(result_count=10, avg_content_length=300, limit=500)
        # 10 results = ~1050 tokens, over 500 limit
        assert result["within_limit"] is False
        assert result["estimated_tokens"] > 500


class TestGetAdaptiveConfig:
    """Test get_adaptive_config function."""

    def test_simple_query_config(self):
        """Test config for simple query."""
        config = get_adaptive_config(complexity_score=20, result_count=15)

        assert config["complexity_score"] == 20
        assert config["complexity_label"] == "Simple"
        assert config["adaptive_limit"] == 20
        assert config["result_count"] == 15
        assert config["within_limit"] is True
        assert config["should_reduce"] is False
        assert config["reduction_target"] is None

    def test_complex_query_config(self):
        """Test config for complex query."""
        config = get_adaptive_config(complexity_score=80, result_count=35)

        assert config["complexity_score"] == 80
        assert config["complexity_label"] == "Complex"
        assert config["adaptive_limit"] == 40
        assert config["result_count"] == 35

    def test_over_limit_triggers_reduction(self):
        """Test that over limit triggers reduction."""
        config = get_adaptive_config(complexity_score=50, result_count=100, avg_content_length=500)

        # Should trigger reduction due to high token count
        assert config["within_limit"] is False
        assert config["should_reduce"] is True
        assert config["reduction_target"] is not None
        assert config["reduction_target"] >= 10  # Minimum 10 results

    def test_warning_present_when_appropriate(self):
        """Test warning is present when approaching/exceeding limits."""
        config = get_adaptive_config(complexity_score=50, result_count=80, avg_content_length=400)

        if not config["within_limit"]:
            assert config["warning"] is not None


class TestRecommendLayer2Limit:
    """Test recommend_layer2_limit function."""

    def test_simple_query_recommendation(self):
        """Test recommendation for simple query."""
        limit = recommend_layer2_limit(complexity_score=20, result_count=25)
        # Simple query: adaptive limit is 20
        assert limit == 20

    def test_medium_query_recommendation(self):
        """Test recommendation for medium query."""
        limit = recommend_layer2_limit(complexity_score=50, result_count=35)
        # Medium query: adaptive limit is 30
        assert limit == 30

    def test_complex_query_recommendation(self):
        """Test recommendation for complex query."""
        limit = recommend_layer2_limit(complexity_score=80, result_count=50)
        # Complex query: adaptive limit is 40
        assert limit == 40

    def test_result_count_lower_than_adaptive(self):
        """Test when result count is lower than adaptive limit."""
        limit = recommend_layer2_limit(complexity_score=20, result_count=15)
        # Simple query adaptive limit is 20, but only 15 results
        assert limit == 15  # Should cap at actual count

    def test_over_limit_reduces_recommendation(self):
        """Test that over limit reduces recommendation."""
        limit = recommend_layer2_limit(complexity_score=50, result_count=100, avg_content_length=500)
        # Should recommend reduced target to stay within token limits
        assert limit < 100
        assert limit >= 10  # Minimum 10 results


class TestIntegrationScenarios:
    """Integration tests for common scenarios."""

    def test_small_result_set_no_issues(self):
        """Test small result set with no token issues."""
        config = get_adaptive_config(complexity_score=30, result_count=10)
        limit = recommend_layer2_limit(complexity_score=30, result_count=10)

        assert config["within_limit"] is True
        assert config["should_reduce"] is False
        assert limit == 10  # All results fit

    def test_medium_result_set_within_limits(self):
        """Test medium result set within token limits."""
        config = get_adaptive_config(complexity_score=50, result_count=30)
        limit = recommend_layer2_limit(complexity_score=50, result_count=30)

        assert config["within_limit"] is True  # Should be within 8k limit
        assert limit == 30  # All results fit

    def test_large_result_set_truncation_needed(self):
        """Test large result set requires truncation."""
        config = get_adaptive_config(complexity_score=70, result_count=100, avg_content_length=500)
        limit = recommend_layer2_limit(complexity_score=70, result_count=100, avg_content_length=500)

        assert config["should_reduce"] is True
        assert limit < 100  # Should recommend reduction
        assert limit >= 10  # But keep at least 10

    def test_token_estimation_accuracy(self):
        """Test token estimation is reasonably accurate."""
        # For 20 results with 300 char avg content:
        # Content: 20 * (300 / 4) = 1500 tokens
        # Metadata: 20 * 30 = 600 tokens
        # Total: ~2100 tokens
        tokens = estimate_tokens(result_count=20, avg_content_length=300)

        # Should be close to expected value (within 20%)
        expected = 2100
        assert abs(tokens - expected) / expected < 0.2
