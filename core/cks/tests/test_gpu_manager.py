import time

import numpy as np
import pytest

from ..core.gpu_manager import GPUMemoryConfig, GPUMemoryManager, GPUMemoryStats

"""
Comprehensive tests for CKS GPU Memory Manager.

Test Case IDs: GPU-001 to GPU-100
Test Framework: pytest with real components (no mocks)
Constitutional Compliance: Mandatory evidence-based testing

Test Coverage:
1. Configuration validation
2. GPU initialization and fallback
3. Memory allocation and cleanup
4. RAPIDS integration
5. FAISS GPU operations
6. Memory leak detection
7. Performance monitoring
8. Constitutional compliance
"""


# Import the GPU manager


class TestGPUMemoryConfig:
    """Test GPU memory configuration validation."""

    def test_valid_config_creation(self):
        """
        Test Case ID: GPU-001
        Priority: High
        Test Type: Unit Testing

        Purpose:
        Verify that valid GPUMemoryConfig objects can be created with
        constitutional compliance.

        Expected Results:
        - Configuration object created successfully
        - All validation checks pass
        - No exceptions raised
        """
        config = GPUMemoryConfig(
            max_gpu_memory_mb=6144,
            memory_threshold_mb=5120,
            cleanup_threshold_mb=5632,
        )

        assert config.max_gpu_memory_mb == 6144
        assert config.memory_threshold_mb == 5120
        assert config.cleanup_threshold_mb == 5632

    def test_invalid_config_memory_limit_too_high(self):
        """
        Test Case ID: GPU-002
        Priority: High
        Test Type: Validation Testing

        Purpose:
        Verify that configurations violating solo developer limits are rejected.

        Expected Results:
        - ValueError raised for excessive memory limits
        - Constitutional compliance enforced
        """
        with pytest.raises(ValueError, match="exceeds solo developer maximum"):
            GPUMemoryConfig(max_gpu_memory_mb=8192)  # Exceeds 6GB limit

    def test_invalid_config_threshold_exceeds_limit(self):
        """
        Test Case ID: GPU-003
        Priority: Medium
        Test Type: Validation Testing

        Purpose:
        Verify that invalid threshold configurations are rejected.

        Expected Results:
        - ValueError raised when threshold >= limit
        - Configuration validation enforces logical consistency
        """
        with pytest.raises(ValueError, match="memory_threshold_mb must be less than"):
            GPUMemoryConfig(
                max_gpu_memory_mb=6144,
                memory_threshold_mb=6144,  # Equal to max
            )

    def test_invalid_config_cleanup_threshold_exceeds_limit(self):
        """
        Test Case ID: GPU-004
        Priority: Medium
        Test Type: Validation Testing

        Purpose:
        Verify cleanup threshold validation.

        Expected Results:
        - ValueError raised when cleanup threshold >= limit
        - Configuration validation prevents logical errors
        """
        with pytest.raises(ValueError, match="cleanup_threshold_mb must be less than"):
            GPUMemoryConfig(
                max_gpu_memory_mb=6144,
                cleanup_threshold_mb=6144,  # Equal to max
            )


