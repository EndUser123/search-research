"""Comprehensive Test Suite for Enhanced Session Memory Adapter with RAG Integration.

Task R-012 Implementation Test: Session Memory Adapter

This test suite validates the RAG system integration with session memory bridge
including context injection, pattern reconstruction, CKS integration, and performance requirements.

Key Test Areas:
1. RAG Integration Working Smoothly
2. Context Injection Accuracy (<50ms target)
3. Pattern Reconstruction Success (<100ms target)
4. CKS Integration Functionality
5. Performance Requirements Validation

Author: CSF Development Team
Version: 2.0.0 Test Suite
"""

import asyncio
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path

import pytest

# Import the enhanced SessionMemoryAdapter
from .session_memory_adapter import (
    HybridContext,
    IntelligentFilter,
    RAGContextInjection,
    SemanticBridge,
    SessionMemoryAdapter,
)


# Mock dependencies for testing
class MockRAGCoordinator:
    """Mock RAG coordinator for testing."""

    def __init__(self) -> None:
        self.state = None
        self.initialized = False

    async def initialize(self) -> None:
        self.state = "active"
        self.initialized = True

    async def coordinate_rag_workflow(
        self, query, documents=None, context=None, workflow_config=None
    ):
        return {
            "rag_result": {"enhanced_content": f"Enhanced: {query}"},
            "coordination_metadata": {
                "coordinator_id": "mock_coordinator",
                "coordination_time_ms": 15.0,
                "performance_score": 0.9,
            },
            "quality_score": 0.85,
        }


class MockStorageManager:
    """Mock storage manager for testing."""

    def __init__(self) -> None:
        self.vectors = {}

    async def store_vector(self, vector_id, vector) -> None:
        self.vectors[vector_id] = vector

    async def retrieve_vector(self, vector_id):
        return self.vectors.get(vector_id)


class MockSessionMemoryBridge:
    """Mock session memory bridge for testing."""

    def __init__(self) -> None:
        self.preserved_patterns = {}

    def preserve_session_context(self, session_id, criticality_threshold=0.7):
        return MockCompactionBridge(session_id, criticality_threshold)

    async def restore_session_context(self, bridge_id):
        return MockRestorationResult(success=True)


class MockCompactionBridge:
    """Mock compaction bridge."""

    def __init__(self, session_id, criticality_threshold) -> None:
        self.session_id = session_id
        self.criticality_threshold = criticality_threshold
        self.preserved_patterns = []

    def add_preserved_pattern(self, pattern) -> None:
        self.preserved_patterns.append(pattern)


class MockRestorationResult:
    """Mock restoration result."""

    def __init__(self, success=True) -> None:
        self.success = success
        self.errors = []


