from pathlib import Path
from unittest.mock import MagicMock, patch

from yt_sync.main_logic import initialize_tui, load_configuration, process_all_channels


def test_load_configuration():
    """Test that configuration is loaded correctly."""
    config_path = Path("config.yaml")
    config = load_configuration(config_path)
    assert config is not None
    assert "api_key" in config
    assert config["api_key"] == "test_api_key"


def test_initialize_tui():
    """Test TUI initialization."""
    with patch("yt_sync.main_logic.TUIDisplay") as mock_display:
        display, thread = initialize_tui(10)
        assert display is not None
        mock_display.assert_called_once_with(total_channels=10)


@patch("yt_sync.main_logic.ChannelSyncer")
def test_process_all_channels(mock_syncer_class):
    """Test that process_all_channels iterates and calls ChannelSyncer for each channel."""
    # Arrange
    mock_syncer_instance = MagicMock()
    mock_syncer_class.return_value = mock_syncer_instance

    channels = ["https://youtube.com/c/channel1", "https://youtube.com/c/channel2"]
    args = MagicMock()
    args.channel_overrides = {}  # Explicitly create the attribute on the mock
    config = {
        "filters": {},
        "channel_overrides": {},  # Ensure this key exists
    }
    api_client = MagicMock()

    # Act
    process_all_channels(
        channels, len(channels), args, config, api_client, display=None
    )

    # Assert
    assert mock_syncer_class.call_count == 2
    assert mock_syncer_instance.process.call_count == 2
