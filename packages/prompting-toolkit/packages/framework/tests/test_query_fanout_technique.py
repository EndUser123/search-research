#!/usr/bin/env python3
"""
Unit tests for query_fanout_technique module.

Tests for Query Fanout technique implementation.
"""


from prompting_framework.query_fanout_technique import (
    AggregationMethod,
    FanoutQuery,
    FanoutResult,
    FanoutStrategy,
)


class TestFanoutStrategy:
    """Test FanoutStrategy enum."""

    def test_all_strategies_defined(self):
        """Verify all expected strategies are defined."""
        expected_strategies = [
            "parallel_diversification",
            "sequential_refinement",
            "hierarchical_decomposition",
            "perspective_multiplied",
        ]
        actual_values = [s.value for s in FanoutStrategy]
        for expected in expected_strategies:
            assert expected in actual_values


class TestAggregationMethod:
    """Test AggregationMethod enum."""

    def test_all_methods_defined(self):
        """Verify all expected methods are defined."""
        expected_methods = [
            "synthesis",
            "voting",
            "weighted_average",
            "best_match",
            "consensus",
        ]
        actual_values = [m.value for m in AggregationMethod]
        for expected in expected_methods:
            assert expected in actual_values


class TestFanoutQuery:
    """Test FanoutQuery dataclass."""

    def test_create_query(self):
        """Create a fanout query."""
        query = FanoutQuery(
            query_id="query_1",
            query_text="What are the pros and cons?",
            query_type="analytical",
            perspective="optimistic",
            context="Evaluating options",
            priority=1,
        )
        assert query.query_id == "query_1"
        assert query.perspective == "optimistic"

    def test_query_with_defaults(self):
        """Create query with default values."""
        query = FanoutQuery(
            query_id="query_2",
            query_text="Analyze this",
            query_type="general",
        )
        assert query.perspective == "neutral"
        assert query.context == ""
        assert query.priority == 5

    def test_multiple_queries(self):
        """Create multiple queries with different perspectives."""
        perspectives = ["optimistic", "pessimistic", "neutral", "critical"]
        queries = [
            FanoutQuery(
                query_id=f"q_{i}",
                query_text=f"Query from {persp} perspective",
                query_type="analysis",
                perspective=persp,
                priority=i,
            )
            for i, persp in enumerate(perspectives, 1)
        ]
        assert len(queries) == 4
        assert queries[0].perspective == "optimistic"
        assert queries[3].perspective == "critical"


class TestFanoutResult:
    """Test FanoutResult dataclass."""

    def test_create_result(self):
        """Create a fanout result."""
        result = FanoutResult(
            original_query="Should I use framework X?",
            queries_generated=[
                FanoutQuery(
                    query_id="q1",
                    query_text="Pros of framework X?",
                    query_type="analysis",
                    perspective="positive",
                )
            ],
            responses={
                "q1": "Framework X is fast and scalable",
            },
            aggregation_method=AggregationMethod.SYNTHESIS,
            aggregated_response="Framework X has both strengths and weaknesses",
            execution_time=2.5,
            success=True,
        )
        assert result.original_query == "Should I use framework X?"
        assert len(result.responses) == 1
        assert result.aggregation_method == AggregationMethod.SYNTHESIS

    def test_result_with_synthesis(self):
        """Result using synthesis aggregation."""
        result = FanoutResult(
            original_query="Evaluate this approach",
            queries_generated=[],
            responses={},
            aggregation_method=AggregationMethod.SYNTHESIS,
            aggregated_response="Synthesized response combining multiple views",
            execution_time=3.0,
            success=True,
        )
        assert result.aggregation_method == AggregationMethod.SYNTHESIS

    def test_result_with_voting(self):
        """Result using voting aggregation."""
        result = FanoutResult(
            original_query="Choose option",
            queries_generated=[],
            responses={"q1": "A", "q2": "A", "q3": "B"},
            aggregation_method=AggregationMethod.VOTING,
            aggregated_response="Option A (majority vote)",
            execution_time=1.5,
            success=True,
        )
        assert result.aggregation_method == AggregationMethod.VOTING

    def test_result_failure(self):
        """Handle failed fanout execution."""
        result = FanoutResult(
            original_query="Test query",
            queries_generated=[],
            responses={},
            aggregation_method=AggregationMethod.CONSENSUS,
            aggregated_response="",
            execution_time=0.5,
            success=False,
            error_message="Failed to generate queries",
        )
        assert result.success is False
        assert result.error_message == "Failed to generate queries"


class TestFanoutStrategies:
    """Test various fanout strategies."""

    def test_parallel_diversification(self):
        """Parallel diversification strategy."""
        assert FanoutStrategy.PARALLEL_DIVERSIFICATION.value == "parallel_diversification"

    def test_sequential_refinement(self):
        """Sequential refinement strategy."""
        assert FanoutStrategy.SEQUENTIAL_REFINEMENT.value == "sequential_refinement"

    def test_hierarchical_decomposition(self):
        """Hierarchical decomposition strategy."""
        assert FanoutStrategy.HIERARCHICAL_DECOMPOSITION.value == "hierarchical_decomposition"

    def test_perspective_multiplied(self):
        """Perspective multiplied strategy."""
        assert FanoutStrategy.PERSPECTIVE_MULTIPLIED.value == "perspective_multiplied"


