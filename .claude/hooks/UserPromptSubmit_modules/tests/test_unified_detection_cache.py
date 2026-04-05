"""Tests for unified_detection.py cache invalidation.

Tests cache invalidation mechanism for config file changes.
"""
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from unified_detection import (
    _CHECK_INTERVAL_SECONDS,
    _CONFIG_FILE_PATH,
    _get_config_mtime,
    _should_reload_patterns,
)


class TestConfigMtime:
    """Test config file modification time tracking."""

    def test_get_config_mtime_returns_float_or_none(self):
        """Test that _get_config_mtime returns float or None."""
        mtime = _get_config_mtime()
        assert mtime is None or isinstance(mtime, float)

    def test_get_config_mtime_none_if_missing(self, tmp_path):
        """Test that _get_config_mtime returns None for missing file."""
        # Save original path
        original_path = _CONFIG_FILE_PATH

        # Temporarily change to non-existent file
        import unified_detection
        unified_detection._CONFIG_FILE_PATH = tmp_path / "nonexistent.json"

        try:
            mtime = _get_config_mtime()
            assert mtime is None
        finally:
            # Restore original path
            unified_detection._CONFIG_FILE_PATH = original_path


class TestCacheInvalidation:
    """Test cache invalidation logic."""

    def test_should_reload_returns_false_on_first_call(self):
        """Test that first call initializes and returns False."""
        # Reset state
        import unified_detection
        unified_detection._CONFIG_MTIME = None
        unified_detection._LAST_CHECK_TIME = 0.0

        # First call should initialize and return False
        result = _should_reload_patterns()
        assert result is False
        assert unified_detection._CONFIG_MTIME is not None

    def test_should_reload_throttles_checks(self):
        """Test that checks are throttled by interval."""
        import unified_detection

        # Set last check to current time
        unified_detection._LAST_CHECK_TIME = time.perf_counter()

        # Immediate second call should return False (throttled)
        result = _should_reload_patterns()
        assert result is False

    def test_should_reload_detects_mtime_change(self, tmp_path):
        """Test that mtime changes are detected."""
        import unified_detection

        # Create test config file
        test_config = tmp_path / "test_config.json"
        test_config.write_text('{"test": "value"}')

        # Set up module to use test config
        original_path = unified_detection._CONFIG_FILE_PATH
        unified_detection._CONFIG_FILE_PATH = test_config

        try:
            # Initialize with current mtime
            unified_detection._CONFIG_MTIME = None
            unified_detection._LAST_CHECK_TIME = 0.0
            _should_reload_patterns()  # Initialize

            initial_mtime = unified_detection._CONFIG_MTIME
            assert initial_mtime is not None

            # Wait to ensure different timestamp
            time.sleep(0.1)

            # Modify file
            test_config.write_text('{"test": "updated"}')

            # Reset throttle timer
            unified_detection._LAST_CHECK_TIME = 0.0

            # Should detect change
            result = _should_reload_patterns()
            assert result is True
            assert unified_detection._CONFIG_MTIME != initial_mtime

        finally:
            # Restore original path
            unified_detection._CONFIG_FILE_PATH = original_path

    def test_check_interval_constant(self):
        """Test that check interval is set reasonably."""
        # Should check at most every 5 seconds
        assert _CHECK_INTERVAL_SECONDS == 5.0


class TestDetectionWithCache:
    """Test that detection works with cache invalidation."""

    def test_detect_prompt_basic(self):
        """Test basic detection still works with cache check."""
        from unified_detection import detect_prompt

        result = detect_prompt("debug this error")
        assert result is not None
        assert isinstance(result.matched_frameworks, list)
        assert isinstance(result.confidence, int)

    def test_detect_prompt_empty(self):
        """Test detection with empty prompt."""
        from unified_detection import detect_prompt

        result = detect_prompt("")
        assert result.confidence == 0
        assert len(result.matched_frameworks) == 0

    def test_detect_prompt_short(self):
        """Test detection with short prompt."""
        from unified_detection import detect_prompt

        result = detect_prompt("hi")
        assert result.confidence == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
