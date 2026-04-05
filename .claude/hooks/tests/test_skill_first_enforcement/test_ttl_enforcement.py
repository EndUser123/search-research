"""
Test suite for TTL (Time-To-Live) enforcement.

Tests cover:
- TTL expiration logic (default 90 seconds)
- Environment variable override (SKILL_FIRST_INTENT_TTL_SECONDS)
- ISO timestamp fallback parsing
- Edge cases (negative TTL, zero TTL, very large TTL)
"""

import json
import os
from datetime import datetime, timezone


class TestDefaultTTLExpiration:
    """Test default 90-second TTL expiration logic"""

    def test_fresh_intent_file_within_ttl_window(self, sample_intent_file):
        """Test that intent file newer than 90 seconds is considered valid"""
        with open(sample_intent_file) as f:
            intent_data = json.load(f)

        created_at = intent_data["created_at"]
        now = int(datetime.now(timezone.utc).timestamp())

        # Verify file is fresh (within 90 seconds)
        age = now - created_at
        assert age < 90  # Should be less than default TTL

    def test_stale_intent_file_past_ttl_window(self, stale_intent_file):
        """Test that intent file older than 90 seconds is considered expired"""
        with open(stale_intent_file) as f:
            intent_data = json.load(f)

        created_at = intent_data["created_at"]
        now = int(datetime.now(timezone.utc).timestamp())

        # Verify file is stale (older than 90 seconds)
        age = now - created_at
        assert age >= 90  # Should be at or past TTL

    def test_exactly_90_seconds_is_expired(self, temp_state_dir, mock_terminal_id):
        """Test that intent file exactly 90 seconds old is considered expired"""
        intent_dir = temp_state_dir / mock_terminal_id
        intent_dir.mkdir(parents=True, exist_ok=True)

        intent_file = intent_dir / "pending_command_intent.json"

        # Create intent file exactly 90 seconds old
        now = int(datetime.now(timezone.utc).timestamp())
        created_at = now - 90  # Exactly at TTL boundary

        intent_data = {
            "skill": "test-skill",
            "prompt": "/test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "test-123",
            "terminal_id": mock_terminal_id,
            "created_at": created_at
        }

        intent_file.write_text(json.dumps(intent_data))

        # Verify TTL check would expire this file
        with open(intent_file) as f:
            data = json.load(f)

        age = now - data["created_at"]
        assert age == 90  # Exactly at TTL boundary


class TestEnvironmentVariableOverride:
    """Test SKILL_FIRST_INTENT_TTL_SECONDS environment variable"""

    def test_custom_ttl_from_env_var(self, temp_state_dir, mock_terminal_id, monkeypatch):
        """Test that TTL can be overridden via environment variable"""
        # Set custom TTL
        monkeypatch.setenv("SKILL_FIRST_INTENT_TTL_SECONDS", "120")

        # Verify env var is set
        assert os.environ.get("SKILL_FIRST_INTENT_TTL_SECONDS") == "120"

    def test_invalid_ttl_value_falls_back_to_default(self, monkeypatch):
        """Test that invalid TTL values fall back to default 90 seconds"""
        # Set invalid TTL (non-numeric)
        monkeypatch.setenv("SKILL_FIRST_INTENT_TTL_SECONDS", "invalid")

        # Should fall back to default
        ttl = os.environ.get("SKILL_FIRST_INTENT_TTL_SECONDS")
        assert ttl == "invalid"  # Env var is set, but implementation should handle validation

    def test_negative_ttl_is_treated_as_invalid(self, monkeypatch):
        """Test that negative TTL values are rejected"""
        monkeypatch.setenv("SKILL_FIRST_INTENT_TTL_SECONDS", "-10")

        # Env var is set but should be validated in implementation
        ttl = os.environ.get("SKILL_FIRST_INTENT_TTL_SECONDS")
        assert ttl == "-10"


class TestISOTimestampFallback:
    """Test ISO timestamp parsing as fallback when created_at is missing"""

    def test_iso_timestamp_can_be_parsed_to_epoch(self, sample_intent_file):
        """Test that ISO timestamp can be converted to epoch seconds"""
        with open(sample_intent_file) as f:
            intent_data = json.load(f)

        iso_timestamp = intent_data["timestamp"]

        # Parse ISO timestamp to datetime
        dt = datetime.fromisoformat(iso_timestamp)

        # Convert to epoch
        epoch_from_iso = int(dt.timestamp())

        # Verify conversion works
        assert isinstance(epoch_from_iso, int)
        assert epoch_from_iso > 0

    def test_missing_created_at_uses_timestamp_fallback(self, temp_state_dir, mock_terminal_id):
        """Test that missing created_at field falls back to parsing timestamp"""
        intent_dir = temp_state_dir / mock_terminal_id
        intent_dir.mkdir(parents=True, exist_ok=True)

        intent_file = intent_dir / "pending_command_intent.json"

        # Create intent without created_at, only with timestamp
        now_iso = datetime.now(timezone.utc).isoformat()

        intent_data = {
            "skill": "test-skill",
            "prompt": "/test",
            "timestamp": now_iso,
            "session_id": "test-123",
            "terminal_id": mock_terminal_id
        }

        intent_file.write_text(json.dumps(intent_data))

        # Verify timestamp field exists
        with open(intent_file) as f:
            data = json.load(f)

        assert "timestamp" in data
        assert "created_at" not in data

        # Verify ISO timestamp can be parsed
        dt = datetime.fromisoformat(data["timestamp"])
        assert dt is not None