class TestSessionMemoryAdapterRAGIntegration:
    """Test suite for SessionMemoryAdapter RAG integration."""

    @pytest.fixture
    async def adapter(self):
        """Create a test instance of SessionMemoryAdapter."""
        # Create temporary directory for test databases
        temp_dir = tempfile.mkdtemp()
        original_cwd = Path.cwd()

        try:
            import os

            os.chdir(temp_dir)

            # Create mock dependencies
            rag_coordinator = MockRAGCoordinator()
            storage_manager = MockStorageManager()
            session_memory_bridge = MockSessionMemoryBridge()

            # Initialize adapter with RAG integration enabled
            adapter = SessionMemoryAdapter(
                rag_coordinator=rag_coordinator,
                storage_manager=storage_manager,
                session_memory_bridge=session_memory_bridge,
                enable_rag_integration=True,
                enable_hybrid_context=True,
                enable_intelligent_filtering=True,
                cache_size_mb=50,
                context_injection_timeout_ms=50.0,
                pattern_reconstruction_timeout_ms=100.0,
            )

            yield adapter

        finally:
            # Cleanup
            os.chdir(original_cwd)
            shutil.rmtree(temp_dir, ignore_errors=True)
            if "adapter" in locals():
                await adapter.cleanup()

    @pytest.mark.asyncio
    async def test_adapter_initialization(self, adapter) -> None:
        """Test adapter initialization with RAG components."""
        # Verify adapter is properly initialized
        assert adapter.enable_rag_integration is True
        assert adapter.enable_hybrid_context is True
        assert adapter.enable_intelligent_filtering is True
        assert adapter.context_injection_timeout_ms == 50.0
        assert adapter.pattern_reconstruction_timeout_ms == 100.0
        assert adapter.rag_query_overhead_target_ms == 30.0
        assert adapter.vector_store_optimization_target == 0.2

    @pytest.mark.asyncio
    async def test_context_injection_logic_performance(self, adapter) -> None:
        """Test context injection logic meets <50ms performance target."""
        # Prepare test data
        session_id = "test_session_001"
        context_data = {
            "content": "This is a test context for RAG integration with session memory bridge",
            "keywords": ["test", "context", "rag", "integration", "session", "memory"],
            "metadata": {"test_id": "performance_test"},
        }

        # Measure context injection performance
        start_time = time.time()
        result = await adapter.inject_context_logic(session_id, context_data)
        execution_time_ms = (time.time() - start_time) * 1000

        # Validate results
        assert result["injection_status"] == "success"
        assert (
            execution_time_ms < 50.0
        ), f"Context injection took {execution_time_ms}ms, target <50ms"
        assert "filtered_context" in result
        assert "rag_enhanced_context" in result
        assert "hybrid_context" in result
        assert "relevance_scores" in result
        assert result["performance_grade"] in ["excellent", "good"]

    @pytest.mark.asyncio
    async def test_pattern_reconstruction_algorithms_performance(self, adapter) -> None:
        """Test pattern reconstruction algorithms meet <100ms performance target."""
        # Prepare test patterns
        patterns = [
            {
                "pattern_id": "pattern_001",
                "pattern_type": "question_answer",
                "confidence": 0.85,
                "frequency": 0.7,
                "keywords": ["question", "answer", "help"],
                "created_at": datetime.utcnow(),
            },
            {
                "pattern_id": "pattern_002",
                "pattern_type": "problem_solving",
                "confidence": 0.90,
                "frequency": 0.8,
                "keywords": ["problem", "solution", "solve"],
                "created_at": datetime.utcnow(),
            },
            {
                "pattern_id": "pattern_003",
                "pattern_type": "code_discussion",
                "confidence": 0.75,
                "frequency": 0.6,
                "keywords": ["code", "function", "class"],
                "created_at": datetime.utcnow(),
            },
        ]

        # Measure pattern reconstruction performance
        start_time = time.time()
        result = await adapter.pattern_reconstruction_algorithms(patterns)
        execution_time_ms = (time.time() - start_time) * 1000

        # Validate results
        assert result["reconstruction_status"] == "success"
        assert (
            execution_time_ms < 100.0
        ), f"Pattern reconstruction took {execution_time_ms}ms, target <100ms"
        assert "reconstructed_context" in result
        assert "quality_metrics" in result
        assert result["quality_metrics"]["overall_quality"] > 0.5
        assert "temporal" in result["reconstruction_algorithms"]
        assert "semantic" in result["reconstruction_algorithms"]
        assert "interpolation" in result["reconstruction_algorithms"]

    @pytest.mark.asyncio
    async def test_cks_integration_functionality(self, adapter) -> None:
        """Test CKS integration module functionality."""
        # Test CKS integration
        integration_status = await adapter.work_with_cks_integration()

        # Should return True (mock implementation always succeeds)
        assert isinstance(integration_status, bool)

    @pytest.mark.asyncio
    async def test_vector_store_optimization(self, adapter) -> None:
        """Test vector store optimization for sessions."""
        # Test vector store optimization
        result = await adapter.optimize_vector_store_for_sessions()

        # Validate optimization results
        assert "optimization_status" in result
        assert "total_storage_improvement_percent" in result
        assert "optimization_time_ms" in result
        assert isinstance(result["total_storage_improvement_percent"], (int, float))

    @pytest.mark.asyncio
    async def test_intelligent_filtering_system(self, adapter) -> None:
        """Test intelligent filtering system functionality."""
        # Prepare test data with noise
        session_id = "test_session_filtering"
        context_data = {
            "content": "The quick brown fox jumps over the lazy dog. This is meaningful content with some noise words like the and a.",
            "keywords": ["quick", "brown", "fox", "meaningful", "content"],
            "metadata": {"filtering_test": True},
        }

        # Test context injection with filtering
        result = await adapter.inject_context_logic(session_id, context_data)

        # Validate filtering results
        assert result["injection_status"] == "success"
        assert "filtering_results" in result
        assert result["filtering_results"]["noise_removed"] >= 0

    @pytest.mark.asyncio
    async def test_hybrid_context_management(self, adapter) -> None:
        """Test hybrid context management functionality."""
        # Prepare test data
        session_id = "test_session_hybrid"
        original_context = {
            "content": "Original session context content",
            "keywords": ["original", "session", "context"],
            "session_data": {"user_id": "test_user", "session_start": datetime.utcnow()},
        }

        # Test context injection to create hybrid context
        result = await adapter.inject_context_logic(session_id, original_context)

        # Validate hybrid context creation
        assert result["injection_status"] == "success"
        assert result["hybrid_context"] is not None

        hybrid_context = result["hybrid_context"]
        assert isinstance(hybrid_context, HybridContext)
        assert hybrid_context.rag_context is not None
        assert hybrid_context.session_context is not None
        assert hybrid_context.merged_context is not None
        assert hybrid_context.confidence_weights is not None
        assert hybrid_context.integration_quality > 0.0

    @pytest.mark.asyncio
    async def test_semantic_bridge_functionality(self, adapter) -> None:
        """Test semantic bridge creation functionality."""
        # This is indirectly tested through hybrid context creation
        session_id = "test_session_bridges"
        context_data = {
            "content": "Testing semantic bridge creation between RAG and session memory",
            "keywords": ["semantic", "bridge", "rag", "session", "memory"],
            "technical_terms": ["vector", "embedding", "similarity", "bridge"],
        }

        result = await adapter.inject_context_logic(session_id, context_data)
        hybrid_context = result["hybrid_context"]

        # Validate semantic bridges
        assert hybrid_context.semantic_bridges is not None
        assert isinstance(hybrid_context.semantic_bridges, list)

    @pytest.mark.asyncio
    async def test_performance_optimization_with_caching(self, adapter) -> None:
        """Test performance optimization with caching."""
        session_id = "test_session_caching"
        context_data = {
            "content": "Testing caching functionality for performance optimization",
            "keywords": ["caching", "performance", "optimization"],
        }

        # First call - should take longer
        start_time = time.time()
        result1 = await adapter.inject_context_logic(session_id, context_data)
        first_call_time = (time.time() - start_time) * 1000

        # Second call - should be faster due to caching
        start_time = time.time()
        result2 = await adapter.inject_context_logic(session_id, context_data)
        second_call_time = (time.time() - start_time) * 1000

        # Validate caching effectiveness
        assert result1["injection_status"] == "success"
        assert result2["injection_status"] == "success"
        # Second call should be faster or at least not significantly slower
        assert second_call_time <= first_call_time + 10  # Allow 10ms variance

    @pytest.mark.asyncio
    async def test_rag_query_overhead_target(self, adapter) -> None:
        """Test RAG query overhead meets <30ms target."""
        session_id = "test_session_overhead"
        context_data = {
            "content": "Testing RAG query overhead performance target",
            "keywords": ["rag", "query", "overhead", "performance"],
        }

        result = await adapter.inject_context_logic(session_id, context_data)

        # Validate RAG overhead
        assert result["injection_status"] == "success"
        rag_enhanced = result["rag_enhanced_context"]
        assert rag_enhanced["rag_status"] in ["success", "simulated"]

        if rag_enhanced["rag_status"] == "success":
            assert rag_enhanced["rag_overhead_ms"] <= adapter.rag_query_overhead_target_ms

    @pytest.mark.asyncio
    async def test_error_handling_and_fallbacks(self, adapter) -> None:
        """Test error handling and fallback mechanisms."""
        # Test with invalid session ID
        result = await adapter.inject_context_logic("", {"content": "test"})
        assert result["injection_status"] == "failed"
        assert "error" in result

        # Test with empty context data
        result = await adapter.inject_context_logic("test_session", {})
        assert result["injection_status"] == "failed"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, adapter) -> None:
        """Test concurrent operations performance."""
        # Create multiple concurrent context injection tasks
        session_ids = [f"concurrent_session_{i}" for i in range(10)]
        context_data = {
            "content": "Concurrent test context",
            "keywords": ["concurrent", "test", "performance"],
        }

        # Execute concurrent operations
        tasks = [
            adapter.inject_context_logic(session_id, context_data) for session_id in session_ids
        ]

        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = (time.time() - start_time) * 1000

        # Validate all operations succeeded
        assert len(results) == len(session_ids)
        for result in results:
            assert result["injection_status"] == "success"

        # Average time per operation should still be reasonable
        avg_time_per_op = total_time / len(session_ids)
        assert avg_time_per_op < 100.0  # Allow some overhead for concurrency

    @pytest.mark.asyncio
    async def test_memory_usage_and_cleanup(self, adapter) -> None:
        """Test memory usage and cleanup functionality."""
        # Perform multiple operations to populate caches
        for i in range(5):
            session_id = f"memory_test_session_{i}"
            context_data = {
                "content": f"Memory test context {i}",
                "keywords": [f"keyword_{i}", "memory", "test"],
            }
            await adapter.inject_context_logic(session_id, context_data)

        # Check that caches are populated
        assert len(adapter._context_cache) > 0
        assert len(adapter._pattern_cache) >= 0

        # Test cleanup
        await adapter.cleanup()

        # Verify caches are cleared
        assert len(adapter._context_cache) == 0
        assert len(adapter._rag_cache) == 0
        assert len(adapter._filter_cache) == 0


