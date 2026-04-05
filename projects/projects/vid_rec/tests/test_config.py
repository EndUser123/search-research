"""
Tests for the configuration loading and saving logic.

This test suite uses pytest and pytest-mock to isolate the configuration logic
from the filesystem, following the testing guidelines. Mocks are used to simulate
file existence, reading, and writing, ensuring tests are fast and reliable.
"""

from pathlib import Path
from unittest.mock import MagicMock, mock_open

import pytest
import tomlkit
from pydantic import ValidationError

from src.config import AppConfig, load_configuration, save_configuration

# A valid TOML configuration string for use in tests.
VALID_CONFIG_TOML = """
[paths]
source = "/test/source"
temp_dir = "/test/temp"

[settings]
no_replace = false
create_subtitles = true
normalize_audio = false

[encoding]
target_height = 1080
crf = 23

[performance]
max_workers = 4
normalization_timeout = 3600

[quality]
vmaf_decision_enabled = true
vmaf_decision_threshold = 94.0
"""

# An invalid TOML configuration string (CRF > 51).
INVALID_CONFIG_TOML = """
[paths]
source = "/test/source"
temp_dir = "/test/temp"

[encoding]
crf = 52
target_height = 1080
"""


@pytest.fixture
def mock_path() -> Path:
    """Fixture to create a mock Path object."""
    return MagicMock(spec=Path)


def test_load_valid_config(mocker, mock_path):
    """
    Test loading a valid configuration file.
    Verifies that a correct TOML file is parsed into the AppConfig model.
    """
    # Arrange: Mock the file system to simulate config.toml's existence and content.
    mocker.patch.object(mock_path, "exists", return_value=True)
    mocker.patch("builtins.open", mock_open(read_data=VALID_CONFIG_TOML))

    # Act: Load the configuration.
    config, doc = load_configuration(mock_path)

    # Assert: Check that the configuration is loaded and parsed correctly.
    assert isinstance(config, AppConfig)
    assert config.paths.source == Path("/test/source").resolve()
    assert config.encoding.crf == 23
    assert config.settings.create_subtitles is True
    assert isinstance(doc, tomlkit.TOMLDocument)


def test_load_missing_file(mocker, mock_path):
    """
    Test handling of a missing config file.
    Verifies that a FileNotFoundError is raised if the config file does not exist.
    """
    # Arrange: Mock the file system to simulate the absence of the config file.
    mocker.patch.object(mock_path, "exists", return_value=False)

    # Act & Assert: Expect a FileNotFoundError.
    with pytest.raises(FileNotFoundError):
        load_configuration(mock_path)


def test_invalid_config_values(mocker, mock_path):
    """
    Test validation of invalid config values.
    Verifies that a Pydantic ValidationError is raised for out-of-range values.
    """
    # Arrange: Mock the file system to provide an invalid config.
    mocker.patch.object(mock_path, "exists", return_value=True)
    mocker.patch("builtins.open", mock_open(read_data=INVALID_CONFIG_TOML))

    # Act & Assert: Expect a Pydantic validation error.
    with pytest.raises(ValidationError):
        load_configuration(mock_path)


def test_save_configuration(mocker, mock_path):
    """
    Test saving configuration changes back to a file.
    Verifies that the modified configuration is correctly written.
    """
    # Arrange:
    # 1. Load an initial configuration to modify.
    mocker.patch.object(mock_path, "exists", return_value=True)
    mocker.patch("builtins.open", mock_open(read_data=VALID_CONFIG_TOML))
    config, doc = load_configuration(mock_path)

    # 2. Mock the file writing process.
    mocked_open = mock_open()
    mocker.patch("builtins.open", mocked_open)
    mocker.patch("os.replace")  # Mock os.replace to avoid filesystem interaction

    # Act: Make changes and save the configuration.
    config.encoding.crf = 24
    config.settings.create_subtitles = False
    save_configuration(doc, config, mock_path)

    # Assert:
    # 1. Check that a temporary file was opened for writing.
    mocked_open.assert_called_once_with(
        mock_path.with_suffix(".toml.tmp"), "w", encoding="utf-8"
    )

    # 2. Check that the content written to the file is correct.
    handle = mocked_open()
    written_content = handle.write.call_args[0][0]
    saved_doc = tomlkit.parse(written_content)

    assert saved_doc["encoding"]["crf"] == 24
    assert saved_doc["settings"]["create_subtitles"] is False


def test_path_resolution(mocker, mock_path):
    """
    Test that paths in the configuration are properly resolved to absolute paths.
    """
    # Arrange
    mocker.patch.object(mock_path, "exists", return_value=True)
    mocker.patch("builtins.open", mock_open(read_data=VALID_CONFIG_TOML))

    # Act
    config, _ = load_configuration(mock_path)

    # Assert
    assert config.paths.source.is_absolute()
    assert config.paths.source == Path("/test/source").resolve()
    assert config.paths.temp_dir.is_absolute()
    assert config.paths.temp_dir == Path("/test/temp").resolve()
