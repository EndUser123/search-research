"""Tests for intent classification latency performance via semantic daemon.

These tests verify that intent classification meets performance requirements
when integrated with the semantic daemon.

Run with: pytest tests/daemons/test_intent_classification.py -v

RED Phase: This test is EXPECTED TO FAIL until daemon intent classification is implemented.
"""

import time

import numpy as np
import pytest
from search_research.query_intent import IntentType, classify_query_intent


class TestIntentLatency:
    """Test suite for intent classification latency performance via semantic daemon."""

    # Test queries spanning different intent types and complexity
    _TEST_QUERIES = [
        "git sync command",
        "how do I use pytest",
        "show me the workflow pattern",
        "where is the config file",
        "find the semantic search code",
        "how to run the daemon",
        "get the cks path",
        "command for database migration",
        "what is CHS",
        "explain MMR algorithm in detail",
        "CKS architecture overview",
        "define reciprocal rank fusion",
        "describe the search system components",
        "meaning of semantic embeddings",
        "BM25 algorithm explanation",
        "async def python syntax",
        "AST traversal implementation",
        "VectorKnowledgeManager API usage",
        "pytest fixture documentation",
        "numpy reshape function signature",
        "class SemanticClient implementation",
        "import sqlite3 connection pool",
        "lambda function syntax in python",
        "best practices for async python",
        "difference between BM25 and semantic search",
        "ways to improve search relevance",
        "approaches to citation tracking",
        "strategies for error handling in daemons",
        "comparison of named pipes vs sockets",
        "better options for caching search results",
    ]

    @pytest.fixture
    def daemon_client(self):
        """Return a semantic daemon client for intent classification.

        RED Phase: This fixture is expected to FAIL because the daemon
        does not yet support intent classification requests.
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import SemanticClient

        client = SemanticClient(auto_start=False)
        return client

    def test_latency_p95_via_daemon(self, daemon_client):
        """
        Test that P95 latency is under 50ms for 100 classifications via daemon.

        Given: A semantic daemon client
        When: Running 100 intent classifications via the daemon
        Then: P95 latency should be < 50ms

        RED Phase: This test EXPECTED TO FAIL because:
        1. The daemon does not support intent scope yet
        2. The daemon intent classification endpoint is not implemented
        """
        # Try to make a single request - it should fail
        query = "what is CHS"

        try:
            response = daemon_client.search("intent", query, limit=1)

            if "error" in response:
                pytest.fail(
                    "Daemon does not support intent scope yet. "
                    + f"Error: {response.get('error', 'unknown')}. "
                    + "This is expected in RED phase."
                )
        except (ConnectionError, FileNotFoundError, Exception) as e:
            pytest.fail(
                "Daemon intent classification not implemented. "
                + f"Error: {type(e).__name__}: {e}. "
                + "This is expected in RED phase."
            )

        # If we somehow get here, the test should fail
        pytest.fail("Test should have failed - daemon intent classification not implemented")


class TestIntentLatencyDirect:
    """Test suite for intent classification latency (direct function call)."""

    @pytest.fixture
    def classification_function(self):
        return classify_query_intent

    def test_latency_p95_baseline(self, classification_function):
        """Test baseline P95 latency for 100 classifications (direct call)."""
        num_runs = 100
        latencies_ms = []

        for i in range(num_runs):
            query = TestIntentLatency._TEST_QUERIES[i % len(TestIntentLatency._TEST_QUERIES)]

            start_time = time.perf_counter()
            result = classification_function(query)
            end_time = time.perf_counter()

            latency_ms = (end_time - start_time) * 1000
            latencies_ms.append(latency_ms)

            assert isinstance(result.intent, IntentType)
            assert 0.0 <= result.confidence <= 1.0

        p95_latency_ms = np.percentile(latencies_ms, 95)
        mean_latency_ms = np.mean(latencies_ms)

        print(
            f"Baseline Latency ({num_runs} runs): Mean={mean_latency_ms:.2f}ms, P95={p95_latency_ms:.2f}ms"
        )

        assert p95_latency_ms < 50.0
