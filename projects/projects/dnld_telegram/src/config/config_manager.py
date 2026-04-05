import json  # Import json for parsing TELEGRAM_CHANNELS
import os

import tomli
from loguru import logger


class ConfigManager:
    _instance = None
    _configs = {}
    _config_path = None  # New attribute to store the config path

    def __new__(cls, config_path=None):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._config_path = config_path  # Store the path
            cls._instance._load_configs()
        return cls._instance

    def _load_configs(self):
        # Use the provided config_path, or default to the original relative path
        config_file_to_load = (
            self._config_path
            if self._config_path
            else os.path.join(os.path.dirname(__file__), "..", "..", "config.toml")
        )
        try:
            with open(config_file_to_load, "rb") as f:
                self._configs = tomli.load(f)
            logger.info(f"Loaded configuration from {config_file_to_load}")
        except FileNotFoundError:
            logger.warning(
                f"Configuration file not found at {config_file_to_load}. Using empty configuration."
            )
            self._configs = {}
        except Exception as e:
            logger.error(f"Error loading configuration from {config_file_to_load}: {e}")
            self._configs = {}

    def get(self, key: str, default=None):
        keys = key.split(".")
        value = self._configs

        # Try to get from loaded TOML configs first
        found_in_toml = True
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                found_in_toml = False
                break

        if found_in_toml:
            return value

        # If not found in TOML, try environment variables
        env_var_name = key.replace(".", "_").upper()
        env_value = os.getenv(env_var_name)

        if env_value is not None:
            # Attempt to convert to appropriate type if possible
            if env_var_name.endswith("_ID"):
                try:
                    return int(env_value)
                except ValueError:
                    logger.warning(
                        f"Environment variable {env_var_name} is not a valid integer. Returning as string."
                    )
                    return env_value
            elif env_var_name.endswith("_HASH") or env_var_name.endswith("_STRING"):
                return env_value
            else:
                # For other types, just return as string
                return env_value

        return default

    def get_channels_config(self):
        """Retrieves channel configuration, handling fallback logic internally."""
        channels = self.get("channels")
        if channels:
            return channels
        else:
            logger.warning(
                "No channels found in TOML config. Attempting to load from environment variables."
            )
            return self._load_channels_from_env()

    def _load_channels_from_env(self):
        """Load channel information from environment variables."""
        logger.debug("ConfigManager: _load_channels_from_env called")
        channels = {}

        # Get channels from TELEGRAM_CHANNELS JSON string
        channels_json = os.getenv("TELEGRAM_CHANNELS")
        if channels_json:
            try:
                channels = json.loads(channels_json)
                logger.debug(
                    f"ConfigManager: Successfully loaded channels from JSON: {channels}"
                )
            except json.JSONDecodeError as e:
                logger.error(
                    f"ConfigManager: Error parsing TELEGRAM_CHANNELS JSON: {e}"
                )
                logger.error(f"ConfigManager: TELEGRAM_CHANNELS value: {channels_json}")

        # If no channels found in JSON, fall back to old format (CHANNEL_*)
        if not channels:
            logger.info(
                "ConfigManager: No channels found in TELEGRAM_CHANNELS, checking for CHANNEL_* variables..."
            )
            for key, value in os.environ.items():
                if key.startswith("CHANNEL_"):
                    channel_name = key[
                        8:
                    ].lower()  # Remove 'CHANNEL_' prefix and convert to lowercase
                    logger.debug(
                        f"ConfigManager: Processing {key} = {value}, channel_name='{channel_name}'"
                    )
                    # Strip whitespace from value
                    cleaned_value = value.strip()
                    try:
                        channels[channel_name] = int(cleaned_value)
                        logger.debug(
                            f"ConfigManager: Successfully loaded channel {channel_name} with ID {channels[channel_name]}"
                        )
                    except ValueError:
                        # Only show warning for non-empty values
                        if cleaned_value:
                            logger.warning(
                                f"ConfigManager: Invalid channel ID for {channel_name}: '{value}' (cleaned: '{cleaned_value}')"
                            )
        return channels


# Example usage (for testing purposes, can be removed later)
if __name__ == "__main__":
    # Create a dummy config.toml for testing
    dummy_config_content = """
    [telegram]
    api_id = 12345
    api_hash = "your_api_hash"

    [channels]
    my_channel = "https://t.me/my_channel"
    """
    dummy_config_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "config.toml"
    )
    with open(dummy_config_path, "w") as f:
        f.write(dummy_config_content)

    config = ConfigManager()
    print(f"Telegram API ID: {config.get('telegram.api_id')}")
    print(f"My Channel: {config.get('channels.my_channel')}")
    print(f"Non-existent key: {config.get('non_existent.key', 'default_value')}")

    # Clean up dummy config
    os.remove(dummy_config_path)
