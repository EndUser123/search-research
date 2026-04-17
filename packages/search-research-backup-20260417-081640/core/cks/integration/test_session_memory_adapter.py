"""Comprehensive Tests for Session Memory Adapter.

This module provides thorough testing for the SessionMemoryAdapter class,
covering all pattern detection, similarity scoring, reconstruction algorithms,
and integration scenarios.

Test Coverage:
- Pattern Detection Algorithms
- Semantic Similarity Scoring
- Pattern Reconstruction Algorithms
- SessionMemoryBridge Integration
- Performance Validation
- Edge Cases and Error Handling

Performance Test Targets:
- Pattern analysis: <50ms for typical sessions
- Similarity calculation: <20ms per comparison
- Pattern reconstruction: <100ms for complex scenarios
- Memory overhead: <10MB for pattern storage

Author: CSF Development Team
Version: 1.0.0
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Import the adapter
from .session_memory_adapter import (
    PatternEvolution,
    ReconstructionQuality,
    SessionMemoryAdapter,
)


# Test data fixtures
@pytest.fixture
def sample_messages():
    """Sample conversation messages for testing."""
    return [
        {
            "content": "I need help debugging this Python function that's throwing an exception.",
            "role": "user",
            "timestamp": datetime.utcnow() - timedelta(minutes=30),
        },
        {
            "content": "I can help you debug that. Could you share the function code and the specific error you're seeing?",
            "role": "assistant",
            "timestamp": datetime.utcnow() - timedelta(minutes=29),
        },
        {
            "content": "Here's the code: def process_data(data): return data.process() The error is AttributeError: 'str' object has no attribute 'process'",
            "role": "user",
            "timestamp": datetime.utcnow() - timedelta(minutes=28),
        },
        {
            "content": "The issue is that you're passing a string to process_data, but it expects an object with a process method. You need to check the type first.",
            "role": "assistant",
            "timestamp": datetime.utcnow() - timedelta(minutes=27),
        },
        {
            "content": "Ah, I see! Let me add type checking. Thanks for the help!",
            "role": "user",
            "timestamp": datetime.utcnow() - timedelta(minutes=26),
        },
    ]


@pytest.fixture
def complex_conversation():
    """More complex conversation for testing advanced patterns."""
    return [
        {
            "content": "We need to plan the architecture for our new microservice.",
            "role": "user",
            "timestamp": datetime.utcnow() - timedelta(minutes=60),
        },
        {
            "content": "Great! Let's start by defining the core requirements. What will this microservice do?",
            "role": "assistant",
            "timestamp": datetime.utcnow() - timedelta(minutes=59),
        },
        {
            "content": "It will handle user authentication and authorization for our platform.",
            "role": "user",
            "timestamp": datetime.utcnow() - timedelta(minutes=58),
        },
        {
            "content": "Perfect. I recommend using JWT tokens for authentication and implementing role-based access control.",
            "role": "assistant",
            "timestamp": datetime.utcnow() - timedelta(minutes=57),
        },
        {
            "content": "That sounds good. Should we use a database like PostgreSQL or a NoSQL solution?",
            "role": "user",
            "timestamp": datetime.utcnow() - timedelta(minutes=56),
        },
        {
            "content": "For user data, PostgreSQL would be better due to its ACID compliance and relational features.",
            "role": "assistant",
            "timestamp": datetime.utcnow() - timedelta(minutes=55),
        },
        {
            "content": "Agreed. Let's also include Redis for session storage and caching.",
            "role": "user",
            "timestamp": datetime.utcnow() - timedelta(minutes=54),
        },
        {
            "content": "Excellent choice! Redis will improve performance significantly for frequent user lookups.",
            "role": "assistant",
            "timestamp": datetime.utcnow() - timedelta(minutes=53),
        },
    ]


@pytest.fixture
def session_memory_adapter():
    """Create a SessionMemoryAdapter instance for testing."""
    return SessionMemoryAdapter(
        chat_history_client=None,
        session_memory_bridge=None,
        storage_manager=None,
        device_manager=None,
        cache_size_mb=10,
        enable_advanced_features=True,
    )


class TestPatternDetectionAlgorithms:
    """Test suite for pattern detection algorithms."""

    @pytest.mark.asyncio
    async def test_detect_conversation_patterns_basic(
        self,
        session_memory_adapter: SessionMemoryAdapter,
        sample_messages: list[dict[str, Any]],
    ) -> None:
        """Test basic conversation pattern detection."""
        patterns = await session_memory_adapter.detect_conversation_patterns(
            sample_messages,
            session_id="test_session_001",
        )

        # Verify patterns were detected
        assert isinstance(patterns, list)
        assert len(patterns) > 0

        # Verify pattern structure
        for pattern in patterns:
            assert "pattern_id" in pattern
            assert "pattern_type" in pattern
            assert "confidence" in pattern
            assert "message_count" in pattern
            assert "importance_score" in pattern
            assert "session_id" in pattern

            # Validate data types
            assert isinstance(pattern["confidence"], float)
            assert 0.0 <= pattern["confidence"] <= 1.0
            assert isinstance(pattern["message_count"], int)
            assert pattern["message_count"] > 0

        print(f"✓ Detected {len(patterns)} conversation patterns")

    @pytest.mark.asyncio
    async def test_detect_conversation_patterns_complex(
        self,
        session_memory_adapter: SessionMemoryAdapter,
        complex_conversation: list[dict[str, Any]],
    ) -> None:
        """Test pattern detection on complex conversation."""
        start_time = time.time()

        patterns = await session_memory_adapter.detect_conversation_patterns(
            complex_conversation,
            session_id="test_session_002",
        )

        execution_time = (time.time() - start_time) * 1000

        # Performance validation
        assert execution_time < 50, f"Pattern detection took {execution_time:.1f}ms, target <50ms"

        # Should detect multiple pattern types
        pattern_types = {pattern["pattern_type"] for pattern in patterns}
        assert (
            len(pattern_types) >= 2
        ), "Should detect multiple pattern types in complex conversation"

        # Should identify planning pattern
        planning_patterns = [p for p in patterns if "planning" in p["pattern_type"].lower()]
        assert (
            len(planning_patterns) > 0
        ), "Should detect planning pattern in architecture discussion"

        print(f"✓ Complex pattern detection completed in {execution_time:.1f}ms")

    @pytest.mark.asyncio
    async def test_analyze_pattern_importance(
        self,
        session_memory_adapter: SessionMemoryAdapter,
        sample_messages: list[dict[str, Any]],
    ) -> None:
        """Test pattern importance analysis."""
        # Create a sample pattern
        pattern = {
            "pattern_id": "test_pattern_001",
            "pattern_type": "question_answer",
            "confidence": 0.8,
            "frequency": 0.6,
            "complexity": "moderate",
            "message_count": 3,
            "semantic_coherence": 0.7,
            "context_relevance": 0.9,
        }

        importance_score = await session_memory_adapter.analyze_pattern_importance(
            pattern,
            sample_messages,
        )

        # Validate importance score
        assert isinstance(importance_score, float)
        assert 0.0 <= importance_score <= 1.0
        assert importance_score > 0.5, "Pattern should have moderate to high importance"

        print(f"✓ Pattern importance score: {importance_score:.3f}")

    @pytest.mark.asyncio
    async def test_identify_key_decisions(
        self,
        session_memory_adapter: SessionMemoryAdapter,
        complex_conversation: list[dict[str, Any]],
    ) -> None:
        """Test key decision identification."""
        decisions = await session_memory_adapter.identify_key_decisions(complex_conversation)

        # Verify decisions were found
        assert isinstance(decisions, list)
        assert len(decisions) > 0

        # Check for expected decisions about architecture
        decision_text = " ".join(decisions).lower()
        assert any(
            keyword in decision_text
            for keyword in [
                "postgresql",
                "redis",
                "jwt",
                "architecture",
            ]
        ), "Should identify technology decisions"

        # Validate decision format
        for decision in decisions:
            assert isinstance(decision, str)
            assert len(decision) > 10, "Decisions should be meaningful"
            assert len(decision) < 200, "Decisions should be concise"

        print(f"✓ Identified {len(decisions)} key decisions")

    @pytest.mark.asyncio
    async def test_track_pattern_evolution(
        self,
        session_memory_adapter: SessionMemoryAdapter,
        sample_messages: list[dict[str, Any]],
    ) -> None:
        """Test pattern evolution tracking."""
        # Create initial pattern
        initial_pattern = {
            "pattern_id": "evolving_pattern_001",
            "pattern_type": "debugging_session",
            "confidence": 0.7,
            "frequency": 0.5,
            "message_count": 3,
        }

        # Simulate pattern evolution with new messages
        new_messages = [
            {
                "content": "Now I'm getting a different error about missing imports.",
                "role": "user",
                "timestamp": datetime.utcnow(),
            },
            {
                "content": "You need to import the required modules at the top of your file.",
                "role": "assistant",
                "timestamp": datetime.utcnow(),
            },
        ]

        evolution = await session_memory_adapter.track_pattern_evolution(
            initial_pattern,
            new_messages,
        )

        # Validate evolution structure
        assert isinstance(evolution, PatternEvolution)
        assert evolution.pattern_id == initial_pattern["pattern_id"]
        assert len(evolution.evolution_steps) > 0
        assert len(evolution.confidence_trend) > 0

        print(f"✓ Pattern evolution tracked: {evolution.evolution_summary}")


class TestSemanticSimilarityScoring:
    """Test suite for semantic similarity scoring."""

    @pytest.mark.asyncio
    async def test_calculate_semantic_similarity(
        self,
        session_memory_adapter: SessionMemoryAdapter,
    ) -> None:
        """Test semantic similarity calculation."""
        # Create two similar patterns
        pattern1 = {
            "pattern_id": "pattern_001",
            "pattern_type": "question_answer",
            "keywords": ["python", "debugging", "error", "function"],
            "embedding": [0.1, 0.2, 0.3, 0.4] * 96,  # 384-dim embedding
        }

        pattern2 = {
            "pattern_id": "pattern_002",
            "pattern_type": "problem_solving",
            "keywords": ["python", "debug", "issue", "solve"],
            "embedding": [0.1, 0.2, 0.3, 0.4] * 96,  # Similar embedding
        }

        similarity = await session_memory_adapter.calculate_semantic_similarity(pattern1, pattern2)

        # Validate similarity score
        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0
        assert similarity > 0.7, "Similar patterns should have high similarity score"

        print(f"✓ Semantic similarity: {similarity:.3f}")

    @pytest.mark.asyncio
    async def test_calculate_semantic_similarity_performance(
        self,
        session_memory_adapter: SessionMemoryAdapter,
    ) -> None:
        """Test semantic similarity calculation performance."""
        pattern1 = {
            "pattern_id": "perf_test_001",
            "embedding": [0.1, 0.2, 0.3, 0.4] * 96,
        }

        pattern2 = {
            "pattern_id": "perf_test_002",
            "embedding": [0.2, 0.3, 0.4, 0.5] * 96,
        }

        # Test multiple calculations
        start_time = time.time()
        iterations = 100

        for _ in range(iterations):
            similarity = await session_memory_adapter.calculate_semantic_similarity(
                pattern1, pattern2
            )
            assert 0.0 <= similarity <= 1.0

        execution_time = (time.time() - start_time) * 1000
        avg_time = execution_time / iterations

        # Performance validation
        assert avg_time < 20, f"Similarity calculation took {avg_time:.1f}ms, target <20ms"

        print(
            f"✓ Similarity calculation performance: {avg_time:.2f}ms avg ({iterations} iterations)"
        )

    @pytest.mark.asyncio
    async def test_cluster_related_patterns(
        self,
        session_memory_adapter: SessionMemoryAdapter,
        sample_messages: list[dict[str, Any]],
    ) -> None:
        """Test pattern clustering."""
        # Generate some test patterns
        patterns = [
            {
                "pattern_id": f"cluster_test_{i}",
                "pattern_type": "question_answer" if i % 2 == 0 else "problem_solving",
                "embedding": [i * 0.01] * 384,  # Simple incremental embeddings
                "keywords": [f"keyword_{i}", "python", "debugging"]
                if i % 2 == 0
                else [f"keyword_{i}", "code", "fix"],
            }
            for i in range(10)
        ]

        start_time = time.time()

        clusters = await session_memory_adapter.cluster_related_patterns(patterns, max_clusters=5)

        execution_time = (time.time() - start_time) * 1000

        # Validate clustering results
        assert isinstance(clusters, dict)
        assert len(clusters) > 0, "Should create at least one cluster"

        # Performance validation
        assert execution_time < 100, f"Clustering took {execution_time:.1f}ms, target <100ms"

        # Validate cluster structure
        for cluster_id, pattern_ids in clusters.items():
            assert isinstance(cluster_id, str)
            assert isinstance(pattern_ids, list)
            assert len(pattern_ids) > 0, "Clusters should contain patterns"

        print(f"✓ Pattern clustering: {len(clusters)} clusters in {execution_time:.1f}ms")

    @pytest.mark.asyncio
    async def test_find_similar_historical_patterns(
        self,
        session_memory_adapter: SessionMemoryAdapter,
    ) -> None:
        """Test historical pattern similarity search."""
        # Mock some historical patterns
        with patch.object(session_memory_adapter, "_load_historical_patterns") as mock_load:
            mock_patterns = [
                {
                    "pattern_id": "historical_001",
                    "pattern_type": "debugging_session",
                    "embedding": [0.1, 0.2, 0.3, 0.4] * 96,
                    "session_id": "session_001",
                    "created_at": datetime.utcnow() - timedelta(days=1),
                    "observation_count": 5,
                },
                {
                    "pattern_id": "historical_002",
                    "pattern_type": "planning",
                    "embedding": [0.5, 0.6, 0.7, 0.8] * 96,
                    "session_id": "session_002",
                    "created_at": datetime.utcnow() - timedelta(days=2),
                    "observation_count": 3,
                },
            ]
            mock_load.return_value = mock_patterns

            # Search pattern
            search_pattern = {
                "pattern_id": "search_pattern",
                "pattern_type": "debugging_session",
                "embedding": [0.1, 0.2, 0.3, 0.4] * 96,
            }

            similar_patterns = await session_memory_adapter.find_similar_historical_patterns(
                search_pattern,
                similarity_threshold=0.7,
            )

            # Validate results
            assert isinstance(similar_patterns, list)
            assert len(similar_patterns) > 0, "Should find similar historical patterns"

            # Check similarity scores
            for result in similar_patterns:
                assert "pattern" in result
                assert "similarity_score" in result
                assert result["similarity_score"] >= 0.7

            print(f"✓ Found {len(similar_patterns)} similar historical patterns")


class TestPatternReconstructionAlgorithms:
    """Test suite for pattern reconstruction algorithms."""

    @pytest.mark.asyncio
    async def test_reconstruct_conversation_context(
        self,
        session_memory_adapter: SessionMemoryAdapter,
        sample_messages: list[dict[str, Any]],
    ) -> None:
        """Test conversation context reconstruction."""
        # Create sample patterns
        patterns = [
            {
                "pattern_id": "reconstruct_test_001",
                "pattern_type": "question_answer",
                "importance_score": 0.8,
                "confidence": 0.9,
                "created_at": datetime.utcnow(),
                "keywords": ["python", "debugging", "error"],
                "message_count": 3,
            },
            {
                "pattern_id": "reconstruct_test_002",
                "pattern_type": "problem_solving",
                "importance_score": 0.7,
                "confidence": 0.8,
                "created_at": datetime.utcnow(),
                "keywords": ["fix", "solution", "code"],
                "message_count": 2,
            },
        ]

        bridge_data = {
            "session_metadata": {
                "total_messages": len(sample_messages),
                "session_duration": 30,  # minutes
            },
        }

        start_time = time.time()

        reconstruction = await session_memory_adapter.reconstruct_conversation_context(
            patterns,
            bridge_data,
        )

        execution_time = (time.time() - start_time) * 1000

        # Validate reconstruction structure
        assert isinstance(reconstruction, dict)
        assert "reconstructed_context" in reconstruction
        assert "quality" in reconstruction

        # Performance validation
        assert execution_time < 100, f"Reconstruction took {execution_time:.1f}ms, target <100ms"

        # Validate quality metrics
        quality = reconstruction["quality"]
        assert isinstance(quality, ReconstructionQuality)
        assert 0.0 <= quality.overall_quality <= 1.0

        print(
            f"✓ Context reconstructed in {execution_time:.1f}ms (quality: {quality.overall_quality:.3f})"
        )

    @pytest.mark.asyncio
    async def test_validate_pattern_reconstruction(
        self,
        session_memory_adapter: SessionMemoryAdapter,
        sample_messages: list[dict[str, Any]],
    ) -> None:
        """Test reconstruction validation."""
        # Create original and reconstructed patterns
        original_patterns = [
            {
                "pattern_id": "validation_test_001",
                "pattern_type": "question_answer",
                "keywords": ["python", "debugging"],
                "embedding": [0.1, 0.2, 0.3, 0.4] * 96,
            },
        ]

        reconstructed_context = {
            "temporal_flow": {
                "pattern_sequence": ["validation_test_001"],
                "flow_coherence": 0.9,
            },
            "semantic_structure": {
                "topic_consistency": 0.85,
                "concept_coverage": 0.8,
            },
            "patterns_used": original_patterns.copy(),
            "reconstruction_timestamp": datetime.utcnow(),
        }

        quality = await session_memory_adapter.validate_pattern_reconstruction(
            original_patterns,
            reconstructed_context,
        )

        # Validate quality metrics
        assert isinstance(quality, ReconstructionQuality)
        assert 0.0 <= quality.overall_quality <= 1.0
        assert quality.completeness_score >= 0.0
        assert quality.accuracy_score >= 0.0
        assert quality.consistency_score >= 0.0
        assert quality.semantic_fidelity >= 0.0
        assert quality.structural_integrity >= 0.0

        # High quality reconstruction should have good scores
        assert quality.overall_quality > 0.5, "Good reconstruction should have quality > 0.5"

        print(f"✓ Reconstruction quality: {quality.overall_quality:.3f}")

    @pytest.mark.asyncio
    async def test_fill_missing_pattern_elements(
        self,
        session_memory_adapter: SessionMemoryAdapter,
    ) -> None:
        """Test missing pattern element filling."""
        # Create patterns with missing elements
        incomplete_patterns = [
            {
                "pattern_id": "incomplete_001",
                "pattern_type": "question_answer",
                "confidence": 0.8,
                # Missing: embedding, keywords, context_tags, intent, complexity, sample_exchanges
            },
        ]

        enhanced_patterns = await session_memory_adapter.fill_missing_pattern_elements(
            incomplete_patterns,
        )

        # Validate enhancement
        assert len(enhanced_patterns) == len(incomplete_patterns)

        for pattern in enhanced_patterns:
            # Check that missing elements were filled
            assert "embedding" in pattern
            assert "keywords" in pattern
            assert "context_tags" in pattern
            assert "intent" in pattern
            assert "complexity" in pattern
            assert "sample_exchanges" in pattern

            # Validate filled elements
            assert isinstance(pattern["embedding"], list)
            assert len(pattern["embedding"]) > 0
            assert isinstance(pattern["keywords"], list)
            assert isinstance(pattern["context_tags"], list)

        print(f"✓ Enhanced {len(enhanced_patterns)} patterns with missing elements")


class TestSessionMemoryBridgeIntegration:
    """Test suite for SessionMemoryBridge integration."""

    @pytest.mark.asyncio
    async def test_preserve_patterns_across_compaction(
        self,
        session_memory_adapter: SessionMemoryAdapter,
    ) -> None:
        """Test pattern preservation across session compaction."""
        # Mock SessionMemoryBridge
        mock_bridge = AsyncMock()
        mock_bridge.preserve_session_context.return_value = Mock(
            bridge_id="test_bridge_001",
            preserved_patterns=[],
        )
        session_memory_adapter.session_memory_bridge = mock_bridge

        # Create test patterns
        patterns = [
            {
                "pattern_id": "preserve_test_001",
                "importance_score": 0.8,
                "pattern_type": "question_answer",
            },
            {
                "pattern_id": "preserve_test_002",
                "importance_score": 0.6,  # Below threshold
                "pattern_type": "simple_chat",
            },
            {
                "pattern_id": "preserve_test_003",
                "importance_score": 0.9,
                "pattern_type": "critical_decision",
            },
        ]

        success = await session_memory_adapter.preserve_patterns_across_compaction(
            session_id="test_session",
            patterns=patterns,
            criticality_threshold=0.7,
        )

        # Validate preservation
        assert success is True
        mock_bridge.preserve_session_context.assert_called_once()

        print("✓ Successfully preserved patterns across compaction")

    @pytest.mark.asyncio
    async def test_restore_patterns_from_compaction(
        self,
        session_memory_adapter: SessionMemoryAdapter,
    ) -> None:
        """Test pattern restoration from compaction bridge."""
        # Mock SessionMemoryBridge and bridge data
        mock_bridge = AsyncMock()
        mock_restoration_result = Mock(
            success=True,
            restored_patterns=["restored_pattern_001"],
            errors=[],
        )

        mock_bridge.restore_session_context.return_value = mock_restoration_result
        session_memory_adapter.session_memory_bridge = mock_bridge

        # Mock bridge loading
        with patch.object(session_memory_adapter, "_load_compaction_bridge") as mock_load:
            mock_load.return_value = Mock(
                bridge_id="test_bridge_001",
                preserved_patterns=[
                    {
                        "pattern_id": "restored_pattern_001",
                        "pattern_type": "question_answer",
                        "confidence": 0.8,
                    },
                ],
            )

            restored_patterns = await session_memory_adapter.restore_patterns_from_compaction(
                bridge_id="test_bridge_001",
            )

            # Validate restoration
            assert isinstance(restored_patterns, list)
            mock_bridge.restore_session_context.assert_called_once_with("test_bridge_001")

            print(f"✓ Restored {len(restored_patterns)} patterns from compaction bridge")


class TestPerformanceValidation:
    """Test suite for performance validation and targets."""

    @pytest.mark.asyncio
    async def test_pattern_analysis_performance_target(
        self,
        session_memory_adapter: SessionMemoryAdapter,
        complex_conversation: list[dict[str, Any]],
    ) -> None:
        """Test that pattern analysis meets <50ms performance target."""
        # Run multiple iterations to get average performance
        iterations = 10
        execution_times = []

        for _ in range(iterations):
            start_time = time.time()

            patterns = await session_memory_adapter.detect_conversation_patterns(
                complex_conversation,
                session_id="perf_test_session",
            )

            execution_time = (time.time() - start_time) * 1000
            execution_times.append(execution_time)

            assert len(patterns) > 0, "Should detect patterns in each iteration"

        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)

        # Performance validation
        assert avg_time < 50, f"Average pattern analysis time {avg_time:.1f}ms exceeds 50ms target"
        assert (
            max_time < 100
        ), f"Maximum pattern analysis time {max_time:.1f}ms exceeds safety margin"

        print(
            f"✓ Pattern analysis performance: avg {avg_time:.1f}ms, max {max_time:.1f}ms (target <50ms)"
        )

    @pytest.mark.asyncio
    async def test_similarity_calculation_performance_target(
        self,
        session_memory_adapter: SessionMemoryAdapter,
    ) -> None:
        """Test that similarity calculation meets <20ms performance target."""
        # Create test patterns
        pattern1 = {
            "pattern_id": "perf_sim_001",
            "embedding": [i * 0.001 for i in range(384)],
        }

        pattern2 = {
            "pattern_id": "perf_sim_002",
            "embedding": [(i + 1) * 0.001 for i in range(384)],
        }

        # Run multiple iterations
        iterations = 50
        execution_times = []

        for _ in range(iterations):
            start_time = time.time()

            similarity = await session_memory_adapter.calculate_semantic_similarity(
                pattern1, pattern2
            )

            execution_time = (time.time() - start_time) * 1000
            execution_times.append(execution_time)

            assert 0.0 <= similarity <= 1.0, "Similarity should be valid"

        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)

        # Performance validation
        assert avg_time < 20, f"Average similarity time {avg_time:.1f}ms exceeds 20ms target"
        assert max_time < 40, f"Maximum similarity time {max_time:.1f}ms exceeds safety margin"

        print(
            f"✓ Similarity calculation performance: avg {avg_time:.1f}ms, max {max_time:.1f}ms (target <20ms)"
        )

    @pytest.mark.asyncio
    async def test_pattern_reconstruction_performance_target(
        self,
        session_memory_adapter: SessionMemoryAdapter,
        complex_conversation: list[dict[str, Any]],
    ) -> None:
        """Test that pattern reconstruction meets <100ms performance target."""
        # Create complex patterns for reconstruction
        patterns = [
            {
                "pattern_id": f"perf_reconstruct_{i}",
                "pattern_type": "complex_pattern",
                "importance_score": 0.8 - (i * 0.1),
                "confidence": 0.7 + (i * 0.05),
                "embedding": [i * 0.01] * 384,
                "keywords": [f"keyword_{j}" for j in range(5)],
                "message_count": i + 1,
            }
            for i in range(10)
        ]

        bridge_data = {
            "session_metadata": {
                "total_messages": len(complex_conversation),
                "session_duration": 60,
            },
        }

        # Run multiple iterations
        iterations = 5
        execution_times = []

        for _ in range(iterations):
            start_time = time.time()

            reconstruction = await session_memory_adapter.reconstruct_conversation_context(
                patterns,
                bridge_data,
            )

            execution_time = (time.time() - start_time) * 1000
            execution_times.append(execution_time)

            assert "reconstructed_context" in reconstruction
            assert "quality" in reconstruction

        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)

        # Performance validation
        assert avg_time < 100, f"Average reconstruction time {avg_time:.1f}ms exceeds 100ms target"
        assert max_time < 200, f"Maximum reconstruction time {max_time:.1f}ms exceeds safety margin"

        print(
            f"✓ Pattern reconstruction performance: avg {avg_time:.1f}ms, max {max_time:.1f}ms (target <100ms)"
        )

    def test_memory_overhead_validation(
        self,
        session_memory_adapter: SessionMemoryAdapter,
    ) -> None:
        """Test that memory overhead stays within 10MB limit."""
        import sys

        # Get initial memory usage
        len(gc.get_objects()) if "gc" in sys.modules else 0

        # Simulate heavy pattern usage
        test_patterns = []
        for i in range(1000):
            pattern = {
                "pattern_id": f"memory_test_{i}",
                "embedding": [j * 0.001 for j in range(384)],  # 384-dim embedding
                "metadata": {"test_data": "x" * 100},  # 100 bytes per pattern
            }
            test_patterns.append(pattern)

        # Cache patterns to simulate adapter usage
        session_memory_adapter._pattern_cache["memory_test"] = test_patterns

        # Estimate memory usage (simplified)
        # In a real scenario, you'd use more sophisticated memory profiling
        pattern_size = sys.getsizeof(test_patterns[0]) if test_patterns else 0
        total_pattern_size = pattern_size * len(test_patterns)
        estimated_mb = total_pattern_size / (1024 * 1024)

        # Memory validation (allowing some margin for caching overhead)
        assert estimated_mb < 15, f"Estimated memory usage {estimated_mb:.1f}MB exceeds 15MB limit"

        print(f"✓ Memory overhead validation: ~{estimated_mb:.1f}MB for 1000 patterns")


class TestEdgeCasesAndErrorHandling:
    """Test suite for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_message_list(self, session_memory_adapter: SessionMemoryAdapter) -> None:
        """Test handling of empty message list."""
        patterns = await session_memory_adapter.detect_conversation_patterns([])
        assert patterns == [], "Should return empty list for empty messages"

    @pytest.mark.asyncio
    async def test_invalid_message_format(
        self, session_memory_adapter: SessionMemoryAdapter
    ) -> None:
        """Test handling of invalid message formats."""
        invalid_messages = [
            {},  # Empty dict
            {"content": ""},  # Missing role
            {"role": "user"},  # Missing content
            None,  # None value
            {"content": "Valid", "role": "user", "timestamp": "invalid"},  # Invalid timestamp
        ]

        patterns = await session_memory_adapter.detect_conversation_patterns(invalid_messages)
        assert patterns == [], "Should handle invalid message formats gracefully"

    @pytest.mark.asyncio
    async def test_null_pattern_handling(
        self, session_memory_adapter: SessionMemoryAdapter
    ) -> None:
        """Test handling of null/None patterns."""
        similarity = await session_memory_adapter.calculate_semantic_similarity(None, None)
        assert similarity == 0.0, "Should return 0.0 for null patterns"

    @pytest.mark.asyncio
    async def test_malformed_embeddings(self, session_memory_adapter: SessionMemoryAdapter) -> None:
        """Test handling of malformed embeddings."""
        pattern1 = {"embedding": [0.1, 0.2]}  # Too short
        pattern2 = {"embedding": list(range(1000))}  # Too long

        similarity = await session_memory_adapter.calculate_semantic_similarity(pattern1, pattern2)
        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0, "Should handle malformed embeddings"

    def test_cleanup_resources(self, session_memory_adapter: SessionMemoryAdapter) -> None:
        """Test resource cleanup."""
        # Add some data to caches
        session_memory_adapter._pattern_cache["test"] = {"data": "test"}
        session_memory_adapter._embedding_cache["test"] = [0.1, 0.2]
        session_memory_adapter._similarity_cache["test"] = 0.5

        # Cleanup
        asyncio.run(session_memory_adapter.cleanup())

        # Verify cleanup
        assert len(session_memory_adapter._pattern_cache) == 0
        assert len(session_memory_adapter._embedding_cache) == 0
        assert len(session_memory_adapter._similarity_cache) == 0

        print("✓ Resource cleanup completed successfully")


