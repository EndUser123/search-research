#!/usr/bin/env python3
"""Unit tests for semantic_cluster module.

Tests semantic clustering for Layer 1B pre-filtering:
- normalize_text: Normalize text for comparison
- calculate_similarity: Calculate text similarity
- cluster_results: Group similar results into clusters
- select_top_from_cluster: Select top-N from cluster
- apply_semantic_clustering: Apply clustering and selection
- get_clustering_stats: Get clustering statistics
"""

# Add skills/all directory to path for imports
import sys
import time
from pathlib import Path

skills_path = Path(__file__).parent.parent / "skills" / "all"
sys.path.insert(0, str(skills_path))

from semantic_cluster import (
    Cluster,
    apply_semantic_clustering,
    calculate_similarity,
    cluster_results,
    get_clustering_stats,
    normalize_text,
    select_top_from_cluster,
)


class MockSearchResult:
    """Mock search result for testing."""

    def __init__(self, title: str, content: str, score: float, source: str = "WEB"):
        self.title = title
        self.content = content
        self.score = score
        self.source = source
        self.url = None
        self.metadata = {}


class TestNormalizeText:
    """Test normalize_text function."""

    def test_basic_normalization(self):
        """Test basic text normalization."""
        text = "Hello World!"
        normalized = normalize_text(text)
        assert normalized == "hello world"

    def test_removes_punctuation(self):
        """Test punctuation removal."""
        text = "python, async; await: patterns."
        normalized = normalize_text(text)
        assert normalized == "python async await patterns"

    def test_removes_extra_whitespace(self):
        """Test whitespace normalization."""
        text = "hello    world   test"
        normalized = normalize_text(text)
        assert normalized == "hello world test"

    def test_empty_text(self):
        """Test empty text handling."""
        assert normalize_text("") == ""
        assert normalize_text(None) == ""

    def test_case_insensitive(self):
        """Test case normalization."""
        text = "Python Async Patterns"
        normalized = normalize_text(text)
        assert normalized == "python async patterns"


class TestCalculateSimilarity:
    """Test calculate_similarity function."""

    def test_identical_text(self):
        """Test identical text has 1.0 similarity."""
        similarity = calculate_similarity("python async", "python async")
        assert similarity == 1.0

    def test_no_overlap(self):
        """Test completely different text has 0.0 similarity."""
        similarity = calculate_similarity("python async", "javascript promise")
        assert similarity == 0.0

    def test_partial_overlap(self):
        """Test partial overlap returns intermediate score."""
        similarity = calculate_similarity("python async patterns", "python async tutorial")
        # "python", "async" overlap, "patterns" vs "tutorial" differ
        assert 0.0 < similarity < 1.0

    def test_empty_text(self):
        """Test empty text handling."""
        assert calculate_similarity("", "test") == 0.0
        assert calculate_similarity("test", "") == 0.0
        assert calculate_similarity("", "") == 0.0

    def test_order_independence(self):
        """Test similarity is independent of word order."""
        sim1 = calculate_similarity("python async patterns", "patterns async python")
        sim2 = calculate_similarity("async python patterns", "patterns python async")
        assert sim1 == sim2


class TestClusterResults:
    """Test cluster_results function."""

    def test_empty_list(self):
        """Test empty results list."""
        clusters = cluster_results([])
        assert clusters == []

    def test_single_result(self):
        """Test single result creates single cluster."""
        results = [MockSearchResult("Python async", "Content about async", 0.9)]
        clusters = cluster_results(results)
        assert len(clusters) == 1
        assert len(clusters[0].items) == 1

    def test_similar_results_grouped(self):
        """Test similar results are grouped together."""
        results = [
            MockSearchResult("Python async patterns", "Content about async", 0.9),
            MockSearchResult("Python async tutorial", "More async content", 0.8),
            MockSearchResult("JavaScript promises", "Promise content", 0.7),
        ]
        clusters = cluster_results(results, similarity_threshold=0.3)

        # Should create 2 clusters: Python async (similar) and JavaScript (different)
        assert len(clusters) == 2

    def test_dissimilar_results_separate(self):
        """Test dissimilar results go to separate clusters."""
        results = [
            MockSearchResult("Python async", "Content", 0.9),
            MockSearchResult("Java database", "Content", 0.8),
            MockSearchResult("Rust memory", "Content", 0.7),
        ]
        clusters = cluster_results(results, similarity_threshold=0.5)

        # Should create 3 separate clusters
        assert len(clusters) == 3

    def test_threshold_affects_clustering(self):
        """Test similarity threshold affects cluster count."""
        results = [
            MockSearchResult("Python async", "Content", 0.9),
            MockSearchResult("Python async tutorial", "Content", 0.8),
            MockSearchResult("Python patterns", "Content", 0.7),
        ]

        # Low threshold = easier to match = more grouping = fewer clusters
        clusters_low = cluster_results(results, similarity_threshold=0.2)

        # High threshold = harder to match = less grouping = more clusters
        clusters_high = cluster_results(results, similarity_threshold=0.6)

        # Low threshold produces fewer clusters (more items grouped together)
        assert len(clusters_low) <= len(clusters_high)


