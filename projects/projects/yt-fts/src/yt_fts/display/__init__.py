"""
Display plugin system for yt-fts.

Provides a standardized interface for display plugins across all commands
(batch-download, search, import, status, etc.).
"""

from .base import DisplayPlugin, PluginContext
from .discovery import (
    discover_plugins,
    get_allowed_plugin_dirs,
    is_safe_plugin_dir,
    load_builtin_plugins,
    register_plugin_dir,
)
from .registry import (
    DisplayPluginRegistry,
    create_plugin,
    get_plugin,
    list_plugins,
    register_plugin,
)
from .rich_table_builder import (
    RichTableBuilder,
    create_simple_table,
    render_table_as_string,
)

__all__ = [
    "DisplayPlugin",
    "DisplayPluginRegistry",
    "PluginContext",
    "RichTableBuilder",
    "create_plugin",
    "create_simple_table",
    "discover_plugins",
    "get_allowed_plugin_dirs",
    "get_plugin",
    "is_safe_plugin_dir",
    "list_plugins",
    "load_builtin_plugins",
    "register_plugin",
    "register_plugin_dir",
    "render_table_as_string",
]

# Default plugin name
DEFAULT_PLUGIN = "default"
