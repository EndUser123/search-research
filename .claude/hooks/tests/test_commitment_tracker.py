#!/usr/bin/env python3
"""
Tests for commitment_tracker.py - Proactive commitment tracking via session boundary hooks.

Test coverage:
- TrackedCommitment dataclass
- CommitmentTracker initialization
- scan_transcript - detecting commitments from user messages
- check_completion - checking completion status
- save_state / load_state - atomic writes with FileLock
- save_checkpoint / load_checkpoint
- Terminal ID validation

All tests use synthetic payloads (no mocks) per testing patterns.
"""

import sys
import tempfile
from pathlib import Path

# Ensure commitment_tracker is importable
_HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HOOKS_DIR))

from __lib.commitment_tracker import CommitmentTracker, TrackedCommitment


class TestTrackedCommitmentDataclass:
    """Tests for TrackedCommitment dataclass."""

    def test_create_commitment(self):
        """Can create a TrackedCommitment with required fields."""
        c = TrackedCommitment(
            content="Fix the authentication bug",
            turn_number=1,
            category="user_goal",
        )
        assert c.content == "Fix the authentication bug"
        assert c.turn_number == 1
        assert c.category == "user_goal"
        assert c.completed is False
        assert c.completion_turn is None
        assert c.session_id == ""

    def test_create_with_all_fields(self):
        """Can create a TrackedCommitment with all fields."""
        c = TrackedCommitment(
            content="Add unit tests",
            turn_number=5,
            category="agent_promise",
            completed=True,
            completion_turn=10,
            session_id="sess_abc123",
        )
        assert c.completed is True
        assert c.completion_turn == 10
        assert c.session_id == "sess_abc123"


class TestCommitmentTrackerInit:
    """Tests for CommitmentTracker initialization."""

    def test_default_home_directory(self):
        """Tracker uses Path.home() / '.claude' when no claude_home provided."""
        tracker = CommitmentTracker()
        expected_home = Path.home() / ".claude"
        assert tracker._home == expected_home

    def test_custom_home_directory(self):
        """Tracker uses provided claude_home when given."""
        custom_path = Path("/custom/path")
        tracker = CommitmentTracker(claude_home=custom_path)
        assert tracker._home == custom_path

    def test_evidence_dir_property(self):
        """Tracker has .evidence directory under home."""
        tracker = CommitmentTracker()
        assert tracker._evidence_dir == tracker._home / ".evidence"

    def test_checkpoint_dir_property(self):
        """Tracker has .checkpoints directory under home."""
        tracker = CommitmentTracker()
        assert tracker._checkpoint_dir == tracker._home / ".checkpoints"


class TestTerminalIdValidation:
    """Tests for terminal ID validation."""

    def test_valid_terminal_ids(self):
        """Valid terminal IDs pass validation."""
        valid_ids = ["console_abc123", "env_xyz", "terminal-1", "TERMINAL_2", "a1b2c3"]
        for tid in valid_ids:
            result = CommitmentTracker._validate_terminal_id(tid)
            assert result == tid, f"Expected {tid} to be valid"

    def test_invalid_terminal_ids_rejected(self):
        """Invalid terminal IDs raise ValueError."""
        invalid_ids = [
            "terminal/abc",
            "terminal\\xyz",
            "terminal.abc",
            "terminal:abc",
            "terminal abc",
        ]
        for tid in invalid_ids:
            try:
                CommitmentTracker._validate_terminal_id(tid)
                assert False, f"Expected {tid} to raise ValueError"
            except ValueError as e:
                assert "Invalid terminal_id" in str(e)