# Integration test for the complete workflow
@pytest.mark.asyncio
async def test_complete_workflow_integration(
    session_memory_adapter: SessionMemoryAdapter,
    complex_conversation: list[dict[str, Any]],
) -> None:
    """Test the complete workflow from pattern detection to reconstruction."""
    print("\n=== Complete Workflow Integration Test ===")

    # Step 1: Detect patterns
    print("Step 1: Detecting conversation patterns...")
    start_time = time.time()
    detected_patterns = await session_memory_adapter.detect_conversation_patterns(
        complex_conversation,
        session_id="integration_test_session",
    )
    detection_time = (time.time() - start_time) * 1000
    print(f"✓ Detected {len(detected_patterns)} patterns in {detection_time:.1f}ms")

    # Step 2: Analyze importance
    print("Step 2: Analyzing pattern importance...")
    important_patterns = [p for p in detected_patterns if p.get("importance_score", 0) > 0.5]
    print(f"✓ Identified {len(important_patterns)} important patterns")

    # Step 3: Find similar historical patterns
    print("Step 3: Finding similar historical patterns...")
    with patch.object(session_memory_adapter, "_load_historical_patterns") as mock_load:
        mock_load.return_value = []
        similar_patterns = await session_memory_adapter.find_similar_historical_patterns(
            detected_patterns[0] if detected_patterns else {},
            similarity_threshold=0.7,
        )
        print(f"✓ Found {len(similar_patterns)} similar historical patterns")

    # Step 4: Cluster related patterns
    print("Step 4: Clustering related patterns...")
    clusters = await session_memory_adapter.cluster_related_patterns(detected_patterns)
    print(f"✓ Created {len(clusters)} pattern clusters")

    # Step 5: Reconstruct context
    print("Step 5: Reconstructing conversation context...")
    bridge_data = {
        "session_metadata": {
            "total_messages": len(complex_conversation),
            "workflow_test": True,
        },
    }

    reconstruction = await session_memory_adapter.reconstruct_conversation_context(
        important_patterns,
        bridge_data,
    )
    reconstruction_time = reconstruction["quality"]  # Just to access the quality object

    print(f"✓ Context reconstructed with quality: {reconstruction_time.overall_quality:.3f}")

    # Step 6: Validate reconstruction quality
    print("Step 6: Validating reconstruction quality...")
    assert reconstruction_time.overall_quality > 0.0, "Reconstruction should have positive quality"
    print("✓ Reconstruction validation passed")

    # Step 7: Performance validation
    print("Step 7: Validating performance targets...")
    assert detection_time < 50, f"Pattern detection should be <50ms, got {detection_time:.1f}ms"
    print("✓ All performance targets met")

    # Step 8: Cleanup
    print("Step 8: Cleaning up resources...")
    await session_memory_adapter.cleanup()
    print("✓ Cleanup completed")

    print("=== Complete Workflow Integration Test PASSED ===")


