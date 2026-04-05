#!/usr/bin/env python3
"""Unit tests for PreToolUse_settings_backup.py

Tests the automatic backup functionality for settings.json Edit/Write operations.
"""

import json
import sys
from pathlib import Path

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import pytest


class TestBackupFunction:
    """Test backup_settings_json() function directly."""

    def test_backup_creates_timestamped_file(self):
        """Test 1: Backup creates timestamped file with correct name."""
        import tempfile

        from PreToolUse_settings_backup import backup_settings_json

        # Create a temporary settings file
        with tempfile.NamedTemporaryFile(mode='w', suffix='_settings.json', delete=False) as f:
            json.dump({"test": "data"}, f)
            temp_settings = Path(f.name)

        try:
            # Test backup creation
            success, message = backup_settings_json(temp_settings)

            assert success, f"Backup should succeed: {message}"
            assert "Backup created:" in message, f"Message should mention backup creation: {message}"

            # Verify backup file exists
            backup_files = list(temp_settings.parent.glob("settings.backup_*.json"))
            assert len(backup_files) > 0, "Backup file should exist"

            # Verify backup contains valid JSON
            with open(backup_files[0], encoding='utf-8') as f:
                backup_data = json.load(f)
            assert backup_data == {"test": "data"}, "Backup should contain original data"

        finally:
            # Cleanup
            temp_settings.unlink(missing_ok=True)
            for backup in temp_settings.parent.glob("settings.backup_*.json"):
                backup.unlink(missing_ok=True)

    def test_backup_validates_json(self):
        """Test 2: Backup function validates JSON in backup."""
        import tempfile

        from PreToolUse_settings_backup import backup_settings_json

        # Create a temporary file with valid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='_settings.json', delete=False) as f:
            json.dump({"valid": "json"}, f)
            temp_settings = Path(f.name)

        try:
            success, message = backup_settings_json(temp_settings)
            assert success, "Valid JSON backup should succeed"

        finally:
            temp_settings.unlink(missing_ok=True)
            for backup in temp_settings.parent.glob("settings.backup_*.json"):
                backup.unlink(missing_ok=True)


class TestRunFunction:
    """Test run() hook entry point."""

    def test_edit_on_settings_json_allows(self):
        """Test 3: Edit on settings.json creates backup and allows."""
        import shutil
        import tempfile

        from PreToolUse_settings_backup import run

        # Create a temporary directory
        temp_dir = Path(tempfile.mkdtemp())

        try:
            # Create settings.json (exact name required)
            temp_settings = temp_dir / "settings.json"
            json.dump({"UNVERIFIED_STANCE_MODE": "warn"}, open(temp_settings, 'w'))

            # Test Edit on settings.json
            data = {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": str(temp_settings)
                }
            }

            result = run(data)

            # Should return None (allow) after creating backup
            assert result is None, "Edit on settings.json should be allowed after backup"

            # Verify backup was created
            backup_files = list(temp_dir.glob("settings.backup_*.json"))
            assert len(backup_files) > 0, "Backup should be created"

        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_non_settings_files_ignored(self):
        """Test 4: Non-settings.json files are ignored."""
        from PreToolUse_settings_backup import run

        # Test with different file
        data = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "P:/.claude/hooks/README.md"
            }
        }

        result = run(data)

        # Should return None (allow, no backup)
        assert result is None, "Non-settings files should be ignored"

    def test_non_edit_write_tools_ignored(self):
        """Test 5: Non-Edit/Write tools are ignored."""
        from PreToolUse_settings_backup import run

        # Test with Read tool
        data = {
            "tool_name": "Read",
            "tool_input": {
                "file_path": "P:/.claude/settings.json"
            }
        }

        result = run(data)

        # Should return None (allow, no backup)
        assert result is None, "Read tool should be ignored"

    def test_exact_filename_match_required(self):
        """Test 6: Only exact 'settings.json' filename triggers backup."""
        from PreToolUse_settings_backup import run

        # Test with similar but different filename
        test_cases = [
            "P:/.claude/my_settings.json",
            "P:/.claude/settings.json.bak",
            "P:/.claude/settings_json",
        ]

        for file_path in test_cases:
            data = {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": file_path
                }
            }

            result = run(data)
            assert result is None, f"File {file_path} should not trigger backup"


class TestJSONValidationFunction:
    """Test validate_json_syntax() function."""

    def test_valid_json_passes(self):
        """Test 7: Valid JSON passes validation."""
        import tempfile

        from PreToolUse_settings_backup import validate_json_syntax

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"valid": "json"}, f)
            temp_file = Path(f.name)

        try:
            is_valid, message = validate_json_syntax(temp_file)
            assert is_valid, "Valid JSON should pass"
            assert "valid" in message.lower(), "Message should indicate validity"

        finally:
            temp_file.unlink(missing_ok=True)

    def test_invalid_json_detected(self):
        """Test 8: Invalid JSON is detected."""
        import tempfile

        from PreToolUse_settings_backup import validate_json_syntax

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json}')  # Missing quotes around json
            temp_file = Path(f.name)

        try:
            is_valid, message = validate_json_syntax(temp_file)
            assert not is_valid, "Invalid JSON should fail"
            assert "syntax error" in message.lower(), "Message should mention syntax error"

        finally:
            temp_file.unlink(missing_ok=True)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
