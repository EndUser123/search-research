from unittest.mock import Mock, patch

from src.log_chunker.config import ChunkingConfig
from src.log_chunker.data_models import ChunkInfo, LogEntry
from src.log_chunker.plugins.enhanced.semantic_clustering import (
    SemanticClusteringPlugin,
)


class TestSemanticClusteringPlugin:
    def setup_method(self):
        """Setup for each test"""
        self.config = ChunkingConfig()
        self.console = Mock()

    def test_initialization_without_dependencies(self):
        """Test plugin falls back gracefully without dependencies"""
        with patch(
            "src.log_chunker.plugins.enhanced.semantic_clustering.HAS_SEMANTIC_DEPS",
            False,
        ):
            plugin = SemanticClusteringPlugin()
            result = plugin.initialize(self.config, self.console)
            assert result
            assert plugin.use_fallback

    def test_fallback_implementation_works(self):
        """Test fallback provides basic functionality"""
        with patch(
            "src.log_chunker.plugins.enhanced.semantic_clustering.HAS_SEMANTIC_DEPS",
            False,
        ):
            plugin = SemanticClusteringPlugin()
            plugin.initialize(self.config, self.console)

            log_entries = [
                LogEntry(
                    message="auth failed user john",
                    original_line="auth failed user john",
                    pattern="auth",
                    language="en",
                    line_number=1,
                ),
                LogEntry(
                    message="database connection timeout",
                    original_line="database connection timeout",
                    pattern="db",
                    language="en",
                    line_number=2,
                ),
                LogEntry(
                    message="auth failed user jane",
                    original_line="auth failed user jane",
                    pattern="auth",
                    language="en",
                    line_number=3,
                ),
            ]

            boundaries = plugin.find_boundaries("test text", log_entries)
            assert isinstance(boundaries, list)

    def test_score_chunk_fallback(self):
        """Test chunk scoring works with fallback"""
        with patch(
            "src.log_chunker.plugins.enhanced.semantic_clustering.HAS_SEMANTIC_DEPS",
            False,
        ):
            plugin = SemanticClusteringPlugin()
            plugin.initialize(self.config, self.console)

            chunk_info = ChunkInfo(
                chunk_id=1, start_line=1, end_line=5, estimated_tokens=100
            )
            score = plugin.score_chunk("test chunk content", chunk_info)

            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0

    def test_analyze_chunks_fallback(self):
        """Test chunk analysis works with fallback"""
        with patch(
            "src.log_chunker.plugins.enhanced.semantic_clustering.HAS_SEMANTIC_DEPS",
            False,
        ):
            plugin = SemanticClusteringPlugin()
            plugin.initialize(self.config, self.console)

            chunks = [
                (
                    "test chunk 1",
                    ChunkInfo(
                        chunk_id=1, start_line=1, end_line=2, estimated_tokens=50
                    ),
                )
            ]
            result = plugin.analyze_chunks(chunks)

            assert isinstance(result, dict)
            assert "semantic_clustering" in result
            assert result["semantic_clustering"]["fallback_mode"]

    def test_plugin_attributes(self):
        """Test plugin has required attributes"""
        plugin = SemanticClusteringPlugin()

        assert hasattr(plugin, "name")
        assert hasattr(plugin, "version")
        assert hasattr(plugin, "dependencies")
        assert plugin.name == "semantic_clustering"
        assert isinstance(plugin.dependencies, list)

    def test_empty_log_entries(self):
        """Test plugin handles empty log entries gracefully"""
        with patch(
            "src.log_chunker.plugins.enhanced.semantic_clustering.HAS_SEMANTIC_DEPS",
            False,
        ):
            plugin = SemanticClusteringPlugin()
            plugin.initialize(self.config, self.console)

            boundaries = plugin.find_boundaries("", [])
            assert boundaries == []

    def test_single_log_entry(self):
        """Test plugin handles single log entry gracefully"""
        with patch(
            "src.log_chunker.plugins.enhanced.semantic_clustering.HAS_SEMANTIC_DEPS",
            False,
        ):
            plugin = SemanticClusteringPlugin()
            plugin.initialize(self.config, self.console)

            log_entries = [
                LogEntry(
                    message="single log entry",
                    original_line="single log entry",
                    pattern="test",
                    language="en",
                    line_number=1,
                )
            ]

            boundaries = plugin.find_boundaries("test", log_entries)
            assert boundaries == []
