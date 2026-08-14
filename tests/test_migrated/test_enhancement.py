"""
Comprehensive tests for enhancement components.

Tests for:
- SimplifiedDependencyAnalyzer: dependency analysis from queries
- LearningSystem: pattern learning from feedback
- ModeRelationshipMapper: mode relationship mapping
- MultiModeOrchestrator: multi-mode orchestration
- QualityPredictor: quality prediction (if available)
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from core.enhancement.enhanced_dependency_analyzer import (
    QueryDependencies,
    ResearchDepth,
    SimplifiedDependencyAnalyzer,
)
from core.enhancement.learning_system import (
    LearningSystem,
    ResearchFeedback,
)
from core.enhancement.mode_relationship_mapper import (
    ModeCombination,
    ModeRelationshipMapper,
    ResearchMode,
)
from core.enhancement.multi_mode_orchestrator import (
    ExecutionStatus,
    ModeExecutionResult,
    MultiModeOrchestrator,
    OrchestratedResult,
)


class TestSimplifiedDependencyAnalyzer:
    """Test suite for SimplifiedDependencyAnalyzer."""

    @pytest.fixture
    def analyzer(self) -> SimplifiedDependencyAnalyzer:
        """Create analyzer instance."""
        return SimplifiedDependencyAnalyzer()

    def test_analyze_code_requirements(self, analyzer):
        """Test detection of code requirements."""
        query = "github repository react hooks implementation example"

        deps = analyzer.analyze_dependencies(query)

        assert deps.requires_code is True
        assert deps.requires_github is True
        assert deps.requires_examples is True

    def test_analyze_documentation_requirements(self, analyzer):
        """Test detection of documentation requirements."""
        query = "python asyncio documentation guide tutorial"

        deps = analyzer.analyze_dependencies(query)

        assert deps.requires_documentation is True
        assert deps.requires_tutorials is True

    def test_analyze_academic_requirements(self, analyzer):
        """Test detection of academic requirements."""
        query = "machine learning research papers academic survey"

        deps = analyzer.analyze_dependencies(query)

        assert deps.requires_academic is True

    def test_analyze_ai_perspective_requirements(self, analyzer):
        """Test detection of AI perspective requirements."""
        query = "best practices comparison analysis recommendations"

        deps = analyzer.analyze_dependencies(query)

        assert deps.requires_ai_perspectives is True

    def test_complexity_score_calculation(self, analyzer):
        """Test complexity score calculation."""
        simple_query = "basic tutorial"
        complex_query = "enterprise distributed microservices architecture scalability optimization"

        simple_deps = analyzer.analyze_dependencies(simple_query)
        complex_deps = analyzer.analyze_dependencies(complex_query)

        # Complex query should have higher complexity
        assert complex_deps.complexity_score > simple_deps.complexity_score

    def test_research_depth_basic(self, analyzer):
        """Test basic research depth classification."""
        query = "simple tutorial"

        deps = analyzer.analyze_dependencies(query)

        assert deps.research_depth == ResearchDepth.BASIC

    def test_research_depth_intermediate(self, analyzer):
        """Test intermediate research depth classification."""
        query = "implementation with best practices and optimization"

        deps = analyzer.analyze_dependencies(query)

        assert deps.research_depth in [ResearchDepth.INTERMEDIATE, ResearchDepth.BASIC]

    def test_research_depth_advanced(self, analyzer):
        """Test advanced research depth classification."""
        query = "enterprise architecture scalability security distributed systems"

        deps = analyzer.analyze_dependencies(query)

        assert deps.research_depth == ResearchDepth.ADVANCED

    def test_confidence_calculation(self, analyzer):
        """Test confidence score calculation."""
        # Clear query with multiple indicators
        clear_query = "github repository code implementation"
        # Vague query
        vague_query = "information about stuff"

        clear_deps = analyzer.analyze_dependencies(clear_query)
        vague_deps = analyzer.analyze_dependencies(vague_query)

        # Clear query should have higher confidence
        assert clear_deps.confidence >= vague_deps.confidence

    def test_primary_indicators_tracking(self, analyzer):
        """Test tracking of primary indicators."""
        query = "github repository react hooks implementation"

        deps = analyzer.analyze_dependencies(query)

        # Should track indicators
        assert deps.primary_indicators is not None
        assert len(deps.primary_indicators) > 0

        # Check format
        for indicator in deps.primary_indicators[:5]:
            assert isinstance(indicator, str)
            assert ":" in indicator

    def test_get_dependency_summary(self, analyzer):
        """Test dependency summary generation."""
        query = "github repository code example tutorial"

        deps = analyzer.analyze_dependencies(query)
        summary = analyzer.get_dependency_summary(deps)

        # Check summary structure
        assert "primary_requirements" in summary
        assert "complexity_score" in summary
        assert "research_depth" in summary
        assert "confidence" in summary
        assert "indicators" in summary

        # Check types
        assert isinstance(summary["primary_requirements"], list)
        assert isinstance(summary["complexity_score"], float)
        assert isinstance(summary["research_depth"], str)
        assert isinstance(summary["confidence"], float)

    def test_empty_query(self, analyzer):
        """Test handling of empty query."""
        deps = analyzer.analyze_dependencies("")

        # Should return valid dependencies object
        assert isinstance(deps, QueryDependencies)
        assert deps.complexity_score == 0.0

    def test_tsk_context_application(self, analyzer):
        """Test TSK context application to dependencies."""
        query = "enterprise distributed architecture"

        tsk_context = {
            "domain_type": "technical",
            "complexity": 0.8
        }

        deps = analyzer.analyze_dependencies(query, tsk_context)

        # TSK context should boost analysis
        assert deps.requires_code is True
        # High complexity from TSK context should be reflected
        # Note: May still be 0 if no complexity keywords in query itself


class TestLearningSystem:
    """Test suite for LearningSystem."""

    @pytest.fixture
    def learning_system(self, temp_feedback_file):
        """Create LearningSystem with temporary feedback file."""
        return LearningSystem(feedback_file=temp_feedback_file)

    def test_initialization(self, learning_system):
        """Test system initialization."""
        assert learning_system.feedback_file is not None
        assert isinstance(learning_system.feedback_history, list)
        assert isinstance(learning_system.patterns, dict)
        assert isinstance(learning_system.query_patterns, dict)
        assert isinstance(learning_system.mode_performance, dict)

    def test_collect_feedback(self, learning_system):
        """Test feedback collection."""
        learning_system.collect_feedback(
            research_id="test_001",
            query="react hooks",
            modes_used=["octocode", "web"],
            predicted_quality=0.85,
            actual_quality_rating=4.2,
            helpful_aspects=["code examples"],
            improvement_suggestions=["more docs"],
            session_duration=120.0,
            user_expertise_level="intermediate",
            research_domain="technical"
        )

        # Should add to history
        assert len(learning_system.feedback_history) == 1

        # Check feedback structure
        feedback = learning_system.feedback_history[0]
        assert feedback.query == "react hooks"
        assert feedback.actual_quality_rating == 4.2
        assert len(feedback.modes_used) == 2

    def test_feedback_persistence(self, learning_system, temp_feedback_file):
        """Test that feedback is persisted to file."""
        learning_system.collect_feedback(
            research_id="test_001",
            query="test query",
            modes_used=["web"],
            predicted_quality=0.8,
            actual_quality_rating=4.0
        )

        # Create new system with same file
        new_system = LearningSystem(feedback_file=temp_feedback_file)

        # Should load previous feedback
        assert len(new_system.feedback_history) == 1
        assert new_system.feedback_history[0].query == "test query"

    def test_pattern_analysis_threshold(self, learning_system):
        """Test that pattern analysis requires minimum data."""
        # Add less than 5 feedback entries
        for i in range(3):
            learning_system.collect_feedback(
                research_id=f"test_{i}",
                query="test",
                modes_used=["web"],
                predicted_quality=0.8,
                actual_quality_rating=4.0
            )

        # Should not analyze patterns yet (insufficient data)
        assert len(learning_system.patterns) == 0

    def test_mode_combination_analysis(self, learning_system):
        """Test analysis of mode combinations."""
        # Add sufficient feedback
        for i in range(5):
            learning_system.collect_feedback(
                research_id=f"test_{i}",
                query="react hooks",
                modes_used=["octocode", "web"],
                predicted_quality=0.85,
                actual_quality_rating=4.2 + (i * 0.1)
            )

        # Should analyze mode performance
        assert len(learning_system.mode_performance) > 0

        # Check mode performance structure
        combo_key = "octocode+web"
        if combo_key in learning_system.mode_performance:
            stats = learning_system.mode_performance[combo_key]
            assert "avg_rating" in stats
            assert "sample_size" in stats
            assert stats["sample_size"] >= 3

    def test_query_pattern_learning(self, learning_system):
        """Test learning from query patterns."""
        # Add feedback with similar queries
        for i in range(5):
            learning_system.collect_feedback(
                research_id=f"test_{i}",
                query="react hooks implementation",
                modes_used=["octocode"],
                predicted_quality=0.8,
                actual_quality_rating=4.0
            )

        # Should learn query patterns
        assert len(learning_system.query_patterns) > 0

    def test_get_pattern_based_recommendation(self, learning_system):
        """Test pattern-based recommendations."""
        # Train system with pattern data
        for i in range(10):
            learning_system.collect_feedback(
                research_id=f"test_{i}",
                query="react hooks example",
                modes_used=["octocode", "web"],
                predicted_quality=0.85,
                actual_quality_rating=4.5
            )

        recommendation = learning_system.get_pattern_based_recommendation(
            query="react hooks implementation",
            candidate_modes=["octocode", "web"]
        )

        # Should provide recommendation
        if recommendation:
            assert "recommended_combination" in recommendation
            assert "confidence" in recommendation
            assert recommendation["confidence"] >= 0.0

    def test_get_recent_feedback(self, learning_system):
        """Test retrieval of recent feedback."""
        # Add old feedback
        old_feedback = ResearchFeedback(
            research_id="old_001",
            query="old query",
            modes_used=["web"],
            predicted_quality=0.8,
            actual_quality_rating=3.5,
            helpful_aspects=[],
            improvement_suggestions=[],
            sources_helpful=[],
            sources_missing=[],
            timestamp=datetime.now() - timedelta(days=40),
            session_duration=100.0,
            user_expertise_level="intermediate",
            research_domain="technical"
        )
        learning_system.feedback_history.append(old_feedback)

        # Add recent feedback
        learning_system.collect_feedback(
            research_id="recent_001",
            query="recent query",
            modes_used=["web"],
            predicted_quality=0.8,
            actual_quality_rating=4.0
        )

        recent = learning_system.get_recent_feedback(days=30)

        # Should only return recent feedback
        assert len(recent) == 1
        assert recent[0].research_id == "recent_001"

    def test_get_learning_summary(self, learning_system):
        """Test learning summary generation."""
        # Add some feedback
        learning_system.collect_feedback(
            research_id="test_001",
            query="test",
            modes_used=["web"],
            predicted_quality=0.8,
            actual_quality_rating=4.0
        )

        summary = learning_system.get_learning_summary()

        # Check summary structure
        assert "total_feedback_sessions" in summary
        assert "average_user_rating" in summary
        assert "patterns_identified" in summary
        assert summary["total_feedback_sessions"] > 0

    def test_export_patterns(self, learning_system, tmp_path):
        """Test pattern export functionality."""
        # Add feedback
        learning_system.collect_feedback(
            research_id="test_001",
            query="test",
            modes_used=["web"],
            predicted_quality=0.8,
            actual_quality_rating=4.0
        )

        export_file = tmp_path / "export.json"
        result_path = learning_system.export_patterns(filename=str(export_file))

        # Should create export file
        assert Path(result_path).exists()

        # Check export structure
        with open(result_path) as f:
            export_data = json.load(f)

        assert "export_timestamp" in export_data
        assert "mode_performance" in export_data
        assert "query_patterns" in export_data


class TestModeRelationshipMapper:
    """Test suite for ModeRelationshipMapper."""

    @pytest.fixture
    def mapper(self) -> ModeRelationshipMapper:
        """Create ModeRelationshipMapper instance."""
        return ModeRelationshipMapper()

    @pytest.fixture
    def sample_dependencies(self, sample_query_dependencies):
        """Sample query dependencies for testing."""
        return sample_query_dependencies

    def test_initialization(self, mapper):
        """Test mapper initialization."""
        assert mapper.mode_strengths is not None
        assert mapper.redundancy_matrix is not None
        assert mapper.cost_factors is not None

        # Check all modes are defined
        assert ResearchMode.OCTOCODE in mapper.mode_strengths
        assert ResearchMode.WEB in mapper.mode_strengths
        assert ResearchMode.MULTI_MODEL in mapper.mode_strengths
        assert ResearchMode.COGNITIVE in mapper.mode_strengths

    def test_find_optimal_combination_basic(self, mapper, sample_dependencies):
        """Test finding optimal mode combination."""
        combination = mapper.find_optimal_combination(sample_dependencies)

        # Should return valid combination
        assert isinstance(combination, ModeCombination)
        assert len(combination.modes) > 0
        assert 0.0 <= combination.predicted_quality <= 1.0
        assert combination.estimated_cost > 0
        assert 0.0 <= combination.redundancy_score <= 1.0
        assert 0.0 <= combination.coverage_score <= 1.0

    def test_find_optimal_with_budget_limit(self, mapper, sample_dependencies):
        """Test optimal combination with budget constraint."""
        combination = mapper.find_optimal_combination(
            sample_dependencies,
            budget_limit=1.5
        )

        # Should respect budget
        assert combination.estimated_cost <= 1.5

    def test_coverage_score_calculation(self, mapper, sample_dependencies):
        """Test coverage score calculation."""
        combination = mapper.find_optimal_combination(sample_dependencies)

        # Should have good coverage for matched dependencies
        assert combination.coverage_score > 0.0

    def test_redundancy_score_calculation(self, mapper, sample_dependencies):
        """Test redundancy score calculation."""
        combination = mapper.find_optimal_combination(sample_dependencies)

        # Should have valid redundancy score
        assert 0.0 <= combination.redundancy_score < 1.0

    def test_cost_calculation(self, mapper):
        """Test cost calculation for combinations."""
        # High complexity query requiring multiple modes
        complex_deps = QueryDependencies(
            requires_code=True,
            requires_github=True,
            requires_academic=True,
            requires_ai_perspectives=True,
            complexity_score=0.9,
            research_depth=ResearchDepth.ADVANCED
        )

        combination = mapper.find_optimal_combination(complex_deps)

        # More modes = higher cost
        assert combination.estimated_cost > 0

    def test_explain_selection(self, mapper, sample_dependencies):
        """Test selection explanation."""
        combination = mapper.find_optimal_combination(sample_dependencies)
        explanation = mapper.explain_selection(combination, sample_dependencies)

        # Check explanation structure
        assert "selected_modes" in explanation
        assert "reasoning" in explanation
        assert "benefits" in explanation
        assert "considerations" in explanation

        # Should have content
        assert len(explanation["selected_modes"]) > 0
        assert len(explanation["reasoning"]) > 0

    def test_fallback_to_web_mode(self, mapper):
        """Test fallback to web mode when no clear dependencies."""
        weak_deps = QueryDependencies(
            requires_code=False,
            requires_github=False,
            complexity_score=0.1,
            research_depth=ResearchDepth.BASIC
        )

        combination = mapper.find_optimal_combination(weak_deps)

        # Should include web mode as fallback
        mode_values = [mode.value for mode in combination.modes]
        assert "web" in mode_values

    def test_advanced_research_multi_mode(self, mapper):
        """Test that advanced research gets multiple modes."""
        advanced_deps = QueryDependencies(
            requires_code=True,
            requires_academic=True,
            requires_ai_perspectives=True,
            complexity_score=0.85,
            research_depth=ResearchDepth.ADVANCED
        )

        combination = mapper.find_optimal_combination(advanced_deps)

        # Advanced research should use multiple modes
        assert len(combination.modes) >= 2


class TestMultiModeOrchestrator:
    """Test suite for MultiModeOrchestrator."""

    @pytest.fixture
    def orchestrator(self) -> MultiModeOrchestrator:
        """Create MultiModeOrchestrator instance."""
        return MultiModeOrchestrator(
            timeout_per_mode=30,
            max_parallel_modes=4
        )

    @pytest.fixture
    def sample_combination(self) -> ModeCombination:
        """Sample mode combination for testing."""
        return ModeCombination(
            modes=[ResearchMode.OCTOCODE, ResearchMode.WEB],
            predicted_quality=0.88,
            estimated_cost=2.5,
            redundancy_score=0.3,
            coverage_score=0.92
        )

    def test_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator.timeout_per_mode == 30
        assert orchestrator.max_parallel_modes == 4
        assert orchestrator.execution_stats is not None

        # Check executors are registered
        assert ResearchMode.OCTOCODE in orchestrator.mode_executors
        assert ResearchMode.WEB in orchestrator.mode_executors

    @pytest.mark.asyncio
    async def test_execute_research_single_mode(self, orchestrator):
        """Test research execution with single mode."""
        combination = ModeCombination(
            modes=[ResearchMode.WEB],
            predicted_quality=0.8,
            estimated_cost=1.0,
            redundancy_score=0.0,
            coverage_score=0.7
        )

        result = await orchestrator.execute_research(
            query="test query",
            combination=combination
        )

        # Check result structure
        assert isinstance(result, OrchestratedResult)
        assert result.query == "test query"
        assert len(result.modes_executed) == 1
        assert "web" in result.individual_results

    @pytest.mark.asyncio
    async def test_execute_research_multiple_modes(self, orchestrator, sample_combination):
        """Test research execution with multiple modes."""
        result = await orchestrator.execute_research(
            query="react hooks",
            combination=sample_combination
        )

        # Should execute all modes
        assert len(result.individual_results) == 2
        assert "octocode" in result.individual_results
        assert "web" in result.individual_results

    @pytest.mark.asyncio
    async def test_mode_execution_result_structure(self, orchestrator):
        """Test ModeExecutionResult structure."""
        combination = ModeCombination(
            modes=[ResearchMode.WEB],
            predicted_quality=0.8,
            estimated_cost=1.0,
            redundancy_score=0.0,
            coverage_score=0.7
        )

        result = await orchestrator.execute_research("test", combination)

        # Check individual results
        for mode_name, mode_result in result.individual_results.items():
            assert isinstance(mode_result, ModeExecutionResult)
            assert mode_result.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.TIMEOUT]
            assert mode_result.execution_time >= 0
            assert mode_result.sources_found >= 0

    @pytest.mark.asyncio
    async def test_synthesized_results(self, orchestrator, sample_combination):
        """Test result synthesis from multiple modes."""
        result = await orchestrator.execute_research(
            query="test query",
            combination=sample_combination
        )

        # Check synthesized results
        assert "query" in result.synthesized_results
        assert "total_sources" in result.synthesized_results
        assert "successful_modes" in result.synthesized_results
        assert "results" in result.synthesized_results

        # Should have results from successful modes
        assert result.synthesized_results["total_sources"] > 0

    @pytest.mark.asyncio
    async def test_execution_summary(self, orchestrator, sample_combination):
        """Test execution summary generation."""
        result = await orchestrator.execute_research(
            query="test",
            combination=sample_combination
        )

        summary = result.execution_summary

        # Check summary structure
        assert "modes_attempted" in summary
        assert "modes_successful" in summary
        assert "total_execution_time" in summary
        assert "total_sources_found" in summary
        assert "average_confidence" in summary

        # Should match executed modes
        assert summary["modes_attempted"] == 2

    @pytest.mark.asyncio
    async def test_timeout_handling(self, orchestrator):
        """Test timeout handling for mode execution."""
        # Create orchestrator with very short timeout
        short_timeout_orchestrator = MultiModeOrchestrator(
            timeout_per_mode=0.001  # 1ms timeout
        )

        combination = ModeCombination(
            modes=[ResearchMode.COGNITIVE],  # Takes 4 seconds normally
            predicted_quality=0.9,
            estimated_cost=2.5,
            redundancy_score=0.1,
            coverage_score=0.95
        )

        result = await short_timeout_orchestrator.execute_research(
            query="test",
            combination=combination
        )

        # Should handle timeout
        cognitive_result = result.individual_results.get("cognitive-enhanced")
        if cognitive_result:
            assert cognitive_result.status in [ExecutionStatus.TIMEOUT, ExecutionStatus.FAILED]

    @pytest.mark.asyncio
    async def test_execution_statistics_tracking(self, orchestrator, sample_combination):
        """Test that execution statistics are tracked."""
        initial_stats = orchestrator.get_execution_statistics()

        await orchestrator.execute_research("test", sample_combination)

        updated_stats = orchestrator.get_execution_statistics()

        # Should update statistics
        assert updated_stats["total_executions"] > initial_stats["total_executions"]

    @pytest.mark.asyncio
    async def test_consensus_identification(self, orchestrator, sample_combination):
        """Test identification of consensus points."""
        result = await orchestrator.execute_research(
            query="react hooks",
            combination=sample_combination
        )

        # Should identify consensus (even if empty)
        assert "consensus_points" in result.synthesized_results
        assert isinstance(result.synthesized_results["consensus_points"], list)

    @pytest.mark.asyncio
    async def test_unique_insights_extraction(self, orchestrator, sample_combination):
        """Test extraction of unique insights from modes."""
        result = await orchestrator.execute_research(
            query="test",
            combination=sample_combination
        )

        # Should extract unique insights
        insights = result.synthesized_results.get("unique_insights", [])
        assert isinstance(insights, list)

    @pytest.mark.asyncio
    async def test_recommendation_generation(self, orchestrator, sample_combination):
        """Test generation of recommendations."""
        result = await orchestrator.execute_research(
            query="test",
            combination=sample_combination
        )

        # Should generate recommendations
        recommendations = result.synthesized_results.get("recommendations", [])
        assert isinstance(recommendations, list)

    @pytest.mark.asyncio
    async def test_deduplication(self, orchestrator):
        """Test result deduplication."""
        # Note: Deduplication is tested internally via synthesis
        # This test ensures the workflow completes without errors
        combination = ModeCombination(
            modes=[ResearchMode.WEB, ResearchMode.OCTOCODE],
            predicted_quality=0.85,
            estimated_cost=2.5,
            redundancy_score=0.3,
            coverage_score=0.9
        )

        result = await orchestrator.execute_research("test", combination)

        # Should successfully complete
        assert result is not None
        assert len(result.synthesized_results["results"]) >= 0

    @pytest.mark.asyncio
    async def test_empty_combination_error(self, orchestrator):
        """Test error handling for empty mode combination."""
        empty_combination = ModeCombination(
            modes=[],
            predicted_quality=0.0,
            estimated_cost=0.0,
            redundancy_score=0.0,
            coverage_score=0.0
        )

        with pytest.raises(ValueError):
            await orchestrator.execute_research("test", empty_combination)
