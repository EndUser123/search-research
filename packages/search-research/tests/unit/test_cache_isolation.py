"""TDD RED: QueryCache terminal_id isolation.

Tests that QueryCache instances with different terminal_ids do not
share cache entries. Uses CLAUDE_TERMINAL_ID env var to simulate
different terminals within a single test process.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

# Import QueryCache - the module under test
from core.cache import QueryCache


class TestCacheIsolation:
    """Two QueryCache instances with different terminal_ids must not share entries."""

    def test_different_terminal_ids_produce_different_keys(self):
        """Same query produces different cache keys when terminal_id differs."""
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "term-a"}):
            cache_a = QueryCache()
            key_a = cache_a._hash_query("test query")

        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "term-b"}):
            cache_b = QueryCache()
            key_b = cache_b._hash_query("test query")

        # Same query, different terminal_id → different keys
        assert key_a != key_b, (
            f"Cache keys must differ when terminal_id differs. "
            f"Got key_a={key_a}, key_b={key_b} for same query 'test query'. "
            f"terminal_id_a={cache_a._terminal_id}, terminal_id_b={cache_b._terminal_id}"
        )

    def test_entries_set_by_terminal_a_not_accessible_by_terminal_b(self):
        """Cache entry set in terminal A is invisible to terminal B."""
        sample_results = [
            {
                "title": "Test Result",
                "content": "Test content",
                "url": None,
                "file_path": "test.py",
                "line_number": 1,
                "source": "test",
                "score": 1.0,
                "metadata": {},
            }
        ]

        # Set entry in terminal A
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "term-a"}):
            cache_a = QueryCache()
            cache_a.set("test query", sample_results)
            hit_a = cache_a.get("test query")
            assert hit_a == sample_results, "Terminal A should retrieve its own entry"

        # Terminal B should NOT see terminal A's entry
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "term-b"}):
            cache_b = QueryCache()
            hit_b = cache_b.get("test query")
            assert hit_b is None, (
                f"Terminal B must NOT see Terminal A's cache entries. "
                f"Got {hit_b}, expected None. "
                f"terminal_id_a={cache_a._terminal_id}, terminal_id_b={cache_b._terminal_id}"
            )

    def test_isolation_holds_across_multiple_queries(self):
        """Multiple queries remain isolated across terminals."""
        queries_and_results = [
            ("query one", [{"title": "Result 1", "content": "Content 1", "url": None, "file_path": "f1.py", "line_number": 1, "source": "test", "score": 0.9, "metadata": {}}]),
            ("query two", [{"title": "Result 2", "content": "Content 2", "url": None, "file_path": "f2.py", "line_number": 2, "source": "test", "score": 0.8, "metadata": {}}]),
        ]

        # Populate terminal A cache
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "term-a"}):
            cache_a = QueryCache()
            for query, results in queries_and_results:
                cache_a.set(query, results)

        # Verify terminal A has both entries
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "term-a"}):
            cache_a_verify = QueryCache()
            for query, expected_results in queries_and_results:
                assert cache_a_verify.get(query) == expected_results

        # Verify terminal B has neither entry
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "term-b"}):
            cache_b = QueryCache()
            for query, _ in queries_and_results:
                assert cache_b.get(query) is None, (
                    f"Terminal B should not see Terminal A's entries. "
                    f"Query '{query}' returned {cache_b.get(query)}, expected None"
                )

    def test_same_terminal_reuses_own_entries(self):
        """Same terminal accessing same query twice returns cached result."""
        sample_results = [{"title": "Cached", "content": "Data", "url": None, "file_path": "x.py", "line_number": 1, "source": "test", "score": 1.0, "metadata": {}}]

        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "same-term"}):
            cache = QueryCache()
            # First set
            cache.set("repeat query", sample_results)
            # Same terminal, same query → cache hit
            hit = cache.get("repeat query")
            assert hit == sample_results, f"Same terminal should return cached result. Got {hit}"

    def test_terminal_id_is_stored_on_instance(self):
        """QueryCache stores its terminal_id on self._terminal_id."""
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "my-terminal-xyz"}):
            cache = QueryCache()
            assert hasattr(cache, "_terminal_id"), "QueryCache must have _terminal_id attribute"
            assert cache._terminal_id == "my-terminal-xyz", (
                f"Expected _terminal_id='my-terminal-xyz', got '{cache._terminal_id}'"
            )
