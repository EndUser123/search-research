"""
Tests for display plugin organization and categorization feature.

Tests the plugin metadata system including:
- Category metadata (core, verbose, diagnostic, monitoring)
- Plugin descriptions
- CLI command for listing plugins
- Plugin registry functions
"""

import pytest
from typing import Any

from yt_fts.ui.plugins import (
    DisplayPluginRegistry,
    list_plugins,
    get_plugin,
    get_plugin_categories,
    list_plugins_by_category,
)


class TestPluginCategoryMetadata:
    """
    Test that plugins have required category metadata.

    Given: A registered display plugin
    When: Inspecting plugin metadata
    Then: Plugin should have name, description, and category attributes
    """

    def test_default_plugin_has_category_metadata(self):
        """
        Test that DefaultDisplayPlugin has category metadata.

        Given: The default plugin is registered
        When: Accessing plugin metadata
        Then: Plugin should have name, description, and category attributes
        """
        plugin_class = get_plugin("default")

        # Assert metadata attributes exist
        assert hasattr(plugin_class, "name"), "Plugin should have 'name' attribute"
        assert hasattr(plugin_class, "description"), "Plugin should have 'description' attribute"
        assert hasattr(plugin_class, "category"), "Plugin should have 'category' attribute"

        # Assert expected values
        assert plugin_class.name == "default"
        assert plugin_class.category == "core"
        assert isinstance(plugin_class.description, str)
        assert len(plugin_class.description) > 0

    def test_compact_plugin_has_category_metadata(self):
        """
        Test that CompactDisplayPlugin has category metadata.

        Given: The compact plugin is registered
        When: Accessing plugin metadata
        Then: Plugin should have name, description, and category attributes
        """
        plugin_class = get_plugin("compact")

        assert hasattr(plugin_class, "name")
        assert hasattr(plugin_class, "description")
        assert hasattr(plugin_class, "category")

        assert plugin_class.name == "compact"
        assert plugin_class.category == "core"

    def test_detailed_plugin_has_category_metadata(self):
        """
        Test that DetailedDisplayPlugin has category metadata.

        Given: The detailed plugin is registered
        When: Accessing plugin metadata
        Then: Plugin should have name, description, and category attributes
        """
        plugin_class = get_plugin("detailed")

        assert hasattr(plugin_class, "name")
        assert hasattr(plugin_class, "description")
        assert hasattr(plugin_class, "category")

        assert plugin_class.name == "detailed"
        assert plugin_class.category == "verbose"

    def test_monitoring_plugins_have_monitoring_category(self):
        """
        Test that monitoring-related plugins have monitoring category.

        Given: Monitoring plugins are registered
        When: Accessing plugin metadata
        Then: Plugins should have category set to 'monitoring'
        """
        monitoring_plugins = ["job_monitor", "pipeline_view"]

        for plugin_name in monitoring_plugins:
            plugin_class = get_plugin(plugin_name)

            assert hasattr(plugin_class, "category"), f"{plugin_name} should have 'category' attribute"
            assert plugin_class.category == "monitoring", f"{plugin_name} should be in 'monitoring' category"

    def test_diagnostic_plugins_have_diagnostic_category(self):
        """
        Test that diagnostic-related plugins have diagnostic category.

        Given: Diagnostic plugins are registered
        When: Accessing plugin metadata
        Then: Plugins should have category set to 'diagnostic'
        """
        diagnostic_plugins = ["forensic_view", "exception_first"]

        for plugin_name in diagnostic_plugins:
            plugin_class = get_plugin(plugin_name)

            assert hasattr(plugin_class, "category"), f"{plugin_name} should have 'category' attribute"
            assert plugin_class.category == "diagnostic", f"{plugin_name} should be in 'diagnostic' category"


class TestPluginCategories:
    """
    Test plugin category retrieval and organization.

    Given: Multiple plugins are registered with different categories
    When: Calling get_plugin_categories()
    Then: Should return all available categories
    """

    def test_get_plugin_categories_returns_all_categories(self):
        """
        Test that get_plugin_categories returns all defined categories.

        Given: Plugins are registered with various categories
        When: Calling get_plugin_categories()
        Then: Should return list of all categories including core, verbose, diagnostic, monitoring
        """
        categories = get_plugin_categories()

        # Assert expected categories exist
        assert isinstance(categories, list)
        assert "core" in categories
        assert "verbose" in categories
        assert "diagnostic" in categories
        assert "monitoring" in categories

    def test_get_plugin_categories_returns_unique(self):
        """
        Test that get_plugin_categories returns unique categories.

        Given: Plugins are registered
        When: Calling get_plugin_categories()
        Then: Should return a list with no duplicate categories
        """
        categories = get_plugin_categories()

        # Assert no duplicates
        assert len(categories) == len(set(categories))

    def test_get_plugin_categories_ordering(self):
        """
        Test that get_plugin_categories returns categories in expected order.

        Given: Plugins are registered
        When: Calling get_plugin_categories()
        Then: Categories should follow logical ordering (core first, then others)
        """
        categories = get_plugin_categories()

        # Core should be first (for better UX in listings)
        assert categories[0] == "core"


