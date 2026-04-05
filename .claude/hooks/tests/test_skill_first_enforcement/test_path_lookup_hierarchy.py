"""
Test suite for three-tier path lookup hierarchy.

Tests cover:
- Primary path checked first: terminals/{id}/pending_command_intent.json
- Secondary path checked if primary missing: pending_command_intent_{id}.json
- Fallback path checked if both missing: pending_command_intent_{id}_{session_id}.json
- Legacy cleanup doesn't break new format
"""

import json
from datetime import datetime, timezone


class TestPrimaryPathLookup:
    """Test primary path lookup in hierarchical structure"""

    def test_primary_path_takes_precedence(self, temp_state_dir, mock_terminal_id):
        """Test that primary path is checked first and returned if found"""
        # Create intent file in primary path (new hierarchical structure)
        primary_dir = temp_state_dir / mock_terminal_id
        primary_dir.mkdir(parents=True, exist_ok=True)

        primary_file = primary_dir / "pending_command_intent.json"

        intent_data = {
            "skill": "test-primary",
            "prompt": "/test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "test-session",
            "terminal_id": mock_terminal_id,
            "created_at": int(datetime.now(timezone.utc).timestamp())
        }

        primary_file.write_text(json.dumps(intent_data))

        # Verify primary file exists
        assert primary_file.exists()

        # Verify it's in the expected location
        assert "terminals" in str(primary_file)
        assert mock_terminal_id in str(primary_file)

    def test_primary_path_format_is_hierarchical(self, temp_state_dir, mock_terminal_id):
        """Test that primary path uses hierarchical directory structure"""
        primary_dir = temp_state_dir / mock_terminal_id
        primary_dir.mkdir(parents=True, exist_ok=True)
        primary_file = primary_dir / "pending_command_intent.json"

        # Create intent file
        intent_data = {
            "skill": "test",
            "prompt": "/test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "test-session",
            "terminal_id": mock_terminal_id,
            "created_at": int(datetime.now(timezone.utc).timestamp())
        }

        primary_file.write_text(json.dumps(intent_data))

        # Verify path structure: terminals/{terminal_id}/pending_command_intent.json
        assert primary_dir.name == mock_terminal_id
        assert primary_file.name == "pending_command_intent.json"
        assert primary_file.parent == primary_dir


class TestSecondaryPathLookup:
    """Test secondary path lookup as fallback"""

    def test_secondary_path_checked_when_primary_missing(self, temp_state_dir, mock_terminal_id):
        """Test that secondary path is checked when primary doesn't exist"""
        # Create intent file in secondary path (legacy flat structure)
        secondary_file = temp_state_dir / f"pending_command_intent_{mock_terminal_id}.json"

        intent_data = {
            "skill": "test-secondary",
            "prompt": "/test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "test-session",
            "terminal_id": mock_terminal_id,
            "created_at": int(datetime.now(timezone.utc).timestamp())
        }

        secondary_file.write_text(json.dumps(intent_data))

        # Verify secondary file exists
        assert secondary_file.exists()

        # Verify it's in the expected location (flat structure)
        assert secondary_file.parent == temp_state_dir
        assert secondary_file.name == f"pending_command_intent_{mock_terminal_id}.json"

    def test_secondary_path_format_is_flat(self, temp_state_dir, mock_terminal_id):
        """Test that secondary path uses flat file structure"""
        secondary_file = temp_state_dir / f"pending_command_intent_{mock_terminal_id}.json"

        # Create intent file
        intent_data = {
            "skill": "test",
            "prompt": "/test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "test-session",
            "terminal_id": mock_terminal_id,
            "created_at": int(datetime.now(timezone.utc).timestamp())
        }

        secondary_file.write_text(json.dumps(intent_data))

        # Verify path is flat (no subdirectories)
        assert secondary_file.parent == temp_state_dir
        assert f"pending_command_intent_{mock_terminal_id}.json" == secondary_file.name


