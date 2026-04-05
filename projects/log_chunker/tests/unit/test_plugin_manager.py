"""Unit tests for plugin_manager module - CORRECTED VERSION."""

from unittest.mock import Mock, patch

import pytest
from rich.console import Console
from src.log_chunker.config import ChunkingConfig
from src.log_chunker.data_models import ChunkInfo
from src.log_chunker.plugin_manager import PluginManager
from src.log_chunker.plugins.base import BaseChunkingPlugin


class MockPlugin(BaseChunkingPlugin):
    """Mock plugin for testing."""

    def __init__(self, name="mock_plugin"):
        self.name = name
        self.enabled = True
        self.weight = 1.0

    def find_boundaries(self, log_lines):
        return [0, len(log_lines)]

    def score_chunk(self, chunk_text, chunk_info):
        return 0.5

    def analyze_chunks(self, chunks):
        return {"mock_analysis": "test_result"}


class MockPluginWithoutAnalysis(BaseChunkingPlugin):
    """Mock plugin without analyze_chunks method for backward compatibility testing."""

    def __init__(self, name="legacy_plugin"):
        self.name = name
        self.enabled = True
        self.weight = 1.0

    def find_boundaries(self, log_lines):
        return [0, len(log_lines)]

    def score_chunk(self, chunk_text, chunk_info):
        return 0.3

    def analyze_chunks(self, chunks):
        # Legacy plugin returns empty dict
        return {}


class TestPluginManager:
    """Test cases for PluginManager class."""

    @pytest.fixture
    def sample_config(self):
        """Create sample ChunkingConfig."""
        return ChunkingConfig(
            target_tokens=1000,
            enabled_plugins=["mock_plugin"],
            plugin_weights={"plugin1": 2.0, "plugin2": 1.0},
        )

    @pytest.fixture
    def mock_console(self):
        """Create mock console."""
        return Mock(spec=Console)

    @pytest.fixture
    def sample_chunks(self):
        """Create sample chunks for testing."""
        return [
            ("First chunk content", ChunkInfo(0, 0, 10, 50)),
            ("Second chunk content", ChunkInfo(1, 11, 20, 45)),
        ]

    def test_init(self, sample_config, mock_console):
        """Test PluginManager initialization."""
        with patch.object(PluginManager, "_load_core_plugins"):
            manager = PluginManager(sample_config, mock_console)
            assert manager.config == sample_config
            assert manager.console == mock_console

    def test_register_plugin(self, sample_config, mock_console):
        """Test plugin registration."""
        with patch.object(PluginManager, "_load_core_plugins"):
            manager = PluginManager(sample_config, mock_console)
            plugin = MockPlugin("test_plugin")

            manager.register_plugin("test_plugin", plugin)

            assert "test_plugin" in manager.plugins
            assert manager.plugins["test_plugin"] == plugin

    def test_validate_plugin_interface_valid(self, sample_config, mock_console):
        """Test plugin interface validation for valid plugin."""
        with patch.object(PluginManager, "_load_core_plugins"):
            manager = PluginManager(sample_config, mock_console)
            plugin = MockPlugin()

            is_valid = manager.validate_plugin_interface(plugin)

            assert is_valid

    def test_analyze_chunks_with_capable_plugins(
        self, sample_chunks, sample_config, mock_console
    ):
        """Test chunk analysis with analysis-capable plugins."""
        with patch.object(PluginManager, "_load_core_plugins"):
            manager = PluginManager(sample_config, mock_console)

            # Register plugin with analysis capability
            plugin = MockPlugin("test_plugin")
            manager.register_plugin("test_plugin", plugin)

            results = manager.run_analysis_plugins(sample_chunks)

            assert "test_plugin" in results
            assert results["test_plugin"]["mock_analysis"] == "test_result"

    def test_analyze_chunks_with_legacy_plugins(
        self, sample_chunks, sample_config, mock_console
    ):
        """Test chunk analysis with legacy plugins (no analyze_chunks method)."""
        with patch.object(PluginManager, "_load_core_plugins"):
            manager = PluginManager(sample_config, mock_console)

            # Register legacy plugin
            legacy_plugin = MockPluginWithoutAnalysis("legacy_plugin")
            manager.register_plugin("legacy_plugin", legacy_plugin)

            results = manager.run_analysis_plugins(sample_chunks)

            # Legacy plugin should return empty dict
            assert "legacy_plugin" in results
            assert results["legacy_plugin"] == {}

    def test_score_chunk_weighted_average(self, sample_config, mock_console):
        """Test chunk scoring with weighted average across plugins."""
        with patch.object(PluginManager, "_load_core_plugins"):
            manager = PluginManager(sample_config, mock_console)

            # Create plugins with different scores and weights
            plugin1 = MockPlugin("plugin1")
            plugin1.weight = 2.0
            plugin1.score_chunk = Mock(return_value=0.8)

            plugin2 = MockPlugin("plugin2")
            plugin2.weight = 1.0
            plugin2.score_chunk = Mock(return_value=0.4)

            manager.register_plugin("plugin1", plugin1)
            manager.register_plugin("plugin2", plugin2)

            chunk_info = ChunkInfo(0, 0, 10, 50)
            manager.score_chunks([("test chunk", chunk_info)])
            score = chunk_info.quality_score

            # Weighted average: (0.8 * 2.0 + 0.4 * 1.0) / (2.0 + 1.0) = 2.0 / 3.0 = 0.667
            expected_score = (0.8 * 2.0 + 0.4 * 1.0) / (2.0 + 1.0)
            assert abs(score - expected_score) < 1e-3