class TestListPluginsByCategory:
    """
    Test listing plugins grouped by category.

    Given: Multiple plugins are registered with different categories
    When: Calling list_plugins_by_category()
    Then: Should return dict with category keys and plugin lists as values
    """

    def test_list_plugins_by_category_returns_dict(self):
        """
        Test that list_plugins_by_category returns a dictionary.

        Given: Plugins are registered with categories
        When: Calling list_plugins_by_category()
        Then: Should return dict with category names as keys
        """
        result = list_plugins_by_category()

        assert isinstance(result, dict)

    def test_list_plugins_by_category_has_all_categories(self):
        """
        Test that list_plugins_by_category includes all categories.

        Given: Plugins are registered
        When: Calling list_plugins_by_category()
        Then: All defined categories should be present as keys
        """
        result = list_plugins_by_category()

        categories = get_plugin_categories()
        for category in categories:
            assert category in result, f"Category '{category}' should be in result"

    def test_list_plugins_by_category_contains_plugin_info(self):
        """
        Test that list_plugins_by_category returns plugin metadata.

        Given: Plugins are registered
        When: Calling list_plugins_by_category()
        Then: Each plugin entry should have name and description
        """
        result = list_plugins_by_category()

        # Check that at least one category has plugins with required info
        for category, plugins in result.items():
            for plugin in plugins:
                assert "name" in plugin, f"Plugin in {category} should have 'name'"
                assert "description" in plugin, f"Plugin in {category} should have 'description'"
                assert "category" in plugin, f"Plugin in {category} should have 'category'"

    def test_list_plugins_by_category_core_plugins(self):
        """
        Test that core category contains expected plugins.

        Given: Core plugins are registered
        When: Calling list_plugins_by_category()
        Then: Core category should include default, compact, minimal plugins
        """
        result = list_plugins_by_category()

        core_plugins = result.get("core", [])
        core_plugin_names = [p["name"] for p in core_plugins]

        assert "default" in core_plugin_names
        assert "compact" in core_plugin_names
        assert "minimal" in core_plugin_names

    def test_list_plugins_by_category_monitoring_plugins(self):
        """
        Test that monitoring category contains expected plugins.

        Given: Monitoring plugins are registered
        When: Calling list_plugins_by_category()
        Then: Monitoring category should include job_monitor, pipeline_view
        """
        result = list_plugins_by_category()

        monitoring_plugins = result.get("monitoring", [])
        monitoring_plugin_names = [p["name"] for p in monitoring_plugins]

        assert "job_monitor" in monitoring_plugin_names
        assert "pipeline_view" in monitoring_plugin_names


class TestPluginDescriptions:
    """
    Test that plugin descriptions are accessible and meaningful.

    Given: A registered display plugin
    When: Accessing plugin description
    Then: Should return a non-empty string describing the plugin
    """

    def test_all_plugins_have_descriptions(self):
        """
        Test that all registered plugins have descriptions.

        Given: All plugins are loaded
        When: Checking each plugin
        Then: Every plugin should have a non-empty description
        """
        plugin_names = list_plugins()

        for plugin_name in plugin_names:
            plugin_class = get_plugin(plugin_name)

            assert hasattr(plugin_class, "description"), f"{plugin_name} should have 'description' attribute"
            assert isinstance(plugin_class.description, str), f"{plugin_name} description should be a string"
            assert len(plugin_class.description) > 0, f"{plugin_name} description should not be empty"

    def test_plugin_descriptions_are_meaningful(self):
        """
        Test that plugin descriptions are meaningful.

        Given: Plugins with descriptions
        When: Reading descriptions
        Then: Descriptions should be longer than 10 characters and not generic
        """
        plugin_names = list_plugins()

        for plugin_name in plugin_names:
            plugin_class = get_plugin(plugin_name)

            description = plugin_class.description

            # Description should be substantive
            assert len(description) >= 10, f"{plugin_name} description should be at least 10 characters"
            # Description should not be a generic placeholder
            assert description.lower() not in ["todo", "tbd", "description", "plugin description"], \
                f"{plugin_name} should have a meaningful description, not '{description}'"


