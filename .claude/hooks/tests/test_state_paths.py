#!/usr/bin/env python3
"""
Tests for state_paths.py - Terminal-scoped state path utilities.

Tests cover:
- Terminal-scoped state directory creation
- Session-scoped state directory creation
- Shared state directory creation
- Path generation for state files
- Legacy state file migration
- Cleanup of migrated files
"""

from __future__ import annotations

import os
import shutil

# Add hooks lib to path
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path("P:/.claude/hooks/__lib").resolve()))


class TestTerminalStatePaths(unittest.TestCase):
    """Test terminal-scoped state path functions."""

    def setUp(self):
        """Create temporary state directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.original_state_dir = os.environ.get("PROJECT_ROOT")

        # Set up test environment
        os.environ["PROJECT_ROOT"] = self.test_dir

        # Import state_paths with new PROJECT_ROOT
        import importlib

        import state_paths

        importlib.reload(state_paths)

        # Update references
        self.get_terminal_state_dir = state_paths.get_terminal_state_dir
        self.get_terminal_state_path = state_paths.get_terminal_state_path

    def tearDown(self):
        """Clean up temporary directory."""
        if self.original_state_dir:
            os.environ["PROJECT_ROOT"] = self.original_state_dir
        else:
            os.environ.pop("PROJECT_ROOT", None)

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_get_terminal_state_dir_creates_directory(self):
        """Test that get_terminal_state_dir creates the directory."""
        terminal_id = "console_abc123"
        terminal_dir = self.get_terminal_state_dir(terminal_id)

        self.assertTrue(terminal_dir.exists())
        self.assertTrue(terminal_dir.is_dir())
        self.assertEqual(terminal_dir.name, terminal_id)
        self.assertIn("terminals", str(terminal_dir))

    def test_get_terminal_state_dir_with_empty_terminal_id(self):
        """Test that empty terminal_id returns global state dir."""
        terminal_dir = self.get_terminal_state_dir("")

        # Should return STATE_DIR, not a terminal subdirectory
        self.assertTrue(terminal_dir.exists())
        self.assertNotIn("terminals", str(terminal_dir))

    def test_get_terminal_state_path_returns_correct_path(self):
        """Test get_terminal_state_path returns correct file path."""
        terminal_id = "console_abc123"
        filename = "pending_command_intent.json"

        file_path = self.get_terminal_state_path(terminal_id, filename)

        self.assertTrue(file_path.name == filename)
        self.assertIn(terminal_id, str(file_path))
        self.assertIn("terminals", str(file_path))

    def test_multiple_terminals_get_separate_directories(self):
        """Test that different terminal_ids get separate directories."""
        terminal_1 = "console_abc123"
        terminal_2 = "console_def456"

        dir_1 = self.get_terminal_state_dir(terminal_1)
        dir_2 = self.get_terminal_state_dir(terminal_2)

        self.assertNotEqual(dir_1, dir_2)
        self.assertTrue(dir_1.exists())
        self.assertTrue(dir_2.exists())


class TestSessionStatePaths(unittest.TestCase):
    """Test session-scoped state path functions."""

    def setUp(self):
        """Create temporary state directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.original_state_dir = os.environ.get("PROJECT_ROOT")

        os.environ["PROJECT_ROOT"] = self.test_dir

        # Reload state_paths with new PROJECT_ROOT
        import importlib

        import state_paths

        importlib.reload(state_paths)

        self.get_session_state_dir = state_paths.get_session_state_dir
        self.get_session_state_path = state_paths.get_session_state_path

    def tearDown(self):
        """Clean up temporary directory."""
        if self.original_state_dir:
            os.environ["PROJECT_ROOT"] = self.original_state_dir
        else:
            os.environ.pop("PROJECT_ROOT", None)

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_get_session_state_dir_creates_directory(self):
        """Test that get_session_state_dir creates the directory."""
        session_id = "env_session_xyz789"
        session_dir = self.get_session_state_dir(session_id)

        self.assertTrue(session_dir.exists())
        self.assertTrue(session_dir.is_dir())
        self.assertEqual(session_dir.name, session_id)
        self.assertIn("sessions", str(session_dir))

    def test_get_session_state_dir_with_empty_session_id(self):
        """Test that empty session_id returns global state dir."""
        session_dir = self.get_session_state_dir("")

        # Should return STATE_DIR, not a session subdirectory
        self.assertTrue(session_dir.exists())
        self.assertNotIn("sessions", str(session_dir))

    def test_get_session_state_path_returns_correct_path(self):
        """Test get_session_state_path returns correct file path."""
        session_id = "env_session_xyz789"
        filename = "actions.log"

        file_path = self.get_session_state_path(session_id, filename)

        self.assertTrue(file_path.name == filename)
        self.assertIn(session_id, str(file_path))
        self.assertIn("sessions", str(file_path))


