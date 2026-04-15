"""Auto-scaffolded test for cache."""

import pytest
from search_research.cache import QueryCache


def test_cache_exists():
    """Smoke test: QueryCache can be imported."""
    assert QueryCache is not None


# TODO: Add more tests based on actual functionality
# Run: pytest tests/test_cache.py -v


# RED phase tests for EmbeddingCache (L2 embedding-based cache).

import json
import os
import time
from pathlib import Path

import pytest

from search_research.cache import EmbeddingCache, CachedQuery


class TestEmbeddingCacheImport:
    """AT-1: EmbeddingCache importable from search_research.cache"""

    def test_embedding_cache_importable(self):
        """EmbeddingCache should be importable from search_research.cache."""
        from search_research.cache import EmbeddingCache
        assert EmbeddingCache is not None

    def test_cached_query_dataclass_importable(self):
        """CachedQuery dataclass should be importable."""
        from search_research.cache import CachedQuery
        assert CachedQuery is not None


class TestEmbeddingCacheFindSimilar:
    """Tests for find_similar() method."""

    @pytest.fixture
    def cache_dir(self, tmp_path):
        """Provide a temporary directory for cache logs."""
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        return logs_dir

    @pytest.fixture
    def embedding_cache(self, cache_dir):
        """Create an EmbeddingCache instance with short TTL for testing."""
        return EmbeddingCache(log_dir=str(cache_dir), ttl_seconds=3600)

    def test_find_similar_empty_cache_returns_none(self, embedding_cache):
        """FM-3: Cosine sim < threshold on empty cache → returns None, pipeline continues."""
        result = embedding_cache.find_similar([0.1] * 768)
        assert result is None

    def test_find_similar_below_threshold_returns_none(self, embedding_cache):
        """FM-3: Cosine sim < current threshold → returns None, pipeline continues."""
        # Store a query with one embedding
        embedding_cache.store(
            "test query",
            [0.1] * 768,
            {"result": "test result"}
        )
        # Search with a very different embedding (low cosine similarity)
        # Use orthogonal-ish vectors by having different sign patterns
        different_embedding = [0.1 if i % 2 == 0 else -0.1 for i in range(768)]
        result = embedding_cache.find_similar(different_embedding)
        assert result is None

    def test_find_similar_above_threshold_returns_cached_query(self, embedding_cache):
        """Cosine similarity > threshold → cache hit returns CachedQuery."""
        # Store a query
        original_embedding = [0.1] * 768
        embedding_cache.store(
            "test query",
            original_embedding,
            {"result": "test result"}
        )
        # Search with very similar embedding
        similar_embedding = [0.1001] * 768  # Very high cosine similarity
        result = embedding_cache.find_similar(similar_embedding)
        assert result is not None
        assert isinstance(result, CachedQuery)
        assert result.query == "test query"
        assert result.result == {"result": "test result"}


class TestEmbeddingCacheStore:
    """Tests for store() method."""

    @pytest.fixture
    def cache_dir(self, tmp_path):
        """Provide a temporary directory for cache logs."""
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        return logs_dir

    @pytest.fixture
    def embedding_cache(self, cache_dir):
        """Create an EmbeddingCache instance."""
        return EmbeddingCache(log_dir=str(cache_dir), ttl_seconds=3600)

    def test_store_appends_to_jsonl(self, embedding_cache):
        """store(query, embedding, result) appends to logs/query_cache.jsonl."""
        cache_file = Path(embedding_cache.log_dir) / "query_cache.jsonl"
        assert not cache_file.exists()

        embedding_cache.store(
            "test query",
            [0.1] * 768,
            {"result": "test"}
        )

        assert cache_file.exists()
        with open(cache_file) as f:
            lines = f.readlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["query"] == "test query"
        assert entry["embedding"] == [0.1] * 768
        assert entry["result"] == {"result": "test"}
        assert "cached_from" in entry
        assert "timestamp" in entry

    def test_store_multiple_entries(self, embedding_cache):
        """Multiple store() calls append multiple lines to jsonl."""
        cache_file = Path(embedding_cache.log_dir) / "query_cache.jsonl"

        embedding_cache.store("query1", [0.1] * 768, {"r": 1})
        embedding_cache.store("query2", [0.2] * 768, {"r": 2})

        with open(cache_file) as f:
            lines = f.readlines()
        assert len(lines) == 2


