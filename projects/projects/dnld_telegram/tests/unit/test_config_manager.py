import os
from unittest.mock import patch  # Import patch

import pytest
from src.config.config_manager import ConfigManager


# Ensure ConfigManager is re-initialized for each test
@pytest.fixture(autouse=True)
def reset_config_manager_singleton():
    ConfigManager._instance = None
    yield
    ConfigManager._instance = None


def test_config_manager_loads_from_file():
    # Define a temporary config file path
    temp_config_dir = os.path.join(os.path.dirname(__file__), "temp_config")
    os.makedirs(temp_config_dir, exist_ok=True)
    temp_config_path = os.path.join(temp_config_dir, "config.toml")

    # Write dummy TOML content to the temporary file
    dummy_content = """
[app]
name = "TestApp"
version = 1.0

[database]
host = "localhost"
port = 5432

[channels]
my_channel = 123
"""
    with open(temp_config_path, "w") as f:
        f.write(dummy_content)

    try:
        # Instantiate ConfigManager, passing the temporary config path
        config = ConfigManager(config_path=temp_config_path)

        # Assert that values are loaded correctly
        assert config.get("app.name") == "TestApp"
        assert config.get("app.version") == 1.0
        assert config.get("database.host") == "localhost"
        assert config.get("database.port") == 5432
        assert config.get("non_existent.key", "default_value") == "default_value"
        assert config.get_channels_config() == {"my_channel": 123}

    finally:
        # Clean up the temporary config file and directory
        os.remove(temp_config_path)
        os.rmdir(temp_config_dir)


def test_config_manager_get_channels_config_from_env_fallback():
    # Simulate no channels in TOML config
    temp_config_dir = os.path.join(os.path.dirname(__file__), "temp_config_no_channels")
    os.makedirs(temp_config_dir, exist_ok=True)
    temp_config_path = os.path.join(temp_config_dir, "config.toml")
    with open(temp_config_path, "w") as f:
        f.write('[app]\nname = "TestApp"')  # No channels section

    # Mock os.getenv to simulate environment variables for channels
    with patch.dict(
        os.environ,
        {
            "TELEGRAM_CHANNELS": '{"env_channel1": 789, "env_channel2": 101}',
            "CHANNEL_OLD_FORMAT": "111",  # Should not be used if TELEGRAM_CHANNELS is present
        },
        clear=True,
    ):
        try:
            config = ConfigManager(config_path=temp_config_path)
            channels = config.get_channels_config()

            # This assertion should fail initially, as ConfigManager.get_channels_config()
            # does not yet implement the environment variable fallback.
            assert channels == {"env_channel1": 789, "env_channel2": 101}

        finally:
            os.remove(temp_config_path)
            os.rmdir(temp_config_dir)


def test_config_manager_loads_telegram_credentials_from_env():
    # Simulate no telegram section in TOML config
    temp_config_dir = os.path.join(os.path.dirname(__file__), "temp_config_no_telegram")
    os.makedirs(temp_config_dir, exist_ok=True)
    temp_config_path = os.path.join(temp_config_dir, "config.toml")
    with open(temp_config_path, "w") as f:
        f.write('[app]\nname = "TestApp"')  # No telegram section

    # Mock os.getenv to simulate environment variables for telegram credentials
    with patch.dict(
        os.environ,
        {
            "TELEGRAM_API_ID": "12345",
            "TELEGRAM_API_HASH": "abcdef0123456789abcdef0123456789",
            "TELEGRAM_SESSION_STRING": "BQC_LONG_SESSION_STRING_EXAMPLE_1234567890ABCDEF_THIS_IS_LONGER_THAN_50_CHARS",
        },
        clear=True,
    ):
        try:
            config = ConfigManager(config_path=temp_config_path)

            # This assertion should fail initially, as ConfigManager does not yet
            # implement loading telegram credentials from environment variables.
            assert config.get("telegram.api_id") == 12345
            assert config.get("telegram.api_hash") == "abcdef0123456789abcdef0123456789"
            assert (
                config.get("telegram.session_string")
                == "BQC_LONG_SESSION_STRING_EXAMPLE_1234567890ABCDEF_THIS_IS_LONGER_THAN_50_CHARS"
            )

        finally:
            os.remove(temp_config_path)
            os.rmdir(temp_config_dir)
