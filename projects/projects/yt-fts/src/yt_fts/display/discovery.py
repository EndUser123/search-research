"""
Plugin discovery mechanism for display plugins.

Dynamically loads display plugins from the plugins/ directory
and from user-configured plugin directories.
"""

import importlib.util
import logging
import os
import sys
from pathlib import Path

from .base import DisplayPlugin
from .registry import register_plugin

_logger = logging.getLogger(__name__)
_USER_PLUGINS_ENABLED = os.getenv("YT_FTS_ALLOW_PLUGINS", "").lower() in (
    "1",
    "true",
    "yes",
)
_allowed_plugin_dirs: set[Path] = set()


def _get_builtin_plugins_dir() -> Path:
    """Get the path to the built-in plugins directory."""
    return Path(__file__).parent / "plugins"


def _get_user_plugins_dir() -> Path | None:
    """Get the path to the user plugins directory."""
    from yt_fts.utils.config import get_config_path

    config_path = get_config_path()
    if config_path:
        return Path(config_path) / "plugins"
    return None


def get_allowed_plugin_dirs() -> set[Path]:
    """
    Get the set of allowed plugin directories.

    Returns:
        Set of directory paths that are approved for plugin loading.
    """
    builtin_dir = _get_builtin_plugins_dir()
    if builtin_dir not in _allowed_plugin_dirs:
        _allowed_plugin_dirs.add(builtin_dir.resolve())
    return _allowed_plugin_dirs.copy()


def is_safe_plugin_dir(plugins_dir: Path) -> bool:
    """
    Check if a plugin directory is in the allowlist.

    Args:
        plugins_dir: Directory to check.

    Returns:
        True if the directory is allowed for plugin loading.
    """
    if not plugins_dir.is_dir():
        return False
    resolved = plugins_dir.resolve()
    allowed = get_allowed_plugin_dirs()
    for allowed_dir in allowed:
        allowed_resolved = allowed_dir.resolve()
        if resolved == allowed_resolved or resolved.is_relative_to(allowed_resolved):
            return True
    return False


def register_plugin_dir(plugins_dir: Path) -> bool:
    """
    Register a directory as safe for plugin loading.

    Args:
        plugins_dir: Directory path to register.

    Returns:
        True if successfully registered, False otherwise.
    """
    if not plugins_dir.is_dir():
        _logger.warning("Cannot register non-directory as plugin dir: %s", plugins_dir)
        return False
    resolved = plugins_dir.resolve()
    _allowed_plugin_dirs.add(resolved)
    _logger.info("Registered plugin directory: %s", resolved)
    return True


def discover_plugins(plugins_dir: Path | None = None) -> int:
    """
    Discover and load display plugins from a directory.

    Args:
        plugins_dir: Directory to search for plugins.
                     Defaults to ~/.config/yt-fts/plugins/

    Returns:
        Number of plugins successfully loaded

    Example:
        >>> discover_plugins()
        3  # Loaded 3 plugins
    """
    if plugins_dir is None:
        user_dir = _get_user_plugins_dir()
        if user_dir and user_dir.exists():
            plugins_dir = user_dir
        else:
            _logger.debug("User plugin directory does not exist")
            return 0
    is_user_dir = plugins_dir != _get_builtin_plugins_dir()
    if is_user_dir:
        if not _USER_PLUGINS_ENABLED:
            _logger.warning(
                "User plugins are disabled. Set YT_FTS_ALLOW_PLUGINS=1 to enable."
            )
            return 0
        if not is_safe_plugin_dir(plugins_dir):
            _logger.warning(
                "Plugin directory %s is not in the allowlist. Use register_plugin_dir() to add it.",
                plugins_dir,
            )
            return 0
    if not plugins_dir.exists():
        _logger.debug("Plugin directory does not exist: %s", plugins_dir)
        return 0
    loaded = 0
    for plugin_file in plugins_dir.glob("*.py"):
        if plugin_file.name.startswith("_"):
            continue
        result = _load_plugin_from_file(plugin_file)
        if result:
            loaded += result
    for plugin_dir in plugins_dir.iterdir():
        if plugin_dir.is_dir() and (not plugin_dir.name.startswith("_")):
            init_file = plugin_dir / "__init__.py"
            if init_file.exists():
                result = _load_plugin_from_file(init_file)
                if result:
                    loaded += result
    return loaded


def _load_plugin_from_file(file_path: Path) -> int:
    """
    Load a plugin from a Python file.

    Args:
        file_path: Path to the plugin file

    Returns:
        Number of plugins registered (0 or 1)
    """
    try:
        module_name = f"yt_fts_plugins.{file_path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            _logger.warning("Could not load plugin spec from %s", file_path)
            return 0
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        registered = 0
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, DisplayPlugin)
                and (attr is not DisplayPlugin)
                and hasattr(attr, "__module__")
                and (attr.__module__ == module_name)
            ):
                plugin_name = _to_snake_case(attr_name)
                if hasattr(attr, "plugin_name"):
                    plugin_name = attr.plugin_name
                register_plugin(plugin_name, attr)
                registered += 1
                _logger.info("Registered plugin: %s from %s", plugin_name, file_path)
        return registered
    except SyntaxError as e:
        _logger.exception("Syntax error in plugin %s: %s", file_path, e)
        return 0
    except ImportError as e:
        _logger.warning("Import error in plugin %s: %s", file_path, e)
        return 0
    except Exception as e:
        _logger.exception(
            "Error loading plugin %s: %s: %s", file_path, type(e).__name__, e
        )
        return 0


def _to_snake_case(name: str) -> str:
    """Convert CamelCase to snake_case."""
    import re

    s1 = re.sub("(.)([A-Z][a-z]+)", "\\1_\\2", name)
    return re.sub("([a-z0-9])([A-Z])", "\\1_\\2", s1).lower()


def load_builtin_plugins() -> None:
    """
    Load all built-in display plugins.

    Registers the default plugin implementations.
    """
    from .plugins.download_default import DownloadDefaultDisplayPlugin
    from .plugins.compact import CompactDisplayPlugin
    from .plugins.default import DefaultDisplayPlugin
    from .plugins.json_output import JsonOutputPlugin

    register_plugin("default", DefaultDisplayPlugin)
    register_plugin("download_default", DownloadDefaultDisplayPlugin)
    register_plugin("compact", CompactDisplayPlugin)
    register_plugin("json", JsonOutputPlugin)
    try:
        from yt_fts.ui.plugins.default import DefaultDisplayPlugin as LegacyDefault

        register_plugin("legacy_default", LegacyDefault)
    except Exception:
        pass
    try:
        from yt_fts.ui.plugins.compact import CompactDisplayPlugin as LegacyCompact

        register_plugin("legacy_compact", LegacyCompact)
    except Exception:
        pass
    try:
        from yt_fts.ui.plugins.detailed import DetailedDisplayPlugin as LegacyDetailed

        register_plugin("legacy_detailed", LegacyDetailed)
    except Exception:
        pass
    try:
        from yt_fts.ui.plugins.minimal import MinimalDisplayPlugin as LegacyMinimal

        register_plugin("legacy_minimal", LegacyMinimal)
    except Exception:
        pass
    try:
        from yt_fts.ui.plugins.table import TableDisplayPlugin as LegacyTable

        register_plugin("legacy_table", LegacyTable)
    except Exception:
        pass
    try:
        from yt_fts.ui.plugins.progress import ProgressDisplayPlugin as LegacyProgress

        register_plugin("legacy_progress", LegacyProgress)
    except Exception:
        pass