class TestEmbeddingCacheTTLExpiry:
    """Tests for TTL expiry behavior."""

    @pytest.fixture
    def cache_dir(self, tmp_path):
        """Provide a temporary directory for cache logs."""
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        return logs_dir

    def test_find_similar_expired_entry_returns_none(self, cache_dir):
        """FM-4: Entry TTL expired (3600s) → returns None, pipeline continues."""
        # Create cache with 1 second TTL for testing
        cache = EmbeddingCache(log_dir=str(cache_dir), ttl_seconds=1)

        # Store a query
        cache.store("test query", [0.1] * 768, {"result": "test"})

        # Immediately find - should work
        result = cache.find_similar([0.1] * 768)
        assert result is not None

        # Wait for TTL to expire
        time.sleep(1.5)

        # After expiry - should return None
        result = cache.find_similar([0.1] * 768)
        assert result is None


class TestEmbeddingCacheAdaptiveThreshold:
    """Tests for adaptive threshold (AT-1) behavior."""

    @pytest.fixture
    def cache_dir(self, tmp_path):
        """Provide a temporary directory for cache logs."""
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        return logs_dir

    def test_adaptive_threshold_lowers_after_low_hit_rate(self, cache_dir):
        """AT-1: After >=100 queries, hit rate < 5% → threshold auto-lowers by 0.05 (floor 0.80)."""
        cache = EmbeddingCache(log_dir=str(cache_dir), ttl_seconds=3600)

        # Initially threshold should be 0.95
        assert cache.threshold == 0.95

        # Simulate 100 queries with no hits (all below threshold)
        # Use orthogonal-ish vectors to ensure LOW similarity
        for i in range(100):
            store_emb = [0.1] * 768
            # Alternate signs to create orthogonal-ish vectors (cosine sim ≈ 0)
            search_emb = [0.1 if j % 2 == 0 else -0.1 for j in range(768)]
            cache.store(f"query_{i}", store_emb, {"result": i})
            cache.find_similar(search_emb)

        # After 100 queries with ~0% hit rate, threshold should lower to 0.90
        assert cache.threshold == 0.90

    def test_adaptive_threshold_floor_at_0_80(self, cache_dir):
        """AT-1: Threshold floor at 0.80, cannot go lower."""
        cache = EmbeddingCache(log_dir=str(cache_dir), ttl_seconds=3600, initial_threshold=0.85)

        # Simulate many rounds of low hit rate using orthogonal vectors
        for round_num in range(10):
            for i in range(100):
                # Use orthogonal-ish vectors for consistently low similarity
                store_emb = [0.1] * 768
                search_emb = [0.1 if j % 2 == 0 else -0.1 for j in range(768)]
                cache.store(f"query_{round_num}_{i}", store_emb, {"result": f"{round_num}_{i}"})
                cache.find_similar(search_emb)

        # Threshold should not go below 0.80
        assert cache.threshold >= 0.80
        assert cache.threshold == 0.80  # Should hit floor

    def test_threshold_tracked_in_metadata(self, cache_dir):
        """Threshold should be tracked in query_cache.jsonl metadata."""
        cache_file = Path(cache_dir) / "query_cache.jsonl"

        cache = EmbeddingCache(log_dir=str(cache_dir), ttl_seconds=3600)

        # Store something and trigger threshold check
        # Use orthogonal vectors for low similarity to trigger threshold change
        for i in range(105):
            store_emb = [0.1] * 768
            search_emb = [0.1 if j % 2 == 0 else -0.1 for j in range(768)]
            cache.store(f"query_{i}", store_emb, {"result": i})
            cache.find_similar(search_emb)

        # Read the log file and check metadata contains threshold
        with open(cache_file) as f:
            lines = f.readlines()

        # At least one entry should have threshold info (threshold change event)
        threshold_found = any("_threshold" in json.loads(line) or "threshold" in json.loads(line) for line in lines)
        assert threshold_found, "No threshold tracking found in log"