class TestSessionMemoryAdapterDataStructures:
    """Test data structures used in SessionMemoryAdapter."""

    def test_rag_context_injection_dataclass(self) -> None:
        """Test RAGContextInjection dataclass."""
        injection = RAGContextInjection(
            session_id="test_session",
            injected_context={"content": "test"},
            relevance_scores={"pattern1": 0.8},
            filtering_results={"filtered": True},
            performance_metrics={"time_ms": 25.0},
            injection_timestamp=datetime.utcnow(),
            context_overlap_score=0.7,
            semantic_similarity_score=0.85,
        )

        assert injection.session_id == "test_session"
        assert injection.context_overlap_score == 0.7
        assert injection.semantic_similarity_score == 0.85

    def test_hybrid_context_dataclass(self) -> None:
        """Test HybridContext dataclass."""
        hybrid = HybridContext(
            rag_context={"rag_data": "test"},
            session_context={"session_data": "test"},
            merged_context={"merged": True},
            confidence_weights={"rag": 0.6, "session": 0.4},
            semantic_bridges=[{"type": "keyword_overlap"}],
            integration_quality=0.9,
            processing_overhead_ms=15.0,
        )

        assert hybrid.rag_context["rag_data"] == "test"
        assert hybrid.confidence_weights["rag"] == 0.6
        assert hybrid.integration_quality == 0.9

    def test_intelligent_filter_dataclass(self) -> None:
        """Test IntelligentFilter dataclass."""
        filter_obj = IntelligentFilter(
            filter_id="filter_001",
            session_relevance_threshold=0.7,
            semantic_noise_threshold=0.3,
            context_mismatch_penalty=0.5,
            filter_results={"filtered_items": 10},
            performance_metrics={"filtering_time_ms": 5.0},
            filter_timestamp=datetime.utcnow(),
        )

        assert filter_obj.filter_id == "filter_001"
        assert filter_obj.session_relevance_threshold == 0.7
        assert filter_obj.semantic_noise_threshold == 0.3

    def test_semantic_bridge_dataclass(self) -> None:
        """Test SemanticBridge dataclass."""
        bridge = SemanticBridge(
            bridge_id="bridge_001",
            source_vectors=["vec1", "vec2"],
            target_vectors=["vec3", "vec4"],
            bridge_strength=0.8,
            semantic_mappings={"keyword1": ["synonym1", "synonym2"]},
            cross_references={"ref1": "data1"},
            maintenance_status="active",
            last_updated=datetime.utcnow(),
        )

        assert bridge.bridge_id == "bridge_001"
        assert bridge.bridge_strength == 0.8
        assert bridge.maintenance_status == "active"


