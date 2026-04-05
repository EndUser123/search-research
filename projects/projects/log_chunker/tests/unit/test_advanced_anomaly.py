from unittest.mock import Mock, patch

from src.log_chunker.config import ChunkingConfig
from src.log_chunker.data_models import ChunkInfo, LogEntry
from src.log_chunker.plugins.enhanced.advanced_anomaly import AdvancedAnomalyPlugin


class TestAdvancedAnomalyPlugin:
    def setup_method(self):
        """Setup for each test"""
        self.config = ChunkingConfig()
        self.console = Mock()

    def test_initialization_without_dependencies(self):
        """Test plugin falls back gracefully without dependencies"""
        with patch(
            "src.log_chunker.plugins.enhanced.advanced_anomaly.HAS_SKLEARN_DEPS", False
        ):
            plugin = AdvancedAnomalyPlugin()
            result = plugin.initialize(self.config, self.console)
            assert result
            assert plugin.use_fallback

    def test_fallback_implementation_works(self):
        """Test fallback provides basic functionality"""
        with patch(
            "src.log_chunker.plugins.enhanced.advanced_anomaly.HAS_SKLEARN_DEPS", False
        ):
            plugin = AdvancedAnomalyPlugin()
            plugin.initialize(self.config, self.console)

            log_entries = [
                LogEntry(
                    message="normal log entry one",
                    original_line="normal log entry one",
                    pattern="normal",
                    language="en",
                    line_number=1,
                ),
                LogEntry(
                    message="critical system failure detected",
                    original_line="critical system failure detected",
                    pattern="error",
                    language="en",
                    line_number=2,
                ),
                LogEntry(
                    message="normal log entry two",
                    original_line="normal log entry two",
                    pattern="normal",
                    language="en",
                    line_number=3,
                ),
                LogEntry(
                    message="unusual anomalous behavior",
                    original_line="unusual anomalous behavior",
                    pattern="anomaly",
                    language="en",
                    line_number=4,
                ),
                LogEntry(
                    message="normal log entry three",
                    original_line="normal log entry three",
                    pattern="normal",
                    language="en",
                    line_number=5,
                ),
            ]

            boundaries = plugin.find_boundaries("test text", log_entries)
            assert isinstance(boundaries, list)

    def test_score_chunk_fallback(self):
        """Test chunk scoring works with fallback"""
        with patch(
            "src.log_chunker.plugins.enhanced.advanced_anomaly.HAS_SKLEARN_DEPS", False
        ):
            plugin = AdvancedAnomalyPlugin()
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
            "src.log_chunker.plugins.enhanced.advanced_anomaly.HAS_SKLEARN_DEPS", False
        ):
            plugin = AdvancedAnomalyPlugin()
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
            assert "advanced_anomaly" in result
            assert result["advanced_anomaly"]["fallback_mode"]

    def test_plugin_attributes(self):
        """Test plugin has required attributes"""
        plugin = AdvancedAnomalyPlugin()

        assert hasattr(plugin, "name")
        assert hasattr(plugin, "version")
        assert hasattr(plugin, "dependencies")
        assert plugin.name == "advanced_anomaly"
        assert isinstance(plugin.dependencies, list)
        assert "scikit-learn" in plugin.dependencies

    def test_empty_log_entries(self):
        """Test plugin handles empty log entries gracefully"""
        with patch(
            "src.log_chunker.plugins.enhanced.advanced_anomaly.HAS_SKLEARN_DEPS", False
        ):
            plugin = AdvancedAnomalyPlugin()
            plugin.initialize(self.config, self.console)

            boundaries = plugin.find_boundaries("", [])
            assert boundaries == []

    def test_insufficient_log_entries(self):
        """Test plugin handles insufficient log entries gracefully"""
        with patch(
            "src.log_chunker.plugins.enhanced.advanced_anomaly.HAS_SKLEARN_DEPS", False
        ):
            plugin = AdvancedAnomalyPlugin()
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

    def test_configuration_integration(self):
        """Test plugin uses configuration correctly"""
        config = ChunkingConfig()
        config.advanced_anomaly.contamination = 0.15
        config.advanced_anomaly.n_estimators = 200

        plugin = AdvancedAnomalyPlugin()
        console = Mock()

        # Test with mocked dependencies
        with patch(
            "src.log_chunker.plugins.enhanced.advanced_anomaly.HAS_SKLEARN_DEPS", True
        ), patch(
            "src.log_chunker.plugins.enhanced.advanced_anomaly.IsolationForest"
        ) as mock_forest, patch(
            "src.log_chunker.plugins.enhanced.advanced_anomaly.TfidfVectorizer"
        ):
            result = plugin.initialize(config, console)
            assert result

            # Verify IsolationForest was called with correct parameters
            mock_forest.assert_called_once()
            call_kwargs = mock_forest.call_args[1]
            assert call_kwargs["contamination"] == 0.15
            assert call_kwargs["n_estimators"] == 200

    def test_fallback_frequency_based_detection(self):
        """Test fallback frequency-based anomaly detection"""
        with patch(
            "src.log_chunker.plugins.enhanced.advanced_anomaly.HAS_SKLEARN_DEPS", False
        ):
            plugin = AdvancedAnomalyPlugin()
            plugin.initialize(self.config, self.console)

            # Create log entries with mostly similar patterns and one rare pattern
            log_entries = []

            # Add many similar entries
            for i in range(20):
                log_entries.append(
                    LogEntry(
                        message="normal application startup complete",
                        original_line="normal application startup complete",
                        pattern="startup",
                        language="en",
                        line_number=i + 1,
                    )
                )

            # Add one rare entry that should be detected as anomaly
            log_entries.append(
                LogEntry(
                    message="extremely rare catastrophic system meltdown detected",
                    original_line="extremely rare catastrophic system meltdown detected",
                    pattern="rare",
                    language="en",
                    line_number=21,
                )
            )

            boundaries = plugin.find_boundaries("test", log_entries)

            # Should detect the rare entry as a boundary
            assert isinstance(boundaries, list)
            # The rare entry should create a boundary
            assert 21 in boundaries or len(boundaries) > 0
