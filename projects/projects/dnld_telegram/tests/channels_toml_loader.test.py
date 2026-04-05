from pathlib import Path
from unittest.mock import patch

import pytest
import tomli
from dnld_telegram.src.config.channels_toml_loader import load_telegram_channels


def test_load_telegram_channels_success(tmp_path):
    d = {"TELEGRAM_CHANNELS": {"channel1": "url1"}}
    p = tmp_path / "channels.toml"
    with open(p, "wb") as f:
        tomli.dump(d, f)

    with patch("your_module.CHANNELS_TOML_PATH", p):
        result = load_telegram_channels()
        assert result == {"channel1": "url1"}


def test_load_telegram_channels_no_telegram_channels(tmp_path):
    d = {"OTHER_SECTION": {"channel1": "url1"}}
    p = tmp_path / "channels.toml"
    with open(p, "wb") as f:
        tomli.dump(d, f)

    with patch("your_module.CHANNELS_TOML_PATH", p):
        result = load_telegram_channels()
        assert result == {}


def test_load_telegram_channels_empty_toml(tmp_path):
    p = tmp_path / "channels.toml"
    with open(p, "wb") as f:
        tomli.dump({}, f)

    with patch("your_module.CHANNELS_TOML_PATH", p):
        result = load_telegram_channels()
        assert result == {}


def test_load_telegram_channels_file_not_found():
    with pytest.raises(FileNotFoundError):
        with patch("your_module.CHANNELS_TOML_PATH", Path("nonexistent.toml")):
            load_telegram_channels()


def test_load_telegram_channels_invalid_toml(tmp_path):
    p = tmp_path / "channels.toml"
    with open(p, "w") as f:
        f.write("invalid toml")

    with patch("your_module.CHANNELS_TOML_PATH", p):
        with pytest.raises(tomli.TOMLDecodeError):
            load_telegram_channels()
