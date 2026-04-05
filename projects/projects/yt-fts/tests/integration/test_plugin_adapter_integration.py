"""
Integration tests for display plugin adapter system.

Tests the integration between legacy plugin adapter, registry,
and base plugin classes for the refactored display system.
"""

from io import StringIO
from unittest.mock import MagicMock, Mock, patch
from dataclasses import dataclass, field
from typing import Any

import pytest
from rich.console import Console

from yt_fts.display.base import DisplayPlugin, PluginContext
from yt_fts.display.legacy_adapter import LegacyDisplayPluginAdapter, wrap_legacy_plugin
from yt_fts.display.registry import (
    DisplayPluginRegistry,
    get_registry,
    register_plugin,
    list_plugins,
    list_plugins_for_command,
)


# =============================================================================
# Mock/Fixtures
# =============================================================================

@dataclass
class MockLegacyPlugin:
    """A mock legacy plugin with required methods."""

    console: Console
    verbose: bool = True
    _calls: list = field(default_factory=list)

    def display_channel_header(self, channel_info: dict) -> None:
        self._calls.append(("display_channel_header", channel_info))

    def display_rss_status(self, rss_info: dict) -> None:
        self._calls.append(("display_rss_status", rss_info))

    def display_download_result(self, result_info: dict) -> None:
        self._calls.append(("display_download_result", result_info))

    def display_batch_summary(self, summary_info: dict) -> None:
        self._calls.append(("display_batch_summary", summary_info))


@dataclass
class MockLegacyPluginWithCleanup:
    """A mock legacy plugin with cleanup method."""

    console: Console
    _cleaned: bool = False

    def display_channel_header(self, channel_info: dict) -> None:
        pass

    def display_rss_status(self, rss_info: dict) -> None:
        pass

    def display_download_result(self, result_info: dict) -> None:
        pass

    def display_batch_summary(self, summary_info: dict) -> None:
        pass

    def cleanup(self) -> None:
        self._cleaned = True


class SimpleDisplayPlugin(DisplayPlugin):
    """A simple modern display plugin for testing."""

    supported_commands = ["search", "download"]

    def get_name(self) -> str:
        return "simple_test"

    def display_search_results(self, results: dict) -> None:
        self.console.print(f"Search results: {results.get('total_matches', 0)} matches")


class MinimalDisplayPlugin(DisplayPlugin):
    """A minimal plugin with no command restrictions."""

    def get_name(self) -> str:
        return "minimal"


# =============================================================================
# PluginContext Tests
# =============================================================================

class TestPluginContext:
    """Test PluginContext dataclass."""

    def test_create_plugin_context(self):
        """Should create context with all fields."""
        console = Console()
        context = PluginContext(
            command="search",
            console=console,
            options={"verbose": True},
            config_dir="/config",
            db_path="/db.sqlite"
        )

        assert context.command == "search"
        assert context.console is console
        assert context.options == {"verbose": True}
        assert context.config_dir == "/config"
        assert context.db_path == "/db.sqlite"

    def test_plugin_context_defaults(self):
        """Should use defaults for optional fields."""
        console = Console()
        context = PluginContext(command="search", console=console)

        assert context.options == {}
        assert context.config_dir is None
        assert context.db_path is None

    def test_get_option_returns_value(self):
        """Should return option value when key exists."""
        context = PluginContext(
            command="search",
            console=Console(),
            options={"key1": "value1", "key2": "value2"}
        )

        assert context.get_option("key1") == "value1"
        assert context.get_option("key2") == "value2"

    def test_get_option_returns_default_when_missing(self):
        """Should return default when key doesn't exist."""
        context = PluginContext(
            command="search",
            console=Console(),
            options={"existing": "value"}
        )

        assert context.get_option("nonexistent") is None
        assert context.get_option("nonexistent", "default") == "default"


# =============================================================================
# DisplayPlugin Base Tests
# =============================================================================