class TestScanTranscript:
    """Tests for scanning transcript for commitments."""

    def _make_transcript(self, *messages):
        """Helper to create transcript entries with role and content."""
        return [{"role": role, "content": content} for role, content in messages]

    def test_detects_user_intent_patterns(self):
        """Detects 'I want to' style commitments in user messages."""
        tracker = CommitmentTracker()
        transcript = self._make_transcript(
            ("user", "I want to fix the login bug"),
            ("assistant", "I'll help you fix that."),
        )
        commitments = tracker.scan_transcript(transcript, session_id="sess_1")
        assert len(commitments) == 1
        assert commitments[0].content == "fix the login bug"
        assert commitments[0].category == "user_goal"
        assert commitments[0].turn_number == 1

    def test_detects_multiple_commitments(self):
        """Detects multiple commitments across multiple user messages.

        Note: We avoid phrases with completion-signal words like 'add', 'fix', 'done'.
        We also use 'I want to' twice since the fallback patterns require exact phrases.
        """
        tracker = CommitmentTracker()
        transcript = self._make_transcript(
            ("user", "I want to fix the login bug"),
            ("assistant", "OK"),
            ("user", "I want to write unit tests for the auth module"),
            ("assistant", "Sure"),
        )
        commitments = tracker.scan_transcript(transcript, session_id="sess_1")
        assert len(commitments) == 2
        assert commitments[0].content == "fix the login bug"
        assert commitments[1].content == "write unit tests for the auth module"

    def test_ignores_assistant_messages(self):
        """Only scans user messages, not assistant."""
        tracker = CommitmentTracker()
        transcript = self._make_transcript(
            ("assistant", "I want to fix the login bug"),  # Wrong role
            ("user", "I want to add unit tests"),
        )
        commitments = tracker.scan_transcript(transcript, session_id="sess_1")
        assert len(commitments) == 1
        assert commitments[0].content == "add unit tests"

    def test_skips_completed_items(self):
        """Skips messages that contain completion signals."""
        tracker = CommitmentTracker()
        transcript = self._make_transcript(
            ("user", "I want to fix the login bug"),  # Commitment
            ("user", "Done, I finished fixing it"),  # Completion signal
        )
        commitments = tracker.scan_transcript(transcript, session_id="sess_1")
        # Should skip "Done, I finished fixing it" because it has completion signals
        assert len(commitments) == 1

    def test_minimum_content_length(self):
        """Requires at least 10 characters of task content."""
        tracker = CommitmentTracker()
        transcript = self._make_transcript(
            ("user", "I want to x"),  # Too short
            ("user", "I want to fix this bug now please"),  # Long enough
        )
        commitments = tracker.scan_transcript(transcript, session_id="sess_1")
        assert len(commitments) == 1
        assert "fix this bug now please" in commitments[0].content

    def test_session_id_attached(self):
        """Attaches session_id to tracked commitments."""
        tracker = CommitmentTracker()
        transcript = self._make_transcript(
            ("user", "I want to fix the login bug"),
        )
        commitments = tracker.scan_transcript(transcript, session_id="sess_xyz")
        assert commitments[0].session_id == "sess_xyz"


class TestCheckCompletion:
    """Tests for checking commitment completion."""

    def _make_transcript(self, *messages):
        """Helper to create transcript entries with role and content."""
        return [{"role": role, "content": content} for role, content in messages]

    def test_completion_detected(self):
        """Detects when commitment content appears near completion signal."""
        tracker = CommitmentTracker()
        commitment = TrackedCommitment(
            content="fix the login bug",
            turn_number=1,
            category="user_goal",
        )
        transcript = self._make_transcript(
            ("user", "I want to fix the login bug"),
            ("assistant", "I'll start working on this."),
            ("user", "Done - I fixed the login bug now"),
        )
        updated = tracker.check_completion(commitment, transcript)
        assert updated.completed is True
        assert updated.completion_turn == 3

    def test_completion_not_detected_without_signal(self):
        """Does not mark complete if no completion signal present."""
        tracker = CommitmentTracker()
        commitment = TrackedCommitment(
            content="fix the login bug",
            turn_number=1,
            category="user_goal",
        )
        transcript = self._make_transcript(
            ("user", "I want to fix the login bug"),
            ("assistant", "I'll start working on this."),
            ("user", "I'm still working on it"),
        )
        updated = tracker.check_completion(commitment, transcript)
        assert updated.completed is False
        assert updated.completion_turn is None

    def test_completion_not_before_commitment_turn(self):
        """Does not check turns before commitment was stated."""
        tracker = CommitmentTracker()
        commitment = TrackedCommitment(
            content="fix the login bug",
            turn_number=3,  # Stated at turn 3
            category="user_goal",
        )
        transcript = self._make_transcript(
            ("user", "Hello"),
            ("user", "I want to fix the login bug"),  # turn 2
            ("user", "Done - I fixed the login bug"),  # turn 3
        )
        updated = tracker.check_completion(commitment, transcript)
        # Completion signal is at turn 3, but commitment was stated at turn 3
        # So check starts at turn 4, finding nothing
        assert updated.completed is False


