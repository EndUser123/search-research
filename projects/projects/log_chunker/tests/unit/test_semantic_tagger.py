"""Unit tests for semantic_tagger module - CORRECTED VERSION."""

from unittest.mock import Mock, patch

import numpy as np
import pytest
from rich.console import Console
from src.log_chunker.config import ChunkingConfig
from src.log_chunker.data_models import ChunkInfo, LogEntry
from src.log_chunker.semantic_tagger import SemanticTagger


class TestSemanticTagger:
    """Test cases for SemanticTagger class."""

    @pytest.fixture
    def sample_config(self):
        """Create sample config for SemanticTagger."""
        return ChunkingConfig(
            semantic_model="sentence-transformers/all-MiniLM-L6-v2",
            min_cluster_size=2,
            min_samples=1,
        )

    @pytest.fixture
    def mock_console(self):
        """Create mock console."""
        console = Mock(spec=Console)
        console.get_time = Mock(return_value=0.0)
        console.is_jupyter = False
        console.is_interactive = True
        console.__enter__ = Mock(return_value=console)
        console.__exit__ = Mock(return_value=None)
        return console

    @pytest.fixture
    def sample_log_entries(self):
        """Create sample log entries for testing."""
        return [
            LogEntry(
                timestamp=None,
                level="INFO",
                message="Application started successfully",
                original_line="2025-07-14 10:00:00 - INFO - Application started successfully",
                line_number=1,
            ),
            LogEntry(
                timestamp=None,
                level="ERROR",
                message="Database connection failed",
                original_line="2025-07-14 10:00:01 - ERROR - Database connection failed",
                line_number=2,
            ),
        ]

    @pytest.fixture
    def sample_chunks(self):
        """Create sample chunks for testing."""
        return [
            (
                "Application started successfully",
                ChunkInfo(chunk_id=0, start_line=1, end_line=1, estimated_tokens=25),
            ),
            (
                "Database connection failed",
                ChunkInfo(chunk_id=1, start_line=2, end_line=2, estimated_tokens=20),
            ),
        ]

    @patch("src.log_chunker.semantic_tagger.SentenceTransformer")
    @patch("torch.cuda.is_available", return_value=False)
    def test_init_default_config(
        self, mock_cuda, mock_transformer, sample_config, mock_console
    ):
        """Test SemanticTagger initialization with default model."""
        mock_model = Mock()
        mock_transformer.return_value = mock_model

        tagger = SemanticTagger(sample_config, mock_console)

        assert tagger.config == sample_config
        assert tagger.console == mock_console
        assert tagger.model == mock_model
        mock_transformer.assert_called_once_with(sample_config.semantic_model)

    @patch("src.log_chunker.semantic_tagger.SentenceTransformer")
    @patch("torch.cuda.is_available", return_value=True)
    def test_init_with_gpu(
        self, mock_cuda, mock_transformer, sample_config, mock_console
    ):
        """Test SemanticTagger initialization with GPU available."""
        mock_model = Mock()
        mock_transformer.return_value = mock_model

        SemanticTagger(sample_config, mock_console)

        # Should log GPU availability
        mock_console.log.assert_called()
        gpu_log_calls = [
            call for call in mock_console.log.call_args_list if "GPU" in str(call)
        ]
        assert len(gpu_log_calls) > 0

    @patch("src.log_chunker.semantic_tagger.SentenceTransformer")
    @patch("src.log_chunker.semantic_tagger.HDBSCAN")
    @patch("rich.progress.Progress")
    def test_cluster_chunks_success(
        self,
        mock_progress,
        mock_hdbscan,
        mock_transformer,
        sample_chunks,
        sample_config,
        mock_console,
    ):
        """Test successful chunk clustering."""
        # Setup mocks
        mock_model = Mock()
        mock_embeddings = np.array([[0.1, 0.2], [0.3, 0.4]])
        mock_model.encode.return_value = mock_embeddings
        mock_transformer.return_value = mock_model

        mock_clusterer = Mock()
        mock_clusterer.fit_predict.return_value = np.array([0, 1])
        mock_hdbscan.return_value = mock_clusterer

        # Mock Progress context manager
        mock_progress_instance = Mock()
        mock_progress_instance.add_task = Mock(return_value="task_id")
        mock_progress_instance.update = Mock()
        mock_progress.__enter__ = Mock(return_value=mock_progress_instance)
        mock_progress.__exit__ = Mock(return_value=None)

        tagger = SemanticTagger(sample_config, mock_console)

        clusters = tagger.cluster_chunks(sample_chunks)

        # Verify clustering was called
        mock_model.encode.assert_called_once()
        mock_clusterer.fit_predict.assert_called_once()

        # Should return list of clusters
        assert isinstance(clusters, list)

    @patch("src.log_chunker.semantic_tagger.SentenceTransformer")
    def test_cluster_chunks_empty_input(
        self, mock_transformer, sample_config, mock_console
    ):
        """Test clustering with empty input."""
        mock_model = Mock()
        mock_transformer.return_value = mock_model

        tagger = SemanticTagger(sample_config, mock_console)

        clusters = tagger.cluster_chunks([])

        assert clusters == []
        # Should not call model.encode for empty input
        mock_model.encode.assert_not_called()

    @patch("src.log_chunker.semantic_tagger.SentenceTransformer")
    @patch("src.log_chunker.semantic_tagger.HDBSCAN")
    def test_label_clusters(
        self, mock_hdbscan, mock_transformer, sample_chunks, sample_config, mock_console
    ):
        """Test cluster labeling functionality."""
        mock_model = Mock()
        mock_transformer.return_value = mock_model

        tagger = SemanticTagger(sample_config, mock_console)

        # Test the _label_clusters method directly
        cluster_labels = np.array([0, 1, 0, -1])  # Two clusters + noise
        test_chunks = [
            ("Application started", ChunkInfo(0, 0, 1, 20)),
            ("Database failed", ChunkInfo(1, 1, 2, 20)),
            ("Application running", ChunkInfo(2, 2, 3, 20)),
            ("Random noise", ChunkInfo(3, 3, 4, 20)),
        ]

        clusters = tagger._label_clusters(cluster_labels, test_chunks)

        # Should create 2 clusters (ignoring noise label -1)
        assert len(clusters) == 2

        # Check cluster structure
        for cluster in clusters:
            assert hasattr(cluster, "cluster_id")
            assert hasattr(cluster, "label")
            assert hasattr(cluster, "chunk_ids")
            assert hasattr(cluster, "keywords")

    @patch("src.log_chunker.semantic_tagger.SentenceTransformer")
    def test_error_handling(self, mock_transformer, sample_config, mock_console):
        """Test error handling in SemanticTagger."""
        # Test with model that raises exception
        mock_transformer.side_effect = Exception("Model loading failed")

        with pytest.raises(Exception, match="Model loading failed"):
            SemanticTagger(sample_config, mock_console)
