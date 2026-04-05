"""
UI Configuration Management
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from ..exceptions import UILoadError
from .base import UIConfig

if TYPE_CHECKING:
    from .base import BaseUIDisplay


class UIConfigManager:
    """Manages UI configuration from files and environment"""

    def __init__(self, config_file: str | None = None):
        self.config_file = config_file
        self._config = self._load_default_config()

        if config_file:
            self._load_config_file(config_file)

    def _load_default_config(self) -> dict[str, Any]:
        """Load default UI configuration"""
        return {
            "ui": {
                "default_display": "tqdm",
                "max_concurrent": 2,
                "show_progress": True,
                "show_speed": True,
                "show_eta": True,
                "timeout": 30,
                "fallback_display": "simple",
            },
            "displays": {
                "tqdm": {
                    "ncols": 100,
                    "bar_format": "{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed:>8}e | {remaining:>9}r | {rate_fmt}]",
                },
                "alive": {"bar": "smooth", "spinner": "dots_waves", "monitor": True},
                "rich": {"transient": False, "show_speed": True},
                "textual": {"auto_exit_delay": 3},
            },
        }

    def _load_config_file(self, config_file: str) -> None:
        """Load configuration from YAML file"""
        config_path = Path(config_file)
        if config_path.exists():
            try:
                with open(config_path) as f:
                    file_config = yaml.safe_load(f)
                    self._merge_config(file_config)
            except Exception as e:
                print(f"Warning: Could not load config file {config_file}: {e}")

    def _merge_config(self, new_config: dict[str, Any]) -> None:
        """Merge new configuration with existing"""

        def deep_merge(base: dict[str, Any], update: dict[str, Any]) -> None:
            for key, value in update.items():
                if (
                    key in base
                    and isinstance(base[key], dict)
                    and isinstance(value, dict)
                ):
                    deep_merge(base[key], value)
                else:
                    base[key] = value

        deep_merge(self._config, new_config)

    def get_ui_config(self, display_type: str | None = None) -> UIConfig:
        """Get UIConfig object for specified display type"""
        ui_settings = self._config.get("ui", {})

        return UIConfig(
            max_concurrent=ui_settings.get("max_concurrent", 2),
            show_progress=ui_settings.get("show_progress", True),
            show_speed=ui_settings.get("show_speed", True),
            show_eta=ui_settings.get("show_eta", True),
            timeout=ui_settings.get("timeout", 30),
            icons_on=ui_settings.get("icons_on", True),
            ascii_only=ui_settings.get("ascii_only", False),
            align_stats=ui_settings.get("align_stats", True),
            max_name_width=ui_settings.get("max_name_width", 25),
        )

    def get_default_display(self) -> str:
        """Get default display type"""
        return self._config.get("ui", {}).get("default_display", "tqdm")

    def get_fallback_display(self) -> str:
        """Get fallback display type"""
        return self._config.get("ui", {}).get("fallback_display", "simple")

    def get_display_settings(self, display_type: str) -> dict[str, Any]:
        """Get specific settings for a display type"""
        return self._config.get("displays", {}).get(display_type, {})

    def save_config(self, config_file: str) -> None:
        """Save current configuration to file"""
        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            yaml.dump(self._config, f, default_flow_style=False, indent=2)


# Global config manager instance
_config_manager = None


def get_config_manager(config_file: str | None = None) -> UIConfigManager:
    """Get global config manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = UIConfigManager(config_file)
    return _config_manager


def create_ui_from_config(
    config_file: str | None = None,
    display_type: str | None = None,
    download_dir: str = "downloads",
) -> "BaseUIDisplay":
    """
    Create UI display from configuration

    Args:
        config_file: Path to configuration file
        display_type: Override display type
        download_dir: Download directory

    Returns:
        BaseUIDisplay instance
    """
    from .factory import UIFactory

    config_manager = get_config_manager(config_file)

    # Determine display type
    if display_type is None:
        display_type = config_manager.get_default_display()

    # Try to create the requested display
    # Note: UI configuration is available via config_manager.get_ui_config(display_type) if needed
    try:
        from rich.console import Console

        console = Console()
        return UIFactory.create(display_type, console)
    except (UILoadError, ImportError) as e:
        # Fall back to fallback display
        fallback_type = config_manager.get_fallback_display()
        print(
            f"Warning: Could not create {display_type} display ({e}), using {fallback_type}"
        )
        from rich.console import Console

        console = Console()
        return UIFactory.create(fallback_type, console)
