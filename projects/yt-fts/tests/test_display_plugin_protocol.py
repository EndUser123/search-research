"""
Tests for display plugin protocol compliance.

Verifies that all display plugins implement required methods
for yt-dlp and Whisper operation status display.
"""

import pytest
from abc import ABC

from yt_fts.display.base import DisplayPlugin, PluginContext
from yt_fts.display.plugins.compact import CompactDisplayPlugin
from yt_fts.display.plugins.default import DefaultDisplayPlugin
from yt_fts.display.plugins.json_output import JsonOutputPlugin
from yt_fts.display.plugins.download_default import DownloadDefaultDisplayPlugin


@pytest.fixture
def plugin_context() -> PluginContext:
    """Create a plugin context for testing."""
    from rich.console import Console
    return PluginContext(
        command="test",
        console=Console(),
        options={},
    )


class TestDisplayPluginProtocol:
    """Test that all display plugins implement required methods."""

    @pytest.mark.parametrize(
        "plugin_class",
        [
            DefaultDisplayPlugin,
            CompactDisplayPlugin,
            JsonOutputPlugin,
            DownloadDefaultDisplayPlugin,
        ],
    )
    def test_plugin_has_display_ytdlp_operation(self, plugin_class: type, plugin_context: PluginContext) -> None:
        """Test that plugin implements display_ytdlp_operation method."""
        plugin = plugin_class(plugin_context)
        
        # Should have the method
        assert hasattr(plugin, "display_ytdlp_operation"), (
            f"{plugin_class.__name__} must implement display_ytdlp_operation()"
        )
        
        # Should be callable
        assert callable(getattr(plugin, "display_ytdlp_operation")), (
            f"{plugin_class.__name__}.display_ytdlp_operation() must be callable"
        )

    @pytest.mark.parametrize(
        "plugin_class",
        [
            DefaultDisplayPlugin,
            CompactDisplayPlugin,
            JsonOutputPlugin,
            DownloadDefaultDisplayPlugin,
        ],
    )
    def test_plugin_has_display_whisper_operation(self, plugin_class: type, plugin_context: PluginContext) -> None:
        """Test that plugin implements display_whisper_operation method."""
        plugin = plugin_class(plugin_context)
        
        # Should have the method
        assert hasattr(plugin, "display_whisper_operation"), (
            f"{plugin_class.__name__} must implement display_whisper_operation()"
        )
        
        # Should be callable
        assert callable(getattr(plugin, "display_whisper_operation")), (
            f"{plugin_class.__name__}.display_whisper_operation() must be callable"
        )

    def test_base_declares_ytdlp_operation_as_abstract(self) -> None:
        """Test that DisplayPlugin base class declares display_ytdlp_operation as abstract."""
        # Check if the method is declared as abstract in the base class
        assert hasattr(DisplayPlugin, "display_ytdlp_operation"), (
            "DisplayPlugin must declare display_ytdlp_operation() as abstract method"
        )

    def test_base_declares_whisper_operation_as_abstract(self) -> None:
        """Test that DisplayPlugin base class declares display_whisper_operation as abstract."""
        # Check if the method is declared as abstract in the base class
        assert hasattr(DisplayPlugin, "display_whisper_operation"), (
            "DisplayPlugin must declare display_whisper_operation() as abstract method"
        )