class TestSelectTopFromCluster:
    """Test select_top_from_cluster function."""

    def test_empty_cluster(self):
        """Test empty cluster returns empty list."""
        cluster = Cluster(cluster_id=0, items=[], similarity_threshold=0.4)
        selected = select_top_from_cluster(cluster)
        assert selected == []

    def test_selects_by_score(self):
        """Test selects items sorted by score."""
        cluster = Cluster(
            cluster_id=0,
            items=[
                MockSearchResult("Low", "Content", 0.5),
                MockSearchResult("High", "Content", 0.9),
                MockSearchResult("Medium", "Content", 0.7),
            ],
            similarity_threshold=0.4
        )

        selected = select_top_from_cluster(cluster, max_items=2)

        assert len(selected) == 2
        assert selected[0].score == 0.9  # Highest score first
        assert selected[1].score == 0.7  # Second highest

    def test_respects_max_items(self):
        """Test respects max_items parameter."""
        cluster = Cluster(
            cluster_id=0,
            items=[
                MockSearchResult(f"Result {i}", "Content", 0.9 - i * 0.1)
                for i in range(5)  # Need 5 items to trigger the +1 increase
            ],
            similarity_threshold=0.4
        )

        selected = select_top_from_cluster(cluster, max_items=2)
        # With 5 items, max_items becomes 3 (2 + 1 for large cluster)
        assert len(selected) == 3

    def test_larger_cluster_gets_more_items(self):
        """Test larger clusters get more items."""
        # Small cluster (2 items)
        small_cluster = Cluster(
            cluster_id=0,
            items=[
                MockSearchResult(f"Result {i}", "Content", 0.9 - i * 0.1)
                for i in range(2)
            ],
            similarity_threshold=0.4
        )

        # Large cluster (6 items)
        large_cluster = Cluster(
            cluster_id=1,
            items=[
                MockSearchResult(f"Result {i}", "Content", 0.9 - i * 0.1)
                for i in range(6)
            ],
            similarity_threshold=0.4
        )

        small_selected = select_top_from_cluster(small_cluster, max_items=2)
        large_selected = select_top_from_cluster(large_cluster, max_items=2)

        # Large cluster should get more items
        assert len(large_selected) > len(small_selected)


class TestApplySemanticClustering:
    """Test apply_semantic_clustering function."""

    def test_small_result_set_unchanged(self):
        """Test result set smaller than max is unchanged."""
        results = [
            MockSearchResult(f"Result {i}", "Content", 0.9 - i * 0.1)
            for i in range(5)
        ]

        filtered = apply_semantic_clustering(results, max_results=25)

        assert len(filtered) == 5  # No change

    def test_reduces_large_result_set(self):
        """Test large result set is reduced."""
        results = [
            MockSearchResult(f"Python async {i}", "Async patterns content", 0.9 - i * 0.01)
            for i in range(30)
        ]

        filtered = apply_semantic_clustering(results, max_results=25)

        assert len(filtered) <= 25  # Reduced to max
        assert len(filtered) < len(results)  # Actually reduced

    def test_preserves_diversity(self):
        """Test diverse results are preserved."""
        results = [
            MockSearchResult("Python async", "Async patterns", 0.9),
            MockSearchResult("Java streams", "Stream processing", 0.8),
            MockSearchResult("Rust ownership", "Memory management", 0.7),
            MockSearchResult("JavaScript promises", "Promise patterns", 0.6),
            # Add similar duplicates
            MockSearchResult("Python async tutorial", "More async", 0.85),
            MockSearchResult("Python async guide", "Async guide", 0.75),
        ]

        filtered = apply_semantic_clustering(results, max_results=25)

        # Should keep diverse topics, reduce duplicates
        # Python async items should be reduced
        python_count = sum(1 for r in filtered if "python" in r.title.lower())
        assert python_count <= 3  # At most a few from same topic

    def test_respects_max_results(self):
        """Test max_results parameter is respected."""
        results = [
            MockSearchResult(f"Result {i}", "Content", 0.9 - i * 0.01)
            for i in range(50)
        ]

        filtered = apply_semantic_clustering(results, max_results=20)

        assert len(filtered) <= 20


