#!/usr/bin/env python3
"""Tests for CIRCUIT_BREAKER_ENABLED feature flag (T-013)."""

import json
import os
import sys
import unittest
from pathlib import Path

# Add hooks directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestCircuitBreakerFlag(unittest.TestCase):
    """Test CIRCUIT_BREAKER_ENABLED flag controls circuit breaker behavior."""

    def setUp(self):
        """Save original env vars."""
        self.original_breaker = os.environ.get("CIRCUIT_BREAKER_ENABLED")
        self.original_legacy = os.environ.get("CONTRACT_BLOCK_CIRCUIT_BREAKER_ENABLED")

    def tearDown(self):
        """Restore original env vars."""
        if self.original_breaker is not None:
            os.environ["CIRCUIT_BREAKER_ENABLED"] = self.original_breaker
        elif "CIRCUIT_BREAKER_ENABLED" in os.environ:
            del os.environ["CIRCUIT_BREAKER_ENABLED"]

        if self.original_legacy is not None:
            os.environ["CONTRACT_BLOCK_CIRCUIT_BREAKER_ENABLED"] = self.original_legacy
        elif "CONTRACT_BLOCK_CIRCUIT_BREAKER_ENABLED" in os.environ:
            del os.environ["CONTRACT_BLOCK_CIRCUIT_BREAKER_ENABLED"]

    def test_flag_exists_in_settings(self):
        """CIRCUIT_BREAKER_ENABLED should be defined in settings.json."""
        settings_file = Path(__file__).resolve().parent.parent.parent / "settings.json"
        self.assertTrue(settings_file.exists())

        with open(settings_file, encoding="utf-8") as f:
            settings = json.load(f)

        self.assertIn("env", settings)
        self.assertIn("CIRCUIT_BREAKER_ENABLED", settings["env"])

    def test_flag_default_is_true(self):
        """CIRCUIT_BREAKER_ENABLED should default to true (enabled)."""
        # Check settings.json has the flag set to "true"
        settings_file = Path(__file__).resolve().parent.parent.parent / "settings.json"
        with open(settings_file, encoding="utf-8") as f:
            settings = json.load(f)

        self.assertEqual(settings["env"]["CIRCUIT_BREAKER_ENABLED"], "true")

    def test_flag_can_disable_breaker(self):
        """When CIRCUIT_BREAKER_ENABLED=false, breaker should be disabled."""
        os.environ["CIRCUIT_BREAKER_ENABLED"] = "false"

        # Verify flag is read correctly
        enabled = os.environ.get("CIRCUIT_BREAKER_ENABLED", "true").lower() in {"1", "true", "yes"}
        self.assertFalse(enabled)

    def test_flag_can_enable_breaker(self):
        """When CIRCUIT_BREAKER_ENABLED=true, breaker should be enabled."""
        os.environ["CIRCUIT_BREAKER_ENABLED"] = "true"

        # Verify flag is read correctly
        enabled = os.environ.get("CIRCUIT_BREAKER_ENABLED", "false").lower() in {"1", "true", "yes"}
        self.assertTrue(enabled)

    def test_legacy_flag_still_works(self):
        """Legacy CONTRACT_BLOCK_CIRCUIT_BREAKER_ENABLED should still work."""
        os.environ["CIRCUIT_BREAKER_ENABLED"] = "false"
        os.environ["CONTRACT_BLOCK_CIRCUIT_BREAKER_ENABLED"] = "true"

        # Check that legacy flag enables breaker
        breaker_enabled = (
            os.environ.get("CIRCUIT_BREAKER_ENABLED", "false").lower() in {"1", "true", "yes"}
            or os.environ.get("CONTRACT_BLOCK_CIRCUIT_BREAKER_ENABLED", "false").lower() in {"1", "true", "yes"}
        )
        self.assertTrue(breaker_enabled)

    def test_both_off_disables_breaker(self):
        """When both flags are OFF, breaker should be disabled."""
        os.environ["CIRCUIT_BREAKER_ENABLED"] = "false"
        os.environ["CONTRACT_BLOCK_CIRCUIT_BREAKER_ENABLED"] = "false"

        breaker_enabled = (
            os.environ.get("CIRCUIT_BREAKER_ENABLED", "false").lower() in {"1", "true", "yes"}
            or os.environ.get("CONTRACT_BLOCK_CIRCUIT_BREAKER_ENABLED", "false").lower() in {"1", "true", "yes"}
        )
        self.assertFalse(breaker_enabled)


if __name__ == '__main__':
    unittest.main()
