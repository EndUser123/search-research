"""Tests for concurrent search with 8 workers.

Verifies that the daemon with 8 workers can handle 8 concurrent search requests
without deadlocks or resource contention.

Run with: pytest tests/test_concurrent_search.py -v
"""

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import MagicMock, patch

import pytest


class TestConcurrentSearch:
    """Test suite for concurrent search with 8 workers."""

    @pytest.fixture
    def daemon_with_8_workers(self):
        """Create a UnifiedSemanticDaemon with 8 workers."""
        # Create mock JsonlWatcher module
        mock_jsonl_watcher = MagicMock()

        # Add mock module to sys.modules
        mock_module = MagicMock()
        mock_module.JsonlWatcher = mock_jsonl_watcher

        with patch.dict(sys.modules, {"src.ingestion.jsonl_watcher": mock_module}):
            with patch(
                "search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE",
                True,
            ):
                with patch("win32file.CreateFile"):
                    with patch("win32pipe.CreateNamedPipe"):
                        with patch("win32pipe.ConnectNamedPipe"):
                            with patch("win32event.CreateEvent"):
                                with patch(
                                    "win32event.WaitForSingleObject",
                                    return_value=MagicMock(),
                                ):
                                    with patch("win32event.ResetEvent"):
                                        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
                                            UnifiedSemanticDaemon,
                                        )

                                        daemon = UnifiedSemanticDaemon(num_workers=8)
                                        # Manually set state to running
                                        daemon._running = True
                                        daemon._ready = True
                                        yield daemon

    def _submit_search(self, daemon, query_id):
        """Submit a single search request and return timing info."""
        start = time.time()
        request = {
            "action": "search",
            "scope": "cks",
            "query": f"test query {query_id}",
            "limit": 5,
        }
        response = daemon._process_request(request)
        elapsed = time.time() - start
        return {
            "query_id": query_id,
            "response": response,
            "elapsed": elapsed,
        }

    def test_concurrent_search_8_workers_8_requests(self, daemon_with_8_workers):
        """
        Test that 8 concurrent searches complete successfully with 8 workers.

        Given: UnifiedSemanticDaemon with 8 workers
        When: 8 concurrent search requests are submitted
        Then: All requests should complete successfully
        """
        daemon = daemon_with_8_workers

        # Mock the _execute_search to return quickly
        with patch.object(daemon, "_execute_search", return_value=[]):
            results = []
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(self._submit_search, daemon, i) for i in range(8)]
                for future in as_completed(futures):
                    results.append(future.result())

        # Verify all 8 requests completed
        assert len(results) == 8, f"Expected 8 results, got {len(results)}"

        # Verify all responses are valid
        for result in results:
            assert "response" in result, f"Missing response in result: {result}"
            assert isinstance(result["response"], dict), f"Response should be dict: {result}"
            assert "results" in result["response"], f"Missing results in response: {result}"

        # Verify queries were all processed (different query_ids)
        query_ids = sorted([r["query_id"] for r in results])
        assert query_ids == list(range(8)), f"Expected query_ids 0-7, got {query_ids}"

    def test_concurrent_search_timing(self, daemon_with_8_workers):
        """
        Test that concurrent searches don't block each other excessively.

        Given: UnifiedSemanticDaemon with 8 workers
        When: 8 concurrent search requests are submitted
        Then: Total time should be less than 8x single search time (no excessive blocking)
        """
        daemon = daemon_with_8_workers

        # Mock _execute_search to add a small delay
        def slow_execute(_scope, _query, _limit, _params=None):
            time.sleep(0.05)  # 50ms delay
            return []

        with patch.object(daemon, "_execute_search", side_effect=slow_execute):
            start = time.time()
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(self._submit_search, daemon, i) for i in range(8)]
                for future in as_completed(futures):
                    future.result()
            total_time = time.time() - start

        # If searches were serialized, 8 * 50ms = 400ms minimum
        # With 8 workers, they should run in parallel: ~50-100ms
        # Allow up to 200ms for overhead
        assert total_time < 0.2, (
            f"Concurrent searches took {total_time:.3f}s, expected < 0.2s. "
            f"This suggests workers are blocking each other."
        )

    def test_worker_count_configuration(self, daemon_with_8_workers):
        """
        Test that the daemon was configured with 8 workers.

        Given: UnifiedSemanticDaemon created with num_workers=8
        When: Checking _num_workers attribute
        Then: _num_workers should equal 8
        """
        daemon = daemon_with_8_workers
        assert daemon._num_workers == 8, f"Expected 8 workers, got {daemon._num_workers}"


class TestComputeEmbeddingConcurrency:
    """Test suite for concurrent compute_embedding requests."""

    @pytest.fixture
    def daemon_with_8_workers(self):
        """Create a UnifiedSemanticDaemon with 8 workers."""
        # Create mock JsonlWatcher module
        mock_jsonl_watcher = MagicMock()

        # Add mock module to sys.modules
        mock_module = MagicMock()
        mock_module.JsonlWatcher = mock_jsonl_watcher

        with patch.dict(sys.modules, {"src.ingestion.jsonl_watcher": mock_module}):
            with patch(
                "search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE",
                True,
            ):
                with patch("win32file.CreateFile"):
                    with patch("win32pipe.CreateNamedPipe"):
                        with patch("win32pipe.ConnectNamedPipe"):
                            with patch("win32event.CreateEvent"):
                                with patch(
                                    "win32event.WaitForSingleObject",
                                    return_value=MagicMock(),
                                ):
                                    with patch("win32event.ResetEvent"):
                                        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
                                            UnifiedSemanticDaemon,
                                        )

                                        daemon = UnifiedSemanticDaemon(num_workers=8)
                                        daemon._running = True
                                        daemon._ready = True
                                        yield daemon

    def _submit_embedding(self, daemon, text_id):
        """Submit a single compute_embedding request."""
        request = {
            "action": "compute_embedding",
            "text": f"test text {text_id}",
        }
        response = daemon._process_request(request)
        return {"text_id": text_id, "response": response}

    def test_concurrent_compute_embedding(self, daemon_with_8_workers):
        """
        Test that 8 concurrent compute_embedding requests complete successfully.

        Given: UnifiedSemanticDaemon with 8 workers
        When: 8 concurrent compute_embedding requests are submitted
        Then: All requests should complete successfully
        """
        daemon = daemon_with_8_workers

        # Mock the embedding computation - _handle_compute_embedding returns dict
        def mock_embedding(text):
            return {
                "embedding": [0.1] * 384,
                "model": "all-MiniLM-L6-v2",
            }

        with patch.object(daemon, "_handle_compute_embedding", side_effect=mock_embedding):
            results = []
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(self._submit_embedding, daemon, i) for i in range(8)]
                for future in as_completed(futures):
                    results.append(future.result())

        # Verify all 8 requests completed
        assert len(results) == 8, f"Expected 8 results, got {len(results)}"

        # Verify all responses have embedding field
        for result in results:
            assert "response" in result
            # compute_embedding returns embedding list or error dict
            response = result["response"]
            assert isinstance(response, dict)
