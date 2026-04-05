"""
Display plugin registry and factory.
"""

from typing import Any

from .base import DisplayPlugin

# Valid plugin categories
VALID_CATEGORIES = {"core", "verbose", "diagnostic", "monitoring"}


class DisplayPluginRegistry:
    """
    Registry for display plugins.

    Manages available display plugins and provides factory methods.
    """

    def __init__(self) -> None:
        """Initialize the plugin registry and load built-in plugins.

        Creates an empty plugin dictionary and automatically loads all
        built-in display plugins.
        """
        self._plugins: dict[str, type[DisplayPlugin]] = {}
        self._load_builtin_plugins()

    def _load_builtin_plugins(self) -> None:
        """Load all built-in display plugins into the registry.

        Imports plugin modules and registers the default plugin implementations
        including: default, compact, detailed, minimal, progress, and table.
        """
        # Import all plugin modules to register them
        from . import (
            compact,
            dashboard_view,
            default,
            detailed,
            entity_view,
            exception_first,
            forensic_view,
            job_monitor,
            minimal,
            pipeline_view,
            progress,
            table,
        )

        # Register built-in plugins
        self.register_plugin("default", default.DefaultDisplayPlugin)
        self.register_plugin("compact", compact.CompactDisplayPlugin)
        self.register_plugin("detailed", detailed.DetailedDisplayPlugin)
        self.register_plugin("minimal", minimal.MinimalDisplayPlugin)
        self.register_plugin("progress", progress.ProgressDisplayPlugin)
        self.register_plugin("table", table.TableDisplayPlugin)

        # Register Gemini solution plugins
        self.register_plugin("pipeline_view", pipeline_view.PipelineViewDisplayPlugin)
        self.register_plugin("dashboard_view", dashboard_view.DashboardViewDisplayPlugin)
        self.register_plugin("entity_view", entity_view.EntityViewDisplayPlugin)
        self.register_plugin("job_monitor", job_monitor.JobMonitorDisplayPlugin)
        self.register_plugin("forensic_view", forensic_view.ForensicViewDisplayPlugin)
        self.register_plugin("exception_first", exception_first.ExceptionFirstDisplayPlugin)

    def register_plugin(self, name: str, plugin_class: type[DisplayPlugin]) -> None:
        """
        Register a display plugin.

        Args:
            name: Plugin name/identifier
            plugin_class: Plugin class (must inherit from DisplayPlugin)

        Raises:
            ValueError: If plugin_class does not inherit from DisplayPlugin
            ValueError: If plugin has an invalid category
        """
        if not issubclass(plugin_class, DisplayPlugin):
            msg = f"Plugin class {plugin_class} must inherit from DisplayPlugin"
            raise ValueError(
                msg
            )

        # Validate plugin category
        if hasattr(plugin_class, "category"):
            category = plugin_class.category
            if category not in VALID_CATEGORIES:
                msg = (
                    f"Invalid category '{category}' for plugin '{name}'. "
                    f"Valid categories are: {sorted(VALID_CATEGORIES)}"
                )
                raise ValueError(
                    msg
                )

        self._plugins[name] = plugin_class

    def get_plugin(self, name: str) -> type[DisplayPlugin]:
        """
        Get a plugin class by name.

        Args:
            name: Plugin name

        Returns:
            Plugin class

        Raises:
            ValueError: If plugin not found
        """
        if name not in self._plugins:
            available = list(self._plugins.keys())
            msg = f"Display plugin '{name}' not found. Available: {available}"
            raise ValueError(
                msg
            )

        return self._plugins[name]

    def list_plugins(self) -> list[str]:
        """List all available plugin names."""
        return list(self._plugins.keys())

    def get_plugins_by_category(self, category: str) -> list[dict[str, Any]]:
        """
        Get all plugins in a specific category.

        Args:
            category: Category name (core, verbose, diagnostic, monitoring)

        Returns:
            List of dicts with plugin info (name, description, category)
        """
        result = []
        for plugin_name, plugin_class in self._plugins.items():
            if hasattr(plugin_class, "category") and plugin_class.category == category:
                result.append({
                    "name": getattr(plugin_class, "name", plugin_name),
                    "description": getattr(plugin_class, "description", ""),
                    "category": plugin_class.category,
                })
        return result

    def create_plugin(self, name: str, **kwargs: Any) -> DisplayPlugin:
        """
        Create a plugin instance.

        Args:
            name: Plugin name
            **kwargs: Arguments to pass to plugin constructor

        Returns:
            Plugin instance
        """
        plugin_class = self.get_plugin(name)
        return plugin_class(**kwargs)


# Global registry instance
_registry = DisplayPluginRegistry()


def register_plugin(name: str, plugin_class: type[DisplayPlugin]) -> None:
    """Register a display plugin globally.

    Args:
        name: Plugin name/identifier
        plugin_class: Plugin class (must inherit from DisplayPlugin)

    Raises:
        ValueError: If plugin_class does not inherit from DisplayPlugin
        ValueError: If plugin has an invalid category
    """
    _registry.register_plugin(name, plugin_class)


def get_plugin(name: str) -> type[DisplayPlugin]:
    """Get a plugin class by name from the global registry.

    Args:
        name: Plugin name

    Returns:
        Plugin class

    Raises:
        ValueError: If plugin not found
    """
    return _registry.get_plugin(name)


def create_plugin(name: str, **kwargs: Any) -> DisplayPlugin:
    """Create a plugin instance from the global registry.

    Args:
        name: Plugin name
        **kwargs: Arguments to pass to plugin constructor

    Returns:
        Plugin instance

    Raises:
        ValueError: If plugin not found
    """
    return _registry.create_plugin(name, **kwargs)


def list_plugins() -> list[str]:
    """List all available plugin names from the global registry.

    Returns:
        List of registered plugin names
    """
    return _registry.list_plugins()


def get_plugin_categories() -> list[str]:
    """Get all available plugin categories.

    Returns:
        List of category names in logical order (core first, then others)
    """
    categories = set()
    for plugin_class in _registry._plugins.values():
        if hasattr(plugin_class, "category"):
            categories.add(plugin_class.category)

    # Return in logical order with core first
    result = []
    if "core" in categories:
        result.append("core")
        categories.remove("core")

    # Add remaining categories in sorted order
    result.extend(sorted(categories))
    return result


def list_plugins_by_category() -> dict[str, list[dict[str, Any]]]:
    """List all plugins grouped by category.

    Returns:
        Dict mapping category names to lists of plugin info dicts.
        Each plugin info dict contains: name, description, category
    """
    categories = get_plugin_categories()
    result: dict[str, list[dict[str, Any]]] = {category: [] for category in categories}

    for plugin_name, plugin_class in _registry._plugins.items():
        plugin_category = getattr(plugin_class, "category", None)
        if plugin_category and plugin_category in result:
            result[plugin_category].append({
                "name": getattr(plugin_class, "name", plugin_name),
                "description": getattr(plugin_class, "description", ""),
                "category": plugin_category,
            })

    return result


# Default plugin name
DEFAULT_PLUGIN = "default"
