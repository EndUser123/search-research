"""Tests for CHS v2 embeddings integration.

These tests verify the embeddings module that wraps the semantic daemon client
and provides utility functions for embedding validation and similarity computation.

Test file: P:\\\\\\__csf/src/knowledge/systems/chs/v2/tests/test_embeddings.py
Implementation: P:\\\\\\__csf/src/knowledge/systems/chs/v2/embeddings.py (to be created)

Run with: pytest P:\\\\\\__csf/src/knowledge/systems/chs/v2/tests/test_embeddings.py -v
"""

from unittest.mock import MagicMock

import numpy as np
import pytest


class TestEmbedClient:
    """Tests for EmbedClient wrapper class."""

    @pytest.fixture
    def mock_daemon_client(self):
        """Create a mock DaemonClient."""
        mock_client = MagicMock()
        return mock_client

    @pytest.fixture
    def embed_client(self, mock_daemon_client):
        """Create EmbedClient instance with mocked daemon client."""
        from core.chs.embeddings import EmbedClient

        return EmbedClient(daemon_client=mock_daemon_client)

    def test_embed_texts_returns_list_of_vectors(self, embed_client, mock_daemon_client):
        """Test that embed_texts() returns a list of embedding vectors.

        Given: An EmbedClient instance
        When: embed_texts() is called with a list of texts
        Then: Returns a list of embedding vectors (bytes)
        """
        texts = ["hello world", "test message"]
        expected_embeddings = [
            np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32).tobytes(),
            np.array([0.5, 0.6, 0.7, 0.8], dtype=np.float32).tobytes(),
        ]
        mock_daemon_client.embed_texts.return_value = expected_embeddings
        result = embed_client.embed_texts(texts)
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(emb, bytes) for emb in result)
        mock_daemon_client.embed_texts.assert_called_once_with(texts)

    def test_embed_texts_uses_retry_on_named_pipe_failure(self, embed_client, mock_daemon_client):
        """Test that embed_texts() uses retry logic on named pipe failure.

        Given: An EmbedClient instance
        When: Daemon connection fails temporarily
        Then: Retry logic is triggered before giving up
        """
        texts = ["test"]
        expected_embeddings = [np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32).tobytes()]
        mock_daemon_client.embed_texts.side_effect = [
            ConnectionError("Pipe not found"),
            expected_embeddings[0],
        ]
        result = embed_client.embed_texts(texts)
        assert mock_daemon_client.embed_texts.call_count == 2
        assert result == expected_embeddings

    def test_embed_texts_falls_back_to_dummy_on_persistent_failure(
        self, embed_client, mock_daemon_client
    ):
        """Test that embed_texts() falls back to dummy embedding on persistent failure.

        Given: An EmbedClient instance
        When: Daemon connection fails repeatedly
        Then: Falls back to dummy embedding generation
        """
        texts = ["test"]
        mock_daemon_client.embed_texts.side_effect = ConnectionError("Daemon unavailable")
        result = embed_client.embed_texts(texts)
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], bytes)


class TestValidateEmbeddingBlob:
    """Tests for validate_embedding_blob() function."""

    def test_validate_embedding_blob_raises_value_error_for_wrong_dimensions(self):
        """Test that validate_embedding_blob() raises ValueError for wrong dimensions.

        Given: An embedding blob with incorrect size
        When: validate_embedding_blob() is called
        Then: Raises ValueError with descriptive message
        """
        wrong_blob = b"\x00\x00\x00\x00"
        expected_dim = 4
        from core.chs.embeddings import validate_embedding_blob

        with pytest.raises(ValueError, match="Embedding size mismatch"):
            validate_embedding_blob(wrong_blob, expected_dim)

    def test_validate_embedding_blob_succeeds_for_correct_dimensions(self):
        """Test that validate_embedding_blob() succeeds for correct dimensions.

        Given: An embedding blob with correct size
        When: validate_embedding_blob() is called
        Then: Does not raise exception
        """
        correct_blob = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32).tobytes()
        expected_dim = 4
        from core.chs.embeddings import validate_embedding_blob

        validate_embedding_blob(correct_blob, expected_dim)