class TestDisplayPluginBase:
    """Test DisplayPlugin abstract base class."""

    def test_cannot_instantiate_base_class(self):
        """Should not allow direct instantiation of DisplayPlugin."""
        context = PluginContext(command="search", console=Console())

        with pytest.raises(TypeError):
            DisplayPlugin(context)

    def test_concrete_plugin_can_be_instantiated(self):
        """Concrete plugin implementing get_name should work."""
        context = PluginContext(command="search", console=Console())
        plugin = SimpleDisplayPlugin(context)

        assert plugin.context is context
        assert plugin.console is context.console
        assert plugin.command == "search"
        assert plugin.options == {}

    def test_plugin_get_name(self):
        """get_name should return plugin identifier."""
        context = PluginContext(command="search", console=Console())
        plugin = SimpleDisplayPlugin(context)

        assert plugin.get_name() == "simple_test"

    def test_plugin_configure_updates_options(self):
        """configure should merge options into self.options."""
        context = PluginContext(command="search", console=Console())
        plugin = SimpleDisplayPlugin(context)

        plugin.configure({"new_option": "value"})

        assert plugin.options == {"new_option": "value"}

    def test_plugin_configure_extends_existing_options(self):
        """configure should extend, not replace existing options."""
        context = PluginContext(
            command="search",
            console=Console(),
            options={"existing": "value"}
        )
        plugin = SimpleDisplayPlugin(context)

        plugin.configure({"new_option": "new_value"})

        assert plugin.options == {"existing": "value", "new_option": "new_value"}

    def test_supports_command_with_supported_commands_list(self):
        """Should check against supported_commands list."""
        context = PluginContext(command="search", console=Console())
        plugin = SimpleDisplayPlugin(context)

        assert plugin.supports_command("search") is True
        assert plugin.supports_command("download") is True
        assert plugin.supports_command("status") is False

    def test_supports_all_commands_when_list_empty(self):
        """Should support all commands when supported_commands is empty."""
        context = PluginContext(command="search", console=Console())
        plugin = MinimalDisplayPlugin(context)

        assert plugin.supports_command("search") is True
        assert plugin.supports_command("any_command") is True


# =============================================================================
# LegacyDisplayPluginAdapter Tests
# =============================================================================

class TestLegacyDisplayPluginAdapter:
    """Test LegacyDisplayPluginAdapter class."""

    def test_adapter_requires_all_legacy_methods(self):
        """Should raise TypeError if legacy plugin missing required methods."""
        console = Console()
        context = PluginContext(command="download", console=console)

        @dataclass
        class IncompleteLegacyPlugin:
            console: Console
            # Missing all required methods

        with pytest.raises(TypeError) as exc_info:
            LegacyDisplayPluginAdapter(context, IncompleteLegacyPlugin(console=console))

        # Should mention at least one of the required methods
        error_msg = str(exc_info.value).lower()
        assert any(method in error_msg for method in [
            "display_channel_header",
            "display_rss_status",
            "display_download_result",
            "display_batch_summary"
        ])

    def test_adapter_delegates_channel_header(self):
        """Should delegate display_channel_header to legacy plugin."""
        console = Console()
        context = PluginContext(command="download", console=console)
        legacy = MockLegacyPlugin(console=console)

        adapter = LegacyDisplayPluginAdapter(context, legacy)

        channel_info = {"index": 1, "total": 5, "name": "Test Channel"}
        adapter.display_channel_header(channel_info)

        assert legacy._calls == [("display_channel_header", channel_info)]

    def test_adapter_delegates_rss_status(self):
        """Should delegate display_rss_status to legacy plugin."""
        console = Console()
        context = PluginContext(command="download", console=console)
        legacy = MockLegacyPlugin(console=console)

        adapter = LegacyDisplayPluginAdapter(context, legacy)

        rss_info = {"status": "new_videos", "message": "Found 10 new videos"}
        adapter.display_rss_status(rss_info)

        assert legacy._calls == [("display_rss_status", rss_info)]

    def test_adapter_delegates_download_result(self):
        """Should delegate display_download_result to legacy plugin."""
        console = Console()
        context = PluginContext(command="download", console=console)
        legacy = MockLegacyPlugin(console=console)

        adapter = LegacyDisplayPluginAdapter(context, legacy)

        result_info = {"success": True, "videos_count": 5}
        adapter.display_download_result(result_info)

        assert legacy._calls == [("display_download_result", result_info)]

    def test_adapter_delegates_batch_summary(self):
        """Should delegate display_batch_summary to legacy plugin."""
        console = Console()
        context = PluginContext(command="download", console=console)
        legacy = MockLegacyPlugin(console=console)

        adapter = LegacyDisplayPluginAdapter(context, legacy)

        summary_info = {"total_channels": 5, "total_videos": 50}
        adapter.display_batch_summary(summary_info)

        assert legacy._calls == [("display_batch_summary", summary_info)]

    def test_adapter_no_op_for_unsupported_methods(self):
        """Should provide no-op implementations for unsupported methods."""
        console = Console()
        context = PluginContext(command="download", console=console)
        legacy = MockLegacyPlugin(console=console)

        adapter = LegacyDisplayPluginAdapter(context, legacy)

        # These should not raise
        adapter.display_search_results({})
        adapter.display_status({})
        adapter.display_import_progress({})
        adapter.display_import_result({})

    def test_adapter_cleanup_delegates_to_legacy(self):
        """Should delegate cleanup to legacy plugin if it exists."""
        console = Console()
        context = PluginContext(command="download", console=console)
        legacy = MockLegacyPluginWithCleanup(console=console)

        adapter = LegacyDisplayPluginAdapter(context, legacy)
        adapter.cleanup()

        assert legacy._cleaned is True

    def test_adapter_cleanup_no_op_when_not_defined(self):
        """Should handle cleanup when legacy plugin doesn't have it."""
        console = Console()
        context = PluginContext(command="download", console=console)
        legacy = MockLegacyPlugin(console=console)

        adapter = LegacyDisplayPluginAdapter(context, legacy)

        # Should not raise
        adapter.cleanup()

    def test_adapter_get_name_prefixes_legacy(self):
        """get_name should prefix legacy plugin class name."""
        console = Console()
        context = PluginContext(command="download", console=console)
        legacy = MockLegacyPlugin(console=console)

        adapter = LegacyDisplayPluginAdapter(context, legacy)

        assert adapter.get_name() == "legacy_MockLegacyPlugin"

    def test_adapter_configure_updates_adapter_options(self):
        """configure should update adapter options (not passed to legacy)."""
        console = Console()
        context = PluginContext(command="download", console=console)
        legacy = MockLegacyPlugin(console=console)

        adapter = LegacyDisplayPluginAdapter(context, legacy)
        adapter.configure({"new_option": "value"})

        assert adapter.options == {"new_option": "value"}

    def test_adapter_emits_deprecation_warning(self):
        """Should emit DeprecationWarning on initialization."""
        console = Console()
        context = PluginContext(command="download", console=console)
        legacy = MockLegacyPlugin(console=console)

        with pytest.warns(DeprecationWarning) as warnings:
            LegacyDisplayPluginAdapter(context, legacy)

        assert len(warnings) == 1
        assert "deprecated" in str(warnings[0].message).lower()

    def test_supported_commands_is_download_only(self):
        """Adapter should only support 'download' command."""
        console = Console()
        context = PluginContext(command="download", console=console)
        legacy = MockLegacyPlugin(console=console)

        adapter = LegacyDisplayPluginAdapter(context, legacy)

        assert adapter.supported_commands == ["download"]
        assert adapter.supports_command("download") is True
        assert adapter.supports_command("search") is False


