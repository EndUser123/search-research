"""
Performance Tests for Validation Overhead
==========================================

Tests that validation overhead meets the sub-2 second requirement and
measures memory usage, cache performance, and parallel execution efficiency.
"""

import asyncio
import gc
import os
import time
from unittest.mock import AsyncMock, Mock

import psutil
import pytest

# Performance requirements
MAX_VALIDATION_OVERHEAD = 2.0  # seconds
MAX_MEMORY_OVERHEAD = 100  # MB
MIN_CACHE_HIT_RATE = 0.85  # 85%
MAX_PARALLEL_TIME = 0.5  # seconds

try:
    from hook_communication import CrossHookCommunicator, EvidenceRepository
    from llm_supervisor import LLMSupervisor, ValidationLevel
    from post_tool_use import BalancedValidationLogic, ParallelValidationEngine
except ImportError:
    pytest.skip("Performance test components not available", allow_module_level=True)


class TestValidationOverhead:
    """Test validation timing overhead."""

    @pytest.fixture
    def performance_monitor(self):
        """Monitor process performance during tests."""
        process = psutil.Process(os.getpid())

        class Monitor:
            def __init__(self, process):
                self.process = process
                self.start_memory = None
                self.start_time = None

            def start(self):
                gc.collect()  # Clear memory before starting
                self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
                self.start_time = time.time()

            def get_stats(self):
                current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
                memory_overhead = current_memory - (self.start_memory or 0)
                elapsed_time = time.time() - (self.start_time or 0)

                return {
                    "elapsed_time": elapsed_time,
                    "memory_overhead_mb": memory_overhead,
                    "current_memory_mb": current_memory,
                }

        return Monitor(process)

    @pytest.fixture
    def mock_contexts(self):
        """Generate various mock contexts for performance testing."""
        return {
            "low_risk": {
                "tool_name": "Edit",
                "metadata": {"operation": "comment_addition", "risk_level": "low"},
                "duration_ms": 50,
            },
            "medium_risk": {
                "tool_name": "Write",
                "metadata": {"operation": "function_creation", "risk_level": "medium"},
                "duration_ms": 200,
            },
            "high_risk": {
                "tool_name": "Bash",
                "command": "python deploy.py",
                "metadata": {"operation": "deployment", "risk_level": "high"},
                "duration_ms": 5000,
            },
            "critical_risk": {
                "tool_name": "Bash",
                "command": "rm -rf /tmp/data",
                "metadata": {"operation": "file_deletion", "risk_level": "critical"},
                "duration_ms": 100,
            },
        }

    def test_balanced_validation_logic_performance(
        self, performance_monitor, mock_contexts
    ):
        """Test BalancedValidationLogic performance overhead."""
        validation_logic = BalancedValidationLogic()

        performance_monitor.start()

        # Test multiple validation scenarios
        for risk_level, context in mock_contexts.items():
            start_time = time.time()

            # Create validation result
            result = validation_logic.validate_operation(context)

            validation_time = time.time() - start_time

            # Individual validation should be very fast
            assert (
                validation_time < 0.1
            ), f"{risk_level} validation took {validation_time:.3f}s"
            assert result is not None

        stats = performance_monitor.get_stats()

        # Overall test should meet performance requirements
        assert stats["elapsed_time"] < MAX_VALIDATION_OVERHEAD
        assert stats["memory_overhead_mb"] < MAX_MEMORY_OVERHEAD

    @pytest.mark.asyncio
    async def test_parallel_validation_engine_performance(
        self, performance_monitor, mock_contexts
    ):
        """Test ParallelValidationEngine parallel execution performance."""
        engine = ParallelValidationEngine()

        # Mock validation methods for consistent timing
        async def mock_security_validation(context):
            await asyncio.sleep(0.05)  # 50ms mock security check
            return []

        async def mock_performance_validation(context):
            await asyncio.sleep(0.03)  # 30ms mock performance check
            return []

        async def mock_evidence_validation(context):
            await asyncio.sleep(0.04)  # 40ms mock evidence check
            return []

        async def mock_safety_validation(context):
            await asyncio.sleep(0.02)  # 20ms mock safety check
            return []

        # Apply mocks
        engine._validate_security = mock_security_validation
        engine._validate_performance = mock_performance_validation
        engine._validate_evidence = mock_evidence_validation
        engine._validate_operation_safety = mock_safety_validation

        performance_monitor.start()

        # Test parallel execution
        start_time = time.time()

        result = await engine.validate_operation(mock_contexts["medium_risk"])

        parallel_time = time.time() - start_time

        # Parallel execution should be much faster than sequential
        sequential_time = 0.05 + 0.03 + 0.04 + 0.02  # Sum of individual times
        parallel_efficiency = sequential_time / parallel_time

        # Should achieve significant parallel speedup
        assert (
            parallel_time < MAX_PARALLEL_TIME
        ), f"Parallel validation took {parallel_time:.3f}s"
        assert (
            parallel_efficiency > 2.0
        ), f"Parallel efficiency only {parallel_efficiency:.1f}x"

        stats = performance_monitor.get_stats()
        assert stats["memory_overhead_mb"] < MAX_MEMORY_OVERHEAD

    @pytest.mark.asyncio
    async def test_llm_supervisor_performance(self, performance_monitor, mock_contexts):
        """Test LLMSupervisor performance with cost optimization."""
        supervisor = LLMSupervisor(validation_level=ValidationLevel.STANDARD)

        # Mock validators with different response times
        async def mock_fast_rule_validation(context):
            await asyncio.sleep(0.05)  # Fast rule validation
            return {
                "is_valid": True,
                "issues": [],
                "confidence": 0.95,  # High confidence - no LLM needed
            }

        async def mock_slow_llm_validation(context):
            await asyncio.sleep(1.0)  # Slow LLM validation
            return {"is_valid": True, "confidence": 0.9}

        supervisor.rule_validator.validate = mock_fast_rule_validation
        supervisor.llm_validator.validate = mock_slow_llm_validation

        performance_monitor.start()

        # Test low-risk operation (should not trigger LLM)
        start_time = time.time()

        result = await supervisor.validate_operation(mock_contexts["low_risk"])

        low_risk_time = time.time() - start_time

        # Should be fast due to cost optimization
        assert low_risk_time < 0.2, f"Low-risk validation took {low_risk_time:.3f}s"
        assert result["is_valid"] is True

        # Test high-risk operation (should trigger LLM)
        # Mock low confidence to trigger LLM
        async def mock_low_confidence_validation(context):
            await asyncio.sleep(0.05)
            return {
                "is_valid": True,
                "issues": [],
                "confidence": 0.7,  # Low confidence - triggers LLM
            }

        supervisor.rule_validator.validate = mock_low_confidence_validation

        start_time = time.time()

        result = await supervisor.validate_operation(mock_contexts["high_risk"])

        high_risk_time = time.time() - start_time

        # Should include LLM validation time but still be reasonable
        assert high_risk_time < 1.5, f"High-risk validation took {high_risk_time:.3f}s"
        assert "llm_analysis" in result

        stats = performance_monitor.get_stats()
        assert stats["elapsed_time"] < MAX_VALIDATION_OVERHEAD

    @pytest.mark.asyncio
    async def test_cross_hook_communication_performance(self, performance_monitor):
        """Test CrossHookCommunicator performance overhead."""
        temp_dir = f"temp_comm_test_{int(time.time())}"
        communicator = CrossHookCommunicator(storage_path=temp_dir)

        # Mock handlers
        handlers = [AsyncMock() for _ in range(10)]

        # Register handlers
        for i, handler in enumerate(handlers):
            communicator.register_handler(f"Hook{i}", handler)

        performance_monitor.start()

        # Test event broadcasting performance
        start_time = time.time()

        event = Mock(
            hook_name="TestHook", event_type="test_event", data={"test": "data"}
        )
        await communicator.broadcast_event(event)

        broadcast_time = time.time() - start_time

        # Broadcasting should be very fast
        assert broadcast_time < 0.1, f"Event broadcast took {broadcast_time:.3f}s"

        # Verify all handlers were called
        for handler in handlers:
            handler.assert_called_once_with(event)

        # Cleanup
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)

        stats = performance_monitor.get_stats()
        assert stats["elapsed_time"] < MAX_VALIDATION_OVERHEAD