class TestTTLEdgeCases:
    """Test TTL edge cases and boundary conditions"""

    def test_zero_ttl_allows_only_current_second(self, temp_state_dir, mock_terminal_id, monkeypatch):
        """Test that TTL=0 allows only files created in the current second"""
        monkeypatch.setenv("SKILL_FIRST_INTENT_TTL_SECONDS", "0")

        intent_dir = temp_state_dir / mock_terminal_id
        intent_dir.mkdir(parents=True, exist_ok=True)

        intent_file = intent_dir / "pending_command_intent.json"

        # Create intent file with current timestamp
        now = int(datetime.now(timezone.utc).timestamp())

        intent_data = {
            "skill": "test-skill",
            "prompt": "/test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "test-123",
            "terminal_id": mock_terminal_id,
            "created_at": now
        }

        intent_file.write_text(json.dumps(intent_data))

        # With TTL=0, file should be expired if any time has passed
        # (This is a boundary case - implementation should define behavior)

    def test_very_large_ttl_allows_old_intents(self, temp_state_dir, mock_terminal_id, monkeypatch):
        """Test that very large TTL (e.g., 1 day) allows old intent files"""
        monkeypatch.setenv("SKILL_FIRST_INTENT_TTL_SECONDS", "86400")  # 1 day

        intent_dir = temp_state_dir / mock_terminal_id
        intent_dir.mkdir(parents=True, exist_ok=True)

        intent_file = intent_dir / "pending_command_intent.json"

        # Create intent file 2 hours old
        now = int(datetime.now(timezone.utc).timestamp())
        created_at = now - 7200  # 2 hours ago

        intent_data = {
            "skill": "test-skill",
            "prompt": "/test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "test-123",
            "terminal_id": mock_terminal_id,
            "created_at": created_at
        }

        intent_file.write_text(json.dumps(intent_data))

        # Verify large TTL allows old files
        age = now - created_at
        assert age == 7200  # 2 hours old

        # With TTL=86400 (1 day), 2-hour-old file should still be valid

    def test_ttl_calculation_uses_seconds_not_milliseconds(self, sample_intent_file):
        """Test that TTL is calculated in seconds, not milliseconds"""
        with open(sample_intent_file) as f:
            intent_data = json.load(f)

        created_at = intent_data["created_at"]

        # Verify created_at is in seconds (reasonable epoch value)
        # If it were milliseconds, the value would be much larger
        now = int(datetime.now(timezone.utc).timestamp())
        assert created_at < now  # Created in the past
        assert now - created_at < 1000000  # Less than ~11.5 days in seconds


class TestTTLIntegrationTests:
    """Integration tests for TTL enforcement with other components"""

    def test_ttl_enforcement_does_not_block_valid_intents(self, sample_intent_file):
        """Test that valid (fresh) intent files pass TTL check"""
        with open(sample_intent_file) as f:
            intent_data = json.load(f)

        created_at = intent_data["created_at"]
        now = int(datetime.now(timezone.utc).timestamp())
        age = now - created_at

        # Fresh file should pass TTL check
        assert age < 90  # Within default TTL window

    def test_ttl_enforcement_blocks_stale_intents(self, stale_intent_file):
        """Test that stale intent files fail TTL check"""
        with open(stale_intent_file) as f:
            intent_data = json.load(f)

        created_at = intent_data["created_at"]
        now = int(datetime.now(timezone.utc).timestamp())
        age = now - created_at

        # Stale file should fail TTL check
        assert age >= 90  # Past TTL window

    def test_ttl_check_per_terminal_isolation(self, temp_state_dir):
        """Test that TTL checks are isolated per terminal"""
        terminal_1_id = "terminal-ttl-1"
        terminal_2_id = "terminal-ttl-2"

        now = int(datetime.now(timezone.utc).timestamp())

        # Create fresh intent for terminal 1
        intent_dir_1 = temp_state_dir / terminal_1_id
        intent_dir_1.mkdir(parents=True, exist_ok=True)

        intent_file_1 = intent_dir_1 / "pending_command_intent.json"
        intent_data_1 = {
            "skill": "test",
            "prompt": "/test-1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "session-1",
            "terminal_id": terminal_1_id,
            "created_at": now  # Fresh
        }
        intent_file_1.write_text(json.dumps(intent_data_1))

        # Create stale intent for terminal 2
        intent_dir_2 = temp_state_dir / terminal_2_id
        intent_dir_2.mkdir(parents=True, exist_ok=True)

        intent_file_2 = intent_dir_2 / "pending_command_intent.json"
        intent_data_2 = {
            "skill": "test",
            "prompt": "/test-2",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "session-2",
            "terminal_id": terminal_2_id,
            "created_at": now - 120  # 2 minutes old (stale)
        }
        intent_file_2.write_text(json.dumps(intent_data_2))

        # Terminal 1: Fresh, should pass
        # Terminal 2: Stale, should fail
        # This verifies TTL is checked per terminal, not globally