# =============================================================================
# wrap_legacy_plugin Tests
# =============================================================================

class TestWrapLegacyPlugin:
    """Test wrap_legacy_plugin factory function."""

    def test_wraps_plugin_with_console_and_verbose(self):
        """Should wrap legacy plugin with console and verbose params."""
        console = Console()
        context = PluginContext(command="download", console=console, options={"verbose": True})

        adapter = wrap_legacy_plugin(MockLegacyPlugin, context)

        assert isinstance(adapter, LegacyDisplayPluginAdapter)
        assert adapter.legacy_plugin.console is console

    def test_wraps_plugin_with_console_only(self):
        """Should wrap legacy plugin with console param only."""
        console = Console()
        context = PluginContext(command="download", console=console)

        @dataclass
        class ConsoleOnlyPlugin:
            console: Console

            def display_channel_header(self, info): pass
            def display_rss_status(self, info): pass
            def display_download_result(self, info): pass
            def display_batch_summary(self, info): pass

        adapter = wrap_legacy_plugin(ConsoleOnlyPlugin, context)

        assert isinstance(adapter, LegacyDisplayPluginAdapter)

    def test_wraps_plugin_with_no_params(self):
        """Should wrap legacy plugin - tests fallthrough behavior."""
        console = Console()
        context = PluginContext(command="download", console=console)

        # Note: The wrap_legacy_plugin always tries console param first
        # If the plugin doesn't support it, this test documents that limitation
        class MinimalParamPlugin:
            def __init__(self, console=None):
                self.console = console

            def display_channel_header(self, info): pass
            def display_rss_status(self, info): pass
            def display_download_result(self, info): pass
            def display_batch_summary(self, info): pass

        adapter = wrap_legacy_plugin(MinimalParamPlugin, context)

        assert isinstance(adapter, LegacyDisplayPluginAdapter)


# =============================================================================
# DisplayPluginRegistry Tests
# =============================================================================