class TestAggregationMethods:
    """Test various aggregation methods."""

    def test_synthesis_method(self):
        """Synthesis combines all responses."""
        assert AggregationMethod.SYNTHESIS.value == "synthesis"

    def test_voting_method(self):
        """Voting selects most common response."""
        assert AggregationMethod.VOTING.value == "voting"

    def test_weighted_average_method(self):
        """Weighted average combines with weights."""
        assert AggregationMethod.WEIGHTED_AVERAGE.value == "weighted_average"

    def test_best_match_method(self):
        """Best match selects optimal response."""
        assert AggregationMethod.BEST_MATCH.value == "best_match"

    def test_consensus_method(self):
        """Consensus finds agreement."""
        assert AggregationMethod.CONSENSUS.value == "consensus"


class TestQueryPerspectives:
    """Test different query perspectives."""

    def test_optimistic_perspective(self):
        """Query with optimistic perspective."""
        query = FanoutQuery(
            query_id="opt_1",
            query_text="Benefits of this approach?",
            query_type="analysis",
            perspective="optimistic",
        )
        assert query.perspective == "optimistic"

    def test_pessimistic_perspective(self):
        """Query with pessimistic perspective."""
        query = FanoutQuery(
            query_id="pes_1",
            query_text="Risks of this approach?",
            query_type="analysis",
            perspective="pessimistic",
        )
        assert query.perspective == "pessimistic"

    def test_neutral_perspective(self):
        """Query with neutral perspective."""
        query = FanoutQuery(
            query_id="neu_1",
            query_text="Evaluate this approach",
            query_type="analysis",
            perspective="neutral",
        )
        assert query.perspective == "neutral"

    def test_critical_perspective(self):
        """Query with critical perspective."""
        query = FanoutQuery(
            query_id="crit_1",
            query_text="Potential issues?",
            query_type="critical_analysis",
            perspective="critical",
        )
        assert query.perspective == "critical"


class TestResultAggregation:
    """Test result aggregation scenarios."""

    def test_multiple_responses_aggregation(self):
        """Aggregate multiple query responses."""
        result = FanoutResult(
            original_query="Is this good?",
            queries_generated=[
                FanoutQuery(
                    query_id="q1",
                    query_text="Pros?",
                    query_type="analysis",
                    perspective="optimistic",
                ),
                FanoutQuery(
                    query_id="q2",
                    query_text="Cons?",
                    query_type="analysis",
                    perspective="pessimistic",
                ),
            ],
            responses={
                "q1": "Many benefits: speed, simplicity",
                "q2": "Some drawbacks: limited scalability",
            },
            aggregation_method=AggregationMethod.SYNTHESIS,
            aggregated_response="Has benefits like speed and simplicity, but limited scalability",
            execution_time=2.0,
            success=True,
        )
        assert len(result.responses) == 2
        assert "benefits" in result.aggregated_response.lower()
        assert "scalability" in result.aggregated_response.lower()

    def test_weighted_aggregation(self):
        """Weighted aggregation considers query priorities."""
        result = FanoutResult(
            original_query="Evaluate",
            queries_generated=[
                FanoutQuery(
                    query_id="q1",
                    query_text="Expert view",
                    query_type="expert",
                    perspective="neutral",
                    priority=1,  # High priority
                ),
                FanoutQuery(
                    query_id="q2",
                    query_text="General view",
                    query_type="general",
                    perspective="neutral",
                    priority=5,  # Lower priority
                ),
            ],
            responses={"q1": "Recommended", "q2": "Use with caution"},
            aggregation_method=AggregationMethod.WEIGHTED_AVERAGE,
            aggregated_response="Generally recommended with some cautions",
            execution_time=2.0,
            success=True,
        )
        assert result.aggregation_method == AggregationMethod.WEIGHTED_AVERAGE


class TestEdgeCases:
    """Test edge cases for query fanout."""

    def test_empty_fanout(self):
        """Handle fanout with no queries."""
        result = FanoutResult(
            original_query="Simple question",
            queries_generated=[],
            responses={},
            aggregation_method=AggregationMethod.BEST_MATCH,
            aggregated_response="Direct answer",
            execution_time=0.5,
            success=True,
        )
        assert len(result.queries_generated) == 0

    def test_single_query_fanout(self):
        """Handle fanout with single query."""
        query = FanoutQuery(
            query_id="single",
            query_text="Only query",
            query_type="direct",
        )

        result = FanoutResult(
            original_query="Direct question",
            queries_generated=[query],
            responses={"single": "Direct answer"},
            aggregation_method=AggregationMethod.BEST_MATCH,
            aggregated_response="Direct answer",
            execution_time=1.0,
            success=True,
        )
        assert len(result.queries_generated) == 1

    def test_failed_response(self):
        """Handle query with failed response."""
        result = FanoutResult(
            original_query="Complex query",
            queries_generated=[
                FanoutQuery(
                    query_id="q1",
                    query_text="Sub-query 1",
                    query_type="analysis",
                )
            ],
            responses={"q1": "ERROR: Failed to process"},
            aggregation_method=AggregationMethod.SYNTHESIS,
            aggregated_response="Partial results with errors",
            execution_time=1.0,
            success=False,
            error_message="Some queries failed",
        )
        assert result.success is False
        assert "ERROR" in result.responses["q1"]

    def test_zero_execution_time(self):
        """Handle cached result (zero execution time)."""
        result = FanoutResult(
            original_query="Cached query",
            queries_generated=[],
            responses={},
            aggregation_method=AggregationMethod.BEST_MATCH,
            aggregated_response="From cache",
            execution_time=0.0,
            success=True,
        )
        assert result.execution_time == 0.0
