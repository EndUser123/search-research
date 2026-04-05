#!/usr/bin/env python3
"""
Tests for GTO self-verifying hooks.

Tests:
1. PostToolUse format validator
2. Stop checklist gate
3. SessionEnd reminder
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "__lib"))

# Import the modules to test
try:
    from PostToolUse_gto_format_validator import (
        CHECKLIST_PATTERNS,
        extract_checklist_items,
        get_terminal_id,
        save_checklist_state,
        save_session_state,
        validate_gto_output,
    )
except ImportError:
    pytest.skip("PostToolUse_gto_format_validator not available", allow_module_level=True)


# =============================================================================
# PostToolUse Format Validator Tests
# =============================================================================


class TestValidateGtoOutput:
    """Tests for validate_gto_output function."""

    def test_empty_output_is_valid(self):
        """Empty output should be valid."""
        is_valid, errors = validate_gto_output("")
        assert is_valid is True
        assert errors == []

    def test_whitespace_only_is_valid(self):
        """Whitespace-only output should be valid."""
        is_valid, errors = validate_gto_output("   \n\n   ")
        assert is_valid is True
        assert errors == []

    def test_missing_status_details(self):
        """Missing Status Details section should be an error."""
        output = """
**Recommended Next Steps**
1 - Test
- 1a: Test action

0 - Do ALL Recommended Next Steps
"""
        is_valid, errors = validate_gto_output(output)
        assert is_valid is False
        assert any("Status Details" in e for e in errors)

    def test_missing_recommended_next_steps(self):
        """Missing Recommended Next Steps section should be an error."""
        output = """
**Status Details**
- Test item
"""
        is_valid, errors = validate_gto_output(output)
        assert is_valid is False
        assert any("Recommended Next Steps" in e for e in errors)

    def test_missing_terminator(self):
        """Missing terminator should be an error when Recommended Next Steps exists."""
        output = """
**Status Details**
- Test item

**Recommended Next Steps**
1 - Test domain
- 1a: Test action
"""
        is_valid, errors = validate_gto_output(output)
        assert is_valid is False
        assert any("terminator" in e.lower() for e in errors)

    def test_nothing_left_to_do_terminator(self):
        """'Nothing left to do' terminator should be valid."""
        output = """
**Status Details**
- All items addressed

**Recommended Next Steps**

0 - Nothing left to do
"""
        is_valid, errors = validate_gto_output(output)
        assert is_valid is True
        assert errors == []

    def test_do_all_terminator(self):
        """'Do ALL Recommended Next Steps' terminator should be valid."""
        output = """
**Status Details**
- Test item

**Recommended Next Steps**
1 - Test domain
- 1a: Test action

0 - Do ALL Recommended Next Steps
"""
        is_valid, errors = validate_gto_output(output)
        assert is_valid is True
        assert errors == []

    def test_missing_domain_header(self):
        """Missing domain header should be an error."""
        output = """
**Status Details**
- Test item

**Recommended Next Steps**
(no domain header lines here, just actions)

0 - Do ALL Recommended Next Steps
"""
        is_valid, errors = validate_gto_output(output)
        assert is_valid is False
        assert any("domain header" in e.lower() for e in errors)

    def test_missing_action_format(self):
        """Missing action format should be an error."""
        output = """
**Status Details**
- Test item

**Recommended Next Steps**
1 - Test domain

0 - Do ALL Recommended Next Steps
"""
        is_valid, errors = validate_gto_output(output)
        assert is_valid is False
        assert any("action" in e.lower() for e in errors)


class TestExtractChecklistItems:
    """Tests for extract_checklist_items function."""

    def test_no_checklist_items(self):
        """Output without checklist items should return empty list."""
        output = "Some regular text without checklist markers."
        items = extract_checklist_items(output)
        assert items == []

    def test_single_checklist_item(self):
        """Output with one checklist item should extract it."""
        output = """
**Did You Forget Anything?**
- 🟋 Documentation updates (CLAUDE.md, README.md, SKILL.md)
"""
        items = extract_checklist_items(output)
        assert len(items) >= 1
        assert any("Documentation updates" in item for item in items)

    def test_multiple_checklist_items(self):
        """Output with multiple checklist items should extract all."""
        output = """
**Did You Forget Anything?**
- 🟋 Documentation updates (CLAUDE.md, README.md, SKILL.md)
- 🟋 Tests for new/modified code
- 🟋 Git commit for completed work
"""
        items = extract_checklist_items(output)
        assert len(items) >= 3

    def test_blue_checklist_items(self):
        """Blue (🟦) checklist items should be extracted."""
        output = """
