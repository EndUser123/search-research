"""
Tests for yt_fts.llm.simple_embeddings module.

Tests SemanticEmbeddingsHandler using sentence-transformers.
"""

from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from yt_fts.llm.simple_embeddings import SemanticEmbeddingsHandler, SimpleEmbeddingsHandler


class TestGetEmbeddingReturnsNumpyArray:
    """Test get_embedding returns numpy array with correct shape."""

    @pytest.fixture
    def handler(self):
        """Create handler with mocked model."""
        with patch.object(SemanticEmbeddingsHandler, "model", create=True):
            return SemanticEmbeddingsHandler()

    def test_returns_numpy_array(self, handler):
        """
        Test that get_embedding returns numpy array.

        Given: A handler with mocked model
        When: Getting embedding for text
        Then: Returns numpy.ndarray
        """
        # Arrange
        mock_embedding = np.array([0.1, 0.2, 0.3, 0.4])
        handler.model.encode = Mock(return_value=mock_embedding)

        # Act
        result = handler.get_embedding("test text")

        # Assert
        assert isinstance(result, np.ndarray)
        assert result.shape == (4,)


class TestGetEmbeddingsBatchEmptyList:
    """Test get_embeddings_batch with empty input."""

    @pytest.fixture
    def handler(self):
        """Create handler."""
        return SemanticEmbeddingsHandler()

    @patch.object(SemanticEmbeddingsHandler, "model")
    def test_empty_list_returns_empty_array(self, mock_model, handler):
        """
        Test that empty input returns empty array.

        Given: A handler instance
        When: Getting embeddings for empty list
        Then: Returns empty numpy array
        """
        # Act
        result = handler.get_embeddings_batch([])

        # Assert
        assert isinstance(result, np.ndarray)
        assert result.size == 0
        # Model should not be called for empty input
        mock_model.encode.assert_not_called()


class TestGetEmbeddingsBatchReturnsEmbeddings:
    """Test get_embeddings_batch normal case."""

    @pytest.fixture
    def handler(self):
        """Create handler with mocked model."""
        with patch.object(SemanticEmbeddingsHandler, "model", create=True):
            return SemanticEmbeddingsHandler()

    def test_returns_embeddings_for_multiple_texts(self, handler):
        """
        Test that batch embedding returns correct number of embeddings.

        Given: A handler with mocked model
        When: Getting embeddings for multiple texts
        Then: Returns array with one embedding per text
        """
        # Arrange
        texts = ["text one", "text two", "text three"]
        mock_embeddings = np.array([
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
            [0.7, 0.8, 0.9]
        ])
        handler.model.encode = Mock(return_value=mock_embeddings)

        # Act
        result = handler.get_embeddings_batch(texts)

        # Assert
        assert result.shape == (3, 3)
        handler.model.encode.assert_called_once()


class TestSimilaritySearchReturnsTopK:
    """Test similarity_search limits results correctly."""

    @pytest.fixture
    def handler(self):
        """Create handler."""
        return SemanticEmbeddingsHandler()

    def test_limits_results_to_top_k(self, handler):
        """
        Test that similarity_search returns exactly top_k results.

        Given: A handler instance
        When: Searching with top_k=3 against 10 documents
        Then: Returns exactly 3 results
        """
        # Arrange
        query_embedding = np.array([1.0, 0.0, 0.0])
        document_embeddings = np.array([
            [1.0, 0.0, 0.0],  # Perfect match
            [0.9, 0.1, 0.0],
            [0.8, 0.2, 0.0],
            [0.0, 1.0, 0.0],  # Less similar
            [0.0, 0.0, 1.0],  # Orthogonal
            [0.5, 0.5, 0.0],
            [0.3, 0.7, 0.0],
            [0.2, 0.8, 0.0],
            [0.1, 0.9, 0.0],
            [0.0, 0.5, 0.5],
        ])

        # Act
        results = handler.similarity_search(query_embedding, document_embeddings, top_k=3)

        # Assert
        assert len(results) == 3

    def test_results_have_similarity_scores(self, handler):
        """
        Test that results include similarity scores.

        Given: A handler instance
        When: Performing similarity search
        Then: Each result has a similarity score
        """
        # Arrange
        query_embedding = np.array([1.0, 0.0])
        document_embeddings = np.array([[1.0, 0.0], [0.0, 1.0]])

        # Act
        results = handler.similarity_search(query_embedding, document_embeddings, top_k=2)

        # Assert
        for result in results:
            assert "similarity" in result
            assert isinstance(result["similarity"], float)
            assert "index" in result


