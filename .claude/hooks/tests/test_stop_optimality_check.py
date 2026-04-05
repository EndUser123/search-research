#!/usr/bin/env python3
"""Tests for Stop_optimality_check.py

Tests the optimality check gate.
"""

from Stop_optimality_check import run


class TestBlockRecommendationWithoutOptimality:
    """Block recommendations without optimality assessment."""

    def test_we_should_blocks(self):
        """Must block when 'we should' without optimality assessment."""
        data = {"response_text": "We should use a dictionary for this."}
        result = run(data)
        assert result["allow"] is False
        assert "OPTIMALITY ASSESSMENT REQUIRED" in result["reason"]

    def test_i_recommend_blocks(self):
        """Must block 'I recommend' without optimality assessment."""
        data = {"response_text": "I recommend using the cache."}
        result = run(data)
        assert result["allow"] is False

    def test_best_approach_blocks(self):
        """Must block 'best approach' without optimality assessment."""
        data = {"response_text": "The best approach is to refactor."}
        result = run(data)
        assert result["allow"] is False

    def test_correct_approach_blocks(self):
        """Must block 'correct approach' without optimality assessment."""
        data = {"response_text": "The correct approach would be to add logging."}
        result = run(data)
        assert result["allow"] is False

    def test_multiple_recommendations_block(self):
        """Must block when multiple recommendations without assessment."""
        data = {"response_text": "We should use A. I recommend B. The best approach is C."}
        result = run(data)
        assert result["allow"] is False


class TestAllowWithOptimalityAssessment:
    """Allow recommendations with optimality tier assessment."""

    def test_immediate_allows(self):
        """Must allow with 'immediate' keyword."""
        data = {
            "response_text": "We should use a dictionary for immediate fixes, but consider WeakValueDictionary for long-term."
        }
        result = run(data)
        assert result["allow"] is True

    def test_optimal_allows(self):
        """Must allow with 'optimal' keyword."""
        data = {"response_text": "I recommend the optimal solution: use a ring buffer."}
        result = run(data)
        assert result["allow"] is True

    def test_long_term_allows(self):
        """Must allow with 'long-term' keyword."""
        data = {"response_text": "The best approach for long-term is to implement a proper cache."}
        result = run(data)
        assert result["allow"] is True

    def test_trade_off_allows(self):
        """Must allow with 'trade-off' keyword."""
        data = {"response_text": "We should add caching - the trade-off is memory vs speed."}
        result = run(data)
        assert result["allow"] is True

    def test_alternatives_allows(self):
        """Must allow with 'alternatives' keyword."""
        data = {"response_text": "I recommend Option A. Alternatives include Option B or C."}
        result = run(data)
        assert result["allow"] is True

    def test_vs_allows(self):
        """Must allow with 'vs' comparison."""
        data = {"response_text": "We should use dict vs list - dict is faster for lookups."}
        result = run(data)
        assert result["allow"] is True

    def test_minimum_acceptable_allows(self):
        """Must allow with 'minimum acceptable' keyword."""
        data = {"response_text": "The minimum acceptable solution is a quick patch."}
        result = run(data)
        assert result["allow"] is True

    def test_quick_fix_allows(self):
        """Must allow with 'quick fix' keyword."""
        data = {
            "response_text": "A quick fix would be to add a timeout. For long-term, use retry logic."
        }
        result = run(data)
        assert result["allow"] is True

    def test_temporary_allows(self):
        """Must allow with 'temporary' keyword."""
        data = {
            "response_text": "The temporary solution is to restart the service. A permanent fix requires a code change."
        }
        result = run(data)
        assert result["allow"] is True


class TestEdgeCases:
    """Edge cases."""

    def test_empty_response_allows(self):
        """Empty response should be allowed."""
        data = {"response_text": ""}
        result = run(data)
        assert result["allow"] is True

    def test_short_response_allows(self):
        """Very short response should be allowed."""
        data = {"response_text": "Hi"}
        result = run(data)
        assert result["allow"] is True

    def test_no_recommendation_allows(self):
        """Response without recommendation phrase should be allowed."""
        data = {"response_text": "The issue is caused by a race condition."}
        result = run(data)
        assert result["allow"] is True

    def test_gate_disabled_allows(self, monkeypatch):
        """When gate is disabled, should allow everything."""
        monkeypatch.setenv("OPTIMALITY_CHECK_ENABLED", "false")
        data = {"response_text": "We should use a dictionary."}
        result = run(data)
        assert result["allow"] is True
        assert "Gate disabled" in result["reason"]

    def test_recommendation_with_now_vs_later_allows(self):
        """Must allow with now/later pattern."""
        data = {"response_text": "We should do it now, but eventually use a proper queue."}
        result = run(data)
        assert result["allow"] is True