class TestSharedStatePaths(unittest.TestCase):
    """Test shared state path functions."""

    def setUp(self):
        """Create temporary state directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.original_state_dir = os.environ.get("PROJECT_ROOT")

        os.environ["PROJECT_ROOT"] = self.test_dir

        # Reload state_paths with new PROJECT_ROOT
        import importlib

        import state_paths

        importlib.reload(state_paths)

        self.get_shared_state_dir = state_paths.get_shared_state_dir
        self.get_shared_state_path = state_paths.get_shared_state_path

    def tearDown(self):
        """Clean up temporary directory."""
        if self.original_state_dir:
            os.environ["PROJECT_ROOT"] = self.original_state_dir
        else:
            os.environ.pop("PROJECT_ROOT", None)

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_get_shared_state_dir_creates_directory(self):
        """Test that get_shared_state_dir creates the directory."""
        shared_dir = self.get_shared_state_dir()

        self.assertTrue(shared_dir.exists())
        self.assertTrue(shared_dir.is_dir())
        self.assertEqual(shared_dir.name, "shared")
        self.assertIn("shared", str(shared_dir))

    def test_get_shared_state_path_returns_correct_path(self):
        """Test get_shared_state_path returns correct file path."""
        filename = "hook_ledger.db"

        file_path = self.get_shared_state_path(filename)

        self.assertTrue(file_path.name == filename)
        self.assertIn("shared", str(file_path))


class TestLegacyMigration(unittest.TestCase):
    """Test legacy state file migration."""

    def setUp(self):
        """Create temporary state directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.original_state_dir = os.environ.get("PROJECT_ROOT")

        os.environ["PROJECT_ROOT"] = self.test_dir

        # Reload state_paths with new PROJECT_ROOT
        import importlib

        import state_paths

        importlib.reload(state_paths)

        self.migrate_legacy_state_file = state_paths.migrate_legacy_state_file
        self.cleanup_legacy_state_file = state_paths.cleanup_legacy_state_file

    def tearDown(self):
        """Clean up temporary directory."""
        if self.original_state_dir:
            os.environ["PROJECT_ROOT"] = self.original_state_dir
        else:
            os.environ.pop("PROJECT_ROOT", None)

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_migrate_terminal_scoped_file(self):
        """Test migration of terminal-scoped state file."""
        # Create legacy file
        state_dir = Path(self.test_dir) / ".claude" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        legacy_file = state_dir / "pending_command_intent.json"
        legacy_file.write_text('{"test": "data"}')

        # Migrate to terminal-scoped location
        terminal_id = "console_abc123"
        new_path = self.migrate_legacy_state_file(legacy_file, terminal_id=terminal_id)

        self.assertIsNotNone(new_path)
        self.assertTrue(new_path.exists())
        self.assertIn("terminals", str(new_path))
        self.assertIn(terminal_id, str(new_path))
        self.assertEqual(new_path.read_text(), '{"test": "data"}')

    def test_migrate_session_scoped_file(self):
        """Test migration of session-scoped state file."""
        # Create legacy file
        state_dir = Path(self.test_dir) / ".claude" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        legacy_file = state_dir / "skill_execution_env_xyz.json"
        legacy_file.write_text('{"env": "data"}')

        # Migrate to session-scoped location
        session_id = "env_session_xyz789"
        new_path = self.migrate_legacy_state_file(legacy_file, session_id=session_id)

        self.assertIsNotNone(new_path)
        self.assertTrue(new_path.exists())
        self.assertIn("sessions", str(new_path))

    def test_migrate_nonexistent_file(self):
        """Test migration of non-existent file returns None."""
        state_dir = Path(self.test_dir) / ".claude" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        legacy_file = state_dir / "does_not_exist.json"

        new_path = self.migrate_legacy_state_file(legacy_file)

        self.assertIsNone(new_path)

    def test_cleanup_legacy_file_after_migration(self):
        """Test cleanup of legacy file after successful migration."""
        # Create legacy file
        state_dir = Path(self.test_dir) / ".claude" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        legacy_file = state_dir / "test_cleanup.json"
        legacy_file.write_text('{"test": "data"}')

        # Migrate
        terminal_id = "console_abc123"
        new_path = self.migrate_legacy_state_file(legacy_file, terminal_id=terminal_id)

        # Cleanup
        success = self.cleanup_legacy_state_file(legacy_file, new_path)

        self.assertTrue(success)
        self.assertFalse(legacy_file.exists())
        self.assertTrue(new_path.exists())

    def test_cleanup_without_migration_does_not_delete(self):
        """Test cleanup without migration does not delete file."""
        # Create file
        state_dir = Path(self.test_dir) / ".claude" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        legacy_file = state_dir / "test_no_migration.json"
        legacy_file.write_text('{"test": "data"}')

        # Cleanup without migration
        success = self.cleanup_legacy_state_file(legacy_file, migrated_to=None)

        self.assertFalse(success)
        self.assertTrue(legacy_file.exists())


if __name__ == "__main__":
    unittest.main()
