from unittest.mock import patch

import pytest
from src.config.config_manager import ConfigManager
from src.download.config.settings import get_channels


# Mock the external functions that get_channels() currently calls
# to ensure they are NOT called after refactoring
@patch("src.download.config.settings.load_channels_from_env")
def test_get_channels_uses_config_manager(mock_load_channels_from_env):
    # Configure ConfigManager.get_channels_config to return a specific set of channels
    with patch.object(
        ConfigManager, "get_channels_config"
    ) as mock_config_get_channels_config:
        expected_channels = {"channel1": 123, "channel2": 456}
        mock_config_get_channels_config.return_value = expected_channels

        # Call the function under test
        result_channels = get_channels()

        # Assert that ConfigManager.get_channels_config was called
        mock_config_get_channels_config.assert_called_once()  # Assert it was called

        # Assert that the old channel loading functions were NOT called
        mock_load_channels_from_env.assert_not_called()

        # Assert that the returned channels match the expected ones from ConfigManager
        assert result_channels == expected_channels


def test_get_channels_raises_error_if_no_channels_in_config_manager():
    # Configure ConfigManager.get_channels_config to return None for channels
    with patch.object(
        ConfigManager, "get_channels_config"
    ) as mock_config_get_channels_config:
        mock_config_get_channels_config.return_value = (
            None  # Simulate no channels found
        )

        # Assert that ValueError is raised
        with pytest.raises(ValueError) as excinfo:
            get_channels()

        assert "No channels found in ConfigManager." in str(excinfo.value)

        # Ensure ConfigManager.get_channels_config was called
        mock_config_get_channels_config.assert_called_once()
