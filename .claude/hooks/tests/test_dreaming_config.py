"""Tests for dreaming config system (T-001).

These tests verify the dreaming config loader behavior:
- Config file created at first run
- Missing keys use defaults
- Invalid JSON falls back to defaults
- Extra keys preserved

Run with: pytest P:/.claude/hooks/tests/test_dreaming_config.py -v
"""
import json


class TestDreamingConfigDefaults:
    """Tests for default config when file is missing."""

    def test_default_config_when_file_missing(self, tmp_path):
        """
        Test that default config is returned when file doesn't exist.

        Given: Config file does not exist
        When: load_config() is called
        Then: Default config is returned with all expected keys
        """
        # Arrange
        config_path = tmp_path / "dreaming-config.json"

        # Act & Assert
        # This will fail because dreaming_config module doesn't exist yet
        from hooks.dreaming_config import load_config
        config = load_config(config_path=str(config_path))

        # Assert default values
        assert config is not None
        assert "enabled" in config
        assert "cycle_interval_minutes" in config
        assert "orphans_per_cycle" in config
        assert "relationship_threshold" in config
        assert "max_relationships_per_orphan" in config

    def test_default_values_are_correct(self, tmp_path):
        """
        Test that default values match specification.

        Given: Config file does not exist
        When: load_config() is called
        Then: Default values match documented defaults
        """
        # Arrange
        config_path = tmp_path / "dreaming-config.json"

        # Act
        from hooks.dreaming_config import load_config
        config = load_config(config_path=str(config_path))

        # Assert
        assert config["enabled"] is True
        assert config["cycle_interval_minutes"] == 60
        assert config["orphans_per_cycle"] == 10
        assert config["relationship_threshold"] == 0.7
        assert config["max_relationships_per_orphan"] == 5


class TestDreamingConfigValidFile:
    """Tests for loading valid config file."""

    def test_load_valid_config_file(self, tmp_path):
        """
        Test that valid config file is loaded correctly.

        Given: Valid config file exists
        When: load_config() is called
        Then: Config values from file are returned
        """
        # Arrange
        config_path = tmp_path / "dreaming-config.json"
        test_config = {
            "enabled": False,
            "cycle_interval_minutes": 120,
            "orphans_per_cycle": 20,
            "relationship_threshold": 0.8,
            "max_relationships_per_orphan": 10
        }
        config_path.write_text(json.dumps(test_config))

        # Act
        from hooks.dreaming_config import load_config
        config = load_config(config_path=str(config_path))

        # Assert
        assert config["enabled"] is False
        assert config["cycle_interval_minutes"] == 120
        assert config["orphans_per_cycle"] == 20
        assert config["relationship_threshold"] == 0.8
        assert config["max_relationships_per_orphan"] == 10


class TestDreamingConfigMissingKeys:
    """Tests for missing keys using defaults."""

    def test_missing_keys_use_defaults(self, tmp_path):
        """
        Test that missing keys fall back to defaults.

        Given: Config file with only some keys
        When: load_config() is called
        Then: Missing keys use default values
        """
        # Arrange
        config_path = tmp_path / "dreaming-config.json"
        partial_config = {
            "enabled": False,
            "cycle_interval_minutes": 120
        }
        config_path.write_text(json.dumps(partial_config))

        # Act
        from hooks.dreaming_config import load_config
        config = load_config(config_path=str(config_path))

        # Assert - present keys from file
        assert config["enabled"] is False
        assert config["cycle_interval_minutes"] == 120

        # Assert - missing keys use defaults
        assert config["orphans_per_cycle"] == 10  # default
        assert config["relationship_threshold"] == 0.7  # default
        assert config["max_relationships_per_orphan"] == 5  # default

    def test_empty_file_uses_all_defaults(self, tmp_path):
        """
        Test that empty JSON object uses all defaults.

        Given: Config file is empty object {}
        When: load_config() is called
        Then: All keys use default values
        """
        # Arrange
        config_path = tmp_path / "dreaming-config.json"
        config_path.write_text("{}")

        # Act
        from hooks.dreaming_config import load_config
        config = load_config(config_path=str(config_path))

        # Assert - all defaults
        assert config["enabled"] is True
        assert config["cycle_interval_minutes"] == 60
        assert config["orphans_per_cycle"] == 10
        assert config["relationship_threshold"] == 0.7
        assert config["max_relationships_per_orphan"] == 5


class TestDreamingConfigInvalidJSON:
    """Tests for invalid JSON falling back to defaults."""

    def test_invalid_json_fallback_to_defaults(self, tmp_path):
        """
        Test that invalid JSON falls back to defaults.

        Given: Config file contains invalid JSON
        When: load_config() is called
        Then: Default config is returned (fallback behavior)
        """
        # Arrange
        config_path = tmp_path / "dreaming-config.json"
        config_path.write_text("{ invalid json }")

        # Act
        from hooks.dreaming_config import load_config
        config = load_config(config_path=str(config_path))

        # Assert - defaults returned
        assert config["enabled"] is True
        assert config["cycle_interval_minutes"] == 60
        assert config["orphans_per_cycle"] == 10
        assert config["relationship_threshold"] == 0.7
        assert config["max_relationships_per_orphan"] == 5

    def test_corrupted_file_fallback_to_defaults(self, tmp_path):
        """
        Test that corrupted file falls back to defaults.

        Given: Config file contains binary/corrupted data
        When: load_config() is called
        Then: Default config is returned
        """
        # Arrange
        config_path = tmp_path / "dreaming-config.json"
        config_path.write_bytes(b'\x00\x01\x02\x03\x04\x05')

        # Act
        from hooks.dreaming_config import load_config
        config = load_config(config_path=str(config_path))

        # Assert - defaults returned
        assert config["enabled"] is True
        assert config["cycle_interval_minutes"] == 60
        assert config["orphans_per_cycle"] == 10


class TestDreamingConfigExtraKeys:
    """Tests for extra keys being preserved."""

    def test_extra_keys_preserved(self, tmp_path):
        """
        Test that extra keys in config file are preserved.

        Given: Config file has extra keys beyond defaults
        When: load_config() is called
        Then: Extra keys are included in returned config
        """
        # Arrange
        config_path = tmp_path / "dreaming-config.json"
        config_with_extras = {
            "enabled": True,
            "cycle_interval_minutes": 60,
            "orphans_per_cycle": 10,
            "relationship_threshold": 0.7,
            "max_relationships_per_orphan": 5,
            "custom_key": "custom_value",
            "another_extra": 123
        }
        config_path.write_text(json.dumps(config_with_extras))

        # Act
        from hooks.dreaming_config import load_config
        config = load_config(config_path=str(config_path))

        # Assert - standard keys
        assert config["enabled"] is True
        assert config["cycle_interval_minutes"] == 60

        # Assert - extra keys preserved
        assert "custom_key" in config
        assert config["custom_key"] == "custom_value"
        assert "another_extra" in config
        assert config["another_extra"] == 123