class TestValidateEmbeddingArray:
    """Tests for validate_embedding_array() function."""

    def test_validate_embedding_array_raises_value_error_for_wrong_dimensions(self):
        """Test that validate_embedding_array() raises ValueError for wrong dimensions.

        Given: A numpy array with incorrect shape
        When: validate_embedding_array() is called
        Then: Raises ValueError with descriptive message
        """
        wrong_array = np.array([0.1, 0.2], dtype=np.float32)
        expected_dim = 4
        from core.chs.embeddings import validate_embedding_array

        with pytest.raises(ValueError, match="Embedding shape mismatch"):
            validate_embedding_array(wrong_array, expected_dim)

    def test_validate_embedding_array_raises_value_error_for_wrong_dtype(self):
        """Test that validate_embedding_array() raises ValueError for wrong dtype.

        Given: A numpy array with incorrect dtype
        When: validate_embedding_array() is called
        Then: Raises ValueError with descriptive message
        """
        wrong_dtype_array = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float64)
        expected_dim = 4
        from core.chs.embeddings import validate_embedding_array

        with pytest.raises(ValueError, match="dtype must be float32"):
            validate_embedding_array(wrong_dtype_array, expected_dim)

    def test_validate_embedding_array_succeeds_for_correct_array(self):
        """Test that validate_embedding_array() succeeds for correct array.

        Given: A numpy array with correct shape and dtype
        When: validate_embedding_array() is called
        Then: Does not raise exception
        """
        correct_array = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
        expected_dim = 4
        from core.chs.embeddings import validate_embedding_array

        validate_embedding_array(correct_array, expected_dim)


class TestBytesToVector:
    """Tests for bytes_to_vector() function."""

    def test_bytes_to_vector_converts_blob_to_numpy_array(self):
        """Test that bytes_to_vector() converts blob to numpy array.

        Given: An embedding blob as bytes
        When: bytes_to_vector() is called
        Then: Returns numpy array with correct values
        """
        original_array = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
        blob = original_array.tobytes()
        dim = 4
        from core.chs.embeddings import bytes_to_vector

        result = bytes_to_vector(blob, dim)
        assert isinstance(result, np.ndarray)
        assert result.shape == (dim,)
        assert result.dtype == np.float32
        np.testing.assert_array_almost_equal(result, original_array)


class TestCosineSimilarity:
    """Tests for cosine_similarity() function."""

    def test_cosine_similarity_returns_1_for_identical_vectors(self):
        """Test that cosine_similarity() returns 1.0 for identical vectors.

        Given: Two identical vectors
        When: cosine_similarity() is called
        Then: Returns 1.0 (perfect similarity)
        """
        vec = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
        from core.chs.embeddings import cosine_similarity

        result = cosine_similarity(vec, vec)
        assert result == pytest.approx(1.0, rel=1e-05)

    def test_cosine_similarity_returns_0_for_orthogonal_vectors(self):
        """Test that cosine_similarity() returns 0.0 for orthogonal vectors.

        Given: Two orthogonal (perpendicular) vectors
        When: cosine_similarity() is called
        Then: Returns 0.0 (no similarity)
        """
        vec_a = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        vec_b = np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32)
        from core.chs.embeddings import cosine_similarity

        result = cosine_similarity(vec_a, vec_b)
        assert result == pytest.approx(0.0, abs=1e-05)

    def test_cosine_similarity_returns_0_for_zero_vector(self):
        """Test that cosine_similarity() returns 0.0 when either vector is zero.

        Given: One zero vector and one normal vector
        When: cosine_similarity() is called
        Then: Returns 0.0 (handles edge case)
        """
        zero_vec = np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32)
        normal_vec = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
        from core.chs.embeddings import cosine_similarity

        result = cosine_similarity(zero_vec, normal_vec)
        assert result == 0.0


class TestGetEmbedClient:
    """Tests for get_embed_client() factory function."""

    def test_get_embed_client_returns_singleton_instance(self):
        """Test that get_embed_client() returns a singleton instance.

        Given: Multiple calls to get_embed_client()
        When: The function is called multiple times
        Then: Returns the same instance (singleton pattern)
        """
        from core.chs.embeddings import get_embed_client

        client1 = get_embed_client()
        client2 = get_embed_client()
        assert client1 is client2
