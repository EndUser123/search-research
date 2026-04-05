"""Tests for Verification Tracker - terminal ID isolation.

These tests verify that terminal IDs are properly hashed to prevent collisions
when generating state file paths. The current implementation uses truncation
(terminal_id[:12]) which can cause different terminal IDs to map to the same
state file.

Run with:
    pytest P:/.claude/hooks/tests/test_verification_tracker_isolation.py -v

Expected: FAILS with current implementation (uses truncation, can collide)
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import VerificationTracker for module-level access in tests
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "posttooluse"))


# ============================================================================
# SHARED FIXTURES
# ============================================================================

@pytest.fixture
def collision_prone_ids():
    """Generate terminal IDs designed to cause collisions with truncation.

    These IDs all share the same first 12 characters, so truncating to 12
    will cause all of them to map to the same state file.

    Returns:
        list[str]: List of terminal IDs that collide with [:12] truncation.
    """
    return [
        "terminal_ab_001",  # First 12: terminal_ab_
        "terminal_ab_002",  # First 12: terminal_ab_  <- COLLISION!
        "terminal_ab_003",  # First 12: terminal_ab_  <- COLLISION!
        "terminal_ab_004",  # First 12: terminal_ab_  <- COLLISION!
        "terminal_ab_005",  # First 12: terminal_ab_  <- COLLISION!
        "terminal_ab_006",  # First 12: terminal_ab_  <- COLLISION!
        "terminal_ab_007",  # First 12: terminal_ab_  <- COLLISION!
        "terminal_ab_008",  # First 12: terminal_ab_  <- COLLISION!
        "terminal_ab_009",  # First 12: terminal_ab_  <- COLLISION!
        "terminal_ab_010",  # First 12: terminal_ab_  <- COLLISION!
    ]


# ============================================================================
# TEST CLASSES
# ============================================================================

class TestTerminalIdIsolation:
    """Tests for terminal ID isolation in state file paths."""

    def test_collision_prone_ids_have_unique_state_files(
        self, collision_prone_ids: list[str]
    ) -> None:
        """Verify that collision-prone IDs still produce unique state files.

        Given: 10 terminal IDs with same first 12 characters
        When: _get_state_file() is called for each ID
        Then: All 10 state file paths are unique

        This test FAILS with current implementation because all these IDs
        truncate to the same 12-character prefix ("terminal_ab_"),
        causing them all to map to "verification_state_terminal_ab_.json".

        After fix (using full hash), each ID will produce a unique state file.
        """
        import verification_tracker

        state_files = []

        for terminal_id in collision_prone_ids:
            # Mock the terminal_detection module's detect_terminal_id function
            # This simulates what happens when terminal_detection returns different IDs
            # that happen to share the same first 12 characters
            mock_module = MagicMock()
            mock_module.detect_terminal_id.return_value = terminal_id

            with patch("importlib.util.spec_from_file_location") as mock_spec:
                with patch("importlib.util.module_from_spec") as mock_module_from_spec:
                    # Set up the mock chain for terminal detection
                    spec = MagicMock()
                    spec.loader = MagicMock()
                    mock_spec.return_value = spec
                    mock_module_from_spec.return_value = mock_module

                    state_file = verification_tracker._get_state_file()
                    state_files.append(state_file)

        # Assert all state files are unique
        unique_state_files = set(state_files)

        assert len(unique_state_files) == len(state_files), (
            f"Expected {len(state_files)} unique state files for collision-prone IDs, "
            f"but got {len(unique_state_files)} unique files. "
            f"This confirms the truncation collision bug. "
            f"State files: {[str(sf) for sf in state_files]}"
        )

    def test_truncation_causes_collision(self) -> None:
        """Directly demonstrate that truncation causes collisions.

        Given: Two different terminal IDs with same first 12 chars
        When: Both are truncated to 12 characters
        Then: They produce the same truncated value (collision)

        This test documents the current bug behavior.
        """
        id1 = "terminal_ab_session_001"
        id2 = "terminal_ab_session_002"

        # Current implementation truncates to 12 chars
        truncated1 = id1[:12]
        truncated2 = id2[:12]

        # This assertion PASSES (demonstrating the bug)
        assert truncated1 == truncated2, (
            f"Truncation causes collision: '{id1}'[:12] == '{id2}'[:12] == '{truncated1}'"
        )

        # This is the problem: different IDs map to same state file
        # First 12 chars of "terminal_ab_session_001" is "terminal_ab_"
        assert truncated1 == "terminal_ab_", f"Expected 'terminal_ab_', got '{truncated1}'"
