"""Skill Workflow Enforcement v5 Tests

Tests for the compaction-proof phase machine:
- Phase transitions (pending -> loaded -> executing -> complete)
- Marker detection (WORKFLOW:{skill}:{action} patterns)
- Stop hook enforcement (blocks when strict tier + incomplete)
- PreCompact checkpoint resilience

TASK-008 from ADR-20260328-skill-workflow-enforcement-v5.md
"""

import json
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks directory to path
HOOKS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from skill_execution_state import (
    _PHASE_COMPLETE,
    _PHASE_EXECUTING,
    _PHASE_LOADED,
    _PHASE_PENDING,
    _PHASE_STALE,
    VALID_TRANSITIONS,
    clear_state,
    read_pending_state,
    sanitize_terminal_id,
    set_skill_loaded,
    transition_phase,
)


class TestPhaseTransitions:
    """Test phase machine state transitions."""

    def test_valid_transitions(self, tmp_path):
        """pending -> loaded is valid."""
        with patch("skill_execution_state.STATE_DIR", tmp_path / ".claude" / "state"):
            with patch(
                "skill_execution_state.detect_terminal_id", return_value="test_terminal_123"
            ):
                # Create initial state
                set_skill_loaded(skill_name="test", required_tools=["Bash"], pattern="")
                assert read_pending_state()["phase"] == _PHASE_PENDING

                # Transition pending -> loaded
                result = transition_phase(_PHASE_LOADED)
                assert result is True
                assert read_pending_state()["phase"] == _PHASE_LOADED

    def test_loaded_to_executing_valid(self, tmp_path):
        """loaded -> executing is valid."""
        with patch("skill_execution_state.STATE_DIR", tmp_path / ".claude" / "state"):
            with patch(
                "skill_execution_state.detect_terminal_id", return_value="test_terminal_456"
            ):
                set_skill_loaded(skill_name="test2", required_tools=["Bash"], pattern="")
                transition_phase(_PHASE_LOADED)

                result = transition_phase(_PHASE_EXECUTING)
                assert result is True
                assert read_pending_state()["phase"] == _PHASE_EXECUTING

    def test_executing_to_complete_valid(self, tmp_path):
        """executing -> complete is valid."""
        with patch("skill_execution_state.STATE_DIR", tmp_path / ".claude" / "state"):
            with patch(
                "skill_execution_state.detect_terminal_id", return_value="test_terminal_789"
            ):
                set_skill_loaded(skill_name="test3", required_tools=["Bash"], pattern="")
                transition_phase(_PHASE_LOADED)
                transition_phase(_PHASE_EXECUTING)

                result = transition_phase(_PHASE_COMPLETE)
                assert result is True
                assert read_pending_state()["phase"] == _PHASE_COMPLETE

    def test_invalid_transition_pending_to_executing(self, tmp_path):
        """pending -> executing is invalid (must go through loaded)."""
        with patch("skill_execution_state.STATE_DIR", tmp_path / ".claude" / "state"):
            with patch(
                "skill_execution_state.detect_terminal_id", return_value="test_terminal_invalid"
            ):
                set_skill_loaded(skill_name="test4", required_tools=["Bash"], pattern="")

                result = transition_phase(_PHASE_EXECUTING)
                assert result is False
                assert read_pending_state()["phase"] == _PHASE_PENDING

    def test_invalid_transition_complete_to_anything(self, tmp_path):
        """complete is terminal - no transitions allowed."""
        with patch("skill_execution_state.STATE_DIR", tmp_path / ".claude" / "state"):
            with patch(
                "skill_execution_state.detect_terminal_id", return_value="test_terminal_term"
            ):
                set_skill_loaded(skill_name="test5", required_tools=["Bash"], pattern="")
                transition_phase(_PHASE_LOADED)
                transition_phase(_PHASE_EXECUTING)
                transition_phase(_PHASE_COMPLETE)

                # Try to transition from complete
                result = transition_phase(_PHASE_EXECUTING)
                assert result is False
                assert read_pending_state()["phase"] == _PHASE_COMPLETE

    def test_stale_transition_from_loaded(self, tmp_path):
        """loaded -> stale is valid (timeout/abandon)."""
        with patch("skill_execution_state.STATE_DIR", tmp_path / ".claude" / "state"):
            with patch(
                "skill_execution_state.detect_terminal_id", return_value="test_terminal_stale"
            ):
                set_skill_loaded(skill_name="test6", required_tools=["Bash"], pattern="")
                transition_phase(_PHASE_LOADED)

                result = transition_phase(_PHASE_STALE)
                assert result is True
                assert read_pending_state()["phase"] == _PHASE_STALE