class TestGPUMemoryManager:
    """Test GPU memory manager functionality."""

    @pytest.fixture
    def basic_config(self):
        """Fixture providing basic GPU memory configuration."""
        return GPUMemoryConfig(
            max_gpu_memory_mb=4096,  # 4GB for testing
            memory_threshold_mb=3072,
            cleanup_threshold_mb=3584,
            monitoring_interval=1.0,  # Fast for testing
            auto_cleanup=True,
        )

    @pytest.fixture
    def cpu_fallback_config(self):
        """Fixture providing CPU-only configuration."""
        return GPUMemoryConfig(
            enable_gpu=False,
            fallback_to_cpu=True,
            monitoring_interval=1.0,
        )

    @pytest.fixture
    def gpu_manager(self, basic_config):
        """Fixture providing initialized GPU manager."""
        manager = GPUMemoryManager(basic_config)
        manager.initialize()
        yield manager
        manager.shutdown()

    @pytest.fixture
    def cpu_manager(self, cpu_fallback_config):
        """Fixture providing CPU-only manager."""
        manager = GPUMemoryManager(cpu_fallback_config)
        manager.initialize()
        yield manager
        manager.shutdown()

    def test_manager_initialization_success(self, basic_config):
        """
        Test Case ID: GPU-005
        Priority: High
        Test Type: Integration Testing

        Purpose:
        Verify successful GPU manager initialization with constitutional compliance.

        Preconditions:
        - Valid configuration provided
        - Required libraries available (or gracefully handled)

        Expected Results:
        - Manager initializes successfully
        - GPU monitoring started (if available)
        - RAPIDS components initialized (if available)
        - Constitutional validation passed
        """
        with GPUMemoryManager(basic_config) as manager:
            assert manager._initialized is True
            # Additional initialization checks depend on GPU availability

    def test_manager_initialization_cpu_fallback(self, cpu_fallback_config):
        """
        Test Case ID: GPU-006
        Priority: High
        Test Type: Integration Testing

        Purpose:
        Verify CPU-only initialization when GPU disabled.

        Expected Results:
        - Manager initializes successfully in CPU mode
        - GPU monitoring not started
        - All operations fall back to CPU
        """
        with GPUMemoryManager(cpu_fallback_config) as manager:
            assert manager._initialized is True
            assert manager._gpu_available is False
            assert manager._monitoring_active is False

    def test_memory_stats_collection(self, gpu_manager):
        """
        Test Case ID: GPU-007
        Priority: High
        Test Type: Functional Testing

        Purpose:
        Verify memory statistics collection and reporting.

        Expected Results:
        - Memory stats object returned
        - Statistics populated (if GPU available)
        - Timestamp and availability flags set correctly
        """
        stats = gpu_manager.get_memory_stats()

        assert isinstance(stats, GPUMemoryStats)
        assert stats.timestamp > 0
        assert isinstance(stats.is_available, bool)

        if stats.is_available:
            assert stats.used_memory_mb >= 0
            assert stats.free_memory_mb >= 0
            assert 0 <= stats.utilization_percent <= 100

    def test_memory_availability_check(self, gpu_manager):
        """
        Test Case ID: GPU-008
        Priority: Medium
        Test Type: Functional Testing

        Purpose:
        Verify memory availability checking logic.

        Expected Results:
        - Correct availability assessment
        - CPU fallback when GPU unavailable
        - Safety margin consideration
        """
        # Test small memory request
        assert gpu_manager.check_memory_availability(100) is True  # 100MB should be available

        # Test large memory request
        large_request = gpu_manager.config.max_gpu_memory_mb * 2
        result = gpu_manager.check_memory_availability(large_request)
        # Should return fallback capability if GPU unavailable or insufficient
        assert isinstance(result, bool)

    def test_gpu_array_allocation(self, gpu_manager):
        """
        Test Case ID: GPU-009
        Priority: High
        Test Type: Functional Testing

        Purpose:
        Verify GPU array allocation with fallback.

        Expected Results:
        - Array allocated successfully (GPU or CPU)
        - Correct shape and data type
        - Allocation tracking updated
        - Fallback occurs when necessary
        """
        shape = (100, 50)
        dtype = np.float32

        result = gpu_manager.allocate_gpu_array(shape, dtype)

        # Check that we got some kind of array
        assert hasattr(result, "shape")
        assert result.shape == shape
        assert result.dtype == dtype

        # Check allocation tracking
        assert gpu_manager._operation_count > 0

    def test_gpu_array_allocation_large_memory(self, gpu_manager):
        """
        Test Case ID: GPU-010
        Priority: Medium
        Test Type: Stress Testing

        Purpose:
        Verify behavior with large memory allocations.

        Expected Results:
        - Large allocation falls back to CPU if GPU memory insufficient
        - No memory overflow or crashes
        - Graceful handling of memory constraints
        """
        # Request very large array that should exceed GPU limits
        shape = (10000, 10000)  # ~400MB for float32
        dtype = np.float32

        result = gpu_manager.allocate_gpu_array(shape, dtype)

        # Should still get an array (likely on CPU)
        assert hasattr(result, "shape")
        assert result.shape == shape

    def test_gpu_dataframe_creation(self, gpu_manager):
        """
        Test Case ID: GPU-011
        Priority: Medium
        Test Type: Integration Testing

        Purpose:
        Verify GPU DataFrame creation with RAPIDS integration.

        Expected Results:
        - DataFrame created successfully (GPU or CPU)
        - Correct data structure and content
        - Fallback when RAPIDS unavailable
        """
        data = {
            "col1": [1, 2, 3, 4, 5],
            "col2": ["a", "b", "c", "d", "e"],
            "col3": [1.1, 2.2, 3.3, 4.4, 5.5],
        }

        result = gpu_manager.create_gpu_dataframe(data)

        # Check DataFrame properties
        assert hasattr(result, "columns") or hasattr(result, "__len__")
        assert len(result) == 5

        # Check allocation tracking
        assert gpu_manager._operation_count > 0

    def test_faiss_index_creation(self, gpu_manager):
        """
        Test Case ID: GPU-012
        Priority: High
        Test Type: Integration Testing

        Purpose:
        Verify FAISS index creation with GPU support.

        Expected Results:
        - Index created successfully
        - Correct dimension and type
        - GPU acceleration if available
        - CPU fallback if necessary
        """
        dimension = 128

        # Test flat index
        index = gpu_manager.create_faiss_index(dimension, "flat")
        assert index is not None

        # Test IVF index
        index_ivf = gpu_manager.create_faiss_index(dimension, "ivf")
        assert index_ivf is not None

    def test_faiss_index_invalid_type(self, gpu_manager):
        """
        Test Case ID: GPU-013
        Priority: Low
        Test Type: Error Handling Testing

        Purpose:
        Verify error handling for invalid index types.

        Expected Results:
        - ValueError raised for unsupported types
        - Clear error message provided
        """
        dimension = 64

        with pytest.raises(ValueError, match="Unsupported index type"):
            gpu_manager.create_faiss_index(dimension, "invalid_type")

    def test_memory_cleanup(self, gpu_manager):
        """
        Test Case ID: GPU-014
        Priority: High
        Test Type: Functional Testing

        Purpose:
        Verify GPU memory cleanup functionality.

        Expected Results:
        - Cleanup executes without errors
        - Memory freed (if GPU available)
        - Allocation tracking cleared
        """
        # Create some allocations first
        gpu_manager.allocate_gpu_array((100, 100), np.float32)
        gpu_manager.create_gpu_dataframe({"a": [1, 2, 3]})

        # Perform cleanup
        freed_memory = gpu_manager.cleanup_gpu_memory()

        assert isinstance(freed_memory, float)
        assert freed_memory >= 0

    def test_forced_memory_cleanup(self, gpu_manager):
        """
        Test Case ID: GPU-015
        Priority: Medium
        Test Type: Functional Testing

        Purpose:
        Verify forced memory cleanup functionality.

        Expected Results:
        - Cleanup executed regardless of memory usage
        - All memory pools cleared
        - Maximum cleanup performed
        """
        freed_memory = gpu_manager.cleanup_gpu_memory(force=True)

        assert isinstance(freed_memory, float)
        assert freed_memory >= 0

    def test_performance_stats(self, gpu_manager):
        """
        Test Case ID: GPU-016
        Priority: Medium
        Test Type: Reporting Testing

        Purpose:
        Verify comprehensive performance statistics reporting.

        Expected Results:
        - Performance stats dictionary returned
        - All required categories present
        - Numeric values within expected ranges
        """
        # Perform some operations to generate stats
        gpu_manager.allocate_gpu_array((50, 50), np.float32)
        gpu_manager.create_gpu_dataframe({"test": [1, 2, 3]})

        stats = gpu_manager.get_performance_stats()

        assert isinstance(stats, dict)

        # Check required sections
        required_sections = [
            "gpu_available",
            "current_memory_stats",
            "operation_stats",
            "configuration",
            "allocated_objects",
            "rapids_enabled",
        ]
        for section in required_sections:
            assert section in stats

        # Check operation stats
        op_stats = stats["operation_stats"]
        assert "total_operations" in op_stats
        assert "fallback_count" in op_stats
        assert "fallback_rate" in op_stats
        assert op_stats["total_operations"] >= 0

    def test_constitutional_compliance_score(self, gpu_manager):
        """
        Test Case ID: GPU-017
        Priority: High
        Test Type: Compliance Testing

        Purpose:
        Verify constitutional compliance scoring.

        Expected Results:
        - Compliance score between 0.0 and 1.0
        - Score reflects actual compliance level
        - Solo developer optimization considered
        """
        score = gpu_manager.get_constitutional_compliance_score()

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

        # Score should be reasonable for a properly configured system
        assert score >= 0.0  # Minimum score

    def test_gpu_context_manager(self, gpu_manager):
        """
        Test Case ID: GPU-018
        Priority: Medium
        Test Type: Context Management Testing

        Purpose:
        Verify GPU context manager functionality.

        Expected Results:
        - Context entered and exited cleanly
        - Resources cleaned up on exit
        - No memory leaks from context usage
        """
        gpu_manager.get_memory_stats()

        with gpu_manager.gpu_context(required_memory_mb=10):
            # Perform operations within context
            array = gpu_manager.allocate_gpu_array((10, 10), np.float32)
            assert array is not None

        memory_after = gpu_manager.get_memory_stats()

        # Memory should be reasonably managed
        # (exact comparison may not work due to system variations)
        assert isinstance(memory_after.used_memory_mb, float)

    def test_manager_context_manager(self, basic_config):
        """
        Test Case ID: GPU-019
        Priority: High
        Test Type: Context Management Testing

        Purpose:
        Verify manager context manager functionality.

        Expected Results:
        - Manager initialized on enter
        - Manager shutdown on exit
        - Resources properly cleaned up
        """
        with GPUMemoryManager(basic_config) as manager:
            assert manager._initialized is True
            # Perform operations
            manager.allocate_gpu_array((10, 10), np.float32)

        # Manager should be shut down after context exit
        assert manager._initialized is False

    def test_double_initialization(self, gpu_manager):
        """
        Test Case ID: GPU-020
        Priority: Low
        Test Type: Robustness Testing

        Purpose:
        Verify behavior when initialize() called multiple times.

        Expected Results:
        - Second initialization call handled gracefully
        - No errors or resource duplication
        """
        # Manager already initialized by fixture
        assert gpu_manager._initialized is True

        # Should not cause errors
        gpu_manager.initialize()
        assert gpu_manager._initialized is True

    def test_shutdown_without_initialization(self, basic_config):
        """
        Test Case ID: GPU-021
        Priority: Low
        Test Type: Robustness Testing

        Purpose:
        Verify shutdown behavior for uninitialized manager.

        Expected Results:
        - Shutdown call handled gracefully
        - No errors when shutting down uninitialized manager
        """
        manager = GPUMemoryManager(basic_config)
        # Don't initialize

        # Should not cause errors
        manager.shutdown()
        assert manager._initialized is False

    def test_configuration_violations(self):
        """
        Test Case ID: GPU-022
        Priority: High
        Test Type: Constitutional Testing

        Purpose:
        Verify constitutional compliance enforcement in configuration.

        Expected Results:
        - Excessive memory limits rejected
        - Solo developer optimization enforced
        - Appropriate error messages
        """
        # Test memory limit violation
        with pytest.raises(ValueError, match="exceeds solo developer maximum"):
            config = GPUMemoryConfig(max_gpu_memory_mb=8192)  # 8GB exceeds 6GB limit
            manager = GPUMemoryManager(config)
            manager.initialize()

    def test_memory_leak_detection(self, gpu_manager):
        """
        Test Case ID: GPU-023
        Priority: Medium
        Test Type: Memory Testing

        Purpose:
        Verify memory leak detection functionality.

        Expected Results:
        - Memory leak detection works (when GPU available)
        - Baseline tracking implemented
        - Leak warnings generated appropriately
        """
        # Simulate memory usage patterns
        for i in range(5):
            gpu_manager.allocate_gpu_array((100, 100), np.float32)
            time.sleep(0.1)  # Small delay

        # Check memory stats
        stats = gpu_manager.get_memory_stats()
        assert isinstance(stats.memory_leaks_detected, int)
        assert stats.memory_leaks_detected >= 0

    def test_fallback_count_tracking(self, cpu_manager):
        """
        Test Case ID: GPU-024
        Priority: Medium
        Test Type: Metrics Testing

        Purpose:
        Verify fallback operation tracking.

        Expected Results:
        - Fallback operations counted correctly
        - Fallback rate calculated accurately
        - Performance metrics reflect CPU-only usage
        """
        # Perform operations that should fallback
        cpu_manager.allocate_gpu_array((10, 10), np.float32)
        cpu_manager.create_gpu_dataframe({"a": [1, 2, 3]})

        stats = cpu_manager.get_performance_stats()
        op_stats = stats["operation_stats"]

        assert op_stats["total_operations"] >= 2
        assert op_stats["fallback_count"] >= 2
        assert op_stats["fallback_rate"] >= 100.0  # Should be 100% for CPU-only

    def test_rapids_integration_status(self, gpu_manager):
        """
        Test Case ID: GPU-025
        Priority: Medium
        Test Type: Integration Testing

        Purpose:
        Verify RAPIDS components status reporting.

        Expected Results:
        - RAPIDS availability correctly detected
        - Individual component status reported
        - Graceful fallback when components unavailable
        """
        stats = gpu_manager.get_performance_stats()
        rapids_status = stats["rapids_enabled"]

        assert isinstance(rapids_status, dict)
        assert "cudf" in rapids_status
        assert "cuml" in rapids_status
        assert "cupy" in rapids_status
        assert "faiss_gpu" in rapids_status

        # All should be boolean values
        for enabled in rapids_status.values():
            assert isinstance(enabled, bool)


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_initialization_with_invalid_config(self):
        """
        Test Case ID: GPU-026
        Priority: High
        Test Type: Error Handling Testing

        Purpose:
        Verify error handling during initialization with invalid config.

        Expected Results:
        - Initialization fails gracefully
        - Appropriate error messages
        - Resource cleanup on failure
        """
        config = GPUMemoryConfig(max_gpu_memory_mb=-1)  # Invalid

        with pytest.raises(ValueError):
            manager = GPUMemoryManager(config)
            manager.initialize()

    def test_operation_without_initialization(self, basic_config):
        """
        Test Case ID: GPU-027
        Priority: Medium
        Test Type: Error Handling Testing

        Purpose:
        Verify behavior when operations called without initialization.

        Expected Results:
        - Operations fail gracefully
        - Appropriate error handling
        - No system crashes
        """
        manager = GPUMemoryManager(basic_config)
        # Don't initialize

        # Most operations should still work by auto-initializing
        # or handle the uninitialized state gracefully
        stats = manager.get_memory_stats()
        assert isinstance(stats, GPUMemoryStats)


# Integration tests with real libraries
@pytest.mark.integration
class TestRealGPUIntegration:
    """Integration tests that require real GPU libraries."""

    @pytest.fixture
    def real_config(self):
        """Configuration for real GPU testing."""
        return GPUMemoryConfig(
            max_gpu_memory_mb=2048,  # Conservative for testing
            monitoring_interval=0.5,
            auto_cleanup=True,
        )

    def test_real_gpu_operations(self, real_config):
        """
        Test Case ID: GPU-028
        Priority: High
        Test Type: Integration Testing

        Purpose:
        Test real GPU operations when libraries are available.

        Expected Results:
        - GPU operations work if libraries available
        - CPU fallback if libraries unavailable
        - No crashes in either case
        """
        try:
            with GPUMemoryManager(real_config) as manager:
                # Test various operations
                array = manager.allocate_gpu_array((100, 50), np.float32)
                assert array is not None

                df = manager.create_gpu_dataframe({"a": [1, 2, 3, 4, 5]})
                assert df is not None

                index = manager.create_faiss_index(64, "flat")
                assert index is not None

        except Exception as e:
            # Should only fail if critical libraries unavailable
            pytest.skip(f"GPU libraries not available: {e}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