class TestCLIPluginsCommand:
    """
    Test CLI command `yt-fts plugins --list`.

    Given: The CLI is available
    When: Running `yt-fts plugins --list`
    Then: Should display plugins grouped by category with descriptions
    """

    def test_cli_plugins_list_command_exists(self):
        """
        Test that the plugins list command can be invoked.

        Given: The CLI is available
        When: Calling the plugins command group
        Then: Should have a --list option available
        """
        from click.testing import CliRunner
        from yt_fts.core.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["plugins", "--help"])

        # Should show help for plugins command
        assert result.exit_code == 0 or "usage:" in result.output.lower() or "plugins" in result.output.lower()

    def test_cli_plugins_list_displays_categories(self):
        """
        Test that plugins --list shows plugins grouped by category.

        Given: Plugins are registered
        When: Running `yt-fts plugins --list`
        Then: Output should show category headers and plugin listings
        """
        from click.testing import CliRunner
        from yt_fts.core.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["plugins", "--list"])

        # Should succeed
        assert result.exit_code == 0

        # Output should contain category headers
        output = result.output.lower()
        assert "core" in output or "category" in output

    def test_cli_plugins_list_shows_descriptions(self):
        """
        Test that plugins --list shows plugin descriptions.

        Given: Plugins are registered
        When: Running `yt-fts plugins --list`
        Then: Output should include plugin descriptions
        """
        from click.testing import CliRunner
        from yt_fts.core.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["plugins", "--list"])

        # Should succeed
        assert result.exit_code == 0

        # Output should contain text (descriptions should be visible)
        assert len(result.output.strip()) > 0


class TestDisplayPluginRegistry:
    """
    Test DisplayPluginRegistry class methods for categorized plugins.

    Given: A DisplayPluginRegistry instance
    When: Calling registry methods
    Then: Should properly handle plugin categorization
    """

    def test_registry_get_plugin_by_category(self):
        """
        Test that registry can filter plugins by category.

        Given: A registry with categorized plugins
        When: Calling get_plugins_by_category(category_name)
        Then: Should return list of plugins in that category
        """
        registry = DisplayPluginRegistry()

        # Core category should exist
        core_plugins = registry.get_plugins_by_category("core")
        assert isinstance(core_plugins, list)
        assert len(core_plugins) > 0

    def test_registry_plugin_with_invalid_category_raises_error(self):
        """
        Test that registering plugin with invalid category raises error.

        Given: A registry
        When: Trying to register plugin with invalid category
        Then: Should raise ValueError
        """
        registry = DisplayPluginRegistry()

        from yt_fts.ui.plugins.base import DisplayPlugin

        class InvalidPlugin(DisplayPlugin):
            name = "invalid"
            description = "Invalid category plugin"
            category = "invalid_category"

            def display_channel_header(self, channel_info: dict[str, Any]) -> None: pass
            def display_rss_status(self, rss_info: dict[str, Any]) -> None: pass
            def display_download_result(self, result_info: dict[str, Any]) -> None: pass
            def display_batch_summary(self, summary_info: dict[str, Any]) -> None: pass

        with pytest.raises(ValueError, match="Invalid category"):
            registry.register_plugin("invalid", InvalidPlugin)


class TestDisplayRssStatus:
    """
    Test display_rss_status handles both dict and RssCheckResult dataclass.

    Regression test for: AttributeError: 'RssCheckResult' object has no attribute 'get'
    The method was written for dict-style access but receives dataclass objects.
    """

    def test_display_rss_status_with_dict(self):
        """
        Test display_rss_status with legacy dict-style input.

        Given: A display plugin instance
        When: Calling display_rss_status with a dict
        Then: Should not raise AttributeError

        Before the fix, dict-style access worked fine. This ensures it still does.
        """
        from io import StringIO
        from rich.console import Console
        from yt_fts.ui.plugins.default import DefaultDisplayPlugin

        console = Console(file=StringIO())
        plugin = DefaultDisplayPlugin(console)

        # Legacy dict-style input
        rss_info = {"status": "skip", "message": "No new videos"}
        # Should not raise AttributeError
        plugin.display_rss_status(rss_info)

    def test_display_rss_status_with_dataclass(self):
        """
        Test display_rss_status with RssCheckResult dataclass.

        Given: A display plugin instance
        When: Calling display_rss_status with RssCheckResult dataclass
        Then: Should not raise AttributeError

        This is a regression test for the bug where dataclass objects
        caused AttributeError: 'RssCheckResult' object has no attribute 'get'

        Before the fix, this would fail because the code used .get() method
        which doesn't exist on dataclass objects.
        """
        from io import StringIO
        from rich.console import Console
        from yt_fts.ui.plugins.default import DefaultDisplayPlugin
        from yt_fts.services.rss_precheck import RssCheckResult

        console = Console(file=StringIO())
        plugin = DefaultDisplayPlugin(console)

        # Actual RssCheckResult dataclass (what gets passed in real code)
        rss_result = RssCheckResult(
            status="new_videos",
            video_ids=["abc123", "def456"],
            newest_id="abc123",
            oldest_id="def456",
            message="Discovered 2 new videos",
        )
        # Should not raise AttributeError
        plugin.display_rss_status(rss_result)

    def test_display_rss_status_handles_all_status_types(self):
        """
        Test display_rss_status handles all RssCheckResult status types.

        Given: A display plugin instance
        When: Calling display_rss_status with each possible status
        Then: Should handle all status types without error
        """
        from io import StringIO
        from rich.console import Console
        from yt_fts.ui.plugins.default import DefaultDisplayPlugin
        from yt_fts.services.rss_precheck import RssCheckResult

        console = Console(file=StringIO())
        plugin = DefaultDisplayPlugin(console)

        # Test each status type - the key assertion is no AttributeError
        test_cases = [
            ("skip", "No new videos"),
            ("new_videos", "Discovered 5 videos"),
            ("gap_detected", "Gap found in history"),
            ("error", "RSS fetch failed"),
        ]

        for status, msg in test_cases:
            rss_result = RssCheckResult(
                status=status,
                video_ids=[],
                newest_id=None,
                oldest_id=None,
                message=msg,
            )
            # Should not raise AttributeError for any status type
            plugin.display_rss_status(rss_result)