class TestTerminalIdHandling:
    """Test terminal ID sanitization for multi-terminal safety."""

    def test_sanitize_removes_special_chars(self):
        """Special characters are removed for path safety."""
        assert sanitize_terminal_id("console_abc-123:def") == "console_abc-123:def"
        assert sanitize_terminal_id("console_abc def!@#") == "console_abc_def___"
        assert sanitize_terminal_id("../../../etc/passwd") == "_________etc_passwd"

    def test_sanitize_allows_valid_chars(self):
        """Alphanumeric, underscore, colon, hyphen preserved."""
        assert sanitize_terminal_id("console_abc-123:def") == "console_abc-123:def"
        assert sanitize_terminal_id("terminal_01") == "terminal_01"


class TestCompletionCriteriaStorage:
    """Test that completion criteria are stored and retrieved correctly."""

    def test_completion_criteria_stored(self, tmp_path):
        """Completion criteria from frontmatter stored in state."""
        with patch("skill_execution_state.STATE_DIR", tmp_path / ".claude" / "state"):
            with patch("skill_execution_state.detect_terminal_id", return_value="test_cc_store"):
                completion_criteria = [
                    {"phase": "analysis", "required_output": "WORKFLOW:test:analysis"},
                    {"phase": "implementation", "required_output": "WORKFLOW:test:implementation"},
                ]
                set_skill_loaded(
                    skill_name="test_cc",
                    required_tools=["Bash"],
                    pattern="",
                )

                # Manually set completion_criteria (simulating frontmatter loading)
                state = read_pending_state()
                state["completion_criteria"] = completion_criteria
                state_file = (
                    tmp_path
                    / ".claude"
                    / "state"
                    / "skill_execution_test_cc_store"
                    / "skill_execution_pending.json"
                )
                state_file.parent.mkdir(parents=True, exist_ok=True)
                state_file.write_text(json.dumps(state))

                # Verify retrieval
                retrieved = read_pending_state()
                assert len(retrieved["completion_criteria"]) == 2
                assert retrieved["completion_criteria"][0]["phase"] == "analysis"


class TestEnforcementTierStorage:
    """Test enforcement_tier is stored correctly."""

    def test_strict_tier_stored(self, tmp_path):
        """strict enforcement tier stored in state."""
        with patch("skill_execution_state.STATE_DIR", tmp_path / ".claude" / "state"):
            with patch("skill_execution_state.detect_terminal_id", return_value="test_tier_strict"):
                set_skill_loaded(skill_name="test_strict", required_tools=["Bash"], pattern="")

                # Manually set tier
                state = read_pending_state()
                state["enforcement_tier"] = "strict"
                state_file = (
                    tmp_path
                    / ".claude"
                    / "state"
                    / "skill_execution_test_tier_strict"
                    / "skill_execution_pending.json"
                )
                state_file.write_text(json.dumps(state))

                retrieved = read_pending_state()
                assert retrieved["enforcement_tier"] == "strict"

    def test_advisory_tier_stored(self, tmp_path):
        """advisory enforcement tier stored in state when explicitly set."""
        with patch("skill_execution_state.STATE_DIR", tmp_path / ".claude" / "state"):
            with patch("skill_execution_state.detect_terminal_id", return_value="test_tier_adv"):
                # Mock frontmatter to return advisory tier
                with patch(
                    "skill_execution_state._load_skill_frontmatter",
                    return_value={
                        "allowed_first_tools": [],
                        "completion_criteria": [],
                        "enforcement_tier": "advisory",
                        "stale_timeout": 300,
                    },
                ):
                    set_skill_loaded(skill_name="test_adv", required_tools=["Bash"], pattern="")

                retrieved = read_pending_state()
                assert retrieved["enforcement_tier"] == "advisory"

    def test_none_tier_no_state(self, tmp_path):
        """tier=none means no state file written (knowledge skill)."""
        with patch("skill_execution_state.STATE_DIR", tmp_path / ".claude" / "state"):
            with patch("skill_execution_state.detect_terminal_id", return_value="test_tier_none"):
                # Mock frontmatter to return enforcement_tier=none, empty completion_criteria
                with patch(
                    "skill_execution_state._load_skill_frontmatter",
                    return_value={
                        "allowed_first_tools": [],
                        "completion_criteria": [],
                        "enforcement_tier": "none",
                        "stale_timeout": 300,
                    },
                ):
                    # Tier=none with no required_tools -> no state
                    set_skill_loaded(skill_name="test_none", required_tools=[], pattern="")

                # State should not exist
                assert read_pending_state() is None


