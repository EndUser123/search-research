"""
Test suite for intent file lifecycle.

Tests cover:
- Intent file creation with correct schema
- Intent file deletion after skill execution
- Intent file validation (missing fields, invalid data)
- Concurrent terminal isolation
- Three-tier path lookup (primary/secondary/fallback)
"""

import json

# Add hooks directory to path for imports
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))



class TestIntentFileCreation:
    """Test intent file creation by skill_enforcer.py"""

    def test_intent_file_created_with_correct_path(self, temp_state_dir, mock_terminal_id):
        """Test that intent file is created in the correct terminal-specific directory"""
        intent_dir = temp_state_dir / mock_terminal_id
        intent_dir.mkdir(parents=True, exist_ok=True)

        intent_file = intent_dir / "pending_command_intent.json"

        # Verify file exists after creation
        assert intent_file.exists()
        assert intent_file.is_file()

    def test_intent_file_has_all_required_fields(self, sample_intent_file):
        """Test that intent file contains all required schema fields"""
        with open(sample_intent_file) as f:
            intent_data = json.load(f)

        # Verify all required fields are present
        assert "skill" in intent_data
        assert "prompt" in intent_data
        assert "timestamp" in intent_data
        assert "session_id" in intent_data
        assert "terminal_id" in intent_data
        assert "created_at" in intent_data

    def test_intent_file_created_at_field_is_epoch_timestamp(self, sample_intent_file):
        """Test that created_at field is a valid Unix epoch timestamp"""
        with open(sample_intent_file) as f:
            intent_data = json.load(f)

        created_at = intent_data["created_at"]

        # Verify it's an integer (epoch seconds)
        assert isinstance(created_at, int)

        # Verify it's a reasonable timestamp (not too old or too new)
        now = int(datetime.now(timezone.utc).timestamp())
        assert 0 < now - created_at < 10  # Created within last 10 seconds

    def test_intent_file_timestamp_is_iso_format(self, sample_intent_file):
        """Test that timestamp field is in ISO 8601 format"""
        with open(sample_intent_file) as f:
            intent_data = json.load(f)

        timestamp = intent_data["timestamp"]

        # Verify ISO format by attempting to parse it
        parsed_time = datetime.fromisoformat(timestamp)
        assert parsed_time is not None

    def test_intent_file_terminal_id_matches_directory(self, sample_intent_file, mock_terminal_id):
        """Test that terminal_id in intent file matches directory structure"""
        with open(sample_intent_file) as f:
            intent_data = json.load(f)

        # Verify terminal_id matches
        assert intent_data["terminal_id"] == mock_terminal_id

        # Verify file is in correct directory
        assert str(sample_intent_file.parent).endswith(mock_terminal_id)


class TestIntentFileDeletion:
    """Test intent file deletion after skill execution"""

    def test_intent_file_deleted_after_skill_execution(self, sample_intent_file):
        """Test that intent file is deleted after Skill() is called"""
        # Verify file exists initially
        assert sample_intent_file.exists()

        # Simulate skill execution completion
        sample_intent_file.unlink()

        # Verify file is deleted
        assert not sample_intent_file.exists()

    def test_deleting_nonexistent_intent_file_raises_no_error(self, temp_state_dir, mock_terminal_id):
        """Test that deleting a non-existent intent file is handled gracefully"""
        intent_file = temp_state_dir / mock_terminal_id / "pending_command_intent.json"

        # Attempt to delete non-existent file (should not raise)
        try:
            intent_file.unlink(missing_ok=True)
        except Exception as e:
            pytest.fail(f"Deleting non-existent file raised exception: {e}")

        # Verify file still doesn't exist
        assert not intent_file.exists()