class TestDisplayPluginRegistry:
    """Test DisplayPluginRegistry class."""

    def test_register_plugin_adds_to_registry(self):
        """Should add plugin class to registry."""
        registry = DisplayPluginRegistry()

        registry.register_plugin("simple", SimpleDisplayPlugin)

        assert "simple" in registry.list_plugins()

    def test_register_plugin_requires_display_plugin_subclass(self):
        """Should raise TypeError if not a DisplayPlugin subclass."""
        registry = DisplayPluginRegistry()

        class NotAPlugin:
            pass

        with pytest.raises(TypeError) as exc_info:
            registry.register_plugin("invalid", NotAPlugin)

        assert "must inherit from DisplayPlugin" in str(exc_info.value)

    def test_unregister_plugin_removes_from_registry(self):
        """Should remove plugin from registry."""
        registry = DisplayPluginRegistry()
        registry.register_plugin("simple", SimpleDisplayPlugin)

        registry.unregister_plugin("simple")

        assert "simple" not in registry.list_plugins()

    def test_unregister_raises_for_nonexistent_plugin(self):
        """Should raise KeyError when unregistering nonexistent plugin."""
        registry = DisplayPluginRegistry()

        with pytest.raises(KeyError) as exc_info:
            registry.unregister_plugin("nonexistent")

        assert "not found" in str(exc_info.value)

    def test_get_plugin_returns_plugin_class(self):
        """Should return registered plugin class."""
        registry = DisplayPluginRegistry()
        registry.register_plugin("simple", SimpleDisplayPlugin)

        plugin_class = registry.get_plugin("simple")

        assert plugin_class is SimpleDisplayPlugin

    def test_get_plugin_raises_for_nonexistent(self):
        """Should raise KeyError when getting nonexistent plugin."""
        registry = DisplayPluginRegistry()

        with pytest.raises(KeyError):
            registry.get_plugin("nonexistent")

    def test_list_plugins_returns_all_registered_names(self):
        """Should return list of all registered plugin names."""
        registry = DisplayPluginRegistry()
        registry.register_plugin("simple", SimpleDisplayPlugin)
        registry.register_plugin("minimal", MinimalDisplayPlugin)

        names = registry.list_plugins()

        assert set(names) == {"simple", "minimal"}

    def test_list_plugins_for_command_filters_by_supported_commands(self):
        """Should return plugins that support specific command."""
        registry = DisplayPluginRegistry()
        registry.register_plugin("simple", SimpleDisplayPlugin)  # supports search, download
        registry.register_plugin("minimal", MinimalDisplayPlugin)  # supports all

        search_plugins = registry.list_plugins_for_command("search")
        status_plugins = registry.list_plugins_for_command("status")

        assert "simple" in search_plugins
        assert "minimal" in search_plugins
        assert "simple" not in status_plugins  # SimpleDisplayPlugin doesn't support status
        assert "minimal" in status_plugins  # MinimalDisplayPlugin supports all

    def test_create_plugin_instantiates_with_context(self):
        """Should create plugin instance with context."""
        registry = DisplayPluginRegistry()
        registry.register_plugin("simple", SimpleDisplayPlugin)

        console = Console()
        context = PluginContext(command="search", console=console)

        plugin = registry.create_plugin("simple", context)

        assert isinstance(plugin, SimpleDisplayPlugin)
        assert plugin.context is context

    def test_create_default_plugin_finds_by_command(self):
        """Should find plugin that supports the command."""
        registry = DisplayPluginRegistry()
        registry.register_plugin("simple", SimpleDisplayPlugin)

        console = Console()
        context = PluginContext(command="search", console=console)

        plugin = registry.create_default_plugin(context, command="search")

        assert isinstance(plugin, SimpleDisplayPlugin)

    def test_create_default_plugin_uses_default_plugin_name(self):
        """Should use plugin named 'default' when no command match."""
        registry = DisplayPluginRegistry()

        class DefaultPlugin(DisplayPlugin):
            def get_name(self): return "default"

        registry.register_plugin("default", DefaultPlugin)

        console = Console()
        context = PluginContext(command="search", console=console)

        plugin = registry.create_default_plugin(context, command="unsupported")

        assert isinstance(plugin, DefaultPlugin)

    def test_create_default_plugin_falls_back_to_first_registered(self):
        """Should use first registered plugin when no default found."""
        registry = DisplayPluginRegistry()
        registry.register_plugin("minimal", MinimalDisplayPlugin)

        console = Console()
        context = PluginContext(command="search", console=console)

        plugin = registry.create_default_plugin(context)

        assert isinstance(plugin, MinimalDisplayPlugin)

    def test_create_default_plugin_raises_when_empty_registry(self):
        """Should raise KeyError when registry is empty."""
        registry = DisplayPluginRegistry()

        console = Console()
        context = PluginContext(command="search", console=console)

        with pytest.raises(KeyError) as exc_info:
            registry.create_default_plugin(context)

        assert "No plugins registered" in str(exc_info.value)