class TestSearchSimilarReturnsTextWithSimilarity:
    """Test search_similar includes text field."""

    @pytest.fixture
    def handler(self):
        """Create handler with mocked model."""
        with patch.object(SemanticEmbeddingsHandler, "model", create=True):
            return SemanticEmbeddingsHandler()

    def test_includes_original_text_in_results(self, handler):
        """
        Test that search_similar returns results with text field.

        Given: A handler with mocked model
        When: Searching similar texts
        Then: Results include the original text
        """
        # Arrange
        query = "search query"
        texts = ["first result", "second result", "third result"]
        mock_query_emb = np.array([1.0, 0.0])
        mock_doc_emb = np.array([[1.0, 0.0], [0.9, 0.1], [0.8, 0.2]])

        handler.model.encode = Mock(side_effect=[mock_query_emb, mock_doc_emb])

        # Act
        results = handler.search_similar(query, texts, top_k=2)

        # Assert
        assert len(results) == 2
        for result in results:
            assert "text" in result
            assert result["text"] in texts
            assert "similarity" in result


class TestCosineSimilarityRange0To1:
    """Test cosine similarity returns values in valid range."""

    def test_similarity_between_0_and_1(self):
        """
        Test that cosine similarity is between 0 and 1.

        Given: A handler instance
        When: Computing cosine similarity
        Then: Result is in range [0, 1]
        """
        # Arrange
        handler = SemanticEmbeddingsHandler()
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0])

        # Act
        result = handler._cosine_similarity(vec1, vec2)

        # Assert
        assert 0.0 <= result <= 1.0

    def test_identical_vectors_have_similarity_1(self):
        """
        Test that identical vectors have similarity of 1.

        Given: A handler instance
        When: Computing similarity of identical vectors
        Then: Result equals 1.0
        """
        # Arrange
        handler = SemanticEmbeddingsHandler()
        vec = np.array([0.5, 0.5, 0.5])

        # Act
        result = handler._cosine_similarity(vec, vec)

        # Assert - use approx for floating point comparison
        assert result == pytest.approx(1.0, rel=1e-9)

    def test_orthogonal_vectors_have_similarity_0(self):
        """
        Test that orthogonal vectors have similarity of 0.

        Given: A handler instance
        When: Computing similarity of orthogonal vectors
        Then: Result equals 0.0
        """
        # Arrange
        handler = SemanticEmbeddingsHandler()
        vec1 = np.array([1.0, 0.0])
        vec2 = np.array([0.0, 1.0])

        # Act
        result = handler._cosine_similarity(vec1, vec2)

        # Assert
        assert result == 0.0


class TestGetModelInfoReturnsMetadata:
    """Test get_model_info returns correct metadata."""

    def test_returns_model_info_dict(self):
        """
        Test that get_model_info returns metadata dictionary.

        Given: A handler instance
        When: Getting model info
        Then: Returns dict with model metadata
        """
        # Arrange
        handler = SemanticEmbeddingsHandler(model_name="custom-model")

        # Act
        info = handler.get_model_info()

        # Assert
        assert isinstance(info, dict)
        assert "model_name" in info
        assert "embedding_size" in info
        assert "type" in info
        assert info["model_name"] == "custom-model"
        assert info["type"] == "sentence_transformers"

    def test_default_model_info(self):
        """
        Test that default model has correct metadata.

        Given: A handler with default model
        When: Getting model info
        Then: Returns correct default model name
        """
        # Arrange
        handler = SemanticEmbeddingsHandler()

        # Act
        info = handler.get_model_info()

        # Assert
        assert info["model_name"] == SemanticEmbeddingsHandler.DEFAULT_MODEL
        assert info["embedding_size"] == SemanticEmbeddingsHandler.EMBEDDING_DIM


class TestSimpleEmbeddingsHandlerAlias:
    """Test that SimpleEmbeddingsHandler is an alias."""

    def test_alias_exists(self):
        """
        Test that SimpleEmbeddingsHandler is an alias.

        Given: The module is imported
        When: Checking SimpleEmbeddingsHandler
        Then: It references SemanticEmbeddingsHandler
        """
        # Assert
        assert SimpleEmbeddingsHandler is SemanticEmbeddingsHandler
