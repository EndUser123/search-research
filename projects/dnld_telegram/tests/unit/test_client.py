import os
from unittest.mock import patch

import pytest

# Import the ConfigManager for mocking
from src.config.config_manager import ConfigManager

# Import the function to be tested
from src.download.client import validate_credentials


@pytest.fixture(autouse=True)
def reset_config_manager_singleton():
    # Ensure ConfigManager is a fresh instance for each test
    ConfigManager._instance = None
    yield
    ConfigManager._instance = None


def test_validate_credentials_uses_config_manager():
    # Mock ConfigManager.get to return expected values
    with patch.object(ConfigManager, "get") as mock_config_get:
        mock_config_get.side_effect = (
            lambda key, default=None: {
                "telegram.api_id": 12345,
                "telegram.api_hash": "abcdef0123456789abcdef0123456789",
                "telegram.session_string": "BQC_LONG_SESSION_STRING_EXAMPLE_1234567890ABCDEF_THIS_IS_LONGER_THAN_50_CHARS",  # Adjusted length
            }.get(key, default)
        )

        # Patch os.getenv to ensure it's not called for these specific keys
        with patch.object(os, "getenv") as mock_os_getenv:
            # Configure mock_os_getenv to return None for the keys we expect ConfigManager to handle
            mock_os_getenv.side_effect = lambda key, default=None: {
                "TELEGRAM_API_ID": None,
                "TELEGRAM_API_HASH": None,
                "TELEGRAM_SESSION_STRING": None,
            }.get(key, default)

            # Call the function under test
            api_id, api_hash, session_string = validate_credentials()

            # Assert that ConfigManager.get was called for each credential
            mock_config_get.assert_any_call("telegram.api_id")
            mock_config_get.assert_any_call("telegram.api_hash")
            mock_config_get.assert_any_call("telegram.session_string")

            # Assert that os.getenv was NOT called for these specific keys
            # This assertion will fail initially, as validate_credentials still uses os.getenv
            assert (
                not mock_os_getenv.called
            )  # This is the primary assertion for the Red state

            # Assert the returned values are correct
            assert api_id == 12345
            assert api_hash == "abcdef0123456789abcdef0123456789"
            assert (
                session_string
                == "BQC_LONG_SESSION_STRING_EXAMPLE_1234567890ABCDEF_THIS_IS_LONGER_THAN_50_CHARS"
            )
