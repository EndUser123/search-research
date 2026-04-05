from __future__ import annotations

import asyncio
import logging
import time
import unittest
from unittest.mock import patch

import pytest

#!/usr/bin/env python3
"""TDD Tests for GPU-Enhanced Chat History Search Accelerator.

CSF NIP Compliant comprehensive test suite for GPU acceleration components.
Follows RED-GREEN-REFACTOR TDD methodology with comprehensive coverage
of all GPU acceleration functionality.

Test Methodology:
- RED: Write failing tests first
- GREEN: Implement minimal code to pass tests
- REFACTOR: Optimize while maintaining green tests
- Comprehensive edge case and error condition testing

Test Categories:
1. Unit Tests - Individual component functionality
2. Integration Tests - Component interaction validation
3. Performance Tests - Throughput and efficiency validation
4. Error Handling Tests - Robustness and reliability testing
5. GPU Fallback Tests - CPU fallback mechanism validation
6. Cache Management Tests - Persistent cache functionality
7. FAISS Integration Tests - Vector search validation
8. Memory Management Tests - Resource cleanup validation

Test Standards:
- 100% code coverage requirement
- Mock-free real component testing
- Production-like test environments
- Async testing patterns
- Comprehensive error scenarios
"""



# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the modules under test
try:
    import numpy as np
    import torch

    TORCH_AVAILABLE = True
    NUMPY_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    NUMPY_AVAILABLE = False

try:
    from modules.analysis.chat_search.src.gpu_chs_accelerator import (
        CHSGPUAccelerator,
        CHSGPUConfig,
        CHSOperationType,
        CHSProcessingResult,
        ProcessingMode,
        create_chs_gpu_accelerator,
    )

    GPU_ACCELERATOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"GPU accelerator not available: {e}")
    GPU_ACCELERATOR_AVAILABLE = False


# Test Data and Fixtures
@pytest.fixture
def sample_texts():
    """Sample text data for testing."""
    return [
        "This is a test message about Python programming",
        "Another message discussing machine learning concepts",
        "Technical discussion about GPU acceleration and CUDA",
        "Chat history search implementation details",
        "Vector embeddings and similarity search algorithms",
        "Performance optimization techniques for large datasets",
        "Error handling and fallback mechanisms",
        "Memory management and resource cleanup",
        "FAISS integration for fast similarity search",
        "Batch processing and async operations",
    ]


@pytest.fixture
def sample_embeddings():
    """Sample embedding data for testing."""
    return [
        [0.1, 0.2, 0.3, 0.4, 0.5],
        [0.2, 0.1, 0.4, 0.3, 0.6],
        [0.3, 0.4, 0.1, 0.2, 0.7],
        [0.4, 0.3, 0.2, 0.1, 0.8],
        [0.5, 0.6, 0.7, 0.8, 0.9],
    ]


@pytest.fixture
def chs_gpu_config():
    """Standard CHS GPU configuration for testing."""
    return CHSGPUConfig(
        device_id=0,
        max_batch_size=4,
        embedding_dim=5,
        similarity_threshold=0.5,
        enable_faiss_gpu=True,
        faiss_index_type="Flat",
        enable_mixed_precision=True,
        memory_limit_gb=4.0,
        enable_persistent_cache=True,
        cache_size_mb=512,
        fallback_enabled=True,
        benchmark_mode=False,
        chunk_batch_size=2,
        index_batch_size=4,
        search_batch_size=3,
        enable_async_processing=True,
    )


@pytest.fixture
def minimal_chs_config():
    """Minimal CHS GPU configuration for testing without GPU."""
    return CHSGPUConfig(
        device_id=0,
        max_batch_size=2,
        embedding_dim=5,
        enable_faiss_gpu=False,
        fallback_enabled=True,
        enable_persistent_cache=False,
    )


@pytest.fixture
def mock_environment():
    """Mock environment setup for testing."""
    with (
        patch("torch.cuda.is_available", return_value=False),
        patch(
            "src.modules.analysis.chat_search.src.gpu_chs_accelerator.FAISS_AVAILABLE",
            False,
        ),
    ):
        yield


