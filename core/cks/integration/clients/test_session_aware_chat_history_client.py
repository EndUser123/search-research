"""Comprehensive tests for session-aware ChatHistoryClient functionality.

Tests cover:
- Session context indexing
- Cross-session query capabilities
- Conversation pattern preservation
- Session memory index functionality
- CKS vector store integration
- Session relevance analysis
- Performance targets
- Error handling and edge cases
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Import exception classes for error testing
from ..exceptions.integration_exceptions import ValidationException

# Import the classes we're testing
from .chat_history_client import (
    ChatHistoryClient,
    ChatMessage,
    IntegrationConfig,
    MessageRole,
    SecurityLevel,
    SessionContext,
    SessionContextType,
    SessionPattern,
)


class TestSessionAwareChatHistoryClient:
    """Test suite for session-aware ChatHistoryClient functionality."""

    @pytest.fixture
    def integration_config(self):
        """Create test integration configuration."""
        return IntegrationConfig(
            enabled=True,
            timeout_seconds=30,
            security_level=SecurityLevel.INTERNAL,
            enable_caching=True,
            metadata={
                "enable_session_awareness": True,
                "session_memory_enabled": True,
                "cross_session_queries": True,
                "pattern_preservation_enabled": True,
                "context_query_target_ms": 200,
                "pattern_accuracy_threshold": 0.85,
                "database_path": ":memory:",  # Use in-memory database for tests
            },
        )

    @pytest.fixture
    def sample_messages(self):
        """Create sample chat messages for testing."""
        return [
            ChatMessage(
                id="msg_001",
                conversation_id="session_debug_001",
                role=MessageRole.USER,
                content="I'm having issues with a Python function that's throwing an exception",
                timestamp=datetime.utcnow() - timedelta(minutes=10),
                metadata={"language": "python", "type": "debugging"},
            ),
            ChatMessage(
                id="msg_002",
                conversation_id="session_debug_001",
                role=MessageRole.ASSISTANT,
                content="I can help you debug that. Could you share the function code and the specific error?",
                timestamp=datetime.utcnow() - timedelta(minutes=8),
                metadata={"type": "debugging_help"},
            ),
            ChatMessage(
                id="msg_003",
                conversation_id="session_debug_001",
                role=MessageRole.USER,
                content="The function is supposed to parse JSON but it's failing on invalid input",
                timestamp=datetime.utcnow() - timedelta(minutes=5),
                metadata={"type": "debugging", "error_type": "json_parsing"},
            ),
        ]

    @pytest.fixture
    def sample_context_data(self, sample_messages):
        """Create sample session context data for testing."""
        return {
            "messages": sample_messages,
            "keywords": ["python", "debugging", "exception", "json", "parsing"],
            "context_type": "debugging",
            "importance_score": 0.8,
            "metadata": {
                "project": "data_processor",
                "user_role": "developer",
                "session_length_minutes": 15,
            },
        }

    @pytest.fixture
    async def chat_client(self, integration_config):
        """Create and initialize ChatHistoryClient for testing."""
        client = ChatHistoryClient(integration_config)
        success = await client.initialize()
        assert success, "ChatHistoryClient initialization failed"
        return client

    @pytest.mark.asyncio
    async def test_session_context_indexing_success(self, chat_client, sample_context_data) -> None:
        """Test successful session context indexing."""
        session_id = "test_session_001"

        # Index the session context
        result = await chat_client.session_context_indexing(session_id, sample_context_data)

        assert result is True, "Session context indexing should succeed"

        # Verify session context was stored
        assert session_id in chat_client._session_contexts, "Session context should be stored"
        context = chat_client._session_contexts[session_id]
        assert context.session_id == session_id, "Session ID should match"
        assert (
            context.context_type == SessionContextType.DEBUGGING
        ), "Context type should be DEBUGGING"
        assert len(context.keywords) > 0, "Keywords should be extracted"
        assert context.importance_score == 0.8, "Importance score should be preserved"

    @pytest.mark.asyncio
    async def test_session_context_indexing_validation(self, chat_client) -> None:
        """Test session context indexing validation."""
        # Test with empty session_id
        with pytest.raises(ValidationException):
            await chat_client.session_context_indexing("", {"test": "data"})

        # Test with empty context_data
        with pytest.raises(ValidationException):
            await chat_client.session_context_indexing("test_session", {})

    @pytest.mark.asyncio
    async def test_cross_session_context_query(self, chat_client, sample_messages) -> None:
        """Test cross-session context retrieval."""
        # First, index some sessions
        session_ids = ["debug_session", "arch_session", "review_session"]

        for i, session_id in enumerate(session_ids):
            context_data = {
                "messages": sample_messages,
                "keywords": [f"keyword_{i}", "python", "development"],
                "context_type": "active_work",
                "importance_score": 0.7,
            }
            await chat_client.session_context_indexing(session_id, context_data)

        # Query for relevant context
        results = await chat_client.get_cross_session_context("python development", max_results=5)

        assert isinstance(results, list), "Results should be a list"
        assert len(results) > 0, "Should find relevant messages"

        # Verify results contain the searched keywords
        for message in results:
            content_lower = message.content.lower()
            assert any(
                keyword in content_lower for keyword in ["python", "development"]
            ), "Results should contain searched keywords"

    @pytest.mark.asyncio
    async def test_cross_session_context_query_disabled(self, chat_client) -> None:
        """Test cross-session query when disabled."""
        chat_client.cross_session_queries = False

        results = await chat_client.get_cross_session_context("test query")
        assert results == [], "Should return empty list when cross-session queries disabled"

    @pytest.mark.asyncio
    async def test_create_session_memory_index(self, chat_client, sample_context_data) -> None:
        """Test session memory index creation."""
        session_id = "memory_index_test"

        # First index the session context
        await chat_client.session_context_indexing(session_id, sample_context_data)

        # Create comprehensive memory index
        result = await chat_client.create_session_memory_index(session_id)

        assert result is True, "Memory index creation should succeed"
        assert session_id in chat_client._session_indices, "Session index should be created"

        index = chat_client._session_indices[session_id]
        assert index.session_id == session_id, "Index session ID should match"
        assert isinstance(index.context_keywords, set), "Context keywords should be a set"
        assert len(index.context_keywords) > 0, "Should have indexed keywords"

    @pytest.mark.asyncio
    async def test_preserve_conversation_patterns(self, chat_client, sample_context_data) -> None:
        """Test conversation pattern preservation."""
        session_id = "pattern_test"

        # Index session with patterns
        await chat_client.session_context_indexing(session_id, sample_context_data)

        # Preserve patterns
        patterns = await chat_client.preserve_conversation_patterns(session_id)

        assert isinstance(patterns, list), "Patterns should be a list"

        if patterns:  # Only test if patterns were detected
            for pattern in patterns:
                assert isinstance(
                    pattern, SessionPattern
                ), "Pattern should be SessionPattern instance"
                assert pattern.session_id == session_id, "Pattern session ID should match"
                assert len(pattern.embedding) > 0, "Pattern should have embedding"
                assert (
                    pattern.confidence_score >= chat_client.pattern_accuracy_threshold
                ), "Pattern confidence should meet threshold"

    @pytest.mark.asyncio
    async def test_analyze_session_relevance(self, chat_client, sample_context_data) -> None:
        """Test session relevance analysis."""
        session_id = "relevance_test"

        # Index session first
        await chat_client.session_context_indexing(session_id, sample_context_data)

        # Analyze relevance of related content
        relevance_score = await chat_client.analyze_session_relevance("python debugging error")

        assert isinstance(relevance_score, float), "Relevance score should be float"
        assert 0.0 <= relevance_score <= 1.0, "Relevance score should be in valid range"

        # Analyze relevance of unrelated content
        unrelated_score = await chat_client.analyze_session_relevance("cooking recipe ingredients")
        assert unrelated_score <= relevance_score, "Unrelated content should have lower relevance"

    @pytest.mark.asyncio
    async def test_analyze_session_relevance_no_context(self, chat_client) -> None:
        """Test session relevance analysis with no indexed sessions."""
        relevance_score = await chat_client.analyze_session_relevance("test content")
        assert relevance_score == 0.0, "Should return 0.0 when no sessions are indexed"

    @pytest.mark.asyncio
    async def test_message_embedding_generation(self, chat_client, sample_messages) -> None:
        """Test message embedding generation."""
        embeddings = await chat_client._generate_message_embeddings(sample_messages)

        assert len(embeddings) == len(sample_messages), "Should generate embedding for each message"

        for embedding in embeddings:
            assert isinstance(embedding, list), "Embedding should be a list"
            assert len(embedding) == 384, "Embedding should have 384 dimensions"
            assert all(isinstance(x, float) for x in embedding), "Embedding values should be floats"

    @pytest.mark.asyncio
    async def test_text_embedding_generation(self, chat_client) -> None:
        """Test text embedding generation."""
        text = "This is a test sentence for embedding generation"
        embedding = await chat_client._generate_text_embedding(text)

        assert isinstance(embedding, list), "Embedding should be a list"
        assert len(embedding) == 384, "Embedding should have 384 dimensions"

        # Test empty text
        empty_embedding = await chat_client._generate_text_embedding("")
        assert empty_embedding == [], "Should return empty list for empty text"

    def test_cosine_similarity_calculation(self, chat_client) -> None:
        """Test cosine similarity calculation."""
        # Identical vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = chat_client._calculate_cosine_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 1e-10, "Identical vectors should have similarity 1.0"

        # Orthogonal vectors
        vec3 = [1.0, 0.0, 0.0]
        vec4 = [0.0, 1.0, 0.0]
        similarity = chat_client._calculate_cosine_similarity(vec3, vec4)
        assert abs(similarity - 0.0) < 1e-10, "Orthogonal vectors should have similarity 0.0"

        # Different length vectors should handle gracefully
        vec5 = [1.0, 0.0]
        vec6 = [1.0, 0.0, 0.0]
        similarity = chat_client._calculate_cosine_similarity(vec5, vec6)
        assert similarity == 0.0, "Different length vectors should return 0.0"

    def test_session_checksum_calculation(self, chat_client, sample_context_data) -> None:
        """Test session checksum calculation."""
        session_id = "checksum_test"
        context = SessionContext(
            session_id=session_id,
            context_type=SessionContextType.DEBUGGING,
            keywords=["test", "debugging"],
            timestamp=datetime.utcnow(),
            importance_score=0.8,
        )
        embeddings = [[0.1, 0.2, 0.3]]
        patterns = []

        checksum1 = chat_client._calculate_session_checksum(context, embeddings, patterns)
        checksum2 = chat_client._calculate_session_checksum(context, embeddings, patterns)

        assert checksum1 == checksum2, "Same data should produce same checksum"
        assert len(checksum1) == 64, "SHA-256 checksum should be 64 characters"
        assert all(c in "0123456789abcdef" for c in checksum1), "Should be valid hex string"

    @pytest.mark.asyncio
    async def test_fallback_embedding_storage(self, chat_client, sample_messages) -> None:
        """Test fallback embedding storage when CKS is not available."""
        chat_client._cks_storage = None  # Force fallback

        session_id = "fallback_test"
        embeddings = await chat_client._generate_message_embeddings(sample_messages)
        vector_ids = await chat_client._store_embeddings_fallback(
            session_id, embeddings, sample_messages
        )

        assert len(vector_ids) == len(sample_messages), "Should store all embeddings"
        assert hasattr(chat_client, "_fallback_embeddings"), "Should create fallback storage"

        # Verify stored data
        for vector_id in vector_ids:
            assert vector_id in chat_client._fallback_embeddings, "Vector ID should be stored"
            stored_data = chat_client._fallback_embeddings[vector_id]
            assert "embedding" in stored_data, "Should store embedding"
            assert "content" in stored_data, "Should store content"

    @pytest.mark.asyncio
    async def test_session_aware_components_initialization(self, integration_config) -> None:
        """Test session-aware components initialization."""
        # Mock the dependencies
        with (
            patch("chat_history_client.SESSION_MEMORY_AVAILABLE", False),
            patch("chat_history_client.CKS_STORAGE_AVAILABLE", False),
            patch("chat_history_client.PYTORCH_STORAGE_AVAILABLE", False),
        ):
            config = integration_config
            config.metadata["enable_session_awareness"] = True

            client = ChatHistoryClient(config)
            await client.initialize()

            # Components should be None when not available
            assert (
                client._session_memory_bridge is None
            ), "SessionMemoryBridge should be None when not available"
            assert client._cks_storage is None, "CKS storage should be None when not available"
            assert (
                client._device_manager is None
            ), "Device manager should be None when not available"

    @pytest.mark.asyncio
    async def test_performance_target_context_indexing(
        self, chat_client, sample_context_data
    ) -> None:
        """Test that session context indexing meets performance target (<100ms)."""
        session_id = "performance_test"

        # Measure execution time
        start_time = datetime.utcnow()
        result = await chat_client.session_context_indexing(session_id, sample_context_data)
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        assert result is True, "Indexing should succeed"
        assert (
            execution_time < 100
        ), f"Indexing should complete in <100ms, took {execution_time:.1f}ms"

    @pytest.mark.asyncio
    async def test_performance_target_cross_session_query(
        self, chat_client, sample_context_data
    ) -> None:
        """Test that cross-session queries meet performance target (<200ms)."""
        # Index multiple sessions
        for i in range(5):
            session_id = f"perf_test_{i}"
            await chat_client.session_context_indexing(session_id, sample_context_data)

        # Measure query time
        start_time = datetime.utcnow()
        results = await chat_client.get_cross_session_context("python debugging", max_results=10)
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        assert isinstance(results, list), "Should return list of results"
        assert (
            execution_time < chat_client.context_query_target_ms
        ), f"Query should complete in <{chat_client.context_query_target_ms}ms, took {execution_time:.1f}ms"

    @pytest.mark.asyncio
    async def test_cleanup_session_aware_components(self, chat_client) -> None:
        """Test cleanup of session-aware components."""
        # Add some session data
        session_id = "cleanup_test"
        context_data = {
            "messages": [],
            "keywords": ["test"],
            "context_type": "active_work",
        }
        await chat_client.session_context_indexing(session_id, context_data)

        # Verify data exists
        assert len(chat_client._session_contexts) > 0, "Should have session contexts"
        assert len(chat_client._session_indices) > 0, "Should have session indices"

        # Cleanup
        await chat_client.cleanup()

        # Verify cleanup
        assert len(chat_client._session_contexts) == 0, "Session contexts should be cleared"
        assert len(chat_client._session_indices) == 0, "Session indices should be cleared"
        assert len(chat_client._session_patterns) == 0, "Session patterns should be cleared"

    @pytest.mark.asyncio
    async def test_session_awareness_disabled(self, integration_config) -> None:
        """Test behavior when session awareness is disabled."""
        config = integration_config
        config.metadata["enable_session_awareness"] = False

        client = ChatHistoryClient(config)
        await client.initialize()

        # Session-aware components should not be initialized
        assert client._session_memory_bridge is None, "SessionMemoryBridge should be None"
        assert client._cks_storage is None, "CKS storage should be None"
        assert client._device_manager is None, "Device manager should be None"

        # Session-aware methods should still work but gracefully
        session_id = "disabled_test"
        context_data = {
            "messages": [],
            "keywords": ["test"],
            "context_type": "active_work",
        }

        # Should not fail but may not fully function
        await client.session_context_indexing(session_id, context_data)
        # Result behavior depends on implementation when session awareness is disabled

    @pytest.mark.asyncio
    async def test_error_handling_in_session_operations(self, chat_client) -> None:
        """Test error handling in session-aware operations."""
        # Test with invalid context type
        invalid_context_data = {
            "messages": [],
            "keywords": ["test"],
            "context_type": "invalid_context_type",
            "importance_score": 0.5,
        }

        # Should handle invalid context type gracefully
        session_id = "error_test"
        result = await chat_client.session_context_indexing(session_id, invalid_context_data)
        assert result is True, "Should handle invalid context type gracefully"

        # Verify default context type was used
        context = chat_client._session_contexts.get(session_id)
        if context:
            assert (
                context.context_type == SessionContextType.ACTIVE_WORK
            ), "Should default to ACTIVE_WORK for invalid context type"

    @pytest.mark.asyncio
    async def test_integration_with_session_memory_bridge(
        self, chat_client, sample_context_data
    ) -> None:
        """Test integration with SessionMemoryBridge."""
        # Mock SessionMemoryBridge
        mock_bridge = AsyncMock()
        mock_bridge.preserve_session_context.return_value = Mock(bridge_id="test_bridge_001")
        chat_client._session_memory_bridge = mock_bridge

        session_id = "integration_test"
        result = await chat_client.session_context_indexing(session_id, sample_context_data)

        assert result is True, "Indexing should succeed"

        # Verify SessionMemoryBridge was called
        mock_bridge.preserve_session_context.assert_called_once_with(
            session_id=session_id,
            criticality_threshold=0.8,
        )


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])