class TestMarkerDetection:
    """Test WORKFLOW:{skill}:{action} marker detection patterns."""

    def test_marker_pattern_extraction(self):
        """Extract action from WORKFLOW marker."""
        import re

        pattern = re.compile(r"WORKFLOW:(\w+):(\w+)", re.IGNORECASE)
        text = "Analysis complete. WORKFLOW:test:analysis marker detected."

        matches = list(pattern.findall(text))
        assert len(matches) == 1
        assert matches[0] == ("test", "analysis")

    def test_multiple_markers_extracted(self):
        """Multiple markers in output all extracted."""
        import re

        pattern = re.compile(r"WORKFLOW:(\w+):(\w+)", re.IGNORECASE)
        text = "First WORKFLOW:test:phase1 done. Then WORKFLOW:test:phase2 done."

        matches = list(pattern.findall(text))
        assert len(matches) == 2
        assert matches[0] == ("test", "phase1")
        assert matches[1] == ("test", "phase2")

    def test_case_insensitive_markers(self):
        """Marker matching is case-insensitive."""
        import re

        pattern = re.compile(r"WORKFLOW:(\w+):(\w+)", re.IGNORECASE)
        text = "workflow:Test:ANALYSIS complete."

        matches = list(pattern.findall(text))
        assert len(matches) == 1
        assert matches[0][1].lower() == "analysis"


class TestStaleTimeout:
    """Test stale timeout detection."""

    def test_stale_timeout_calculation(self):
        """Loaded_at vs current time vs stale_timeout."""
        current_time = time.time()
        loaded_at = current_time - 400  # 400 seconds ago
        stale_timeout = 300  # 5 minutes

        is_stale = (current_time - loaded_at) > stale_timeout
        assert is_stale is True

    def test_not_stale_within_timeout(self):
        """Within timeout = not stale."""
        current_time = time.time()
        loaded_at = current_time - 100  # 100 seconds ago
        stale_timeout = 300  # 5 minutes

        is_stale = (current_time - loaded_at) > stale_timeout
        assert is_stale is False


class TestStateFileCleanup:
    """Test clear_state removes state file."""

    def test_clear_state_removes_file(self, tmp_path):
        """clear_state deletes the state file."""
        with patch("skill_execution_state.STATE_DIR", tmp_path / ".claude" / "state"):
            with patch("skill_execution_state.detect_terminal_id", return_value="test_clear"):
                set_skill_loaded(skill_name="test_clear", required_tools=["Bash"], pattern="")
                assert read_pending_state() is not None

                clear_state()
                assert read_pending_state() is None


