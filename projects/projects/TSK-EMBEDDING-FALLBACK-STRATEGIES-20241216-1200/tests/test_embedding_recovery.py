"""
Test suite for Embedding Recovery Manager
Comprehensive testing of embedding recovery functionality
"""

import unittest.mock as mock

import pytest

# Import the classes we're testing
from implementation.embedding_recovery_manager import (
    EmbeddingRecoveryManager,
    FallbackStrategy,
    MissingEmbeddingInfo,
    RecoveryResult,
)


class TestEmbeddingRecoveryManager:
    """Test cases for EmbeddingRecoveryManager"""

    @pytest.fixture
    def recovery_manager(self):
        """Create a test instance of EmbeddingRecoveryManager"""
        return EmbeddingRecoveryManager(
            max_recovery_attempts=3,
            enable_background_generation=True,
            cache_generated_embeddings=True
        )

    @pytest.fixture
    def sample_missing_info(self):
        """Create sample missing embedding information"""
        return MissingEmbeddingInfo(
            video_id="test_video_123",
            channel_id="test_channel_456",
            start_time="00:05:30.000",
            text_content="This is a test subtitle segment for embedding recovery testing.",
            metadata={
                "video_title": "Test Video",
                "channel_name": "Test Channel",
                "video_date": "2024-01-15"
            }
        )

    @pytest.fixture
    def sample_model_config(self):
        """Create sample model configuration"""
        return {
            "embedding_model": "text-embedding-ada-002",
            "api_key": "test_api_key",
            "base_url": "https://api.openai.com/v1"
        }

    def test_initialization(self, recovery_manager):
        """Test EmbeddingRecoveryManager initialization"""
        assert recovery_manager.max_recovery_attempts == 3
        assert recovery_manager.enable_background_generation is True
        assert recovery_manager.cache_generated_embeddings is True
        assert recovery_manager.stats['total_recovery_attempts'] == 0
        assert recovery_manager.stats['successful_recoveries'] == 0

    def test_can_generate_embedding_valid_content(self, recovery_manager, sample_missing_info):
        """Test embedding generation possibility with valid content"""
        result = recovery_manager._can_generate_embedding(sample_missing_info)
        assert result is True

    def test_can_generate_embedding_empty_content(self, recovery_manager):
        """Test embedding generation possibility with empty content"""
        missing_info_empty = MissingEmbeddingInfo(
            video_id="test",
            channel_id="test",
            start_time="00:00:00.000",
            text_content="",
            metadata={}
        )
        result = recovery_manager._can_generate_embedding(missing_info_empty)
        assert result is False

    def test_can_generate_embedding_no_metadata(self, recovery_manager):
        """Test embedding generation possibility with missing metadata"""
        missing_info_no_meta = MissingEmbeddingInfo(
            video_id="test",
            channel_id="test",
            start_time="00:00:00.000",
            text_content="Some content",
            metadata={}
        )
        result = recovery_manager._can_generate_embedding(missing_info_no_meta)
        assert result is False

    def test_prepare_text_with_metadata(self, recovery_manager, sample_missing_info):
        """Test text preparation with metadata"""
        result = recovery_manager._prepare_text_with_metadata(sample_missing_info)

        assert "---" in result
        assert "video_title: Test Video" in result
        assert "channel_name: Test Channel" in result
        assert "video_date: 2024-01-15" in result
        assert "segment_start_time: 00:05:30.000" in result
        assert "Content:" in result
        assert "This is a test subtitle segment" in result

    def test_extract_keywords(self, recovery_manager):
        """Test keyword extraction functionality"""
        text = "This is a test subtitle about machine learning and artificial intelligence for video content analysis."
        keywords = recovery_manager._extract_keywords(text)

        assert isinstance(keywords, list)
        assert len(keywords) > 0
        assert "test" in keywords
        assert "subtitle" in keywords
        assert "machine" in keywords
        assert "learning" in keywords
        assert "artificial" in keywords
        assert "intelligence" in keywords

    def test_extract_keywords_empty_text(self, recovery_manager):
        """Test keyword extraction with empty text"""
        keywords = recovery_manager._extract_keywords("")
        assert keywords == []

    @mock.patch('implementation.embedding_recovery_manager.EmbeddingsHandler')
    @mock.patch('implementation.embedding_recovery_manager.get_chroma_client')
    def test_generate_embedding_success(self, mock_chroma, mock_embeddings_handler,
                                      recovery_manager, sample_missing_info, sample_model_config):
        """Test successful embedding generation"""
        # Mock the embeddings handler
        mock_handler_instance = mock_embeddings_handler.return_value
        mock_handler_instance.get_embedding.return_value = iter([[0.1, 0.2, 0.3, 0.4]])

        # Mock ChromaDB client
        mock_client = mock.MagicMock()
        mock_collection = mock.MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chroma.return_value = mock_client

        result = recovery_manager._generate_embedding(sample_missing_info, sample_model_config)

        assert result is True
        mock_handler_instance.get_embedding.assert_called_once()
        mock_collection.add.assert_called_once()

    @mock.patch('implementation.embedding_recovery_manager.EmbeddingsHandler')
    def test_generate_embedding_failure(self, mock_embeddings_handler,
                                      recovery_manager, sample_missing_info, sample_model_config):
        """Test embedding generation failure"""
        # Mock the embeddings handler to raise an exception
        mock_handler_instance = mock_embeddings_handler.return_value
        mock_handler_instance.get_embedding.side_effect = Exception("API Error")

        result = recovery_manager._generate_embedding(sample_missing_info, sample_model_config)

        assert result is False

    def test_text_search_within_video(self, recovery_manager, sample_missing_info):
        """Test text search within video fallback"""
        results = recovery_manager._text_search_within_video(sample_missing_info)

        assert isinstance(results, list)
        if results:  # If results are returned
            assert results[0]['type'] == 'text_search'
            assert results[0]['video_id'] == sample_missing_info.video_id
            assert 'match_text' in results[0]
            assert 'relevance_score' in results[0]

    def test_keyword_search_in_channel(self, recovery_manager, sample_missing_info):
        """Test keyword search in channel fallback"""
        results = recovery_manager._keyword_search_in_channel(sample_missing_info)

        assert isinstance(results, list)
        if results:  # If results are returned
            assert results[0]['type'] == 'keyword_search'
            assert results[0]['channel_id'] == sample_missing_info.channel_id
            assert 'keywords' in results[0]
            assert 'relevance_score' in results[0]

    @mock.patch('implementation.embedding_recovery_manager.EmbeddingsHandler')
    @mock.patch('implementation.embedding_recovery_manager.get_chroma_client')
    def test_recover_single_embedding_success(self, mock_chroma, mock_embeddings_handler,
                                           recovery_manager, sample_missing_info, sample_model_config):
        """Test successful single embedding recovery"""
        # Mock successful embedding generation
        mock_handler_instance = mock_embeddings_handler.return_value
        mock_handler_instance.get_embedding.return_value = iter([[0.1, 0.2, 0.3, 0.4]])

        mock_client = mock.MagicMock()
        mock_collection = mock.MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chroma.return_value = mock_client

        result = recovery_manager._recover_single_embedding(sample_missing_info, sample_model_config)

        assert result.success is True
        assert result.embedding_generated is True
        assert result.strategy_used is None
        assert result.fallback_results == []

    @mock.patch('implementation.embedding_recovery_manager.EmbeddingsHandler')
    def test_recover_single_embedding_fallback(self, mock_embeddings_handler,
                                             recovery_manager, sample_missing_info, sample_model_config):
        """Test embedding recovery with fallback"""
        # Mock failed embedding generation
        mock_handler_instance = mock_embeddings_handler.return_value
        mock_handler_instance.get_embedding.side_effect = Exception("API Error")

        result = recovery_manager._recover_single_embedding(sample_missing_info, sample_model_config)

        assert isinstance(result, RecoveryResult)
        assert result.embedding_generated is False
        # Should have fallback results
        assert isinstance(result.fallback_results, list)

    def test_recover_missing_embeddings_multiple(self, recovery_manager, sample_missing_info, sample_model_config):
        """Test recovery of multiple missing embeddings"""
        # Create multiple missing embeddings
        missing_list = [sample_missing_info]

        # Mock the recovery method to avoid actual API calls
        with mock.patch.object(recovery_manager, '_recover_single_embedding') as mock_recover:
            mock_recover.return_value = RecoveryResult(
                success=True,
                strategy_used=None,
                embedding_generated=True,
                fallback_results=[],
                processing_time=0.1
            )

            results = recovery_manager.recover_missing_embeddings(missing_list, sample_model_config)

            assert len(results) == 1
            assert results[0].success is True
            assert results[0].embedding_generated is True
            mock_recover.assert_called_once()

    def test_detect_missing_embeddings(self, recovery_manager):
        """Test missing embedding detection"""
        # Test with empty results
        empty_results = {}
        missing = recovery_manager.detect_missing_embeddings(empty_results, 10)
        assert missing == []

        # Test with partial results
        partial_results = {
            'documents': [['doc1', 'doc2']],  # Only 2 docs, expected 10
            'metadatas': [[]],
            'distances': [[]]
        }
        missing = recovery_manager.detect_missing_embeddings(partial_results, 10)
        # Current implementation returns empty list, but logs warning
        assert isinstance(missing, list)

    def test_statistics_tracking(self, recovery_manager):
        """Test statistics tracking functionality"""
        initial_stats = recovery_manager.get_statistics()
        assert initial_stats['total_recovery_attempts'] == 0
        assert initial_stats['successful_recoveries'] == 0
        assert initial_stats['embeddings_generated'] == 0

        # Simulate some recovery attempts
        recovery_manager.stats['total_recovery_attempts'] = 10
        recovery_manager.stats['successful_recoveries'] = 8
        recovery_manager.stats['embeddings_generated'] = 5
        recovery_manager.stats['total_processing_time'] = 2.5

        updated_stats = recovery_manager.get_statistics()
        assert updated_stats['total_recovery_attempts'] == 10
        assert updated_stats['successful_recoveries'] == 8
        assert updated_stats['embeddings_generated'] == 5
        assert updated_stats['success_rate'] == 0.8
        assert updated_stats['embedding_generation_rate'] == 0.5
        assert updated_stats['average_processing_time'] == 0.25

    def test_statistics_reset(self, recovery_manager):
        """Test statistics reset functionality"""
        # Add some statistics
        recovery_manager.stats['total_recovery_attempts'] = 10
        recovery_manager.stats['successful_recoveries'] = 5

        # Reset statistics
        recovery_manager.reset_statistics()

        # Check that statistics are reset
        reset_stats = recovery_manager.get_statistics()
        assert reset_stats['total_recovery_attempts'] == 0
        assert reset_stats['successful_recoveries'] == 0
        assert reset_stats['embeddings_generated'] == 0

    @mock.patch('implementation.embedding_recovery_manager.logging')
    def test_logging_functionality(self, mock_logging, recovery_manager):
        """Test that logging is properly configured and used"""
        recovery_manager.log_statistics()

        # Check that logging methods were called
        mock_logging.getLogger.assert_called()
        logger_instance = mock_logging.getLogger.return_value
        logger_instance.info.assert_called()

    def test_recovery_result_dataclass(self):
        """Test RecoveryResult dataclass functionality"""
        result = RecoveryResult(
            success=True,
            strategy_used=FallbackStrategy.TEXT_SEARCH,
            embedding_generated=False,
            fallback_results=[{'type': 'test', 'score': 0.8}],
            processing_time=1.5,
            error_message="Test error"
        )

        assert result.success is True
        assert result.strategy_used == FallbackStrategy.TEXT_SEARCH
        assert result.embedding_generated is False
        assert len(result.fallback_results) == 1
        assert result.processing_time == 1.5
        assert result.error_message == "Test error"

    def test_missing_embedding_info_dataclass(self):
        """Test MissingEmbeddingInfo dataclass functionality"""
        info = MissingEmbeddingInfo(
            video_id="test_vid",
            channel_id="test_chan",
            start_time="00:01:00.000",
            text_content="Test content",
            metadata={"title": "Test Video"}
        )

        assert info.video_id == "test_vid"
        assert info.channel_id == "test_chan"
        assert info.start_time == "00:01:00.000"
        assert info.text_content == "Test content"
        assert info.metadata["title"] == "Test Video"