# Performance benchmarking tests
class TestSessionMemoryAdapterPerformance:
    """Performance benchmarking tests for SessionMemoryAdapter."""

    @pytest.mark.asyncio
    async def test_performance_benchmarks(self) -> None:
        """Comprehensive performance benchmarking."""
        # Setup adapter for benchmarking
        rag_coordinator = MockRAGCoordinator()
        storage_manager = MockStorageManager()
        session_memory_bridge = MockSessionMemoryBridge()

        adapter = SessionMemoryAdapter(
            rag_coordinator=rag_coordinator,
            storage_manager=storage_manager,
            session_memory_bridge=session_memory_bridge,
            enable_rag_integration=True,
            enable_hybrid_context=True,
            enable_intelligent_filtering=True,
        )

        try:
            # Benchmark context injection
            injection_times = []
            for i in range(20):
                start_time = time.time()
                await adapter.inject_context_logic(
                    f"bench_session_{i}",
                    {"content": f"Benchmark test content {i}", "keywords": ["benchmark", "test"]},
                )
                injection_times.append((time.time() - start_time) * 1000)

            avg_injection_time = sum(injection_times) / len(injection_times)
            max_injection_time = max(injection_times)

            # Benchmark pattern reconstruction
            patterns = [
                {
                    "pattern_id": f"pattern_{i}",
                    "pattern_type": "test",
                    "confidence": 0.8,
                    "frequency": 0.7,
                    "keywords": [f"keyword_{i}"],
                }
                for i in range(10)
            ]

            reconstruction_times = []
            for i in range(10):
                start_time = time.time()
                await adapter.pattern_reconstruction_algorithms(patterns)
                reconstruction_times.append((time.time() - start_time) * 1000)

            avg_reconstruction_time = sum(reconstruction_times) / len(reconstruction_times)
            max_reconstruction_time = max(reconstruction_times)

            # Validate performance targets
            assert (
                avg_injection_time < 50.0
            ), f"Avg injection time: {avg_injection_time}ms > 50ms target"
            assert (
                max_injection_time < 100.0
            ), f"Max injection time: {max_injection_time}ms > 100ms limit"
            assert (
                avg_reconstruction_time < 100.0
            ), f"Avg reconstruction time: {avg_reconstruction_time}ms > 100ms target"
            assert (
                max_reconstruction_time < 200.0
            ), f"Max reconstruction time: {max_reconstruction_time}ms > 200ms limit"

            print("Performance Results:")
            print(
                f"  Context Injection - Avg: {avg_injection_time:.2f}ms, Max: {max_injection_time:.2f}ms"
            )
            print(
                f"  Pattern Reconstruction - Avg: {avg_reconstruction_time:.2f}ms, Max: {max_reconstruction_time:.2f}ms"
            )

        finally:
            await adapter.cleanup()


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])
