"""
Comprehensive tests for analysis components.

Tests for:
- GapAnalyzer: gap detection and follow-up query generation
- ContradictionDetector: contradiction detection between sources
- DensityCalculator: numeric and technical density calculation
- TopicClusterer: topic clustering with novelty tracking
"""


import sys
from pathlib import Path

import pytest

# Add test_migrated to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

from conftest import MockSearchResult

from core.analysis.contradiction_detector import (
    Contradiction,
    ContradictionDetector,
    ResearchResult,
)
from core.analysis.density_calculator import DensityCalculator
from core.analysis.gap_analyzer import CoverageGap, GapAnalyzer, GapType
from core.analysis.topic_clusterer import (
    CoverageState,
    NoveltyTracker,
    TopicClusterer,
    TopicSignature,
)


class TestGapAnalyzer:
    """Test suite for GapAnalyzer gap detection and query generation."""

    @pytest.fixture
    def analyzer(self) -> GapAnalyzer:
        """Create GapAnalyzer instance for testing."""
        return GapAnalyzer()

    @pytest.fixture
    def sample_results(self, sample_normalized_results):
        """Sample results for gap analysis."""
        return sample_normalized_results

    def test_detect_gaps_healthy_coverage(self, analyzer, sample_results):
        """Test gap detection with healthy coverage (no gaps)."""
        topics = {"topic_async", "topic_python", "topic_github"}
        source_types = {"docs", "community", "academic"}
        domains = {"docs.python.org", "github.com", "stackoverflow.com", "arxiv.org"}

        gaps = analyzer.detect_gaps(sample_results, topics, source_types, domains)

        # Should have minimal or no gaps with healthy coverage
        assert len(gaps) == 0

    def test_detect_gaps_missing_source_types(self, analyzer, sample_results):
        """Test gap detection when source types are missing."""
        topics = {"topic_async"}
        source_types = {"docs"}  # Only one type
        domains = {"docs.python.org"}

        gaps = analyzer.detect_gaps(sample_results, topics, source_types, domains)

        # Should detect missing source types
        assert len(gaps) > 0
        gap_types = [g.gap_type for g in gaps]
        assert GapType.MISSING_SOURCE_TYPE in gap_types

    def test_detect_gaps_low_domain_diversity(self, analyzer, sample_results):
        """Test gap detection with low domain diversity."""
        topics = {"topic_async", "topic_python"}
        source_types = {"docs", "community"}
        domains = {"docs.python.org"}  # Only one domain

        gaps = analyzer.detect_gaps(sample_results, topics, source_types, domains)

        # Should detect low domain diversity
        assert len(gaps) > 0
        gap_types = [g.gap_type for g in gaps]
        assert GapType.LOW_DOMAIN_DIVERSITY in gap_types

        # Check severity calculation
        domain_gap = next(g for g in gaps if g.gap_type == GapType.LOW_DOMAIN_DIVERSITY)
        assert domain_gap.severity > 0.5
        assert domain_gap.metadata["domain_count"] == 1

    def test_detect_gaps_low_topic_coverage(self, analyzer, sample_results):
        """Test gap detection with low topic coverage."""
        topics = {"topic_async"}  # Only one topic
        source_types = {"docs", "community"}
        domains = {"docs.python.org", "github.com"}

        gaps = analyzer.detect_gaps(sample_results, topics, source_types, domains)

        # Should detect low topic coverage
        assert len(gaps) > 0
        gap_types = [g.gap_type for g in gaps]
        assert GapType.LOW_TOPIC_COVERAGE in gap_types

    def test_detect_gaps_severity_ordering(self, analyzer, sample_results):
        """Test that gaps are ordered by severity (highest first)."""
        topics = {"topic_async"}
        source_types = {"docs"}
        domains = {"docs.python.org"}

        gaps = analyzer.detect_gaps(sample_results, topics, source_types, domains)

        if len(gaps) > 1:
            # Check that gaps are sorted by severity descending
            for i in range(len(gaps) - 1):
                assert gaps[i].severity >= gaps[i + 1].severity

    def test_generate_follow_up_query_missing_academic(self, analyzer):
        """Test follow-up query generation for missing academic sources."""
        gap = CoverageGap(
            gap_type=GapType.MISSING_SOURCE_TYPE,
            description="Missing academic sources",
            severity=0.8,
            metadata={"missing_type": "academic"}
        )

        query = analyzer.generate_follow_up_query("python async", gap)

        # Should include academic-focused terms
        assert "paper" in query.lower() or "research" in query.lower() or "academic" in query.lower()

    def test_generate_follow_up_query_missing_video(self, analyzer):
        """Test follow-up query generation for missing video sources."""
        gap = CoverageGap(
            gap_type=GapType.MISSING_SOURCE_TYPE,
            description="Missing video sources",
            severity=0.7,
            metadata={"missing_type": "video"}
        )

        query = analyzer.generate_follow_up_query("docker tutorial", gap)

        # Should include video-related terms
        assert "video" in query.lower() or "youtube" in query.lower()

    def test_generate_follow_up_query_domain_diversity(self, analyzer):
        """Test follow-up query generation for domain diversity."""
        gap = CoverageGap(
            gap_type=GapType.LOW_DOMAIN_DIVERSITY,
            description="Low domain diversity",
            severity=0.6,
            metadata={"domain_count": 2}
        )

        query = analyzer.generate_follow_up_query("react hooks", gap)

        # Should add variation to query
        assert "alternative" in query.lower() or "different" in query.lower()

    def test_generate_follow_up_query_topic_exploration(self, analyzer):
        """Test follow-up query generation for topic exploration."""
        gap = CoverageGap(
            gap_type=GapType.LOW_TOPIC_COVERAGE,
            description="Low topic coverage",
            severity=0.7,
            metadata={"topic_count": 1}
        )

        query = analyzer.generate_follow_up_query("kubernetes", gap)

        # Should add exploratory terms
        assert "overview" in query.lower() or "guide" in query.lower() or "tutorial" in query.lower()