**Did You Forget Anything?**
- 🟦 Package media & documentation check
- 🟦 Git state hygiene check
"""
        items = extract_checklist_items(output)
        assert any("Package media" in item for item in items)
        assert any("Git state hygiene" in item for item in items)


class TestTerminalId:
    """Tests for terminal ID handling."""

    def test_default_terminal_id(self):
        """Should return 'default' when no env var is set."""
        with patch.dict(os.environ, {}, clear=True):
            tid = get_terminal_id()
            assert tid == "default"

    def test_env_terminal_id(self):
        """Should return env var value when set."""
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "test_terminal_123"}):
            tid = get_terminal_id()
            assert tid == "test_terminal_123"


class TestSaveState:
    """Tests for state saving functions."""

    def test_save_session_state(self):
        """Should save session state to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("PostToolUse_gto_format_validator._STATE_DIR", Path(tmpdir)):
                save_session_state("test_terminal")
                state_file = Path(tmpdir) / "gto_session_test_terminal.json"
                assert state_file.exists()

                with open(state_file) as f:
                    state = json.load(f)
                assert state["gto_invoked"] is True
                assert "timestamp" in state

    def test_save_checklist_state(self):
        """Should save checklist state to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("PostToolUse_gto_format_validator._STATE_DIR", Path(tmpdir)):
                items = ["item1", "item2"]
                save_checklist_state("test_terminal", items)
                state_file = Path(tmpdir) / "gto_checklist_test_terminal.json"
                assert state_file.exists()

                with open(state_file) as f:
                    state = json.load(f)
                assert state["items"] == items
                assert state["addressed"] == []
                assert "timestamp" in state


# =============================================================================
# Stop GTO Checklist Gate Tests
# =============================================================================


class TestStopGtoChecklistGate:
    """Tests for Stop_gto_checklist_gate.py."""

    @pytest.fixture
    def hook_module(self):
        """Import the hook module."""
        try:
            from stop.Stop_gto_checklist_gate import load_checklist_state, run

            return {"run": run, "load_checklist_state": load_checklist_state}
        except ImportError:
            pytest.skip("Stop_gto_checklist_gate not available")

    def test_no_state_no_block(self, hook_module):
        """Should not block when no state exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("stop.Stop_gto_checklist_gate.STATE_DIR", Path(tmpdir)):
                result = hook_module["run"]({"response": "test"})
                assert result is None or result.get("decision") != "block"

    def test_disabled_hook(self, hook_module):
        """Should not run when disabled."""
        with patch.dict(os.environ, {"GTO_CHECKLIST_GATE_ENABLED": "false"}):
            result = hook_module["run"]({"response": "test"})
            assert result is None

    def test_bypass_flag(self, hook_module):
        """Should allow with bypass flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("stop.Stop_gto_checklist_gate.STATE_DIR", Path(tmpdir)):
                # Create state with pending items
                state_file = Path(tmpdir) / "gto_checklist_default.json"
                with open(state_file, "w") as f:
                    json.dump(
                        {
                            "items": ["🟋 Documentation updates"],
                            "addressed": [],
                        },
                        f,
                    )

                result = hook_module["run"](
                    {
                        "response": "--skip-gto-checklist",
                        "transcript_path": "",
                    }
                )
                assert result is None


# =============================================================================
# SessionEnd GTO Reminder Tests
# =============================================================================


class TestSessionEndGtoReminder:
    """Tests for SessionEnd_gto_reminder.py."""

    @pytest.fixture
    def hook_module(self):
        """Import the hook module."""
        try:
            from SessionEnd_gto_reminder import format_reminder, run

            return {"run": run, "format_reminder": format_reminder}
        except ImportError:
            pytest.skip("SessionEnd_gto_reminder not available")

    def test_gto_not_invoked(self, hook_module):
        """Should show warning when /gto was not invoked."""
        reminder = hook_module["format_reminder"](
            {"gto_invoked": False}, {"items": [], "addressed": []}
        )
        assert "not invoked" in reminder.lower() or "was not" in reminder.lower()

    def test_gto_invoked_no_items(self, hook_module):
        """Should show success when /gto was invoked with no pending items."""
        reminder = hook_module["format_reminder"](
            {"gto_invoked": True}, {"items": [], "addressed": []}
        )
        assert "invoked" in reminder.lower() or "no checklist" in reminder.lower()

    def test_pending_items(self, hook_module):
        """Should list pending items."""
        reminder = hook_module["format_reminder"](
            {"gto_invoked": True},
            {"items": ["🟋 Documentation updates"], "addressed": []},
        )
        assert "pending" in reminder.lower() or "documentation" in reminder.lower()

    def test_addressed_items(self, hook_module):
        """Should show addressed items."""
        reminder = hook_module["format_reminder"](
            {"gto_invoked": True},
            {"items": [], "addressed": ["🟋 Documentation updates"]},
        )
        assert "addressed" in reminder.lower() or "documentation" in reminder.lower()

    def test_disabled_hook(self, hook_module):
        """Should not run when disabled."""
        with patch.dict(os.environ, {"GTO_SESSION_REMINDER_ENABLED": "false"}):
            result = hook_module["run"]({})
            assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