# =============================================================================
# Global Registry Function Tests
# =============================================================================

class TestGlobalRegistry:
    """Test global registry functions."""

    def test_get_registry_returns_singleton(self):
        """get_registry should return the same instance."""
        registry1 = get_registry()
        registry2 = get_registry()

        assert registry1 is registry2

    def test_register_plugin_adds_to_global_registry(self):
        """Should add plugin to global registry."""
        # Use unique name to avoid conflicts
        plugin_name = "test_simple_global"

        try:
            register_plugin(plugin_name, SimpleDisplayPlugin)
            assert plugin_name in list_plugins()
        finally:
            # Cleanup
            registry = get_registry()
            if plugin_name in registry._plugins:
                del registry._plugins[plugin_name]

    def test_list_plugins_returns_from_global_registry(self):
        """Should return plugins from global registry."""
        # Just verify the function works
        plugins = list_plugins()
        assert isinstance(plugins, list)

    def test_list_plugins_for_command_from_global(self):
        """Should filter global registry by command."""
        search_plugins = list_plugins_for_command("search")
        assert isinstance(search_plugins, list)


# =============================================================================
# Integration Tests
# =============================================================================

class TestPluginAdapterIntegration:
    """Integration tests for complete adapter workflow."""

    def test_full_legacy_adapter_workflow(self):
        """Test complete workflow: legacy plugin -> adapter -> registry -> usage."""
        console = Console()
        context = PluginContext(command="download", console=console)
        legacy = MockLegacyPlugin(console=console)

        # Create adapter
        adapter = LegacyDisplayPluginAdapter(context, legacy)

        # Use adapter for download workflow
        adapter.display_channel_header({
            "index": 1,
            "total": 3,
            "name": "Test Channel",
            "db_count": 10,
            "db_stats": "10 videos"
        })

        adapter.display_rss_status({
            "status": "new_videos",
            "message": "Found 5 new videos",
            "scan_count": 5
        })

        adapter.display_download_result({
            "success": True,
            "videos_count": 3,
            "total_videos": 5
        })

        adapter.display_batch_summary({
            "total_channels": 1,
            "total_videos": 3,
            "successful_downloads": 1
        })

        # Verify all calls were made
        assert len(legacy._calls) == 4

    def test_modern_plugin_workflow(self):
        """Test complete workflow with modern plugin."""
        registry = DisplayPluginRegistry()
        registry.register_plugin("simple", SimpleDisplayPlugin)

        console = Console(file=StringIO())
        context = PluginContext(command="search", console=console)

        plugin = registry.create_plugin("simple", context)

        plugin.display_search_results({
            "query": "test",
            "total_matches": 42
        })

        output = console.file.getvalue()
        assert "42" in output

    def test_registry_with_mixed_plugin_types(self):
        """Test registry with both legacy and modern plugins."""
        registry = DisplayPluginRegistry()

        # Register modern plugin
        registry.register_plugin("simple", SimpleDisplayPlugin)

        # Create adapter for legacy
        console = Console()
        context = PluginContext(command="download", console=console)
        legacy = MockLegacyPlugin(console=console)
        adapter = LegacyDisplayPluginAdapter(context, legacy)

        # List plugins for download command
        # Modern SimpleDisplayPlugin supports download
        download_plugins = registry.list_plugins_for_command("download")
        assert "simple" in download_plugins

        # Adapter reports it supports download
        assert adapter.supports_command("download") is True
        assert adapter.supports_command("search") is False

    def test_plugin_context_propagation_through_registry(self):
        """Test that context is properly propagated through registry."""
        registry = DisplayPluginRegistry()
        registry.register_plugin("simple", SimpleDisplayPlugin)

        custom_options = {"verbose": True, "show_timestamps": False}
        console = Console()
        context = PluginContext(
            command="search",
            console=console,
            options=custom_options,
            config_dir="/custom/config",
            db_path="/custom/db.sqlite"
        )

        plugin = registry.create_plugin("simple", context)

        assert plugin.context is context
        assert plugin.options == custom_options
        # get_option is on context, not plugin
        assert plugin.context.get_option("verbose") is True
        assert plugin.context.get_option("show_timestamps") is False