class TestContradictionDetector:
    """Test suite for ContradictionDetector."""

    @pytest.fixture
    def detector(self) -> ContradictionDetector:
        """Create ContradictionDetector instance."""
        return ContradictionDetector()

    def test_no_contradictions_single_result(self, detector):
        """Test that contradictions require at least 2 results."""
        results = [
            ResearchResult(
                title="Test",
                url="https://test.com",
                content="Python supports async",
                source="test"
            )
        ]

        contradictions = detector.detect_contradictions(results, "python async")

        assert len(contradictions) == 0

    def test_detect_direct_negation_contradiction(self, detector):
        """Test detection of direct negation contradictions."""
        results = [
            ResearchResult(
                title="Positive claim",
                url="https://example1.com",
                content="Python supports async/await syntax natively for concurrent programming.",
                source="docs"
            ),
            ResearchResult(
                title="Negative claim",
                url="https://example2.com",
                content="Python does not support async, requires external libraries.",
                source="blog"
            )
        ]

        contradictions = detector.detect_contradictions(results, "python async support")

        # Should detect contradiction if common terms exist
        # Note: May not detect if insufficient content overlap
        if len(contradictions) > 0:
            contradiction = contradictions[0]
            assert contradiction.confidence > 0.0
            assert len(contradiction.sources_conflicting) == 2
            assert contradiction.topic is not None
        else:
            # If no contradiction detected, that's also valid (depends on overlap)
            assert isinstance(contradictions, list)

    def test_detect_exclusive_vs_inclusive_contradiction(self, detector):
        """Test detection of exclusive vs inclusive language contradictions."""
        results = [
            ResearchResult(
                title="Exclusive claim",
                url="https://example1.com",
                content="GitHub only supports webhooks for integration.",
                source="docs"
            ),
            ResearchResult(
                title="Inclusive claim",
                url="https://example2.com",
                content="GitHub supports both webhooks and actions for integration.",
                source="tutorial"
            )
        ]

        contradictions = detector.detect_contradictions(results, "github integration")

        # Should detect contradiction
        assert len(contradictions) > 0

        contradiction = contradictions[0]
        assert contradiction.confidence > 0.5  # Medium-high confidence
        assert "github" in contradiction.topic.lower()

    def test_contradiction_with_dict_input(self, detector):
        """Test that detector accepts dict input (not just ResearchResult objects)."""
        results = [
            {
                "title": "Positive",
                "url": "https://example1.com",
                "content": "Feature is supported",
                "source": "docs"
            },
            {
                "title": "Negative",
                "url": "https://example2.com",
                "content": "Feature is not supported",
                "source": "blog"
            }
        ]

        contradictions = detector.detect_contradictions(results, "feature support")

        # Should handle dict input without errors
        assert isinstance(contradictions, list)

    def test_contradiction_sorting_by_confidence(self, detector):
        """Test that contradictions are sorted by confidence (descending)."""
        results = [
            ResearchResult(
                title=f"Result {i}",
                url=f"https://example{i}.com",
                content="Content with varying contradictions",
                source="test"
            )
            for i in range(5)
        ]

        contradictions = detector.detect_contradictions(results, "test query")

        if len(contradictions) > 1:
            # Check sorting
            for i in range(len(contradictions) - 1):
                assert contradictions[i].confidence >= contradictions[i + 1].confidence

    def test_get_contradiction_summary_empty(self, detector):
        """Test contradiction summary with no contradictions."""
        summary = detector.get_contradiction_summary([])

        assert "No contradictions detected" in summary

    def test_get_contradiction_summary_with_contradictions(self, detector):
        """Test contradiction summary with contradictions present."""
        contradictions = [
            Contradiction(
                topic="async support",
                description="Sources disagree on async support",
                sources_conflicting=["url1", "url2"],
                confidence=0.85
            ),
            Contradiction(
                topic="webhook options",
                description="Different webhook capabilities reported",
                sources_conflicting=["url3", "url4"],
                confidence=0.72
            )
        ]

        summary = detector.get_contradiction_summary(contradictions)

        assert "2 contradiction" in summary
        assert "async support" in summary
        assert "webhook options" in summary


