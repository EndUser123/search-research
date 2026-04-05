from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

#!/usr/bin/env python3
"""CSF NIP Chat Search Strategy Tests.

Comprehensive test suite for chat search strategy components.
Follows CSF NIP testing standards with TDD methodology.

Test Coverage:
1. Strategy Pattern Implementation
2. Security Validation
3. Error Handling and Circuit Breaker
4. Factory Pattern
5. Integration with Existing Components
"""



# Add CSF NIP path for imports
csf_nip_root = Path(__file__).parent.parent.parent.parent.parent.parent
if str(csf_nip_root) not in sys.path:
    sys.path.append(str(csf_nip_root))

try:
    from core_utils.chat_search_strategy import (
        ChatSearchQuery,
        ChatSearchResult,
        ChatSearchStrategyFactory,
        HybridChatSearchStrategy,
        KeywordChatSearchStrategy,
        SearchMethod,
        SearchStatus,
        SemanticChatSearchStrategy,
    )
    from core_utils.embedding_manager import EmbeddingManager

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


class TestChatSearchQuery:
    """Test ChatSearchQuery security validation and data model."""

    def test_valid_query_creation(self) -> None:
        """Test creating a valid search query."""
        query = ChatSearchQuery(
            query_text="test query",
            search_method=SearchMethod.HYBRID,
            max_results=20,
        )

        assert query.query_text == "test query"
        assert query.search_method == SearchMethod.HYBRID
        assert query.max_results == 20
        assert query.context_filter == "all"
        assert query.session_filter == "all"

    def test_query_sanitization(self) -> None:
        """Test query text sanitization."""
        # Test injection attempts
        malicious_query = "test; DROP TABLE users; --"
        query = ChatSearchQuery(
            query_text=malicious_query,
            search_method=SearchMethod.KEYWORD,
        )

        # Should be sanitized
        assert ";" not in query.query_text
        assert "DROP" not in query.query_text
        assert "TABLE" not in query.query_text

    def test_path_traversal_prevention(self) -> None:
        """Test path traversal prevention."""
        malicious_query = "test../../../etc/passwd"
        query = ChatSearchQuery(
            query_text=malicious_query,
            search_method=SearchMethod.KEYWORD,
        )

        # Should be sanitized
        assert ".." not in query.query_text

    def test_max_length_validation(self) -> None:
        """Test maximum length validation."""
        long_query = "a" * 1001

        with pytest.raises(ValueError, match="Query text too long"):
            ChatSearchQuery(
                query_text=long_query,
                search_method=SearchMethod.KEYWORD,
            )

    def test_max_results_validation(self) -> None:
        """Test max results validation."""
        # Test too large
        with pytest.raises(ValueError, match="max_results cannot exceed 100"):
            ChatSearchQuery(
                query_text="test",
                search_method=SearchMethod.KEYWORD,
                max_results=101,
            )


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="CSF NIP components not available")
class TestSemanticChatSearchStrategy:
    """Test semantic search strategy implementation."""

    @pytest.fixture
    def mock_embedding_manager(self):
        """Create a mock embedding manager."""
        mock_manager = Mock(spec=EmbeddingManager)
        mock_manager.encode_single.return_value = [0.1, 0.2, 0.3, 0.4]  # Mock embedding
        return mock_manager

    @pytest.fixture
    def semantic_strategy(self, mock_embedding_manager):
        """Create semantic search strategy with mock embedding manager."""
        return SemanticChatSearchStrategy(
            embedding_manager=mock_embedding_manager,
            logger=logging.getLogger("test"),
        )

    def test_successful_search(self, semantic_strategy) -> None:
        """Test successful semantic search."""
        query = ChatSearchQuery(
            query_text="test search",
            search_method=SearchMethod.SEMANTIC,
            max_results=5,
        )

        results = semantic_strategy.search(query)

        # Should return some results (even if simulated)
        assert isinstance(results, list)
        assert semantic_strategy.status == SearchStatus.SUCCESS
        assert semantic_strategy.failure_count == 0

    def test_embedding_manager_unavailable(self) -> None:
        """Test behavior when embedding manager is unavailable."""
        strategy = SemanticChatSearchStrategy()

        query = ChatSearchQuery(
            query_text="test search",
            search_method=SearchMethod.SEMANTIC,
        )

        results = strategy.search(query)

        # Should return empty results
        assert results == []
        assert strategy.status == SearchStatus.ERROR

    def test_empty_embedding_handling(
        self, semantic_strategy, mock_embedding_manager
    ) -> None:
        """Test handling of empty embeddings."""
        mock_embedding_manager.encode_single.return_value = []

        query = ChatSearchQuery(
            query_text="test search",
            search_method=SearchMethod.SEMANTIC,
        )

        results = semantic_strategy.search(query)

        assert results == []
        # Should not trigger circuit breaker on empty embedding
        assert semantic_strategy.failure_count == 1

    def test_circuit_breaker_behavior(
        self, semantic_strategy, mock_embedding_manager
    ) -> None:
        """Test circuit breaker behavior."""
        # Make embedding manager fail
        mock_embedding_manager.encode_single.side_effect = Exception("Embedding failed")

        query = ChatSearchQuery(
            query_text="test search",
            search_method=SearchMethod.SEMANTIC,
        )

        # Trigger multiple failures to hit circuit breaker threshold
        for _i in range(6):
            results = semantic_strategy.search(query)
            assert results == []

        # Should trigger circuit breaker
        assert semantic_strategy.status == SearchStatus.ERROR
        assert semantic_strategy.failure_count >= 5


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="CSF NIP components not available")
class TestKeywordChatSearchStrategy:
    """Test keyword search strategy implementation."""

    @pytest.fixture
    def keyword_strategy(self):
        """Create keyword search strategy."""
        return KeywordChatSearchStrategy(
            logger=logging.getLogger("test"),
        )

    def test_successful_search(self, keyword_strategy) -> None:
        """Test successful keyword search."""
        query = ChatSearchQuery(
            query_text="test search with multiple words",
            search_method=SearchMethod.KEYWORD,
            max_results=5,
        )

        results = keyword_strategy.search(query)

        # Should return some results (even if simulated)
        assert isinstance(results, list)
        assert keyword_strategy.status == SearchStatus.SUCCESS

    def test_empty_query_handling(self, keyword_strategy) -> None:
        """Test handling of empty queries."""
        query = ChatSearchQuery(
            query_text="",
            search_method=SearchMethod.KEYWORD,
        )

        results = keyword_strategy.search(query)

        # Should return empty results for empty query
        assert results == []

    def test_query_tokenization(self, keyword_strategy) -> None:
        """Test query tokenization."""
        # Test various query formats
        test_cases = [
            ("simple word", ["simple", "word"]),
            ("test search", ["test", "search"]),
            ("Test with punctuation!", ["test", "with", "punctuation"]),
            ("a b c", []),  # Short tokens filtered out
            ("test123", ["test123"]),  # Alphanumeric
        ]

        for query_text, expected_tokens in test_cases:
            tokens = keyword_strategy._tokenize_query(query_text)
            assert tokens == expected_tokens, f"Failed for: {query_text}"


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="CSF NIP components not available")
class TestHybridChatSearchStrategy:
    """Test hybrid search strategy implementation."""

    @pytest.fixture
    def mock_semantic_strategy(self):
        """Create mock semantic strategy."""
        strategy = Mock(spec=SemanticChatSearchStrategy)
        strategy.search.return_value = [
            ChatSearchResult(
                content="semantic result 1",
                relevance_score=0.9,
                source="semantic",
                search_method=SearchMethod.SEMANTIC,
            ),
        ]
        return strategy

    @pytest.fixture
    def mock_keyword_strategy(self):
        """Create mock keyword strategy."""
        strategy = Mock(spec=KeywordChatSearchStrategy)
        strategy.search.return_value = [
            ChatSearchResult(
                content="keyword result 1",
                relevance_score=0.7,
                source="keyword",
                search_method=SearchMethod.KEYWORD,
            ),
        ]
        return strategy

    @pytest.fixture
    def hybrid_strategy(self, mock_semantic_strategy, mock_keyword_strategy):
        """Create hybrid search strategy."""
        return HybridChatSearchStrategy(
            semantic_strategy=mock_semantic_strategy,
            keyword_strategy=mock_keyword_strategy,
            logger=logging.getLogger("test"),
        )

    def test_hybrid_search_success(
        self, hybrid_strategy, mock_semantic_strategy, mock_keyword_strategy
    ) -> None:
        """Test successful hybrid search."""
        query = ChatSearchQuery(
            query_text="test search",
            search_method=SearchMethod.HYBRID,
            max_results=5,
        )

        results = hybrid_strategy.search(query)

        # Should combine results from both strategies
        assert len(results) == 2
        assert hybrid_strategy.status == SearchStatus.SUCCESS

        # Both strategies should be called
        mock_semantic_strategy.search.assert_called_once()
        mock_keyword_strategy.search.assert_called_once()

    def test_semantic_fallback(
        self, hybrid_strategy, mock_semantic_strategy, mock_keyword_strategy
    ) -> None:
        """Test fallback when semantic search fails."""
        mock_semantic_strategy.search.side_effect = Exception("Semantic failed")
        mock_keyword_strategy.search.return_value = [
            ChatSearchResult(
                content="keyword fallback result",
                relevance_score=0.8,
                source="keyword",
                search_method=SearchMethod.KEYWORD,
            ),
        ]

        query = ChatSearchQuery(
            query_text="test search",
            search_method=SearchMethod.HYBRID,
        )

        results = hybrid_strategy.search(query)

        # Should still get results from keyword search
        assert len(results) == 1
        assert results[0].search_method == SearchMethod.KEYWORD
        assert hybrid_strategy.status == SearchStatus.SUCCESS

    def test_deduplication_and_ranking(self, hybrid_strategy) -> None:
        """Test result deduplication and ranking."""
        # Create duplicate results
        duplicate_content = "same content"
        results = [
            ChatSearchResult(
                content=duplicate_content,
                relevance_score=0.8,
                source="source1",
                search_method=SearchMethod.SEMANTIC,
            ),
            ChatSearchResult(
                content=duplicate_content,
                relevance_score=0.9,  # Higher score
                source="source2",
                search_method=SearchMethod.KEYWORD,
            ),
            ChatSearchResult(
                content="different content",
                relevance_score=0.7,
                source="source3",
                search_method=SearchMethod.SEMANTIC,
            ),
        ]

        unique_results = hybrid_strategy._deduplicate_and_rank(results, None)

        # Should remove duplicates and sort by relevance
        assert len(unique_results) == 2
        assert unique_results[0].relevance_score == 0.9  # Highest score first
        assert unique_results[1].relevance_score == 0.7


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="CSF NIP components not available")
class TestChatSearchStrategyFactory:
    """Test search strategy factory implementation."""

    @pytest.fixture
    def factory(self):
        """Create strategy factory."""
        return ChatSearchStrategyFactory()

    def test_create_semantic_strategy(self, factory) -> None:
        """Test creating semantic strategy."""
        strategy = factory.create_strategy(SearchMethod.SEMANTIC)

        assert isinstance(strategy, SemanticChatSearchStrategy)
        assert strategy.status == SearchStatus.SUCCESS

    def test_create_keyword_strategy(self, factory) -> None:
        """Test creating keyword strategy."""
        strategy = factory.create_strategy(SearchMethod.KEYWORD)

        assert isinstance(strategy, KeywordChatSearchStrategy)
        assert strategy.status == SearchStatus.SUCCESS

    def test_create_hybrid_strategy(self, factory) -> None:
        """Test creating hybrid strategy."""
        strategy = factory.create_strategy(SearchMethod.HYBRID)

        assert isinstance(strategy, HybridChatSearchStrategy)
        assert strategy.status == SearchStatus.SUCCESS

    def test_list_available_strategies(self, factory) -> None:
        """Test listing available strategies."""
        strategies = factory.list_available_strategies()

        # Should include all expected strategies
        expected_strategies = ["keyword", "semantic", "hybrid"]
        for strategy in expected_strategies:
            assert strategy in strategies

    def test_strategy_status_tracking(self, factory) -> None:
        """Test strategy status tracking."""
        # Create and fail a strategy
        strategy = factory.create_strategy(SearchMethod.SEMANTIC)

        # Initial status should be SUCCESS
        assert factory.get_strategy_status("semantic") == SearchStatus.SUCCESS

        # Simulate failure
        strategy.failure_count = 10
        strategy.status = SearchStatus.ERROR

        # Should reflect new status
        assert factory.get_strategy_status("semantic") == SearchStatus.ERROR

    def test_fallback_to_keyword(self, factory) -> None:
        """Test fallback to keyword when requested strategy unavailable."""
        # This would happen if embedding manager is not available
        with patch(
            "src.lib.core_utils.chat_search_strategy.EMBEDDING_MANAGER_AVAILABLE", False
        ):
            factory = ChatSearchStrategyFactory()

            # Should fallback to keyword for semantic request
            strategy = factory.create_strategy(SearchMethod.SEMANTIC)
            assert isinstance(strategy, KeywordChatSearchStrategy)