class TestCachePerformance:
    """Test caching performance and hit rates."""

    @pytest.fixture
    def cache_test_engine(self):
        """Create validation engine for cache testing."""
        engine = ParallelValidationEngine()

        # Mock validation with tracking
        call_count = {"security": 0, "performance": 0, "evidence": 0, "safety": 0}

        async def mock_security_validation(context):
            call_count["security"] += 1
            await asyncio.sleep(0.05)
            return []

        async def mock_performance_validation(context):
            call_count["performance"] += 1
            await asyncio.sleep(0.03)
            return []

        async def mock_evidence_validation(context):
            call_count["evidence"] += 1
            await asyncio.sleep(0.04)
            return []

        async def mock_safety_validation(context):
            call_count["safety"] += 1
            await asyncio.sleep(0.02)
            return []

        engine._validate_security = mock_security_validation
        engine._validate_performance = mock_performance_validation
        engine._validate_evidence = mock_evidence_validation
        engine._validate_operation_safety = mock_safety_validation

        engine.call_count = call_count
        return engine

    @pytest.mark.asyncio
    async def test_cache_hit_rate_performance(self, cache_test_engine):
        """Test that cache hit rate meets requirements."""
        context = {
            "tool_name": "Edit",
            "metadata": {"operation": "test_operation", "file_path": "test.py"},
            "duration_ms": 100,
        }

        # First validation - cache miss
        initial_calls = cache_test_engine.call_count.copy()

        start_time = time.time()
        result1 = await cache_test_engine.validate_operation(context)
        first_time = time.time() - start_time

        # Verify all validators were called (cache miss)
        for validator in ["security", "performance", "evidence", "safety"]:
            assert cache_test_engine.call_count[validator] > initial_calls[validator]

        # Second validation - should hit cache
        calls_before_second = cache_test_engine.call_count.copy()

        start_time = time.time()
        result2 = await cache_test_engine.validate_operation(context)
        second_time = time.time() - start_time

        # Should be faster due to caching
        assert second_time < first_time
        assert second_time < 0.1  # Should be very fast with cache

        # Validators should not be called again (cache hit)
        for validator in ["security", "performance", "evidence", "safety"]:
            assert (
                cache_test_engine.call_count[validator]
                == calls_before_second[validator]
            )

        # Results should be identical
        assert result1.execution_time == result2.execution_time

    @pytest.mark.asyncio
    async def test_cache_memory_efficiency(self, cache_test_engine):
        """Test cache memory usage efficiency."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Generate many unique contexts to fill cache
        contexts = []
        for i in range(100):
            context = {
                "tool_name": "Edit",
                "metadata": {
                    "operation": f"test_operation_{i}",
                    "file_path": f"test_{i}.py",
                },
                "duration_ms": 100 + i,
            }
            contexts.append(context)
            await cache_test_engine.validate_operation(context)

        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory

        # Cache should not use excessive memory
        assert (
            memory_increase < MAX_MEMORY_OVERHEAD
        ), f"Cache used {memory_increase:.1f}MB"

        # Test cache cleanup/ejection
        # Validate some contexts again to test cache hit performance
        start_time = time.time()
        for context in contexts[:10]:  # Re-validate first 10
            await cache_test_engine.validate_operation(context)

        cache_test_time = time.time() - start_time

        # Should be very fast with cache hits
        assert cache_test_time < 1.0, f"Cache validation took {cache_test_time:.3f}s"


class TestConcurrentPerformance:
    """Test performance under concurrent load."""

    @pytest.mark.asyncio
    async def test_concurrent_validation_performance(self):
        """Test performance with multiple concurrent validations."""
        engine = ParallelValidationEngine()

        # Mock validation methods
        async def mock_validation(context):
            await asyncio.sleep(0.05)  # 50ms per validation
            return []

        engine._validate_security = mock_validation
        engine._validate_performance = mock_validation
        engine._validate_evidence = mock_validation
        engine._validate_operation_safety = mock_validation

        # Create multiple concurrent requests
        concurrent_requests = 20
        contexts = [
            {
                "tool_name": "Edit",
                "metadata": {"operation": f"test_{i}", "file_path": f"test_{i}.py"},
                "duration_ms": 100,
            }
            for i in range(concurrent_requests)
        ]

        start_time = time.time()

        # Execute all validations concurrently
        tasks = [engine.validate_operation(context) for context in contexts]
        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time

        # Should complete much faster than sequential execution
        sequential_time = concurrent_requests * 0.2  # Approximate sequential time
        speedup = sequential_time / total_time

        assert total_time < 2.0, f"Concurrent validation took {total_time:.3f}s"
        assert speedup > 5.0, f"Concurrent speedup only {speedup:.1f}x"

        # All validations should succeed
        assert len(results) == concurrent_requests
        assert all(result.is_valid for result in results)

    @pytest.mark.asyncio
    async def test_memory_pressure_handling(self):
        """Test performance under memory pressure."""
        engine = ParallelValidationEngine()

        # Simulate memory pressure with large contexts
        large_contexts = []
        for i in range(50):
            # Create contexts with large data to test memory handling
            large_data = "x" * 10000  # 10KB per context
            context = {
                "tool_name": "Edit",
                "metadata": {
                    "operation": f"large_test_{i}",
                    "file_path": f"large_test_{i}.py",
                    "large_data": large_data,
                },
                "duration_ms": 100,
            }
            large_contexts.append(context)

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Mock fast validation to focus on memory performance
        async def mock_fast_validation(context):
            return []

        engine._validate_security = mock_fast_validation
        engine._validate_performance = mock_fast_validation
        engine._validate_evidence = mock_fast_validation
        engine._validate_operation_safety = mock_fast_validation

        start_time = time.time()

        # Process all large contexts
        tasks = [engine.validate_operation(context) for context in large_contexts]
        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory

        # Should handle large contexts efficiently
        assert total_time < 3.0, f"Large context validation took {total_time:.3f}s"
        assert (
            memory_increase < MAX_MEMORY_OVERHEAD * 2
        ), f"Memory increase: {memory_increase:.1f}MB"

        # All validations should succeed
        assert len(results) == len(large_contexts)
        assert all(result.is_valid for result in results)


class TestPerformanceRegression:
    """Test for performance regressions."""

    @pytest.mark.asyncio
    async def test_validation_overhead_regression(self):
        """Regression test for validation overhead."""
        # This test establishes baseline performance expectations
        baseline_overhead = 1.5  # seconds - should be well under 2s requirement

        engine = ParallelValidationEngine()

        # Mock realistic validation times
        async def mock_security_validation(context):
            await asyncio.sleep(0.02)  # 20ms security check
            return []

        async def mock_performance_validation(context):
            await asyncio.sleep(0.01)  # 10ms performance check
            return []

        async def mock_evidence_validation(context):
            await asyncio.sleep(0.015)  # 15ms evidence check
            return []

        async def mock_safety_validation(context):
            await asyncio.sleep(0.005)  # 5ms safety check
            return []

        engine._validate_security = mock_security_validation
        engine._validate_performance = mock_performance_validation
        engine._validate_evidence = mock_evidence_validation
        engine._validate_operation_safety = mock_safety_validation

        # Test multiple scenarios
        test_contexts = [
            {"tool_name": "Edit", "metadata": {"risk_level": "low"}, "duration_ms": 50},
            {
                "tool_name": "Write",
                "metadata": {"risk_level": "medium"},
                "duration_ms": 200,
            },
            {
                "tool_name": "Bash",
                "metadata": {"risk_level": "high"},
                "duration_ms": 1000,
            },
        ]

        total_time = 0
        for context in test_contexts:
            start_time = time.time()
            result = await engine.validate_operation(context)
            validation_time = time.time() - start_time
            total_time += validation_time

            assert result.is_valid is True

        average_time = total_time / len(test_contexts)

        # Should meet baseline performance
        assert (
            average_time < baseline_overhead
        ), f"Avg validation {average_time:.3f}s > baseline {baseline_overhead}s"
        assert (
            total_time < MAX_VALIDATION_OVERHEAD
        ), f"Total validation {total_time:.3f}s exceeded limit"

    def test_memory_baseline_regression(self):
        """Regression test for memory usage baseline."""
        baseline_memory_overhead = 50  # MB - should be well under 100MB limit

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create multiple validation components
        components = []
        for _ in range(10):
            validation_logic = BalancedValidationLogic()
            components.append(validation_logic)

        # Simulate some validation work
        for component in components:
            context = {"tool_name": "Test", "metadata": {"test": "data"}}
            result = component.validate_operation(context)
            assert result is not None

        current_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_overhead = current_memory - initial_memory

        # Should meet baseline memory usage
        assert (
            memory_overhead < baseline_memory_overhead
        ), f"Memory overhead {memory_overhead:.1f}MB > baseline {baseline_memory_overhead}MB"