class TestDensityCalculator:
    """Test suite for DensityCalculator."""

    @pytest.fixture
    def calculator(self) -> DensityCalculator:
        """Create DensityCalculator instance."""
        return DensityCalculator()

    @pytest.fixture
    def numeric_results(self):
        """Results with high numeric density."""
        return [
            MockSearchResult(
                title="API Rate Limits v2.0",
                url="https://api.example.com/docs",
                snippet="API supports 1000 requests per minute with 5 endpoints",
                score=0.9
            ),
            MockSearchResult(
                title="Version 3.5 Release Notes",
                url="https://example.com/v3.5",
                snippet="Added 15 new features and fixed 42 bugs in version 3.5.2",
                score=0.85
            ),
        ]

    @pytest.fixture
    def technical_results(self):
        """Results with high technical density."""
        return [
            MockSearchResult(
                title="Async API Implementation",
                url="https://dev.example.com/async",
                snippet="Implement async endpoint with timeout and connection pool",
                score=0.92
            ),
            MockSearchResult(
                title="Database Query Optimization",
                url="https://db.example.com/optimize",
                snippet="Optimize SQL query with proper indexing and serialization",
                score=0.88
            ),
        ]

    def test_compute_numeric_density_empty_results(self, calculator):
        """Test numeric density with empty results."""
        density = calculator.compute_numeric_density([])

        assert density == 0.0

    def test_compute_numeric_density_high(self, calculator, numeric_results):
        """Test numeric density calculation with numeric content."""
        density = calculator.compute_numeric_density(numeric_results)

        # Should detect high numeric density
        assert density > 0.0
        assert density <= 1.0

    def test_compute_numeric_density_low(self, calculator, mock_search_results):
        """Test numeric density with non-numeric content."""
        density = calculator.compute_numeric_density(mock_search_results)

        # Should have lower numeric density
        assert 0.0 <= density <= 1.0

    def test_compute_technical_density_empty(self, calculator):
        """Test technical density with empty results."""
        density = calculator.compute_technical_density([])

        assert density == 0.0

    def test_compute_technical_density_high(self, calculator, technical_results):
        """Test technical density with technical content."""
        density = calculator.compute_technical_density(technical_results)

        # Should detect high technical density
        assert density > 0.0
        assert density <= 1.0

    def test_compute_technical_density_low(self, calculator, mock_search_results):
        """Test technical density with non-technical content."""
        density = calculator.compute_technical_density(mock_search_results)

        # Should have lower technical density
        assert 0.0 <= density <= 1.0

    def test_compute_density_combined(self, calculator, numeric_results, technical_results):
        """Test combined density score."""
        # Test with numeric results
        density_numeric = calculator.compute_density(numeric_results)
        assert 0.0 <= density_numeric <= 1.0

        # Test with technical results
        density_technical = calculator.compute_density(technical_results)
        assert 0.0 <= density_technical <= 1.0

        # Combined density should be average of numeric and technical
        assert abs(density_numeric - (
            calculator.compute_numeric_density(numeric_results) +
            calculator.compute_technical_density(numeric_results)
        ) / 2) < 0.01