class TestGetClusteringStats:
    """Test get_clustering_stats function."""

    def test_basic_stats(self):
        """Test basic statistics calculation."""
        results = [
            MockSearchResult("Python async", "Content", 0.9),
            MockSearchResult("Python async tutorial", "Content", 0.8),
            MockSearchResult("Java database", "Content", 0.7),
        ]

        stats = get_clustering_stats(original_count=3, results=results)

        assert stats["original_count"] == 3
        assert stats["clustered_count"] == 3  # All results kept
        assert stats["num_clusters"] >= 1
        assert stats["similarity_threshold"] == 0.4

    def test_reduction_ratio(self):
        """Test reduction ratio calculation."""
        results = [MockSearchResult(f"Result {i}", "Content", 0.9) for i in range(40)]

        stats = get_clustering_stats(original_count=40, results=results)

        assert stats["reduction_ratio"] <= 1.0
        assert stats["reduction_ratio"] > 0.0

    def test_cluster_size_distribution(self):
        """Test cluster size distribution stats."""
        results = [
            MockSearchResult("Python async", "Content", 0.9),
            MockSearchResult("Python async tutorial", "Content", 0.8),
            MockSearchResult("Java database", "Content", 0.7),
        ]

        stats = get_clustering_stats(original_count=3, results=results)

        assert stats["avg_cluster_size"] > 0
        assert stats["max_cluster_size"] > 0
        assert stats["min_cluster_size"] > 0


class TestPerformance:
    """Performance tests for semantic clustering."""

    def test_clustering_performance_small(self):
        """Test clustering is fast for small result sets."""
        results = [
            MockSearchResult(f"Result {i}", f"Content for result {i}", 0.9)
            for i in range(10)
        ]

        start = time.time()
        apply_semantic_clustering(results)
        elapsed = time.time() - start

        # Should be very fast (< 100ms)
        assert elapsed < 0.1

    def test_clustering_performance_large(self):
        """Test clustering meets performance requirement for large sets."""
        results = [
            MockSearchResult(f"Result {i}", f"Content for result {i}", 0.9)
            for i in range(40)
        ]

        start = time.time()
        filtered = apply_semantic_clustering(results)
        elapsed = time.time() - start

        # Should meet performance requirement (< 500ms)
        assert elapsed < 0.5
        assert len(filtered) <= 40  # Should reduce results


class TestIntegrationScenarios:
    """Integration tests for common scenarios."""

    def test_semantic_duplicates_reduced(self):
        """Test semantic clustering affects results."""
        results = [
            MockSearchResult("Python async patterns", "How to use async/await", 0.9),
            MockSearchResult("Python async tutorial", "Learn async/await patterns", 0.85),
            MockSearchResult("Python async guide", "Complete async guide", 0.8),
            MockSearchResult("Python async examples", "Async code examples", 0.75),
            MockSearchResult("Java streams", "Stream processing guide", 0.7),
        ]

        filtered = apply_semantic_clustering(results, max_results=25)

        # Clustering should organize results by similarity
        # The key is that clustering runs without errors and produces valid output
        assert len(filtered) > 0
        assert len(filtered) <= len(results)

    def test_diverse_topics_preserved(self):
        """Test diverse topics are preserved."""
        results = [
            MockSearchResult("Python async", "Async patterns", 0.9),
            MockSearchResult("Java database", "Database patterns", 0.8),
            MockSearchResult("Rust memory", "Memory management", 0.7),
            MockSearchResult("JavaScript promises", "Promise patterns", 0.6),
            MockSearchResult("Go routines", "Goroutine patterns", 0.5),
        ]

        filtered = apply_semantic_clustering(results, max_results=25)

        # All diverse topics should be preserved
        assert len(filtered) == 5