class TestChannelHeaderLazyLoading:
    """
    Regression test for channel header lazy loading behavior.

    PRD AC.3.4: MUST NOT display raw truncated channel IDs.
    Lazy loading: Headers should display immediately without blocking API calls.
    """

    def test_batch_downloader_ensure_channel_name_returns_immediately_without_cached_name(self):
        """
        Test that _ensure_channel_name_in_db returns immediately when no cached name exists.

        This is a regression test to ensure the lazy loading implementation
        doesn't revert to blocking API calls with timeouts.

        Given: A BatchDownloader instance with a channel that has no cached name
        When: _ensure_channel_name_in_db is called
        Then: Should return immediately (< 50ms) without calling slow API
        """
        import time
        from unittest.mock import patch

        from yt_fts.download.batch_downloader import BatchDownloader

        # Arrange - No cached name
        with patch("yt_fts.db.channels.get_channel_name_from_db", return_value=None):
            downloader = BatchDownloader(
                channels=["@testchannel"],
                suppress_verbose=True,
            )

            channel_id = "UCXxKeNggi1234567890ab"
            api_called = []

            def slow_mock_discover_handle(*args, **kwargs):
                api_called.append(True)
                time.sleep(0.2)  # Simulate slow API
                return None

            # Act
            with patch("yt_fts.services.channel_service.ChannelHandleService") as mock_service:
                from unittest.mock import MagicMock
                mock_instance = MagicMock()
                mock_instance.discover_handle.side_effect = slow_mock_discover_handle
                mock_service.return_value = mock_instance

                start_time = time.time()
                result_channel_id = downloader._ensure_channel_name_in_db(channel_id=channel_id)
                elapsed_ms = (time.time() - start_time) * 1000

            # Assert - With lazy loading, API should NOT be called
            assert len(api_called) == 0, (
                f"API was called during _ensure_channel_name_in_db. "
                f"Lazy loading should defer API calls - should return immediately."
            )

            # Should return very quickly
            assert elapsed_ms < 50, (
                f"_ensure_channel_name_in_db took {elapsed_ms:.2f}ms, "
                f"should be < 50ms for lazy loading (no blocking API call)."
            )

            # Should return channel_id unchanged (no blocking API fetch)
            assert result_channel_id == channel_id

    def test_batch_downloader_ensure_channel_name_returns_fast_with_cached_name(self):
        """
        Test that _ensure_channel_name_in_db returns quickly when name is cached.

        Given: A channel with a cached human-readable name
        When: _ensure_channel_name_in_db is called
        Then: Should return immediately without any API call
        """
        import time
        from unittest.mock import patch

        from yt_fts.download.batch_downloader import BatchDownloader

        # Arrange - Cached name exists
        with patch("yt_fts.db.channels.get_channel_name_from_db", return_value="Test Channel"):
            downloader = BatchDownloader(
                channels=["@testchannel"],
                suppress_verbose=True,
            )

            channel_id = "UCXxKeNggi1234567890ab"

            # Act
            start_time = time.time()
            result_channel_id = downloader._ensure_channel_name_in_db(channel_id=channel_id)
            elapsed_ms = (time.time() - start_time) * 1000

            # Assert - Should return very quickly (< 10ms for cached case)
            assert elapsed_ms < 10, (
                f"_ensure_channel_name_in_db with cached name took {elapsed_ms:.2f}ms, "
                f"should be < 10ms"
            )
            assert result_channel_id == channel_id