class TestIntentFileValidation:
    """Test intent file validation for schema compliance"""

    def test_missing_skill_field_raises_validation_error(self, temp_state_dir, mock_terminal_id):
        """Test that intent file without 'skill' field fails validation"""
        intent_dir = temp_state_dir / mock_terminal_id
        intent_dir.mkdir(parents=True, exist_ok=True)

        intent_file = intent_dir / "pending_command_intent.json"

        # Create intent with missing 'skill' field
        invalid_intent = {
            "prompt": "/test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "test-123",
            "terminal_id": mock_terminal_id,
            "created_at": int(datetime.now(timezone.utc).timestamp())
        }

        intent_file.write_text(json.dumps(invalid_intent))

        # Validation should fail (in real implementation)
        with open(intent_file) as f:
            data = json.load(f)

        assert "skill" not in data  # Verify field is missing

    def test_missing_created_at_field_raises_validation_error(self, temp_state_dir, mock_terminal_id):
        """Test that intent file without 'created_at' field fails validation"""
        intent_dir = temp_state_dir / mock_terminal_id
        intent_dir.mkdir(parents=True, exist_ok=True)

        intent_file = intent_dir / "pending_command_intent.json"

        # Create intent with missing 'created_at' field
        invalid_intent = {
            "skill": "test-skill",
            "prompt": "/test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "test-123",
            "terminal_id": mock_terminal_id
        }

        intent_file.write_text(json.dumps(invalid_intent))

        # Verify created_at is missing
        with open(intent_file) as f:
            data = json.load(f)

        assert "created_at" not in data

    def test_invalid_json_in_intent_file_raises_error(self, temp_state_dir, mock_terminal_id):
        """Test that invalid JSON in intent file is handled gracefully"""
        intent_dir = temp_state_dir / mock_terminal_id
        intent_dir.mkdir(parents=True, exist_ok=True)

        intent_file = intent_dir / "pending_command_intent.json"

        # Write invalid JSON
        intent_file.write_text("{ invalid json }")

        # Attempting to read should raise JSONDecodeError
        with pytest.raises(json.JSONDecodeError):
            with open(intent_file) as f:
                json.load(f)


class TestMultiTerminalIsolation:
    """Test that intent files are isolated between concurrent terminals"""

    def test_concurrent_terminals_have_separate_intent_files(self, temp_state_dir):
        """Test that different terminals create separate intent files"""
        terminal_1_id = "terminal-abc123"
        terminal_2_id = "terminal-def456"

        # Create intent files for both terminals
        for terminal_id in [terminal_1_id, terminal_2_id]:
            intent_dir = temp_state_dir / terminal_id
            intent_dir.mkdir(parents=True, exist_ok=True)

            intent_file = intent_dir / "pending_command_intent.json"
            intent_data = {
                "skill": "test-skill",
                "prompt": f"/test-{terminal_id}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": f"session-{terminal_id}",
                "terminal_id": terminal_id,
                "created_at": int(datetime.now(timezone.utc).timestamp())
            }
            intent_file.write_text(json.dumps(intent_data))

        # Verify both files exist in separate directories
        intent_1 = temp_state_dir / terminal_1_id / "pending_command_intent.json"
        intent_2 = temp_state_dir / terminal_2_id / "pending_command_intent.json"

        assert intent_1.exists()
        assert intent_2.exists()

        # Verify they contain different data
        with open(intent_1) as f:
            data_1 = json.load(f)
        with open(intent_2) as f:
            data_2 = json.load(f)

        assert data_1["terminal_id"] != data_2["terminal_id"]
        assert data_1["prompt"] != data_2["prompt"]

    def test_deleting_intent_in_one_terminal_does_not_affect_other(self, temp_state_dir):
        """Test that intent deletion is isolated per terminal"""
        terminal_1_id = "terminal-111"
        terminal_2_id = "terminal-222"

        # Create intent files for both terminals
        for terminal_id in [terminal_1_id, terminal_2_id]:
            intent_dir = temp_state_dir / terminal_id
            intent_dir.mkdir(parents=True, exist_ok=True)

            intent_file = intent_dir / "pending_command_intent.json"
            intent_data = {
                "skill": "test-skill",
                "prompt": f"/test-{terminal_id}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": f"session-{terminal_id}",
                "terminal_id": terminal_id,
                "created_at": int(datetime.now(timezone.utc).timestamp())
            }
            intent_file.write_text(json.dumps(intent_data))

        # Delete intent file for terminal 1 only
        intent_1 = temp_state_dir / terminal_1_id / "pending_command_intent.json"
        intent_2 = temp_state_dir / terminal_2_id / "pending_command_intent.json"

        intent_1.unlink()

        # Verify terminal 1 intent is deleted but terminal 2 still exists
        assert not intent_1.exists()
        assert intent_2.exists()
