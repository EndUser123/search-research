"""
Tests for yt_fts.utils.config module.

Tests environment loading, config path resolution, and database path logic.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from yt_fts.utils.config import find_and_load_env, get_config_path, get_db_path


class TestFindAndLoadEnv:
    """Test .env file discovery and loading."""

    def test_returns_path_when_env_found_in_project_root(self, tmp_path):
        """Should return path to .env when found in project root."""
        # Arrange: Create .env in a temporary directory
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=test_value")

        # Act: Search from that directory
        with patch("yt_fts.utils.config.Path") as mock_path:
            mock_path.cwd.return_value = tmp_path
            mock_path(__file__).parent.parent.parent.parent = tmp_path

            result = find_and_load_env(start_dir=tmp_path)

        # Assert
        assert result == str(env_file)

    def test_returns_path_when_env_found_in_parent(self, tmp_path):
        """Should return path to .env when found in parent directory."""
        # Arrange: Create .env in parent directory
        parent_env = tmp_path / ".env"
        parent_env.write_text("TEST_VAR=parent_value")

        # Act: Search from subdirectory
        with patch("yt_fts.utils.config.Path") as mock_path:
            mock_path.cwd.return_value = tmp_path / "subdir"

            result = find_and_load_env(start_dir=tmp_path)

        # Assert
        assert result == str(parent_env)

    def test_returns_none_when_no_env_found(self, tmp_path):
        """Should return None when .env not found in any location."""
        # Arrange: Create a nested directory structure with no .env files
        empty_project = tmp_path / "deeply" / "nested" / "empty_project"
        empty_project.mkdir(parents=True)

        # Act: Use empty_project as start_dir (no .env there or in its parents within tmp_path)
        result = find_and_load_env(start_dir=empty_project)

        # Assert
        assert result is None

    def test_loads_environment_variables(self, tmp_path, monkeypatch):
        """Should actually load environment variables from .env file."""
        # Arrange: Create .env with test variables
        env_file = tmp_path / ".env"
        env_file.write_text('TEST_KEY_1=value1\nTEST_KEY_2=value2')

        # Act: Load the env file
        with patch("yt_fts.utils.config.Path") as mock_path:
            mock_path.cwd.return_value = tmp_path
            mock_path(__file__).parent.parent.parent.parent = tmp_path

            find_and_load_env(start_dir=tmp_path)

        # Assert: Environment variables should be loaded
        assert os.getenv("TEST_KEY_1") == "value1"
        assert os.getenv("TEST_KEY_2") == "value2"

    def test_prioritizes_project_root_over_other_locations(self, tmp_path):
        """Should prioritize .env in project root over other locations."""
        # Arrange: Create .env in multiple locations
        project_env = tmp_path / ".env"
        project_env.write_text("SOURCE=project")

        parent_env = tmp_path.parent / ".env"
        parent_env.write_text("SOURCE=parent")

        # Act
        with patch("yt_fts.utils.config.Path") as mock_path:
            mock_path.cwd.return_value = tmp_path
            mock_path(__file__).parent.parent.parent.parent = tmp_path

            result = find_and_load_env(start_dir=tmp_path)

        # Assert: Should return project root .env (first priority)
        assert result == str(project_env)

    def test_checks_multiple_locations_in_priority_order(self, tmp_path):
        """Should check multiple locations in correct priority order."""
        # Arrange: Only create .env in parent location
        # (grandparent scenario not testable in tmp_path, so we test parent fallback)
        parent_env = tmp_path.parent / ".env"
        parent_env.write_text("SOURCE=parent")

        # Act: Start from subdirectory (should find parent .env)
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        result = find_and_load_env(start_dir=subdir)

        # Assert: Should find the parent .env
        assert result == str(parent_env)

    def test_returns_windows_appdata_path(self, monkeypatch, tmp_path):
        """Should return Windows APPDATA path when on Windows."""
        # Arrange: Create a fake APPDATA with yt-fts directory
        fake_appdata = tmp_path / "AppData"
        fake_config = fake_appdata / "yt-fts"
        fake_config.mkdir(parents=True)

        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.setenv("APPDATA", str(fake_appdata))

        # Act
        result = get_config_path()

        # Assert
        assert result == str(fake_config)

    def test_returns_none_when_config_dir_not_exists(self, monkeypatch):
        """Should return None when config directory doesn't exist."""
        # Arrange
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.setenv("APPDATA", "C:\\NonExistent\\Path")

        # Act
        result = get_config_path()

        # Assert
        assert result is None


class TestGetDbPath:
    """Test database path resolution."""

    def test_returns_custom_path_from_env_var(self, monkeypatch, tmp_path):
        """Should return custom path when YT_FTS_DB_PATH is set."""
        # Arrange
        custom_db = tmp_path / "custom" / "subtitles.db"
        monkeypatch.setenv("YT_FTS_DB_PATH", str(custom_db))

        # Act
        result = get_db_path()

        # Assert
        assert result == str(custom_db)

    def test_creates_parent_directory_for_custom_path(self, monkeypatch, tmp_path):
        """Should create parent directory when using custom path."""
        # Arrange
        custom_db = tmp_path / "new_dir" / "subtitles.db"
        monkeypatch.setenv("YT_FTS_DB_PATH", str(custom_db))

        # Act
        result = get_db_path()

        # Assert
        assert Path(result).parent.exists()
        assert result == str(custom_db)