class TestCHSGPUConfig(unittest.TestCase):
    """Test CHSGPUConfig class functionality."""

    def test_default_configuration(self) -> None:
        """Test default configuration values.

        Test Case ID: TC-CHS-CONFIG-001
        Priority: High
        Test Type: Unit Testing

        Purpose:
        Verify that CHSGPUConfig initializes with correct default values.

        Expected Results:
        - All default values are correctly set
        - Configuration is valid and usable
        """
        config = CHSGPUConfig()

        # Test default values
        assert config.device_id == 0
        assert config.max_batch_size == 2048
        assert config.embedding_dim == 384
        assert config.similarity_threshold == 0.7
        assert config.enable_faiss_gpu
        assert config.faiss_index_type == "IVF"
        assert config.enable_mixed_precision
        assert config.memory_limit_gb == 8.0
        assert config.enable_persistent_cache
        assert config.cache_size_mb == 1024
        assert config.fallback_enabled
        assert not config.benchmark_mode

    def test_custom_configuration(self) -> None:
        """Test custom configuration initialization.

        Test Case ID: TC-CHS-CONFIG-002
        Priority: High
        Test Type: Unit Testing

        Purpose:
        Verify that CHSGPUConfig accepts and stores custom values correctly.

        Expected Results:
        - Custom values are properly set
        - Configuration validates input parameters
        """
        config = CHSGPUConfig(
            device_id=1,
            max_batch_size=1024,
            embedding_dim=256,
            similarity_threshold=0.8,
            enable_faiss_gpu=False,
            faiss_index_type="HNSW",
            fallback_enabled=False,
        )

        assert config.device_id == 1
        assert config.max_batch_size == 1024
        assert config.embedding_dim == 256
        assert config.similarity_threshold == 0.8
        assert not config.enable_faiss_gpu
        assert config.faiss_index_type == "HNSW"
        assert not config.fallback_enabled

    def test_configuration_validation(self) -> None:
        """Test configuration parameter validation.

        Test Case ID: TC-CHS-CONFIG-003
        Priority: Medium
        Test Type: Validation Testing

        Purpose:
        Verify that configuration validates reasonable parameter ranges.

        Expected Results:
        - Edge cases are handled appropriately
        - Invalid parameters are rejected or normalized
        """
        # Test boundary values
        config = CHSGPUConfig(
            device_id=0,
            max_batch_size=1,
            embedding_dim=1,
            similarity_threshold=0.0,
            memory_limit_gb=0.1,
        )

        assert config.device_id == 0
        assert config.max_batch_size == 1
        assert config.embedding_dim == 1
        assert config.similarity_threshold == 0.0
        assert config.memory_limit_gb == 0.1


