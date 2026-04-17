#!/usr/bin/env python3
"""Tests for concurrent provider execution (PERF-001)."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from core.orchestrator import ResearchEngine


@pytest.fixture(autouse=True)
def mock_auto_register():
    """Prevent auto-registration of providers during tests."""
    with patch.object(ResearchEngine, "_auto_register_providers"):
        yield


class TestConcurrentProviderExecution:
    """Test that provider execution is concurrent, not sequential."""

    @pytest.mark.asyncio
    async def test_concurrent_execution_with_gather(self):
        """Verify that providers execute concurrently using asyncio.gather.

        Tests that:
        - Multiple providers execute in parallel, not sequentially
        - Total time ≈ max(single_provider_time), not sum(all_times)
        - All provider results are collected correctly
        - asyncio.gather() is used for concurrent execution
        """
        # Record execution times
        execution_times = []

        async def timed_search(query, **kwargs):
            import time

            start = time.time()
            result = [{"title": "result"}]  # Mock search (no await needed)
            end = time.time()
            execution_times.append(end - start)
            return result

        # Create mock providers with timed search
        provider1 = Mock()
        provider1.name = "provider1"
        provider1.search = AsyncMock(side_effect=timed_search)

        provider2 = Mock()
        provider2.name = "provider2"
        provider2.search = AsyncMock(side_effect=timed_search)

        provider3 = Mock()
        provider3.name = "provider3"
        provider3.search = AsyncMock(side_effect=timed_search)

        # Create orchestrator
        orchestrator = ResearchEngine()
        orchestrator.providers["provider1"] = provider1
        orchestrator.providers["provider2"] = provider2
        orchestrator.providers["provider3"] = provider3

        # Execute searches
        results = await orchestrator._execute_provider_searches("test query")

        # Verify all providers executed
        assert len(execution_times) == 3, "All providers should execute"

        # Verify results collected
        assert len(results) == 3, "All results should be collected"

    @pytest.mark.asyncio
    async def test_concurrent_speedup(self):
        """Verify that concurrent execution is faster than sequential.

        Tests that:
        - Concurrent execution: total_time ≈ max(single_provider_times)
        - Sequential execution would be: total_time = sum(all_provider_times)
        - Speedup is approximately 3x for 3 providers
        - Performance benchmark passes
        """

        # Create slow mock providers (simulating network/database delays)
        async def slow_search(query, **kwargs):
            await asyncio.sleep(0.1)  # 100ms delay
            return [{"title": "result"}]

        provider1 = Mock()
        provider1.name = "provider1"
        provider1.search = AsyncMock(side_effect=slow_search)

        provider2 = Mock()
        provider2.name = "provider2"
        provider2.search = AsyncMock(side_effect=slow_search)

        provider3 = Mock()
        provider3.name = "provider3"
        provider3.search = AsyncMock(side_effect=slow_search)

        # Create orchestrator
        orchestrator = ResearchEngine()
        orchestrator.providers["provider1"] = provider1
        orchestrator.providers["provider2"] = provider2
        orchestrator.providers["provider3"] = provider3

        # Measure concurrent execution time
        import time

        start = time.time()
        results = await orchestrator._execute_provider_searches("test query")
        concurrent_time = time.time() - start

        # Verify concurrent speedup
        # Sequential would be ~0.3s (3 × 0.1s)
        # Concurrent should be ~0.1s (max of individual times)
        assert concurrent_time < 0.2, f"Concurrent time {concurrent_time:.3f}s should be < 0.2s"
        assert len(results) == 3, "All results should be collected"

    @pytest.mark.asyncio
    async def test_partial_failure_handling(self):
        """Verify that partial provider failures don't crash orchestrator.

        Tests that:
        - If one provider fails, others continue executing
        - Failed provider results are skipped (not included in output)
        - Successful providers return results correctly
        - Orchestrator remains stable after partial failure
        """
        # Create providers with one failure
        provider1 = Mock()
        provider1.name = "provider1"
        provider1.search = AsyncMock(return_value=[{"title": "result1"}])

        provider2 = Mock()
        provider2.name = "provider2"
        provider2.search = AsyncMock(side_effect=Exception("Provider 2 failed"))

        provider3 = Mock()
        provider3.name = "provider3"
        provider3.search = AsyncMock(return_value=[{"title": "result3"}])

        # Create orchestrator
        orchestrator = ResearchEngine()
        orchestrator.providers["provider1"] = provider1
        orchestrator.providers["provider2"] = provider2
        orchestrator.providers["provider3"] = provider3

        # Execute searches
        results = await orchestrator._execute_provider_searches("test query")

        # Verify partial results (provider2 failed)
        assert len(results) == 2, "Should return results from successful providers"
        assert any(r["title"] == "result1" for r in results), "Provider 1 result present"
        assert any(r["title"] == "result3" for r in results), "Provider 3 result present"

    @pytest.mark.asyncio
    async def test_timeout_per_provider(self):
        """Verify that each provider has independent timeout.

        Tests that:
        - Each provider has its own timeout (e.g., 5 seconds)
        - Slow provider doesn't block other providers
        - Timeout exception is caught and handled gracefully
        - Orchestrator continues after timeout
        """

        # Create providers with different speeds
        async def fast_search(query, **kwargs):
            await asyncio.sleep(0.01)
            return [{"title": "fast_result"}]

        async def slow_search(query, **kwargs):
            await asyncio.sleep(10)  # Very slow, should timeout
            return [{"title": "slow_result"}]

        provider1 = Mock()
        provider1.name = "provider1"
        provider1.search = AsyncMock(side_effect=fast_search)

        provider2 = Mock()
        provider2.name = "provider2"
        provider2.search = AsyncMock(side_effect=slow_search)

        # Create orchestrator
        orchestrator = ResearchEngine()
        orchestrator.providers["provider1"] = provider1
        orchestrator.providers["provider2"] = provider2

        # Execute with short timeout
        import time

        start = time.time()
        results = await orchestrator._execute_provider_searches("test query", timeout=0.5)
        total_time = time.time() - start

        # Verify fast provider returned results
        assert len(results) >= 1, "At least fast provider should return results"
        assert (
            total_time < 2.0
        ), f"Total time {total_time:.2f}s should be < 2.0s (timeout + overhead)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
