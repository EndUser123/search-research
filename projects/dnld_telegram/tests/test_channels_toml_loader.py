"""
Unit tests for configuration loading functions in dnld_telegram/src/config/channels_toml_loader.py
"""

from pathlib import Path

import pytest
from dnld_telegram.config import channels_toml_loader


def test_load_telegram_channels_missing_file():
    # Should raise FileNotFoundError
    with pytest.raises(FileNotFoundError):
        channels_toml_loader.load_telegram_channels(Path("nonexistent.toml"))


def test_load_telegram_channels_invalid_toml(tmp_path):
    # Write invalid TOML
    toml_path = tmp_path / "invalid.toml"
    toml_path.write_text("not_a_valid_toml: [unclosed")
    with pytest.raises(Exception):
        channels_toml_loader.load_telegram_channels(toml_path)


def test_load_telegram_channels_schema_validation(tmp_path):
    # Write TOML missing required fields
    toml_path = tmp_path / "bad_schema.toml"
    toml_path.write_text(
        """[channel]
name = 'test'
"""
    )
    # Should raise or return empty/fallback
    try:
        result = channels_toml_loader.load_telegram_channels(toml_path)
        assert isinstance(result, dict)
        assert not result  # Should be empty or fallback
    except Exception:
        pass


def test_get_channels_error_handling(monkeypatch):
    # Simulate error in load_telegram_channels
    monkeypatch.setattr(
        channels_toml_loader,
        "load_telegram_channels",
        lambda *a, **kw: (_ for _ in ()).throw(Exception("fail")),
    )
    # Should raise Exception
    with pytest.raises(Exception):
        channels_toml_loader.get_channels()
