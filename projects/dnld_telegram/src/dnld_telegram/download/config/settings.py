from pathlib import Path

from loguru import logger

# Import from new configuration system
try:
    from ...config.integration import get_channels as get_channels_new

    NEW_CONFIG_AVAILABLE = True
except ImportError:
    # Fall back to old system if new config not available
    NEW_CONFIG_AVAILABLE = False
    get_channels_new = None

# Import legacy TOML loader
try:
    from ...config.channels_toml_loader import load_telegram_channels
except ImportError:
    load_telegram_channels = None


def get_channels():
    """Load channel information using optimal configuration system from config/ directory."""
    # Try new configuration system first
    if NEW_CONFIG_AVAILABLE and get_channels_new is not None:
        try:
            channels = get_channels_new()
            if channels:
                logger.info(
                    "Loaded channels from optimal configuration system in config/ directory."
                )
                return channels
        except Exception as e:
            logger.warning(f"Could not load channels from new config system: {e}")

    # Fall back to legacy TOML loading from config directory
    if load_telegram_channels is not None:
        try:
            # Try to load from project config directory first
            config_dir = Path(__file__).resolve().parents[3] / "config"
            channels_file = config_dir / "channels.toml"
            if channels_file.exists():
                channels = load_telegram_channels(channels_file)
                if channels:
                    logger.info("Loaded channels from TOML file in config/ directory.")
                    return channels
        except Exception as e:
            logger.warning(f"Could not load channels from config directory TOML: {e}")

        # Fall back to legacy loading from project root
        try:
            channels = load_telegram_channels()
            if channels:
                logger.info("Loaded channels from legacy TOML file in project root.")
                return channels
        except Exception as e:
            logger.warning(f"Could not load channels from legacy TOML: {e}")

    # If all else fails, raise an error with helpful message
    raise ValueError(
        "No channels configuration found. Please ensure channels.toml exists in the config/ directory."
    )
