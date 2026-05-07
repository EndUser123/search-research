"""
Tests for CHS v2 Clustering module.

Tests verify the clustering functionality for organizing search results
into thematic groups using different clustering modes.

Run with: pytest P:\\\\__csf/src/knowledge/systems/chs/v2/tests/test_clustering.py -v
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import numpy as np
import pytest
from .clustering import (
    MIN_RESULTS_FOR_CLUSTERING,
    ClusteredSearchResults,
    cluster_results,
    filter_results_by_cluster,
)


class TestClusterByBackend:
    """Tests for backend-based clustering."""

    @pytest.fixture
    def sample_results(self):
        """Create sample search results with different backends."""
        return [
            {"id": 1, "content": "async patterns in python", "backend": "chs"},
            {"id": 2, "content": "coroutine best practices", "backend": "chs"},
            {"id": 3, "content": "event loop tutorial", "backend": "cks"},
            {"id": 4, "content": "asyncio internals", "backend": "cks"},
            {"id": 5, "content": "async await syntax", "backend": "chs"},
            {"id": 6, "content": "task scheduling", "backend": "cks"},
            {"id": 7, "content": "async generators", "backend": "code"},
            {"id": 8, "content": "async context managers", "backend": "code"},
            {"id": 9, "content": "future objects", "backend": "code"},
            {"id": 10, "content": "async iterators", "backend": "code"},
        ]

    def test_cluster_by_backend_groups_correctly(self, sample_results):
        """
        Test that cluster_by_backend groups results by source backend.

        Given: Results from multiple backends
        When: Clustering with mode='backend'
        Then: Results are grouped by backend with correct counts
        """
        result = cluster_results(sample_results, mode="backend")
        assert result["mode"] == "backend"
        assert result["total_results"] == 10
        assert len(result["clusters"]) == 3
        clusters_by_label = {c["label"]: c for c in result["clusters"]}
        assert "Chs Results" in clusters_by_label
        assert clusters_by_label["Chs Results"]["count"] == 3
        assert "Cks Results" in clusters_by_label
        assert clusters_by_label["Cks Results"]["count"] == 3
        assert "Code Results" in clusters_by_label
        assert clusters_by_label["Code Results"]["count"] == 4

    def test_cluster_by_backend_confidence_is_one(self, sample_results):
        """
        Test that backend clustering has confidence=1.0.

        Given: Results with backend field
        When: Clustering by backend
        Then: All clusters have confidence=1.0 (deterministic grouping)
        """
        result = cluster_results(sample_results, mode="backend")
        for cluster in result["clusters"]:
            assert cluster["confidence"] == 1.0

    def test_cluster_by_backend_with_source_field(self):
        """
        Test that backend clustering uses 'source' field if 'backend' missing.

        Given: Results with 'source' instead of 'backend' field
        When: Clustering by backend
        Then: Results are grouped by 'source' field
        """
        results = []
        for i in range(5):
            results.append({"id": i * 2 + 1, "content": f"result {i * 2 + 1}", "source": "docs"})
            results.append({"id": i * 2 + 2, "content": f"result {i * 2 + 2}", "source": "skills"})
        result = cluster_results(results, mode="backend")
        assert len(result["clusters"]) == 2
        assert result["clusters"][0]["count"] == 5
        assert result["clusters"][1]["count"] == 5


class TestClusterByTemporal:
    """Tests for temporal-based clustering."""

    @pytest.fixture
    def sample_results_with_timestamps(self):
        """Create sample results with different timestamps."""
        now = datetime.now(UTC)
        return [
            {"id": 1, "content": "recent result 1", "timestamp": now},
            {"id": 2, "content": "recent result 2", "timestamp": now - timedelta(days=3)},
            {"id": 3, "content": "recent result 3", "timestamp": now - timedelta(days=5)},
            {"id": 4, "content": "older result 1", "timestamp": now - timedelta(days=10)},
            {"id": 5, "content": "older result 2", "timestamp": now - timedelta(days=20)},
            {"id": 6, "content": "older result 3", "timestamp": now - timedelta(days=25)},
            {"id": 7, "content": "archived result 1", "timestamp": now - timedelta(days=35)},
            {"id": 8, "content": "archived result 2", "timestamp": now - timedelta(days=50)},
            {"id": 9, "content": "archived result 3", "timestamp": now - timedelta(days=100)},
            {"id": 10, "content": "archived result 4", "timestamp": now - timedelta(days=200)},
        ]

    def test_cluster_by_temporal_groups_by_time(self, sample_results_with_timestamps):
        """
        Test that cluster_by_temporal groups results by time periods.

        Given: Results with different timestamps
        When: Clustering with mode='temporal'
        Then: Results are grouped by recent/older/archived periods
        """
        result = cluster_results(sample_results_with_timestamps, mode="temporal")
        assert result["mode"] == "temporal"
        assert result["total_results"] == 10
        assert len(result["clusters"]) == 3
        clusters_by_label = {c["label"]: c for c in result["clusters"]}
        recent = clusters_by_label.get("Recent (Last 7 days)")
        assert recent is not None
        assert recent["count"] == 3
        older = clusters_by_label.get("Previous (7-30 days)")
        assert older is not None
        assert older["count"] == 3
        archived = clusters_by_label.get("Archived (30+ days)")
        assert archived is not None
        assert archived["count"] == 4

    def test_cluster_by_temporal_with_unix_timestamp(self):
        """
        Test that temporal clustering handles Unix timestamps.

        Given: Results with Unix timestamp (int/float)
        When: Clustering by temporal mode
        Then: Correctly parses and groups by time
        """
        now = datetime.now(UTC)
        results = []
        for i in range(4):
            results.append(
                {"id": i * 3 + 1, "content": f"recent {i}", "timestamp": now.timestamp()}
            )
        for i in range(4):
            results.append(
                {
                    "id": i * 3 + 2,
                    "content": f"older {i}",
                    "timestamp": (now - timedelta(days=15)).timestamp(),
                }
            )
        for i in range(2):
            results.append(
                {
                    "id": i * 3 + 3,
                    "content": f"archived {i}",
                    "timestamp": (now - timedelta(days=40)).timestamp(),
                }
            )
        result = cluster_results(results, mode="temporal")
        assert len(result["clusters"]) >= 2

    def test_cluster_by_temporal_with_iso_string(self):
        """
        Test that temporal clustering handles ISO timestamp strings.

        Given: Results with ISO format timestamp strings
        When: Clustering by temporal mode
        Then: Correctly parses and groups by time
        """
        now = datetime.now(UTC)
        results = []
        for i in range(4):
            results.append(
                {"id": i * 3 + 1, "content": f"recent {i}", "created_at": now.isoformat()}
            )
        for i in range(4):
            results.append(
                {
                    "id": i * 3 + 2,
                    "content": f"older {i}",
                    "created_at": (now - timedelta(days=15)).isoformat(),
                }
            )
        for i in range(2):
            results.append(
                {
                    "id": i * 3 + 3,
                    "content": f"archived {i}",
                    "created_at": (now - timedelta(days=40)).isoformat(),
                }
            )
        result = cluster_results(results, mode="temporal")
        assert len(result["clusters"]) >= 2


class TestClusterByTopic:
    """Tests for semantic topic clustering."""

    @pytest.fixture
    def sample_results_with_embeddings(self):
        """Create sample results with embedding vectors."""
        async_embeddings = []
        for i in range(5):
            emb = (
                np.ones(384, dtype=np.float32)
                + np.random.RandomState(40 + i).randn(384).astype(np.float32) * 0.05
            )
            async_embeddings.append(emb)
        loop_embeddings = []
        for i in range(5):
            emb = (
                np.full(384, -1.0, dtype=np.float32)
                + np.random.RandomState(50 + i).randn(384).astype(np.float32) * 0.05
            )
            loop_embeddings.append(emb)
        all_embeddings = async_embeddings + loop_embeddings
        results = []
        for i, emb in enumerate(all_embeddings):
            if i < 5:
                content = f"async await pattern {i}"
            else:
                content = f"event loop mechanic {i - 5}"
            results.append({"id": i + 1, "content": content, "embedding": emb.tobytes()})
        return results

    def test_cluster_by_topic_creates_semantic_groups(self, sample_results_with_embeddings):
        """
        Test that cluster_by_topic groups semantically similar results.

        Given: Results with embedding vectors
        When: Clustering with mode='topic'
        Then: Creates clusters based on embedding similarity
        """
        result = cluster_results(sample_results_with_embeddings, mode="topic")
        assert result["mode"] == "topic"
        assert result["total_results"] == 10
        assert len(result["clusters"]) >= 1
        if result["clusters"]:
            assert result["clusters"][0]["count"] >= 2

    def test_cluster_by_topic_respects_n_clusters_limit(self, sample_results_with_embeddings):
        """
        Test that topic clustering respects n_clusters parameter.

        Given: Results with embeddings
        When: Clustering with n_clusters=2
        Then: Returns at most 2 clusters
        """
        result = cluster_results(sample_results_with_embeddings, mode="topic", n_clusters=2)
        assert len(result["clusters"]) <= 2

    def test_cluster_by_topic_with_numpy_array_embeddings(self):
        """
        Test that topic clustering handles numpy array embeddings.

        Given: Results with embedding as numpy array
        When: Clustering by topic
        Then: Correctly processes numpy array embeddings
        """
        base_embedding = np.ones(384, dtype=np.float32)
        results = []
        for i in range(10):
            results.append(
                {
                    "id": i + 1,
                    "content": f"similar content {i}",
                    "embedding": base_embedding.tobytes(),
                }
            )
        result = cluster_results(results, mode="topic")
        assert len(result["clusters"]) >= 1
        if result["clusters"]:
            assert result["clusters"][0]["count"] >= 2


class TestClusteringEdgeCases:
    """Tests for edge cases and error handling."""

    def test_cluster_with_empty_results(self):
        """
        Test that clustering handles empty results.

        Given: Empty results list
        When: Calling cluster_results
        Then: Returns empty clustering output
        """
        result = cluster_results([], mode="topic")
        assert result["total_results"] == 0
        assert result["clusters"] == []
        assert result["unclustered"] == 0

    def test_cluster_with_fewer_than_min_results(self):
        """
        Test that clustering doesn't activate for small result sets.

        Given: Results with fewer than MIN_RESULTS_FOR_CLUSTERING
        When: Calling cluster_results
        Then: Returns empty clustering (not useful for small sets)
        """
        results = [
            {"id": 1, "content": "result 1", "backend": "chs"},
            {"id": 2, "content": "result 2", "backend": "cks"},
        ]
        result = cluster_results(results, mode="topic")
        assert result["total_results"] == 2
        assert result["clusters"] == []
        assert result["unclustered"] == 2

    def test_cluster_with_unknown_mode(self):
        """
        Test that clustering falls back to 'backend' for unknown modes.

        Given: Results and an invalid cluster mode
        When: Calling cluster_results with unknown mode
        Then: Falls back to backend clustering
        """
        results = [
            {"id": 1, "content": "result 1", "backend": "chs"},
            {"id": 2, "content": "result 2", "backend": "cks"},
        ] * MIN_RESULTS_FOR_CLUSTERING
        result = cluster_results(results, mode="unknown_mode")
        assert result["mode"] == "unknown_mode"
        assert len(result["clusters"]) >= 1

    def test_cluster_with_results_missing_embeddings(self):
        """
        Test that topic clustering handles missing embeddings gracefully.

        Given: Results without embedding field
        When: Clustering by topic mode
        Then: Falls back gracefully (no clusters or uses available data)
        """
        results = [{"id": i, "content": f"result {i}"} for i in range(15)]
        result = cluster_results(results, mode="topic")
        assert result["total_results"] == 15
        assert len(result["clusters"]) == 0
        assert result["unclustered"] == 15


class TestFilterResultsByCluster:
    """Tests for filtering results by cluster ID."""

    @pytest.fixture
    def sample_results_and_clustering(self):
        """Create sample results and clustering output."""
        results = [
            {"id": 1, "content": "async patterns"},
            {"id": 2, "content": "coroutine"},
            {"id": 3, "content": "event loop"},
            {"id": 4, "content": "task scheduling"},
            {"id": 5, "content": "future objects"},
        ]
        clustering = {
            "mode": "topic",
            "total_results": 5,
            "clusters": [
                {
                    "id": "c1",
                    "label": "Async Patterns",
                    "count": 2,
                    "result_ids": [0, 1],
                    "confidence": 0.9,
                    "summary": "Async related",
                },
                {
                    "id": "c2",
                    "label": "Event Loop",
                    "count": 2,
                    "result_ids": [2, 3],
                    "confidence": 0.85,
                    "summary": "Event loop related",
                },
            ],
            "unclustered": 1,
        }
        return (results, clustering)

    def test_filter_by_cluster_id(self, sample_results_and_clustering):
        """
        Test that filter_results_by_cluster returns correct subset.

        Given: Results and clustering output
        When: Filtering by cluster ID 'c1'
        Then: Returns only results in cluster c1
        """
        results, clustering = sample_results_and_clustering
        filtered = filter_results_by_cluster(results, clustering, "c1")
        assert len(filtered) == 2
        assert filtered[0]["id"] == 1
        assert filtered[1]["id"] == 2

    def test_filter_by_nonexistent_cluster(self, sample_results_and_clustering):
        """
        Test that filtering by non-existent cluster returns empty.

        Given: Results and clustering output
        When: Filtering by cluster ID that doesn't exist
        Then: Returns empty list
        """
        results, clustering = sample_results_and_clustering
        filtered = filter_results_by_cluster(results, clustering, "c99")
        assert filtered == []

    def test_filter_preserves_result_order(self, sample_results_and_clustering):
        """
        Test that filtering preserves original result order.

        Given: Results and clustering output
        When: Filtering by cluster ID
        Then: Filtered results maintain original order
        """
        results, clustering = sample_results_and_clustering
        filtered = filter_results_by_cluster(results, clustering, "c1")
        assert filtered[0]["id"] == results[0]["id"]
        assert filtered[1]["id"] == results[1]["id"]


class TestClusteredSearchResults:
    """Tests for ClusteredSearchResults wrapper class."""

    def test_initialization(self):
        """
        Test that ClusteredSearchResults initializes correctly.

        Given: Results and clustering output
        When: Creating ClusteredSearchResults instance
        Then: Instance stores both results and clustering
        """
        results = [{"id": 1, "content": "test"}]
        clustering = {"mode": "topic", "total_results": 1, "clusters": [], "unclustered": 1}
        csr = ClusteredSearchResults(results, clustering)
        assert csr.results == results
        assert csr.clustering == clustering

    def test_get_clusters(self):
        """
        Test that get_clusters returns clusters list.

        Given: ClusteredSearchResults with clustering
        When: Calling get_clusters()
        Then: Returns list of clusters
        """
        clustering = {
            "mode": "backend",
            "total_results": 10,
            "clusters": [
                {"id": "c1", "label": "Chs", "count": 5},
                {"id": "c2", "label": "Cks", "count": 5},
            ],
            "unclustered": 0,
        }
        csr = ClusteredSearchResults([], clustering)
        clusters = csr.get_clusters()
        assert len(clusters) == 2
        assert clusters[0]["id"] == "c1"

    def test_filter_by_cluster_method(self):
        """
        Test that filter_by_cluster returns filtered results.

        Given: ClusteredSearchResults with multiple clusters
        When: Calling filter_by_cluster with cluster ID
        Then: Returns filtered results
        """
        results = [
            {"id": 1, "content": "result 1"},
            {"id": 2, "content": "result 2"},
            {"id": 3, "content": "result 3"},
        ]
        clustering = {
            "mode": "topic",
            "total_results": 3,
            "clusters": [{"id": "c1", "label": "Cluster 1", "count": 2, "result_ids": [0, 1]}],
            "unclustered": 1,
        }
        csr = ClusteredSearchResults(results, clustering)
        filtered = csr.filter_by_cluster("c1")
        assert len(filtered) == 2
        assert filtered[0]["id"] == 1
        assert filtered[1]["id"] == 2

    def test_filter_by_cluster_without_clustering(self):
        """
        Test that filter_by_cluster returns all results when no clustering.

        Given: ClusteredSearchResults without clustering
        When: Calling filter_by_cluster
        Then: Returns all original results
        """
        results = [{"id": 1, "content": "result 1"}]
        csr = ClusteredSearchResults(results, None)
        filtered = csr.filter_by_cluster("c1")
        assert filtered == results

    def test_get_cluster_summary(self):
        """
        Test that get_cluster_summary returns formatted summary.

        Given: ClusteredSearchResults with clustering
        When: Calling get_cluster_summary()
        Then: Returns formatted string summary
        """
        results = [{"id": 1, "content": "test"}]
        clustering = {
            "mode": "topic",
            "total_results": 10,
            "clusters": [
                {"id": "c1", "label": "Async Patterns", "count": 5, "confidence": 0.89},
                {"id": "c2", "label": "Event Loop", "count": 3, "confidence": 0.82},
            ],
            "unclustered": 2,
        }
        csr = ClusteredSearchResults(results, clustering)
        summary = csr.get_cluster_summary()
        assert "Clustering mode: topic" in summary
        assert "Total results: 10" in summary
        assert "Clusters found: 2" in summary
        assert "c1: Async Patterns" in summary
        assert "Unclustered: 2" in summary

    def test_get_cluster_summary_without_clustering(self):
        """
        Test that get_cluster_summary handles no clustering.

        Given: ClusteredSearchResults without clustering
        When: Calling get_cluster_summary()
        Then: Returns "No clustering applied" message
        """
        csr = ClusteredSearchResults([], None)
        summary = csr.get_cluster_summary()
        assert summary == "No clustering applied"


class TestClusterLabelGeneration:
    """Tests for auto-generated cluster labels."""

    def test_label_from_content_keywords(self):
        """
        Test that cluster labels are extracted from content.

        Given: Results with similar content keywords
        When: Creating topic clusters
        Then: Labels reflect common keywords
        """
        results = [
            {
                "id": 1,
                "content": "async await patterns in python",
                "embedding": np.ones(384, dtype=np.float32).tobytes(),
            },
            {
                "id": 2,
                "content": "async function best practices",
                "embedding": np.ones(384, dtype=np.float32).tobytes(),
            },
            {
                "id": 3,
                "content": "different topic here",
                "embedding": np.zeros(384, dtype=np.float32).tobytes(),
            },
        ]
        more_results = results * 5
        result = cluster_results(more_results, mode="topic")
        if result["clusters"]:
            for cluster in result["clusters"]:
                assert cluster["label"]
                assert len(cluster["label"]) > 0
                assert len(cluster["label"]) <= 50


class TestClusterConfidence:
    """Tests for cluster confidence calculation."""

    def test_confidence_between_zero_and_one(self):
        """
        Test that cluster confidence is in [0, 1] range.

        Given: Results with embeddings
        When: Creating topic clusters
        Then: All confidence scores are between 0 and 1
        """
        base_embedding = np.ones(384, dtype=np.float32)
        results = [
            {"id": i, "content": f"similar content {i}", "embedding": base_embedding.tobytes()}
            for i in range(15)
        ]
        clustering = cluster_results(results, mode="topic")
        for cluster in clustering.get("clusters", []):
            assert 0 <= cluster["confidence"] <= 1

    def test_confidence_high_for_similar_results(self):
        """
        Test that confidence is higher for tightly-clustered results.

        Given: Results with identical embeddings
        When: Creating topic clusters
        Then: Confidence is close to 1.0
        """
        identical_embedding = np.ones(384, dtype=np.float32)
        results = [
            {"id": i, "content": f"content {i}", "embedding": identical_embedding.tobytes()}
            for i in range(15)
        ]
        clustering = cluster_results(results, mode="topic")
        if clustering["clusters"]:
            assert clustering["clusters"][0]["confidence"] > 0.9