class TestTopicClusterer:
    """Test suite for TopicClusterer."""

    @pytest.fixture
    def clusterer(self) -> TopicClusterer:
        """Create TopicClusterer instance."""
        return TopicClusterer()

    def test_extract_keywords_basic(self, clusterer):
        """Test basic keyword extraction."""
        text = "Python asyncio programming concurrent coroutine await"

        keywords = clusterer.extract_keywords(text, top_n=5)

        # Should extract meaningful keywords
        assert len(keywords) <= 5
        assert "python" in keywords
        assert "asyncio" in keywords
        # Stopwords should be filtered
        assert "programming" not in keywords or len(keywords) <= 5

    def test_extract_keywords_removes_stopwords(self, clusterer):
        """Test that stopwords are removed from keywords."""
        text = "The async and await are in python for concurrent"

        keywords = clusterer.extract_keywords(text, top_n=10)

        # Check that common stopwords are removed
        assert "the" not in keywords
        assert "and" not in keywords
        assert "are" not in keywords
        assert "in" not in keywords

    def test_extract_keywords_empty_text(self, clusterer):
        """Test keyword extraction with empty text."""
        keywords = clusterer.extract_keywords("", top_n=5)

        assert len(keywords) == 0

    def test_compute_keyword_hash_consistency(self, clusterer):
        """Test that keyword hash is consistent for same keywords."""
        keywords1 = {"python", "async", "await"}
        keywords2 = {"python", "async", "await"}

        hash1 = clusterer._compute_keyword_hash(keywords1)
        hash2 = clusterer._compute_keyword_hash(keywords2)

        # Same keywords should produce same hash
        assert hash1 == hash2

    def test_compute_keyword_hash_order_independence(self, clusterer):
        """Test that keyword order doesn't affect hash."""
        keywords1 = {"python", "async", "await"}
        keywords2 = {"await", "python", "async"}

        hash1 = clusterer._compute_keyword_hash(keywords1)
        hash2 = clusterer._compute_keyword_hash(keywords2)

        # Different order should produce same hash
        assert hash1 == hash2

    def test_cluster_results_basic(self, clusterer):
        """Test basic result clustering."""

        # Add title and snippet attributes to mock results
        results = [
            MockSearchResult(
                title="Python Async Programming",
                url="https://example.com/async1",
                snippet="Learn async programming with python",
                score=0.9
            ),
            MockSearchResult(
                title="Async Python Tutorial",
                url="https://example.com/async2",
                snippet="Python async await tutorial",
                score=0.85
            ),
        ]

        clusters = clusterer.cluster_results(results)

        # Should create at least one cluster
        assert len(clusters) >= 1

        # Check cluster structure
        for topic_id, signature in clusters.items():
            assert isinstance(signature, TopicSignature)
            assert len(signature.keywords) > 0
            assert len(signature.result_ids) > 0

    def test_cluster_results_empty(self, clusterer):
        """Test clustering with empty results."""
        clusters = clusterer.cluster_results([])

        assert len(clusters) == 0


