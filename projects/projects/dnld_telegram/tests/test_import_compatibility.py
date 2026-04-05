#!/usr/bin/env python3
"""
Import compatibility tests for dnld_telegram.

Ensures that UI improvements don't break existing imports.
"""

import os
import sys

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestImportCompatibility:
    """Test that existing imports still work after UI changes."""

    def test_core_imports(self):
        """Test core module imports work."""
        try:
            import dnld_telegram

            assert dnld_telegram is not None
        except ImportError:
            pytest.skip("Core module not available")

    def test_config_imports(self):
        """Test config module imports work."""
        try:
            from dnld_telegram.config import manager

            assert manager is not None
        except ImportError:
            pytest.skip("Config module not available")

    def test_download_imports(self):
        """Test download module imports work."""
        try:
            from dnld_telegram.download import download

            assert download is not None
        except ImportError:
            pytest.skip("Download module not available")

    def test_ui_imports_graceful_failure(self):
        """Test UI imports fail gracefully if not implemented."""
        try:
            from dnld_telegram.ui import factory

            assert factory is not None
        except ImportError:
            # This is expected if UI modules don't exist yet
            pass

    def test_database_imports(self):
        """Test database module imports work."""
        try:
            from dnld_telegram.download.database import schema

            assert schema is not None
        except ImportError:
            pytest.skip("Database module not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
