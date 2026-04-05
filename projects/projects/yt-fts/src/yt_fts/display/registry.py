"""
Display plugin registry and factory.

Manages available display plugins and provides factory methods for creating
plugin instances.
"""


from .base import DisplayPlugin, PluginContext


class DisplayPluginRegistry:
    """
    Registry for display plugins.

    Manages available display plugins and provides factory methods.
    """

    def __init__(self) -> None:
        """Initialize the plugin registry."""
        self._plugins: dict[str, type[DisplayPlugin]] = {}

    def register_plugin(self, name: str, plugin_class: type[DisplayPlugin]) -> None:
        """
        Register a display plugin.

        Args:
            name: Plugin name/identifier (snake_case)
            plugin_class: Plugin class (must inherit from DisplayPlugin)

        Raises:
            TypeError: If plugin_class does not inherit from DisplayPlugin
        """
        if not issubclass(plugin_class, DisplayPlugin):
            msg = f"Plugin class {plugin_class} must inherit from DisplayPlugin"
            raise TypeError(
                msg
            )

        self._plugins[name] = plugin_class

    def unregister_plugin(self, name: str) -> None:
        """
        Unregister a display plugin.

        Args:
            name: Plugin name to unregister

        Raises:
            KeyError: If plugin not found
        """
        if name not in self._plugins:
            msg = f"Plugin '{name}' not found in registry"
            raise KeyError(msg)
        del self._plugins[name]

    def get_plugin(self, name: str) -> type[DisplayPlugin]:
        """
        Get a plugin class by name.

        Args:
            name: Plugin name

        Returns:
            Plugin class

        Raises:
            KeyError: If plugin not found
        """
        if name not in self._plugins:
            available = list(self._plugins.keys())
            msg = f"Display plugin '{name}' not found. Available: {available}"
            raise KeyError(
                msg
            )

        return self._plugins[name]

    def list_plugins(self) -> list[str]:
        """List all registered plugin names."""
        return list(self._plugins.keys())

    def list_plugins_for_command(self, command: str) -> list[str]:
        """
        List plugins that support a specific command.

        Args:
            command: Command name (search, download, etc.)

        Returns:
            List of plugin names that support the command
        """
        return [
            name
            for name, plugin_class in self._plugins.items()
            if command in plugin_class.supported_commands or not plugin_class.supported_commands
        ]

    def create_plugin(self, name: str, context: PluginContext) -> DisplayPlugin:
        """
        Create a plugin instance.

        Args:
            name: Plugin name
            context: Plugin context

        Returns:
            Plugin instance

        Raises:
            KeyError: If plugin not found
        """
        plugin_class = self.get_plugin(name)
        return plugin_class(context)

    def create_default_plugin(self, context: PluginContext, command: str | None = None) -> DisplayPlugin:
        """
        Create a default plugin for the given command.

        Args:
            context: Plugin context
            command: Optional command name to filter plugins

        Returns:
            Default plugin instance

        Raises:
            KeyError: If no suitable plugin found
        """
        # Try to find a plugin specifically for the command
        if command:
            for _name, plugin_class in self._plugins.items():
                if command in plugin_class.supported_commands:
                    return plugin_class(context)

        # Fall back to any plugin named "default"
        if "default" in self._plugins:
            return self._plugins["default"](context)

        # Use the first registered plugin
        if self._plugins:
            first_name = next(iter(self._plugins))
            return self._plugins[first_name](context)

        msg = "No plugins registered"
        raise KeyError(msg)


# Global registry instance
_global_registry = DisplayPluginRegistry()


def register_plugin(name: str, plugin_class: type[DisplayPlugin]) -> None:
    """
    Register a display plugin globally.

    Args:
        name: Plugin name/identifier (snake_case)
        plugin_class: Plugin class (must inherit from DisplayPlugin)

    Raises:
        TypeError: If plugin_class does not inherit from DisplayPlugin
    """
    _global_registry.register_plugin(name, plugin_class)


def unregister_plugin(name: str) -> None:
    """
    Unregister a display plugin globally.

    Args:
        name: Plugin name to unregister

    Raises:
        KeyError: If plugin not found
    """
    _global_registry.unregister_plugin(name)


def get_plugin(name: str) -> type[DisplayPlugin]:
    """
    Get a plugin class by name from the global registry.

    Args:
        name: Plugin name

    Returns:
        Plugin class

    Raises:
        KeyError: If plugin not found
    """
    return _global_registry.get_plugin(name)


def create_plugin(name: str, context: PluginContext) -> DisplayPlugin:
    """
    Create a plugin instance from the global registry.

    Args:
        name: Plugin name
        context: Plugin context

    Returns:
        Plugin instance

    Raises:
        KeyError: If plugin not found
    """
    return _global_registry.create_plugin(name, context)


def list_plugins() -> list[str]:
    """
    List all available plugin names from the global registry.

    Returns:
        List of registered plugin names
    """
    return _global_registry.list_plugins()


def list_plugins_for_command(command: str) -> list[str]:
    """
    List plugins that support a specific command.

    Args:
        command: Command name (search, download, etc.)

    Returns:
        List of plugin names that support the command
    """
    return _global_registry.list_plugins_for_command(command)


def get_registry() -> DisplayPluginRegistry:
    """
    Get the global registry instance.

    Returns:
        Global DisplayPluginRegistry instance
    """
    return _global_registry