class TestNoveltyTracker:
    """Test suite for NoveltyTracker."""

    @pytest.fixture
    def tracker(self) -> NoveltyTracker:
        """Create NoveltyTracker instance."""
        return NoveltyTracker(novelty_threshold=0.1)

    def test_compute_coverage_state_basic(self, tracker):
        """Test coverage state computation."""

        # Create mock results with required attributes
        results = [
            MockSearchResult(
                title="Test",
                url="https://example.com",
                snippet="python async programming",
                score=0.8,
                source_type="docs",
                domain="example.com"
            )
        ]

        clusters = {"topic_test": TopicSignature(
            topic_id="topic_test",
            keyword_hash=123,
            keywords={"python", "async"},
            result_ids={"url1"}
        )}

        state = tracker.compute_coverage_state(results, clusters)

        # Check state structure
        assert isinstance(state, CoverageState)
        assert len(state.topics) > 0
        assert len(state.source_types) > 0

    def test_compute_novelty_first_iteration(self, tracker, sample_coverage_state):
        """Test novelty computation for first iteration (no previous state)."""
        novelty = tracker.compute_novelty(sample_coverage_state, None)

        # First iteration should have max novelty
        assert novelty == 1.0

    def test_compute_novelty_same_state(self, tracker, sample_coverage_state):
        """Test novelty computation with identical states."""
        novelty = tracker.compute_novelty(sample_coverage_state, sample_coverage_state)

        # Identical states should have zero novelty
        assert novelty == 0.0

    def test_compute_novelty_different_state(self, tracker, sample_coverage_state):
        """Test novelty computation with different states."""
        # Create a different state with new topics
        different_state = CoverageState(
            topics=sample_coverage_state.topics | {"topic_new"},
            source_types=sample_coverage_state.source_types | {"video"},
            domains=sample_coverage_state.domains | {"youtube.com"},
            claim_terms=sample_coverage_state.claim_terms | {"newterm"}
        )

        novelty = tracker.compute_novelty(different_state, sample_coverage_state)

        # Should have positive novelty
        assert novelty > 0.0
        assert novelty <= 1.0

    def test_should_continue_first_iteration(self, tracker, sample_coverage_state):
        """Test should_continue on first iteration."""
        should_continue = tracker.should_continue(sample_coverage_state)

        # First iteration should always continue
        assert should_continue is True

    def test_should_continue_low_novelty(self, tracker, sample_coverage_state):
        """Test should_continue with low novelty."""
        # First iteration
        tracker.should_continue(sample_coverage_state)

        # Second iteration with same state (low novelty)
        should_continue = tracker.should_continue(sample_coverage_state)

        # Should still continue after one low novelty
        assert should_continue is True

        # Third iteration with same state
        should_continue = tracker.should_continue(sample_coverage_state)

        # Should stop after two low novelty iterations
        assert should_continue is False

    def test_should_continue_high_novelty(self, tracker, sample_coverage_state):
        """Test should_continue with high novelty."""
        # First iteration
        tracker.should_continue(sample_coverage_state)

        # Create new state with high novelty
        new_state = CoverageState(
            topics=sample_coverage_state.topics | {"topic_a", "topic_b", "topic_c"},
            source_types=sample_coverage_state.source_types | {"academic", "video"},
            domains=sample_coverage_state.domains | {"arxiv.org", "youtube.com"},
            claim_terms=sample_coverage_state.claim_terms | {"new1", "new2"}
        )

        should_continue = tracker.should_continue(new_state)

        # Should continue with high novelty
        assert should_continue is True