class TestStatePersistence:
    """Tests for save_state and load_state with atomic writes."""

    def _tracker_with_temp_home(self):
        """Create tracker with temporary home directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            tracker = CommitmentTracker(claude_home=tmp_path)
            yield tracker, tmp_path

    def test_save_and_load_state(self):
        """Can save commitments and load them back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            tracker = CommitmentTracker(claude_home=tmp_path)

            commitments = [
                TrackedCommitment(
                    content="fix the login bug",
                    turn_number=1,
                    category="user_goal",
                ),
                TrackedCommitment(
                    content="add unit tests",
                    turn_number=3,
                    category="agent_promise",
                ),
            ]

            tracker.save_state(commitments, "console_test")
            loaded = tracker.load_state("console_test")

            assert len(loaded) == 2
            assert loaded[0].content == "fix the login bug"
            assert loaded[1].content == "add unit tests"

    def test_load_state_missing_file(self):
        """Load returns empty list when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            tracker = CommitmentTracker(claude_home=tmp_path)
            loaded = tracker.load_state("nonexistent_terminal")
            assert loaded == []

    def test_save_state_creates_directory(self):
        """Save creates .evidence directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            tracker = CommitmentTracker(claude_home=tmp_path)

            commitments = [
                TrackedCommitment(
                    content="test",
                    turn_number=1,
                    category="user_goal",
                ),
            ]

            # Directory shouldn't exist yet
            evidence_dir = tracker._evidence_dir
            assert not evidence_dir.exists()

            tracker.save_state(commitments, "console_test")

            # Now it should exist
            assert evidence_dir.exists()


class TestCheckpointPersistence:
    """Tests for save_checkpoint and load_checkpoint."""

    def test_save_and_load_checkpoint(self):
        """Can save checkpoint and load it back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            tracker = CommitmentTracker(claude_home=tmp_path)

            commitments = [
                TrackedCommitment(
                    content="unfinished task",
                    turn_number=1,
                    category="user_goal",
                ),
            ]

            tracker.save_checkpoint(commitments, "console_test")
            loaded = tracker.load_checkpoint("console_test")

            assert len(loaded) == 1
            assert loaded[0].content == "unfinished task"

    def test_load_checkpoint_missing_file(self):
        """Load checkpoint returns empty list when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            tracker = CommitmentTracker(claude_home=tmp_path)
            loaded = tracker.load_checkpoint("nonexistent")
            assert loaded == []


class TestPathConstruction:
    """Tests for path construction methods."""

    def test_state_path_format(self):
        """State path uses correct format: .evidence/gto-commitments-{terminal_id}.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            tracker = CommitmentTracker(claude_home=tmp_path)
            state_path = tracker._get_state_path("console_abc123")
            assert state_path == tmp_path / ".evidence" / "gto-commitments-console_abc123.json"

    def test_checkpoint_path_format(self):
        """Checkpoint path uses correct format: .checkpoints/gto-commitments-{terminal_id}.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            tracker = CommitmentTracker(claude_home=tmp_path)
            checkpoint_path = tracker._get_checkpoint_path("console_abc123")
            assert (
                checkpoint_path == tmp_path / ".checkpoints" / "gto-commitments-console_abc123.json"
            )

    def test_checkpoints_dir_property_creates_directory(self):
        """_checkpoints_dir property creates directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            tracker = CommitmentTracker(claude_home=tmp_path)
            ckpt_dir = tracker._checkpoints_dir
            assert ckpt_dir.exists()
            assert ckpt_dir == tmp_path / ".checkpoints"


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