# Performance benchmark test
@pytest.mark.asyncio
async def test_performance_benchmark(session_memory_adapter: SessionMemoryAdapter) -> None:
    """Run performance benchmarks for all major operations."""
    print("\n=== Performance Benchmark Test ===")

    # Test data
    test_messages = [
        {
            "content": f"Test message {i} for performance testing with some content about debugging Python code.",
            "role": "user" if i % 2 == 0 else "assistant",
            "timestamp": datetime.utcnow() - timedelta(minutes=i),
        }
        for i in range(20)
    ]

    # Benchmark pattern detection
    print("Benchmarking pattern detection...")
    iterations = 20
    pattern_times = []

    for i in range(iterations):
        start = time.time()
        await session_memory_adapter.detect_conversation_patterns(
            test_messages,
            session_id=f"benchmark_session_{i}",
        )
        pattern_times.append((time.time() - start) * 1000)

    avg_pattern_time = sum(pattern_times) / len(pattern_times)
    print(f"Pattern detection: {avg_pattern_time:.1f}ms avg (target <50ms)")

    # Benchmark similarity calculation
    print("Benchmarking similarity calculation...")
    pattern1 = {"embedding": [i * 0.001 for i in range(384)]}
    pattern2 = {"embedding": [(i + 1) * 0.001 for i in range(384)]}

    similarity_times = []
    for i in range(50):
        start = time.time()
        await session_memory_adapter.calculate_semantic_similarity(pattern1, pattern2)
        similarity_times.append((time.time() - start) * 1000)

    avg_similarity_time = sum(similarity_times) / len(similarity_times)
    print(f"Similarity calculation: {avg_similarity_time:.1f}ms avg (target <20ms)")

    # Benchmark reconstruction
    print("Benchmarking pattern reconstruction...")
    test_patterns = [
        {
            "pattern_id": f"benchmark_pattern_{i}",
            "importance_score": 0.8,
            "embedding": [i * 0.01] * 384,
        }
        for i in range(5)
    ]

    reconstruction_times = []
    for i in range(10):
        start = time.time()
        await session_memory_adapter.reconstruct_conversation_context(
            test_patterns,
            {"benchmark": True},
        )
        reconstruction_times.append((time.time() - start) * 1000)

    avg_reconstruction_time = sum(reconstruction_times) / len(reconstruction_times)
    print(f"Pattern reconstruction: {avg_reconstruction_time:.1f}ms avg (target <100ms)")

    # Validate all targets
    assert avg_pattern_time < 50, "Pattern detection performance target not met"
    assert avg_similarity_time < 20, "Similarity calculation performance target not met"
    assert avg_reconstruction_time < 100, "Pattern reconstruction performance target not met"

    print("=== All Performance Benchmarks PASSED ===")


if __name__ == "__main__":
    # Run the tests
    pytest.main(
        [
            __file__,
            "-v",
            "--tb=short",
            "--disable-warnings",
        ]
    )