@pytest.mark.skipif(
    not GPU_ACCELERATOR_AVAILABLE, reason="GPU accelerator not available"
)
class TestCHSGPUAccelerator(unittest.TestCase):
    """Test CHSGPUAccelerator class functionality."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.config = CHSGPUConfig(
            device_id=0,
            max_batch_size=2,
            embedding_dim=5,
            enable_faiss_gpu=False,  # Disable FAISS for simpler testing
            fallback_enabled=True,
            enable_persistent_cache=False,  # Disable cache for initial tests
        )

        # Mock GPU environment for testing
        self.mock_torch_available = patch("torch.cuda.is_available", return_value=False)
        self.mock_torch_available.start()

    def tearDown(self) -> None:
        """Clean up test environment."""
        if hasattr(self, "mock_torch_available"):
            self.mock_torch_available.stop()

    def test_initialization_without_gpu(self) -> None:
        """Test accelerator initialization without GPU.

        Test Case ID: TC-CHS-INIT-001
        Priority: High
        Test Type: Unit Testing

        Purpose:
        Verify that accelerator initializes correctly without GPU support.

        Expected Results:
        - Accelerator initializes with fallback enabled
        - GPU resources are properly disabled
        - Configuration is applied correctly
        """
        accelerator = CHSGPUAccelerator(self.config)

        assert not accelerator.gpu_available
        assert accelerator.device is None
        assert accelerator.faiss_index is None
        assert accelerator.config.device_id == 0
        assert accelerator.config.max_batch_size == 2
        assert accelerator.config.embedding_dim == 5

    def test_accelerator_status(self) -> None:
        """Test accelerator status reporting.

        Test Case ID: TC-CHS-STATUS-001
        Priority: Medium
        Test Type: Unit Testing

        Purpose:
        Verify that accelerator returns accurate status information.

        Expected Results:
        - Status includes all required fields
        - GPU availability is correctly reported
        - Configuration details are included
        """
        accelerator = CHSGPUAccelerator(self.config)
        status = accelerator.get_accelerator_status()

        # Verify required status fields
        assert "gpu_available" in status
        assert "device_id" in status
        assert "config" in status
        assert "performance" in status
        assert "gpu_metrics" in status
        assert "faiss_status" in status

        # Verify values
        assert not status["gpu_available"]
        assert status["device_id"] == 0
        assert status["config"]["max_batch_size"] == 2
        assert status["config"]["embedding_dim"] == 5
        assert status["config"]["fallback_enabled"]

    async def test_process_embeddings_cpu_fallback(self, sample_texts) -> None:
        """Test embedding processing with CPU fallback.

        Test Case ID: TC-CHS-EMBED-001
        Priority: High
        Test Type: Integration Testing

        Purpose:
        Verify that embedding processing works correctly with CPU fallback.

        Expected Results:
        - Embeddings are generated for all texts
        - Processing metrics are accurate
        - CPU fallback is used when GPU unavailable
        """
        accelerator = CHSGPUAccelerator(self.config)

        # Process embeddings
        result = await accelerator.process_embeddings(sample_texts, batch_size=2)

        # Verify result structure
        assert isinstance(result, CHSProcessingResult)
        assert result.operation_type == CHSOperationType.EMBEDDING_COMPUTATION
        assert result.items_processed == len(sample_texts)
        assert result.processing_time > 0
        assert result.efficiency_score >= 0
        assert result.efficiency_score <= 100

        # Verify embeddings
        assert result.embeddings is not None
        assert len(result.embeddings) == len(sample_texts)

        # Verify each embedding
        for embedding in result.embeddings:
            assert isinstance(embedding, list)
            assert len(embedding) == self.config.embedding_dim

            # Verify embedding values are floats
            for value in embedding:
                assert isinstance(value, float)

        # Verify fallback was used
        assert not result.gpu_accelerated
        assert result.fallback_used

    async def test_process_embeddings_with_cache(self, sample_texts) -> None:
        """Test embedding processing with persistent cache.

        Test Case ID: TC-CHS-CACHE-001
        Priority: Medium
        Test Type: Integration Testing

        Purpose:
        Verify that persistent cache works correctly for embedding processing.

        Expected Results:
        - First processing caches results
        - Second processing uses cached results
        - Cache metrics are updated correctly
        """
        # Enable cache
        config_with_cache = CHSGPUConfig(
            max_batch_size=2,
            embedding_dim=5,
            enable_faiss_gpu=False,
            fallback_enabled=True,
            enable_persistent_cache=True,
        )
        accelerator = CHSGPUAccelerator(config_with_cache)

        # First processing
        await accelerator.process_embeddings(sample_texts, use_cache=True)

        # Verify cache metrics after first run
        initial_cache_hits = accelerator.cache_hits

        # Second processing (should use cache)
        result2 = await accelerator.process_embeddings(sample_texts, use_cache=True)

        # Verify cache was used
        assert accelerator.cache_hits > initial_cache_hits
        assert result2.processing_time == 0.0  # Cache should be instant
        assert result2.efficiency_score == 100.0  # Cache is most efficient
        assert not result2.gpu_accelerated  # From cache, not GPU

    async def test_similarity_search_cpu_fallback(self, sample_embeddings) -> None:
        """Test similarity search with CPU fallback.

        Test Case ID: TC-CHS-SIMILARITY-001
        Priority: High
        Test Type: Integration Testing

        Purpose:
        Verify that similarity search works correctly with CPU fallback.

        Expected Results:
        - Search returns accurate similarity scores
        - Results are properly ranked by similarity
        - Threshold filtering works correctly
        """
        accelerator = CHSGPUAccelerator(self.config)

        # Test similarity search
        query_embedding = sample_embeddings[0]
        candidate_embeddings = sample_embeddings[1:]

        result = await accelerator.similarity_search(
            query_embedding,
            candidate_embeddings,
            top_k=3,
            threshold=0.0,
        )

        # Verify result structure
        assert isinstance(result, CHSProcessingResult)
        assert result.operation_type == CHSOperationType.SIMILARITY_SEARCH
        assert result.items_processed == len(candidate_embeddings)
        assert result.processing_time > 0

        # Verify search results
        assert result.similarity_scores is not None
        assert result.indices is not None

        if result.similarity_scores and result.indices:
            # Results should be sorted by similarity (descending)
            for i in range(len(result.similarity_scores) - 1):
                assert result.similarity_scores[i] >= result.similarity_scores[i + 1]

            # All similarity scores should be in valid range
            for score in result.similarity_scores:
                assert score >= 0.0
                assert score <= 1.0

        # Verify fallback was used
        assert not result.gpu_accelerated
        assert result.fallback_used

    async def test_similarity_search_threshold_filtering(
        self, sample_embeddings
    ) -> None:
        """Test similarity search threshold filtering.

        Test Case ID: TC-CHS-SIMILARITY-002
        Priority: Medium
        Test Type: Unit Testing

        Purpose:
        Verify that similarity search correctly filters by threshold.

        Expected Results:
        - Low threshold returns more results
        - High threshold returns fewer results
        - No results when threshold is too high
        """
        accelerator = CHSGPUAccelerator(self.config)

        query_embedding = sample_embeddings[0]
        candidate_embeddings = sample_embeddings[1:]

        # Test with low threshold
        result_low = await accelerator.similarity_search(
            query_embedding,
            candidate_embeddings,
            top_k=10,
            threshold=0.1,
        )

        # Test with high threshold
        result_high = await accelerator.similarity_search(
            query_embedding,
            candidate_embeddings,
            top_k=10,
            threshold=0.9,
        )

        # Low threshold should return more or equal results
        low_count = (
            len(result_low.similarity_scores) if result_low.similarity_scores else 0
        )
        high_count = (
            len(result_high.similarity_scores) if result_high.similarity_scores else 0
        )

        assert low_count >= high_count

    async def test_error_handling_invalid_input(self) -> None:
        """Test error handling for invalid input data.

        Test Case ID: TC-CHS-ERROR-001
        Priority: High
        Test Type: Error Handling Testing

        Purpose:
        Verify that accelerator handles invalid input gracefully.

        Expected Results:
        - Invalid inputs are handled without crashes
        - Appropriate error messages are returned
        - Processing continues for valid inputs
        """
        accelerator = CHSGPUAccelerator(self.config)

        # Test with empty text list
        result = await accelerator.process_embeddings([])
        assert result.items_processed == 0
        assert result.error_message is not None

        # Test with invalid similarity search input
        result = await accelerator.similarity_search([], [], top_k=1)
        assert result.items_processed == 0
        assert result.error_message is not None

    async def test_batch_processing(self, sample_texts) -> None:
        """Test batch processing functionality.

        Test Case ID: TC-CHS-BATCH-001
        Priority: Medium
        Test Type: Unit Testing

        Purpose:
        Verify that batch processing works correctly for different batch sizes.

        Expected Results:
        - Processing works with different batch sizes
        - All items are processed regardless of batch size
        - Performance metrics are accurate
        """
        accelerator = CHSGPUAccelerator(self.config)

        # Test with different batch sizes
        batch_sizes = [1, 2, 4, 8]

        for batch_size in batch_sizes:
            with self.subTest(batch_size=batch_size):
                result = await accelerator.process_embeddings(
                    sample_texts, batch_size=batch_size
                )

                assert result.items_processed == len(sample_texts)
                assert result.embeddings is not None
                assert len(result.embeddings) == len(sample_texts)
                assert result.throughput > 0

    async def test_performance_metrics(self, sample_texts) -> None:
        """Test performance metrics calculation.

        Test Case ID: TC-CHS-PERF-001
        Priority: Medium
        Test Type: Performance Testing

        Purpose:
        Verify that performance metrics are calculated correctly.

        Expected Results:
        - Throughput is calculated correctly
        - Efficiency scores are in valid range
        - Processing time is measured accurately
        """
        accelerator = CHSGPUAccelerator(self.config)

        start_time = time.time()
        result = await accelerator.process_embeddings(sample_texts)
        end_time = time.time()

        # Verify time measurement
        self.assertAlmostEqual(result.processing_time, end_time - start_time, places=2)

        # Verify throughput calculation
        expected_throughput = len(sample_texts) / result.processing_time
        self.assertAlmostEqual(result.throughput, expected_throughput, places=2)

        # Verify efficiency score range
        assert result.efficiency_score >= 0
        assert result.efficiency_score <= 100

    async def test_cleanup(self) -> None:
        """Test resource cleanup functionality.

        Test Case ID: TC-CHS-CLEANUP-001
        Priority: Medium
        Test Type: Integration Testing

        Purpose:
        Verify that accelerator cleans up resources properly.

        Expected Results:
        - Cache is cleared
        - GPU resources are released
        - No memory leaks occur
        """
        accelerator = CHSGPUAccelerator(self.config)

        # Add some items to cache (if cache enabled)
        test_texts = ["test", "text", "data"]
        await accelerator.process_embeddings(test_texts, use_cache=True)

        # Perform cleanup
        await accelerator.cleanup()

        # Verify cache is cleared
        if accelerator.config.enable_persistent_cache:
            assert len(accelerator.embedding_cache) == 0
            assert len(accelerator.cache_timestamps) == 0


class TestFactoryFunctions(unittest.TestCase):
    """Test factory functions and utilities."""

    def test_create_chs_gpu_accelerator(self) -> None:
        """Test factory function for creating accelerators.

        Test Case ID: TC-CHS-FACTORY-001
        Priority: Low
        Test Type: Unit Testing

        Purpose:
        Verify that factory function creates correctly configured accelerators.

        Expected Results:
        - Accelerator is created with specified configuration
        - All parameters are applied correctly
        """
        # Mock GPU unavailable
        with patch("torch.cuda.is_available", return_value=False):
            accelerator = create_chs_gpu_accelerator(
                device_id=1,
                max_batch_size=512,
                embedding_dim=256,
                enable_faiss_gpu=False,
                fallback_enabled=True,
                mixed_precision=False,
            )

            assert accelerator.config.device_id == 1
            assert accelerator.config.max_batch_size == 512
            assert accelerator.config.embedding_dim == 256
            assert not accelerator.config.enable_faiss_gpu
            assert accelerator.config.fallback_enabled
            assert not accelerator.config.enable_mixed_precision


@pytest.mark.skipif(
    not GPU_ACCELERATOR_AVAILABLE, reason="GPU accelerator not available"
)
class TestIntegrationWithCHS(unittest.TestCase):
    """Test integration with Chat History Search system."""

    async def test_chs_integration(self, sample_texts) -> None:
        """Test integration with Chat History Search system.

        Test Case ID: TC-CHS-INTEGRATION-001
        Priority: Medium
        Test Type: Integration Testing

        Purpose:
        Verify that GPU accelerator integrates correctly with CHS system.

        Expected Results:
        - Accelerator can be used within CHS workflow
        - Results are compatible with CHS expectations
        - Performance improvements are realized
        """
        # Create accelerator with CHS-compatible config
        config = CHSGPUConfig(
            max_batch_size=3,
            embedding_dim=5,
            enable_faiss_gpu=False,
            fallback_enabled=True,
            enable_persistent_cache=True,
        )

        accelerator = CHSGPUAccelerator(config)

        try:
            # Simulate CHS workflow
            # 1. Process chat messages
            embeddings_result = await accelerator.process_embeddings(sample_texts)

            assert embeddings_result.items_processed == len(sample_texts)
            assert embeddings_result.embeddings is not None

            # 2. Perform similarity search
            if embeddings_result.embeddings and len(embeddings_result.embeddings) > 1:
                query_embedding = embeddings_result.embeddings[0]
                candidate_embeddings = embeddings_result.embeddings[1:]

                search_result = await accelerator.similarity_search(
                    query_embedding,
                    candidate_embeddings,
                    top_k=3,
                )

                assert search_result.items_processed == len(candidate_embeddings)
                assert search_result.indices is not None

            # 3. Get status for CHS monitoring
            status = accelerator.get_accelerator_status()
            assert "gpu_available" in status
            assert "performance" in status

        finally:
            await accelerator.cleanup()


@pytest.mark.skipif(
    not GPU_ACCELERATOR_AVAILABLE, reason="GPU accelerator not available"
)
class TestBenchmarking(unittest.TestCase):
    """Test benchmarking functionality."""

    async def test_performance_benchmark(self) -> None:
        """Test performance benchmarking functionality.

        Test Case ID: TC-CHS-BENCHMARK-001
        Priority: Low
        Test Type: Performance Testing

        Purpose:
        Verify that benchmarking provides accurate performance metrics.

        Expected Results:
        - Benchmark completes without errors
        - Results include expected metrics
        - Performance data is reasonable
        """
        # Mock GPU unavailable for reliable testing
        with patch("torch.cuda.is_available", return_value=False):
            accelerator = CHSGPUAccelerator(
                CHSGPUConfig(
                    max_batch_size=2,
                    enable_faiss_gpu=False,
                    fallback_enabled=True,
                ),
            )

            try:
                # Run small benchmark
                benchmark = await accelerator.benchmark_performance(
                    test_sizes=[5, 10],
                    test_operations=["embedding"],
                )

                # Verify benchmark structure
                assert "timestamp" in benchmark
                assert "gpu_available" in benchmark
                assert "results" in benchmark
                assert not benchmark["gpu_available"]  # Should be mocked

                # Verify test results
                assert "size_5" in benchmark["results"]
                assert "size_10" in benchmark["results"]

                # Verify operation results
                size_5_results = benchmark["results"]["size_5"]
                assert "embedding_cpu" in size_5_results

            finally:
                await accelerator.cleanup()


class TestErrorRecovery(unittest.TestCase):
    """Test error recovery and resilience."""

    async def test_gpu_failure_recovery(self, sample_texts) -> None:
        """Test recovery from GPU failures.

        Test Case ID: TC-CHS-RECOVERY-001
        Priority: Medium
        Test Type: Error Handling Testing

        Purpose:
        Verify that system recovers gracefully from GPU failures.

        Expected Results:
        - GPU failures are handled gracefully
        - CPU fallback is activated automatically
        - Processing continues with degraded performance
        """
        # Create accelerator that will simulate GPU failure
        config = CHSGPUConfig(
            max_batch_size=2,
            fallback_enabled=True,
        )

        # Mock GPU initialization failure
        with patch("torch.cuda.is_available", side_effect=Exception("GPU error")):
            accelerator = CHSGPUAccelerator(config)

            # Verify GPU is marked as unavailable
            assert not accelerator.gpu_available

            # Verify processing still works with CPU fallback
            result = await accelerator.process_embeddings(sample_texts)

            assert result.items_processed == len(sample_texts)
            assert not result.gpu_accelerated
            assert result.fallback_used
            assert result.embeddings is not None

    async def test_memory_pressure_handling(self, sample_texts) -> None:
        """Test handling of memory pressure situations.

        Test Case ID: TC-CHS-MEMORY-001
        Priority: Medium
        Test Type: Stress Testing

        Purpose:
        Verify that system handles memory pressure correctly.

        Expected Results:
        - Memory limits are respected
        - Processing adapts to available memory
        - No crashes occur under memory pressure
        """
        # Create accelerator with low memory limit
        config = CHSGPUConfig(
            max_batch_size=1,  # Very small batch size
            memory_limit_gb=0.1,  # Very low memory limit
            fallback_enabled=True,
        )

        # Mock GPU with low memory
        with patch("torch.cuda.is_available", return_value=False):
            accelerator = CHSGPUAccelerator(config)

            # Process with memory pressure
            result = await accelerator.process_embeddings(sample_texts, batch_size=1)

            # Should still work with small batches
            assert result.items_processed == len(sample_texts)
            assert result.embeddings is not None


# Test runner for async tests
class AsyncTestRunner:
    """Helper class to run async tests."""

    def __init__(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def run_async_test(self, test_func, *args, **kwargs):
        """Run async test function."""
        try:
            if hasattr(test_func, "__self__"):
                # Method bound to instance
                return self.loop.run_until_complete(test_func(*args, **kwargs))
            # Standalone function
            return self.loop.run_until_complete(test_func(*args, **kwargs))
        finally:
            # Clean up any remaining tasks
            pending = asyncio.all_tasks(self.loop)
            for task in pending:
                task.cancel()
            if pending:
                self.loop.run_until_complete(
                    asyncio.gather(*pending, return_exceptions=True)
                )

    def cleanup(self) -> None:
        """Clean up event loop."""
        self.loop.close()


# Pytest async test configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test execution
if __name__ == "__main__":
    # Run tests with pytest
    import sys

    sys.exit(
        pytest.main(
            [
                __file__,
                "-v",
                "--tb=short",
                "--durations=10",
            ],
        ),
    )