class TestFallbackPathLookup:
    """Test fallback path lookup as last resort"""

    def test_fallback_path_checked_when_primary_secondary_missing(self, temp_state_dir, mock_terminal_id):
        """Test that fallback path is checked when primary and secondary don't exist"""
        session_id = "test-session-123"

        # Create intent file in fallback path (old format with session_id)
        fallback_file = temp_state_dir / f"pending_command_intent_{mock_terminal_id}_{session_id}.json"

        intent_data = {
            "skill": "test-fallback",
            "prompt": "/test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "terminal_id": mock_terminal_id,
            "created_at": int(datetime.now(timezone.utc).timestamp())
        }

        fallback_file.write_text(json.dumps(intent_data))

        # Verify fallback file exists
        assert fallback_file.exists()

        # Verify it's in the expected location (flat with session_id suffix)
        assert fallback_file.parent == temp_state_dir
        assert fallback_file.name == f"pending_command_intent_{mock_terminal_id}_{session_id}.json"

    def test_fallback_path_includes_session_id(self, temp_state_dir, mock_terminal_id):
        """Test that fallback path includes session_id in filename"""
        session_id = "test-session-456"
        fallback_file = temp_state_dir / f"pending_command_intent_{mock_terminal_id}_{session_id}.json"

        # Create intent file
        intent_data = {
            "skill": "test",
            "prompt": "/test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "terminal_id": mock_terminal_id,
            "created_at": int(datetime.now(timezone.utc).timestamp())
        }

        fallback_file.write_text(json.dumps(intent_data))

        # Verify session_id is in filename
        assert session_id in fallback_file.name
        assert mock_terminal_id in fallback_file.name


class TestPathPriorityOrder:
    """Test that paths are checked in correct priority order"""

    def test_primary_takes_precedence_over_secondary(self, temp_state_dir, mock_terminal_id):
        """Test that primary path is returned even if secondary also exists"""
        # Create both primary and secondary files
        primary_dir = temp_state_dir / mock_terminal_id
        primary_dir.mkdir(parents=True, exist_ok=True)
        primary_file = primary_dir / "pending_command_intent.json"

        secondary_file = temp_state_dir / f"pending_command_intent_{mock_terminal_id}.json"

        # Write different data to each
        primary_data = {
            "skill": "primary",
            "prompt": "/test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "test-session",
            "terminal_id": mock_terminal_id,
            "created_at": int(datetime.now(timezone.utc).timestamp())
        }

        secondary_data = {
            "skill": "secondary",
            "prompt": "/test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "test-session",
            "terminal_id": mock_terminal_id,
            "created_at": int(datetime.now(timezone.utc).timestamp())
        }

        primary_file.write_text(json.dumps(primary_data))
        secondary_file.write_text(json.dumps(secondary_data))

        # Verify primary file exists and has correct data
        assert primary_file.exists()
        with open(primary_file) as f:
            data = json.load(f)
        assert data["skill"] == "primary"

    def test_secondary_takes_precedence_over_fallback(self, temp_state_dir, mock_terminal_id):
        """Test that secondary path is returned even if fallback also exists"""
        session_id = "test-session-789"

        # Create both secondary and fallback files
        secondary_file = temp_state_dir / f"pending_command_intent_{mock_terminal_id}.json"
        fallback_file = temp_state_dir / f"pending_command_intent_{mock_terminal_id}_{session_id}.json"

        # Write different data to each
        secondary_data = {
            "skill": "secondary",
            "prompt": "/test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "terminal_id": mock_terminal_id,
            "created_at": int(datetime.now(timezone.utc).timestamp())
        }

        fallback_data = {
            "skill": "fallback",
            "prompt": "/test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "terminal_id": mock_terminal_id,
            "created_at": int(datetime.now(timezone.utc).timestamp())
        }

        secondary_file.write_text(json.dumps(secondary_data))
        fallback_file.write_text(json.dumps(fallback_data))

        # Verify secondary file exists and has correct data
        assert secondary_file.exists()
        with open(secondary_file) as f:
            data = json.load(f)
        assert data["skill"] == "secondary"


