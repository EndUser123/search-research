#!/usr/bin/env python3
"""
Tests for VerifyStateManager - multi-terminal state isolation.

Tests verify that:
1. Each terminal gets its own state directory
2. Session validation prevents cross-terminal interference
3. Concurrent terminals don't share state
"""

import json
import os
import shutil

# Add parent directory to path for imports
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.state_manager import VerifyStateManager


class TestVerifyStateManager:
    """Test suite for VerifyStateManager multi-terminal isolation."""

    def setup_method(self):
        """Create temporary directory for test state."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        # Actually change to temp directory for proper isolation
        os.chdir(self.test_dir)

    def teardown_method(self):
        """Clean up temporary directory."""
        # Restore original working directory
        os.chdir(self.original_cwd)
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)

    def test_terminal_id_based_state_directory(self):
        """Test that each terminal gets its own state directory."""
        # Create state manager for terminal A
        sm_a = VerifyStateManager(terminal_id="term_a", session_id="session_1")

        # Create state manager for terminal B
        sm_b = VerifyStateManager(terminal_id="term_b", session_id="session_1")

        # Verify different state directories
        assert sm_a.state_dir != sm_b.state_dir
        assert "term_a" in str(sm_a.state_dir)
        assert "term_b" in str(sm_b.state_dir)

    def test_session_validation_passes(self):
        """Test that session validation passes for matching session IDs."""
        # Create state manager with session_id
        sm = VerifyStateManager(terminal_id="term_1", session_id="session_123")

        # Validate same session - should pass
        assert sm.validate_session("session_123") is True

    def test_session_validation_fails_on_mismatch(self):
        """Test that session validation fails for mismatched session IDs."""
        # Create state manager with session_id
        sm = VerifyStateManager(terminal_id="term_1", session_id="session_123")

        # Try to validate different session - should fail
        assert sm.validate_session("session_456") is False

    def test_session_reset_on_new_session(self):
        """Test that session resets when new session is detected."""
        # Create state manager with session_1
        sm = VerifyStateManager(terminal_id="term_1", session_id="session_1")

        # Save some state
        sm.save_verification_state("verification_1", {"status": "pass"})

        # Verify state exists
        assert sm.get_verification_state("verification_1") is not None

        # Now create new state manager with different session (simulates new session)
        sm_new = VerifyStateManager(terminal_id="term_1", session_id="session_2")

        # Old state should be archived, new state should be empty
        # (The session file should be reset, but verifications file might still exist)
        session_state = sm_new._read_session_state()
        assert session_state.get("session_id") == "session_2"

    def test_verification_state_isolated_per_terminal(self):
        """Test that verification state is isolated per terminal."""
        # Create state manager for terminal A
        sm_a = VerifyStateManager(terminal_id="term_a", session_id="session_1")

        # Create state manager for terminal B
        sm_b = VerifyStateManager(terminal_id="term_b", session_id="session_1")

        # Save state in terminal A
        sm_a.save_verification_state(
            "verification_1", {"target": "skill:arch", "overall_status": "verified"}
        )

        # Verify state exists in terminal A
        state_a = sm_a.get_verification_state("verification_1")
        assert state_a is not None
        assert state_a["overall_status"] == "verified"

        # Verify state does NOT exist in terminal B
        state_b = sm_b.get_verification_state("verification_1")
        assert state_b is None

    def test_evidence_ledger_path_isolated_per_terminal(self):
        """Test that evidence ledger path is isolated per terminal."""
        # Create state managers for two terminals
        sm_a = VerifyStateManager(terminal_id="term_a", session_id="session_1")
        sm_b = VerifyStateManager(terminal_id="term_b", session_id="session_1")

        # Get evidence ledger paths
        ledger_path_a = sm_a.get_evidence_ledger_path()
        ledger_path_b = sm_b.get_evidence_ledger_path()

        # Verify different paths
        assert ledger_path_a != ledger_path_b
        assert "term_a" in str(ledger_path_a)
        assert "term_b" in str(ledger_path_b)

    def test_get_stats_returns_correct_metadata(self):
        """Test that get_stats returns correct terminal metadata."""
        sm = VerifyStateManager(terminal_id="test_term", session_id="test_session")

        stats = sm.get_stats()

        assert stats["terminal_id"] == "test_term"
        assert stats["session_id"] == "test_session"
        assert "state_dir" in stats
        assert stats["verifications_count"] == 0
        assert "session_created_at" in stats

    def test_cleanup_old_states(self):
        """Test that cleanup_old_states keeps only recent verifications."""
        sm = VerifyStateManager(terminal_id="term_cleanup", session_id="session_1")

        # Save 15 verifications
        for i in range(15):
            sm.save_verification_state(f"verification_{i}", {"status": "pass"})

        # Verify all 15 exist
        for i in range(15):
            assert sm.get_verification_state(f"verification_{i}") is not None

        # Cleanup keeping only 10
        sm.cleanup_old_states(keep_count=10)

        # Load and verify only 10 remain (the most recent)
        verifications = json.loads(sm.verifications_file.read_text())
        assert len(verifications) == 10

    def test_auto_generate_terminal_id_when_not_provided(self):
        """Test that terminal_id is auto-generated when not provided."""
        sm = VerifyStateManager()

        # Should have generated a terminal_id
        assert sm.terminal_id is not None
        assert len(sm.terminal_id) > 0

    def test_session_id_defaults_to_environment_variable(self):
        """Test that session_id defaults to CLAUDE_SESSION_ID env var."""
        with patch.dict("os.environ", {"CLAUDE_SESSION_ID": "env_session_123"}):
            sm = VerifyStateManager(terminal_id="term_1")

            # Should have used environment variable
            assert sm.session_id == "env_session_123"

    def test_verification_count_increments_with_saves(self):
        """Test that verification count increments with each save."""
        sm = VerifyStateManager(terminal_id="term_counter", session_id="session_1")

        # Initial count should be 0
        stats = sm.get_stats()
        assert stats["verifications_count"] == 0

        # Save 3 verifications
        sm.save_verification_state("v1", {"status": "pass"})
        sm.save_verification_state("v2", {"status": "pass"})
        sm.save_verification_state("v3", {"status": "pass"})

        # Count should be 3
        stats = sm.get_stats()
        assert stats["verifications_count"] == 3
