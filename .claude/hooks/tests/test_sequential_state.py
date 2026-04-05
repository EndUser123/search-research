"""
Tests for sequential thinking state management.

Tests state file CRUD operations with multi-terminal safety.
"""

import uuid
from pathlib import Path
from unittest.mock import patch

# Test constants
TEST_STATE_DIR = Path("P:/").resolve() / ".claude" / "state" / "sequential-thinking"


class TestSequentialState:
    """Test suite for sequential thinking state management."""

    def test_create_state_file_initializes_with_defaults(self, tmp_path):
        """Test that creating a new state file initializes with correct defaults."""
        # Use tmp_path for isolation
        with patch("hooks.__lib.sequential_state.STATE_DIR", tmp_path):
            from hooks.__lib.sequential_state import create_state, load_state

            session_id = uuid.uuid4()
            trigger_phrase = "think step by step"
            terminal_id = "console_abc123"

            # Create state
            state = create_state(session_id, trigger_phrase, terminal_id)

            # Verify defaults
            assert state["session_id"] == str(session_id)
            assert state["trigger_phrase"] == trigger_phrase
            assert state["current_iteration"] == 0
            assert state["max_iterations"] == 2
            assert state["mode"] == "initial"
            assert state["intermediate_answers"] == []
            assert state["final_answer"] is None
            assert state["active"] is True
            assert state["terminal_id"] == terminal_id

            # Verify persistence (must use same terminal_id for isolation)
            loaded = load_state(session_id, terminal_id=terminal_id)
            assert loaded == state

    def test_load_state_returns_none_for_missing_session(self, tmp_path):
        """Test that loading a non-existent session returns None."""
        with patch("hooks.__lib.sequential_state.STATE_DIR", tmp_path):
            from hooks.__lib.sequential_state import load_state

            result = load_state(uuid.uuid4())
            assert result is None

    def test_update_state_increments_iteration(self, tmp_path):
        """Test that updating state increments iteration counter."""
        with patch("hooks.__lib.sequential_state.STATE_DIR", tmp_path):
            from hooks.__lib.sequential_state import create_state, load_state, update_state

            session_id = uuid.uuid4()
            terminal_id = "console_abc123"
            state = create_state(session_id, "think step by step", terminal_id)

            # Update iteration
            update_state(session_id, {"current_iteration": 1, "mode": "critique"}, terminal_id)

            # Verify update persisted
            loaded = load_state(session_id, terminal_id=terminal_id)
            assert loaded["current_iteration"] == 1
            assert loaded["mode"] == "critique"

    def test_delete_state_removes_file(self, tmp_path):
        """Test that deleting state removes the file."""
        with patch("hooks.__lib.sequential_state.STATE_DIR", tmp_path):
            from hooks.__lib.sequential_state import create_state, delete_state, load_state

            session_id = uuid.uuid4()
            create_state(session_id, "think step by step", "console_abc123")

            # Delete state
            delete_state(session_id)

            # Verify file removed
            assert load_state(session_id) is None

    def test_multi_terminal_isolation_with_terminal_id(self, tmp_path):
        """Test that different terminals maintain separate state."""
        with patch("hooks.__lib.sequential_state.STATE_DIR", tmp_path):
            from hooks.__lib.sequential_state import create_state, load_state

            session_id = uuid.uuid4()

            # Create state for terminal A
            state_a = create_state(session_id, "think step by step", "console_A")

            # Load for terminal B should return None (different terminal)
            state_b = load_state(session_id, terminal_id="console_B")
            assert state_b is None

            # Load for terminal A should return the state
            loaded_a = load_state(session_id, terminal_id="console_A")
            assert loaded_a == state_a

    def test_add_intermediate_answer_saves_to_list(self, tmp_path):
        """Test that intermediate answers are appended to the list."""
        with patch("hooks.__lib.sequential_state.STATE_DIR", tmp_path):
            from hooks.__lib.sequential_state import (
                add_intermediate_answer,
                create_state,
                load_state,
            )

            session_id = uuid.uuid4()
            terminal_id = "console_abc123"
            create_state(session_id, "think step by step", terminal_id)

            # Add first answer
            add_intermediate_answer(session_id, "First answer", terminal_id)
            state = load_state(session_id, terminal_id=terminal_id)
            assert state["intermediate_answers"] == ["First answer"]

            # Add second answer
            add_intermediate_answer(session_id, "Second answer", terminal_id)
            state = load_state(session_id, terminal_id=terminal_id)
            assert state["intermediate_answers"] == ["First answer", "Second answer"]

    def test_set_final_answer_and_deactivate(self, tmp_path):
        """Test that setting final answer deactivates the session."""
        with patch("hooks.__lib.sequential_state.STATE_DIR", tmp_path):
            from hooks.__lib.sequential_state import (
                create_state,
                load_state,
                set_final_answer,
            )

            session_id = uuid.uuid4()
            terminal_id = "console_abc123"
            create_state(session_id, "think step by step", terminal_id)

            # Set final answer
            set_final_answer(session_id, "Final improved answer", terminal_id)
            state = load_state(session_id, terminal_id=terminal_id)

            assert state["final_answer"] == "Final improved answer"
            assert state["active"] is False

    def test_should_continue_returns_true_for_active_session(self, tmp_path):
        """Test that should_continue returns True for active sessions below max."""
        with patch("hooks.__lib.sequential_state.STATE_DIR", tmp_path):
            from hooks.__lib.sequential_state import (
                create_state,
                should_continue,
            )

            session_id = uuid.uuid4()
            terminal_id = "console_abc123"
            create_state(session_id, "think step by step", terminal_id)

            # Iteration 0, should continue
            assert should_continue(session_id, terminal_id=terminal_id) is True

            # Increment to 1, should still continue
            from hooks.__lib.sequential_state import update_state

            update_state(session_id, {"current_iteration": 1}, terminal_id)
            assert should_continue(session_id, terminal_id=terminal_id) is True

    def test_should_continue_returns_false_at_max_iterations(self, tmp_path):
        """Test that should_continue returns False at max iterations."""
        with patch("hooks.__lib.sequential_state.STATE_DIR", tmp_path):
            from hooks.__lib.sequential_state import (
                create_state,
                should_continue,
                update_state,
            )

            session_id = uuid.uuid4()
            terminal_id = "console_abc123"
            create_state(session_id, "think step by step", terminal_id)

            # Set to max iterations
            update_state(session_id, {"current_iteration": 2}, terminal_id)

            # Should not continue
            assert should_continue(session_id, terminal_id=terminal_id) is False

    def test_should_continue_returns_false_for_inactive_session(self, tmp_path):
        """Test that should_continue returns False for inactive sessions."""
        with patch("hooks.__lib.sequential_state.STATE_DIR", tmp_path):
            from hooks.__lib.sequential_state import (
                create_state,
                set_final_answer,
                should_continue,
            )

            session_id = uuid.uuid4()
            terminal_id = "console_abc123"
            create_state(session_id, "think step by step", terminal_id)

            # Deactivate session
            set_final_answer(session_id, "Done", terminal_id)

            # Should not continue
            assert should_continue(session_id, terminal_id=terminal_id) is False