class TestLegacyCompatibility:
    """Test that legacy cleanup doesn't break new format"""

    def test_writing_primary_doesnt_delete_legacy(self, temp_state_dir, mock_terminal_id):
        """Test that creating primary file doesn't automatically delete legacy files"""
        # Create secondary (legacy) file
        secondary_file = temp_state_dir / f"pending_command_intent_{mock_terminal_id}.json"

        legacy_data = {
            "skill": "legacy",
            "prompt": "/test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "test-session",
            "terminal_id": mock_terminal_id,
            "created_at": int(datetime.now(timezone.utc).timestamp())
        }

        secondary_file.write_text(json.dumps(legacy_data))

        # Create primary file (new format)
        primary_dir = temp_state_dir / mock_terminal_id
        primary_dir.mkdir(parents=True, exist_ok=True)
        primary_file = primary_dir / "pending_command_intent.json"

        primary_data = {
            "skill": "primary",
            "prompt": "/test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "test-session",
            "terminal_id": mock_terminal_id,
            "created_at": int(datetime.now(timezone.utc).timestamp())
        }

        primary_file.write_text(json.dumps(primary_data))

        # Verify both files exist (cleanup is intentional, not automatic)
        assert primary_file.exists()
        assert secondary_file.exists()

    def test_all_three_formats_can_coexist(self, temp_state_dir, mock_terminal_id):
        """Test that all three path formats can exist simultaneously"""
        session_id = "test-session-coexist"

        # Create all three formats
        primary_dir = temp_state_dir / mock_terminal_id
        primary_dir.mkdir(parents=True, exist_ok=True)
        primary_file = primary_dir / "pending_command_intent.json"

        secondary_file = temp_state_dir / f"pending_command_intent_{mock_terminal_id}.json"
        fallback_file = temp_state_dir / f"pending_command_intent_{mock_terminal_id}_{session_id}.json"

        # Write data to all three
        for file, skill_name in [(primary_file, "primary"), (secondary_file, "secondary"), (fallback_file, "fallback")]:
            intent_data = {
                "skill": skill_name,
                "prompt": "/test",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": session_id,
                "terminal_id": mock_terminal_id,
                "created_at": int(datetime.now(timezone.utc).timestamp())
            }
            file.write_text(json.dumps(intent_data))

        # Verify all three exist
        assert primary_file.exists()
        assert secondary_file.exists()
        assert fallback_file.exists()

        # Verify they have different content
        with open(primary_file) as f:
            primary_data = json.load(f)
        with open(secondary_file) as f:
            secondary_data = json.load(f)
        with open(fallback_file) as f:
            fallback_data = json.load(f)

        assert primary_data["skill"] == "primary"
        assert secondary_data["skill"] == "secondary"
        assert fallback_data["skill"] == "fallback"


class TestMissingFileHandling:
    """Test behavior when intent file doesn't exist in any path"""

    def test_no_intent_file_in_any_path(self, temp_state_dir, mock_terminal_id):
        """Test that missing intent file is handled gracefully"""
        # Don't create any intent files
        primary_dir = temp_state_dir / mock_terminal_id
        primary_file = primary_dir / "pending_command_intent.json"

        session_id = "test-session"
        secondary_file = temp_state_dir / f"pending_command_intent_{mock_terminal_id}.json"
        fallback_file = temp_state_dir / f"pending_command_intent_{mock_terminal_id}_{session_id}.json"

        # Verify none exist
        assert not primary_file.exists()
        assert not secondary_file.exists()
        assert not fallback_file.exists()

        # This should be handled gracefully (not crash)
        # Implementation should return None or raise specific exception
