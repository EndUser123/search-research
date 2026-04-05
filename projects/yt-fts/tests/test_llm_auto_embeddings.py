"""Tests for AutoEmbeddingsManager in auto_embeddings.py."""

from unittest.mock import MagicMock, patch
import sys
import pytest

from yt_fts.llm.auto_embeddings import AutoEmbeddingsManager


@pytest.fixture
def manager():
    """Create AutoEmbeddingsManager instance."""
    return AutoEmbeddingsManager(db_path=":memory:")


class TestEnsureEmbeddingsForChannelSuccess:
    """Tests for successful embedding generation."""

    @patch("yt_fts.llm.faiss_store.FaissVectorStore")
    @patch("yt_fts.llm.simple_embeddings.SemanticEmbeddingsHandler")
    def test_ensure_embeddings_returns_true_on_success(self, mock_handler_class, mock_store_class, manager):
        mock_handler = MagicMock()
        mock_handler.get_embedding_status.return_value = {"complete": False}
        mock_handler.generate_and_store_embeddings.return_value = 100
        mock_handler_class.return_value = mock_handler

        mock_store = MagicMock()
        mock_store.index_exists.return_value = False
        mock_store_class.return_value = mock_store

        result = manager.ensure_embeddings_for_channel("test_channel_id")

        assert result is True


class TestEnsureEmbeddingsSkipsIfComplete:
    """Tests for skipping regeneration when embeddings exist."""

    @patch("yt_fts.llm.faiss_store.FaissVectorStore")
    @patch("yt_fts.llm.simple_embeddings.SemanticEmbeddingsHandler")
    def test_ensure_embeddings_skips_if_complete(self, mock_handler_class, mock_store_class, manager):
        mock_handler = MagicMock()
        mock_handler.get_embedding_status.return_value = {"complete": True}
        mock_handler_class.return_value = mock_handler

        mock_store = MagicMock()
        mock_store.index_exists.return_value = True
        mock_store_class.return_value = mock_store

        result = manager.ensure_embeddings_for_channel("test_channel_id")

        assert result is True


class TestEnsureEmbeddingsRebuildsIfForced:
    """Tests for force rebuild behavior."""

    @patch("yt_fts.llm.faiss_store.FaissVectorStore")
    @patch("yt_fts.llm.simple_embeddings.SemanticEmbeddingsHandler")
    def test_ensure_embeddings_rebuilds_if_forced(self, mock_handler_class, mock_store_class, manager):
        mock_handler = MagicMock()
        mock_handler.get_embedding_status.return_value = {"complete": True}
        mock_handler.generate_and_store_embeddings.return_value = 150
        mock_handler_class.return_value = mock_handler

        mock_store = MagicMock()
        mock_store.index_exists.return_value = True
        mock_store_class.return_value = mock_store

        result = manager.ensure_embeddings_for_channel("test_channel_id", force_rebuild=True)

        assert result is True


class TestEnsureEmbeddingsForSearchDelegates:
    """Tests for ensure_embeddings_for_search delegation."""

    @patch("yt_fts.llm.faiss_store.FaissVectorStore")
    @patch("yt_fts.llm.simple_embeddings.SemanticEmbeddingsHandler")
    def test_ensure_embeddings_for_search_delegates(self, mock_handler_class, mock_store_class, manager):
        mock_handler = MagicMock()
        mock_handler.get_embedding_status.return_value = {"complete": False}
        mock_handler.generate_and_store_embeddings.return_value = 50
        mock_handler_class.return_value = mock_handler

        mock_store = MagicMock()
        mock_store.index_exists.return_value = False
        mock_store_class.return_value = mock_store

        result = manager.ensure_embeddings_for_search("test query", channel_id="test_channel_id")

        assert result is True

    def test_ensure_embeddings_for_search_returns_false_without_channel_id(self, manager):
        result = manager.ensure_embeddings_for_search("test query", channel_id=None)
        assert result is False


class TestGetEmbeddingStatus:
    """Tests for get_embedding_status method."""

    @patch("yt_fts.llm.faiss_store.FaissVectorStore")
    @patch("yt_fts.llm.simple_embeddings.SemanticEmbeddingsHandler")
    def test_get_embedding_status_returns_info(self, mock_handler_class, mock_store_class, manager):
        mock_handler = MagicMock()
        mock_handler.DEFAULT_MODEL = "all-MiniLM-L6-v2"
        mock_handler.EMBEDDING_DIM = 384
        mock_handler_class.return_value = mock_handler

        mock_store = MagicMock()
        mock_store_class.return_value = mock_store

        result = manager.get_embedding_status()

        assert result["model_name"] == "all-MiniLM-L6-v2"
        assert result["embedding_dim"] == 384
        assert result["type"] == "sentence_transformers"


class TestEnsureEmbeddingsErrorHandling:
    """Tests for error handling in ensure_embeddings_for_channel."""

    @patch("yt_fts.llm.faiss_store.FaissVectorStore")
    @patch("yt_fts.llm.simple_embeddings.SemanticEmbeddingsHandler")
    def test_ensure_embeddings_returns_false_on_exception(self, mock_handler_class, mock_store_class, manager):
        mock_handler = MagicMock()
        mock_handler.get_embedding_status.side_effect = Exception("Database error")
        mock_handler_class.return_value = mock_handler

        mock_store = MagicMock()
        mock_store_class.return_value = mock_store

        result = manager.ensure_embeddings_for_channel("test_channel_id")

        assert result is False

    @patch("yt_fts.llm.faiss_store.FaissVectorStore")
    @patch("yt_fts.llm.simple_embeddings.SemanticEmbeddingsHandler")
    def test_ensure_embeddings_returns_false_when_zero_count(self, mock_handler_class, mock_store_class, manager):
        mock_handler = MagicMock()
        mock_handler.get_embedding_status.return_value = {"complete": False}
        mock_handler.generate_and_store_embeddings.return_value = 0
        mock_handler_class.return_value = mock_handler

        mock_store = MagicMock()
        mock_store.index_exists.return_value = False
        mock_store_class.return_value = mock_store

        result = manager.ensure_embeddings_for_channel("test_channel_id")

        assert result is False