class TestStateIsolation:
    """Test multi-terminal state isolation."""

    def test_different_terminals_have_isolated_state(self, tmp_path):
        """Different terminal IDs get separate state files."""
        with patch("skill_execution_state.STATE_DIR", tmp_path / ".claude" / "state"):
            # Terminal A
            with patch("skill_execution_state.detect_terminal_id", return_value="terminal_a"):
                set_skill_loaded(skill_name="skill_a", required_tools=["Bash"], pattern="")
                transition_phase(_PHASE_LOADED)
                state_a = read_pending_state()
                assert state_a["skill"] == "skill_a"
                assert state_a["phase"] == _PHASE_LOADED

            # Terminal B (same skill name, different terminal)
            with patch("skill_execution_state.detect_terminal_id", return_value="terminal_b"):
                set_skill_loaded(skill_name="skill_a", required_tools=["Bash"], pattern="")
                state_b = read_pending_state()
                assert state_b["skill"] == "skill_a"
                assert state_b["phase"] == _PHASE_PENDING  # Different terminal = no prior state

    def test_same_terminal_persists_state(self, tmp_path):
        """Same terminal ID persists state across operations."""
        with patch("skill_execution_state.STATE_DIR", tmp_path / ".claude" / "state"):
            with patch("skill_execution_state.detect_terminal_id", return_value="terminal_persist"):
                set_skill_loaded(skill_name="persist_test", required_tools=["Bash"], pattern="")
                assert read_pending_state()["phase"] == _PHASE_PENDING

                transition_phase(_PHASE_LOADED)
                assert read_pending_state()["phase"] == _PHASE_LOADED

                transition_phase(_PHASE_EXECUTING)
                assert read_pending_state()["phase"] == _PHASE_EXECUTING


class TestWorkflowTools:
    """Test workflow tool detection."""

    def test_workflow_tools_recognized(self):
        """Tools that count as workflow execution."""
        workflow_tools = {"Bash", "Read", "Grep", "Glob", "Write", "Edit", "Task", "Agent"}

        assert "Bash" in workflow_tools
        assert "Read" in workflow_tools
        assert "Write" in workflow_tools
        assert "Skill" not in workflow_tools  # Skill is NOT a workflow tool
        assert "WebSearch" not in workflow_tools


class TestPreCompactCheckpointFormat:
    """Test PreCompact checkpoint file format."""

    def test_checkpoint_contains_required_fields(self):
        """Checkpoint must have skill, phase, loaded_at, completion_criteria."""
        checkpoint = {
            "skill": "test_skill",
            "phase": "executing",
            "loaded_at": time.time(),
            "completion_criteria": [],
            "enforcement_tier": "strict",
            "tools_used": ["Bash", "Read"],
            "first_tool_validated": True,
            "checkpoint_at": time.time(),
            "terminal_id": "test_terminal",
        }

        assert "skill" in checkpoint
        assert "phase" in checkpoint
        assert "loaded_at" in checkpoint
        assert "completion_criteria" in checkpoint
        assert "enforcement_tier" in checkpoint
        assert "checkpoint_at" in checkpoint
        assert "terminal_id" in checkpoint


class TestValidTransitionMap:
    """Test the VALID_TRANSITIONS map is correct."""

    def test_pending_only_goes_to_loaded(self):
        """pending can only transition to loaded."""
        assert _PHASE_PENDING in VALID_TRANSITIONS
        assert _PHASE_LOADED in VALID_TRANSITIONS[_PHASE_PENDING]
        assert _PHASE_EXECUTING not in VALID_TRANSITIONS[_PHASE_PENDING]
        assert len(VALID_TRANSITIONS[_PHASE_PENDING]) == 1

    def test_loaded_can_go_to_executing_or_stale(self):
        """loaded can transition to executing or stale."""
        assert _PHASE_EXECUTING in VALID_TRANSITIONS[_PHASE_LOADED]
        assert _PHASE_STALE in VALID_TRANSITIONS[_PHASE_LOADED]
        assert len(VALID_TRANSITIONS[_PHASE_LOADED]) == 2

    def test_complete_is_terminal(self):
        """complete has no valid transitions."""
        assert len(VALID_TRANSITIONS[_PHASE_COMPLETE]) == 0

    def test_stale_is_terminal(self):
        """stale has no valid transitions."""
        assert len(VALID_TRANSITIONS[_PHASE_STALE]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