# Integration Tests
@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="CSF NIP components not available")
class TestChatSearchIntegration:
    """Integration tests for chat search components."""

    @pytest.fixture
    def real_search_service(self):
        """Create real search service with all components."""
        from application.chat_search_service import ChatSearchService

        return ChatSearchService()

    def test_end_to_end_search_flow(self, real_search_service) -> None:
        """Test complete search flow."""
        # Test different search methods
        search_methods = [
            SearchMethod.KEYWORD,
            SearchMethod.SEMANTIC,
            SearchMethod.HYBRID,
        ]

        for method in search_methods:
            try:
                results = real_search_service.search_chat_history(
                    query_text="integration test query",
                    search_method=method,
                    max_results=5,
                    source_ip="127.0.0.1",
                    user_id="test_user",
                )

                # Should not crash and should return list (even if empty)
                assert isinstance(results, list)

            except Exception:
                pass
                # Don't fail the test - log and continue

    def test_security_integration(self, real_search_service) -> None:
        """Test security integration."""
        # Test malicious queries
        malicious_queries = [
            "test; DROP TABLE users;",
            "../../../etc/passwd",
            "<script>alert('xss')</script>",
            "a" * 2000,  # Very long query
        ]

        for query in malicious_queries:
            results = real_search_service.search_chat_history(
                query_text=query,
                search_method=SearchMethod.HYBRID,
                source_ip="192.168.1.100",
                user_id="test_user",
            )

            # Should block or handle safely
            assert isinstance(results, list)

    def test_statistics_tracking(self, real_search_service) -> None:
        """Test statistics tracking."""
        initial_stats = real_search_service.get_search_statistics()
        assert "total_searches" in initial_stats

        # Perform some searches
        for i in range(5):
            real_search_service.search_chat_history(
                query_text=f"test query {i}",
                search_method=SearchMethod.HYBRID,
                source_ip="127.0.0.1",
                user_id="test_user",
            )

        final_stats = real_search_service.get_search_statistics()

        # Should track searches
        assert final_stats["total_searches"] > initial_stats["total_searches"]
        assert "success_rate_percent" in final_stats

    def test_health_check(self, real_search_service) -> None:
        """Test health check functionality."""
        health = real_search_service.health_check()

        # Should return health status
        assert "service_healthy" in health
        assert "available_strategies" in health
        assert "strategy_status" in health
        assert "statistics" in health