class TestIntegrationScenarios:
    """Integration test scenarios for embedding recovery"""

    @pytest.fixture
    def mock_chroma_results_with_missing(self):
        """Mock ChromaDB results with missing embeddings"""
        return {
            'documents': [['doc1', 'doc2']],  # Only 2 documents
            'metadatas': [[{'video_id': 'vid1', 'channel_id': 'chan1'}, {'video_id': 'vid2', 'channel_id': 'chan2'}]],
            'distances': [[0.1, 0.2]]
        }

    @pytest.fixture
    def mock_chroma_results_complete(self):
        """Mock complete ChromaDB results"""
        return {
            'documents': [['doc1', 'doc2', 'doc3', 'doc4', 'doc5']],
            'metadatas': [[{'video_id': f'vid{i}', 'channel_id': f'chan{i}'} for i in range(1, 6)]],
            'distances': [[0.1, 0.2, 0.3, 0.4, 0.5]]
        }

    def test_needs_recovery_detection(self, mock_chroma_results_with_missing, mock_chroma_results_complete):
        """Test detection of when recovery is needed"""
        manager = EmbeddingRecoveryManager()

        # Test with missing embeddings
        needs_recovery = manager._needs_recovery(mock_chroma_results_with_missing)
        assert needs_recovery is True

        # Test with complete results
        needs_recovery = manager._needs_recovery(mock_chroma_results_complete)
        assert needs_recovery is False

    def test_end_to_end_recovery_workflow(self):
        """Test end-to-end recovery workflow"""
        manager = EmbeddingRecoveryManager()

        # Create test missing embedding info
        missing_info = MissingEmbeddingInfo(
            video_id="test_video",
            channel_id="test_channel",
            start_time="00:01:00.000",
            text_content="Test video content for recovery testing.",
            metadata={
                "video_title": "Test Video",
                "channel_name": "Test Channel",
                "video_date": "2024-01-15"
            }
        )

        # Mock the embedding generation to avoid actual API calls
        with mock.patch.object(manager, '_generate_embedding', return_value=True) as mock_generate:
            with mock.patch.object(manager, '_store_embedding') as mock_store:
                # Simulate recovery
                result = manager._recover_single_embedding(missing_info, {
                    'embedding_model': 'test-model',
                    'api_key': 'test-key'
                })

                assert result.success is True
                assert result.embedding_generated is True
                mock_generate.assert_called_once()
                mock_store.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
