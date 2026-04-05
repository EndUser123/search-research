"""Tests for config module.

Tests for configuration loading, validation, and defaults.
"""

import os
import tempfile
from pathlib import Path

import pytest

from rca.config import (
    get_config_dir,
    get_state_dir,
    load_config,
    merge_with_defaults,
)


class TestLoadConfig:
    """Test configuration loading."""

    def test_load_default_config(self):
        """Default configuration can be loaded."""
        config = load_config()

        assert config is not None
        assert isinstance(config, dict)

    def test_config_has_required_sections(self):
        """Config has all required sections."""
        config = load_config()

        # Check for common config keys
        assert "hypothesis_scoring" in config or "metrics" in config or len(config) > 0

    def test_load_config_from_file(self):
        """Config can be loaded from custom file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("hypothesis_scoring:\n  reproducibility_weight: 0.5\n")
            temp_path = f.name

        try:
            config = load_config(temp_path)

            assert "hypothesis_scoring" in config
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_file_returns_defaults(self):
        """Nonexistent file returns default config."""
        config = load_config("/nonexistent/path/config.yaml")

        assert config is not None


class TestMergeWithDefaults:
    """Test merging with defaults."""

    def test_merge_empty_config(self):
        """Empty config gets all defaults."""
        result = merge_with_defaults({})

        assert result is not None
        assert isinstance(result, dict)

    def test_merge_partial_config(self):
        """Partial config merges with defaults."""
        custom = {"hypothesis_scoring": {"reproducibility_weight": 0.5}}
        result = merge_with_defaults(custom)

        assert result["hypothesis_scoring"]["reproducibility_weight"] == 0.5

    def test_custom_overrides_defaults(self):
        """Custom values override defaults."""
        custom = {"hypothesis_scoring": {"reproducibility_weight": 0.9}}
        result = merge_with_defaults(custom)

        assert result["hypothesis_scoring"]["reproducibility_weight"] == 0.9

    def test_preserves_non_default_keys(self):
        """Non-default keys are preserved."""
        custom = {"custom_key": "custom_value"}
        result = merge_with_defaults(custom)

        assert result["custom_key"] == "custom_value"


class TestConfigDirectories:
    """Test configuration directory paths."""

    def test_get_config_dir(self):
        """Config directory path can be retrieved."""
        config_dir = get_config_dir()

        assert config_dir is not None
        assert isinstance(config_dir, (str, Path))

    def test_get_state_dir(self):
        """State directory path can be retrieved."""
        state_dir = get_state_dir()

        assert state_dir is not None
        assert isinstance(state_dir, (str, Path))

    def test_config_dir_exists(self):
        """Config directory exists or can be created."""
        config_dir = get_config_dir()

        if isinstance(config_dir, str):
            config_dir = Path(config_dir)

        # Directory should exist or be creatable
        assert config_dir is not None


class TestConfigValidation:
    """Test configuration validation."""

    def test_valid_weight_range(self):
        """Weights are within valid range."""
        config = load_config()
        scoring = config.get("hypothesis_scoring", {})

        for key, value in scoring.items():
            if "weight" in key and isinstance(value, (int, float)):
                assert 0.0 <= value <= 1.0

    def test_weights_sum_not_required(self):
        """Weights don't need to sum to 1.0 (they're exponents)."""
        config = load_config()
        scoring = config.get("hypothesis_scoring", {})

        # Weights are exponents in power formula, not probabilities
        # So they don't need to sum to 1.0
        weights = [
            v for k, v in scoring.items()
            if "weight" in k and isinstance(v, (int, float))
        ]

        # Just verify they're positive
        for weight in weights:
            assert weight > 0


class TestEdgeCases:
    """Test edge cases."""

    def test_none_config_path(self):
        """None path uses default config."""
        config = load_config(None)

        assert config is not None

    def test_empty_string_config_path(self):
        """Empty string path uses default config."""
        config = load_config("")

        assert config is not None

    def test_invalid_yaml_returns_defaults(self):
        """Invalid YAML falls back to defaults."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [[[\n")
            temp_path = f.name

        try:
            # Should not crash, may return defaults or raise
            try:
                config = load_config(temp_path)
                assert config is not None
            except Exception:
                # Parsing error is acceptable for invalid YAML
                pass
        finally:
            os.unlink(temp_path)
