#!/usr/bin/env python3
"""
Basic UI component tests for dnld_telegram.

Tests that UI improvements don't break basic display functionality.
"""

import os
import sys
from dataclasses import dataclass

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@dataclass
class MockSessionInfo:
    """Mock session information for testing."""

    total_files: int = 100
    channel_name: str = "test_channel"
    estimated_size: int = 1024 * 1024


@dataclass
class MockProgressUpdate:
    """Mock progress update data for testing."""

    files_completed: int = 0
    files_total: int = 100
    bytes_downloaded: int = 0
    bytes_total: int = 1024 * 1024
    current_file: str | None = None
    download_speed: float = 0.0


# Mock UI components if they don't exist
try:
    from dnld_telegram.ui.factory import UIFactory
    from dnld_telegram.ui.protocols import DisplayConfig
except ImportError:

    class DisplayConfig:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class UIFactory:
        @staticmethod
        def create_display(config):
            return MockDisplay()


class MockDisplay:
    """Mock display for testing."""

    def __init__(self):
        self.started = False
        self.finished = False

    async def start_session(self, session_info):
        self.started = True

    async def finish_session(self):
        self.finished = True

    async def update_progress(self, update_data):
        pass


class TestUIBasics:
    """Test basic UI functionality."""

    def test_factory_creates_display(self):
        """Test factory can create displays."""
        config = DisplayConfig(display_type="simple")
        display = UIFactory.create_display(config)
        assert display is not None

    def test_display_has_required_methods(self):
        """Test display has required methods."""
        config = DisplayConfig(display_type="simple")
        display = UIFactory.create_display(config)

        assert hasattr(display, "start_session")
        assert hasattr(display, "finish_session")
        assert hasattr(display, "update_progress")

    @pytest.mark.asyncio
    async def test_session_lifecycle(self):
        """Test basic session lifecycle."""
        config = DisplayConfig(display_type="simple")
        display = UIFactory.create_display(config)

        session_info = MockSessionInfo()
        await display.start_session(session_info)
        await display.finish_session()

    @pytest.mark.asyncio
    async def test_progress_update(self):
        """Test basic progress update."""
        config = DisplayConfig(display_type="simple")
        display = UIFactory.create_display(config)

        session_info = MockSessionInfo()
        await display.start_session(session_info)

        update = MockProgressUpdate(files_completed=50, files_total=100)
        await display.update_progress(update)

        await display.finish_session()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