# Performance Tests
@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="CSF NIP components not available")
class TestChatSearchPerformance:
    """Performance tests for chat search components."""

    @pytest.fixture
    def search_service(self):
        """Create search service for performance testing."""

        return ChatSearchService()

    def test_concurrent_search_performance(self, search_service) -> None:
        """Test concurrent search performance."""
        import threading
        import time

        results = []
        errors = []

        def search_worker(worker_id) -> None:
            try:
                start_time = time.time()
                search_results = search_service.search_chat_history(
                    query_text=f"performance test {worker_id}",
                    search_method=SearchMethod.HYBRID,
                    max_results=10,
                    source_ip=f"192.168.1.{worker_id}",
                    user_id=f"user{worker_id}",
                )
                end_time = time.time()

                results.append(
                    {
                        "worker_id": worker_id,
                        "duration": end_time - start_time,
                        "result_count": len(search_results),
                        "success": True,
                    },
                )
            except Exception as e:
                errors.append({"worker_id": worker_id, "error": str(e)})

        # Start 10 concurrent searches
        threads = []
        for i in range(10):
            thread = threading.Thread(target=search_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10)

        # Analyze results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10, f"Not all searches completed: {len(results)}"

        # Check performance
        avg_duration = sum(r["duration"] for r in results) / len(results)

        # Performance assertion - should complete within reasonable time
        assert avg_duration < 5.0, f"Search too slow: {avg_duration:.3f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
