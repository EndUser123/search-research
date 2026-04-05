#!/usr/bin/env python3
"""
test_rca_contract_gate.py - Tests for RCA Contract Gate
=======================================================

Tests for StopHook_rca_contract.py using mocked skill_state.
Verifies:
1. RCA turn activation from skill_state
2. Non-RCA turns are skipped
3. Hook demotions for RCA turns
4. Contract field validation
5. Dead-code regression fixture

Tests run against the mocked interface, not the real Stop_router.
"""

import sys
from pathlib import Path

# Add hooks dir to path for imports
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import pytest

# Import the module under test
import StopHook_overconfidence_detector as overconfidence_hook
import StopHook_unverified_stance as unverified_stance_hook

# Import RCA utilities from Stop_router (not in StopHook_rca_contract)
from Stop_router import _is_hook_skipped_for_rca, _is_rca_turn
from StopHook_rca_contract import (
    _extract_sections,
    _get_current_turn_tools,
    _validate_rca_contract,
    check,
    run,
)

# --- Fixtures ---------------------------------------------------------------


@pytest.fixture
def base_data():
    """Base hook data without RCA context."""
    return {
        "assistant_response": "Some response",
        "response": "Some response",
        "session_id": "test-session-123",
        "terminal_id": "test-terminal-abc",
        "skill_state": None,
        "rca_turn": False,
        "rca_skill": None,
        "tool_events": [],
    }


@pytest.fixture
def rca_data():
    """Hook data with RCA turn context."""
    return {
        "assistant_response": "",
        "response": "",
        "session_id": "test-session-123",
        "terminal_id": "test-terminal-abc",
        "skill_state": {"skill": "debugrca", "loaded_at": 1234567890.0},
        "rca_turn": True,
        "rca_skill": "debugrca",
        "tool_events": [],
    }


# --- RCA Turn Detection Tests -----------------------------------------------


class TestRcaTurnDetection:
    """Tests for RCA turn detection via skill_state."""

    def test_rca_turn_with_debugrca_skill(self):
        """debugRCA skill name should activate RCA mode."""
        skill_state = {"skill": "debugrca", "loaded_at": 1234567890.0}
        is_rca, skill_name = _is_rca_turn(skill_state)
        assert is_rca is True
        assert skill_name == "debugrca"

    def test_rca_turn_with_rca_alias(self):
        """RCA skill aliases should activate RCA mode."""
        for alias in ["rca", "r", "rca-v2", "rv2", "debug-rca"]:
            skill_state = {"skill": alias, "loaded_at": 1234567890.0}
            is_rca, skill_name = _is_rca_turn(skill_state)
            assert is_rca is True, f"Failed for alias: {alias}"
            assert skill_name == alias

    def test_rca_turn_case_insensitive(self):
        """RCA turn detection should be case-insensitive."""
        skill_state = {"skill": "DebugRCA", "loaded_at": 1234567890.0}
        is_rca, skill_name = _is_rca_turn(skill_state)
        assert is_rca is True

    def test_no_rca_turn_with_none_skill_state(self):
        """None skill_state should not activate RCA mode."""
        is_rca, skill_name = _is_rca_turn(None)
        assert is_rca is False
        assert skill_name is None

    def test_no_rca_turn_with_empty_skill(self):
        """Empty skill should not activate RCA mode."""
        skill_state = {"skill": "", "loaded_at": 1234567890.0}
        is_rca, skill_name = _is_rca_turn(skill_state)
        assert is_rca is False

    def test_no_rca_turn_with_non_rca_skill(self):
        """Non-RCA skill should not activate RCA mode."""
        skill_state = {"skill": "gto", "loaded_at": 1234567890.0}
        is_rca, skill_name = _is_rca_turn(skill_state)
        assert is_rca is False


# --- Hook Skip Tests --------------------------------------------------------


class TestHookSkipPolicy:
    """Tests for RCA turn hook skip policy."""

    def test_step_header_verifier_skipped_on_rca(self):
        """StopHook_step_header_verifier.py should be skipped for RCA turns."""
        assert _is_hook_skipped_for_rca("StopHook_step_header_verifier.py", True) is True

    def test_step_header_verifier_not_skipped_non_rca(self):
        """StopHook_step_header_verifier.py should run for non-RCA turns."""
        assert _is_hook_skipped_for_rca("StopHook_step_header_verifier.py", False) is False

    def test_other_hooks_not_skipped(self):
        """Other hooks should not be skipped for RCA turns."""
        hooks = [
            "StopHook_overconfidence_detector.py",
            "StopHook_unverified_stance.py",
            "Stop_negative_existence_guard.py",
            "StopHook_skill_execution_gate.py",
        ]
        for hook in hooks:
            assert (
                _is_hook_skipped_for_rca(hook, True) is False
            ), f"Hook {hook} should not be skipped"


class TestRcaTurnDemotions:
    """Tests for RCA-turn advisory behavior on prose-policing hooks."""

    def test_overconfidence_is_advisory_on_rca_turn(self):
        data = {
            "assistant_response": "This clearly proves the root cause is config.py.",
            "rca_turn": True,
            "tool_events": [],
        }
        result = overconfidence_hook.run(data)
        assert result is not None
        assert result.get("block") is not True
        assert "note" in result

    def test_unverified_stance_system_claim_is_advisory_on_rca_turn(self):
        data = {
            "assistant_response": "Because the hook blocks this path, the system cannot continue.",
            "response": "Because the hook blocks this path, the system cannot continue.",
            "rca_turn": True,
            "tool_events": [{"name": "Read", "command": "read config.py"}],
            "tools_used": ["Read"],
            "session_id": "12345678-1234-1234-1234-123456789abc",
        }
        result = unverified_stance_hook.run(data)
        assert result is None or result.get("block") is not True


# --- Section Extraction Tests ------------------------------------------------


class TestSectionExtraction:
    """Tests for RCA section parsing."""

    def test_extract_markdown_sections(self):
        """Should extract markdown-style sections."""
        response = """
## Symptom
The system crashed with a KeyError.

## Evidence
Read on `config.json` showed missing key.

## Executed Path
config.py:42

## Alternative Hypothesis
The config file is corrupted.

## Falsifier
Re-reading the file shows it is valid JSON.

## Root Cause
config.py:42 calls dict.get() on None.

## Fix
Add null check before calling dict.get().

## Verification
Run pytest tests/test_config.py to confirm fix.
"""
        sections = _extract_sections(response)
        assert "Symptom" in sections
        assert "Evidence" in sections
        assert "Executed Path" in sections
        assert sections["Symptom"] == "The system crashed with a KeyError."

    def test_extract_plaintext_sections(self):
        """Should extract all-caps plaintext sections."""
        response = """
SYMPTOM:
The system crashed with a KeyError.

EVIDENCE:
Read on `config.json` showed missing key.

EXECUTED PATH:
config.py:42

ALTERNATIVE HYPOTHESIS:
The config file is corrupted.

FALSIFIER:
Re-reading the file shows it is valid JSON.

ROOT CAUSE:
config.py:42 calls dict.get() on None.

FIX:
Add null check before calling dict.get().

VERIFICATION:
Run pytest tests/test_config.py to confirm fix.
"""
        sections = _extract_sections(response)
        assert "SYMPTOM" in sections or "Symptom" in sections

    def test_missing_sections(self):
        """Should handle missing sections gracefully."""
        response = """
## Symptom
Only the symptom is present.
"""
        sections = _extract_sections(response)
        assert "Symptom" in sections
        assert "Evidence" not in sections


# --- Contract Validation Tests -----------------------------------------------


class TestContractValidation:
    """Tests for RCA contract field validation."""

    def test_valid_rca_response_passes(self, rca_data):
        """Complete RCA response with all fields should pass."""
        rca_data["assistant_response"] = """
## Symptom
The system crashed with a KeyError.

## Evidence
Grep found showed the missing timeout key in the configuration.

## Executed Path
config.py:42 - calls dict.get() on config object

## Alternative Hypothesis
The config file is missing the timeout key.

## Falsifier
Adding timeout key to config.json does not fix the crash.

## Root Cause
config.py:42 - Missing null check before dict.get()

## Fix
Add null check: if config and 'timeout' in config:

## Verification
Run pytest tests/test_config.py - all tests pass.
"""
        rca_data["tool_events"] = [{"name": "Read", "tool_name": "Read"}]

        result = check(rca_data)
        assert result is None  # None = allow

    def test_missing_symptom_blocks(self, rca_data):
        """Missing Symptom should block."""
        rca_data["assistant_response"] = """
## Evidence
Read on `config.json` showed missing key.

## Executed Path
config.py:42

## Alternative Hypothesis
The config file is missing the timeout key.

## Falsifier
Adding timeout key to config.json does not fix the crash.

## Root Cause
config.py:42

## Fix
Add null check

## Verification
Run pytest
"""
        rca_data["tool_events"] = [{"name": "Read"}]

        result = check(rca_data)
        assert result is not None
        assert result["decision"] == "block"
        assert any(
            "missing-symptom" in r or "Symptom section missing" in r
            for r in result.get("block_reasons", [])
        )

    def test_missing_alternative_blocks(self, rca_data):
        """Missing Alternative Hypothesis should block."""
        rca_data["assistant_response"] = """
## Symptom
The system crashed.

## Evidence
Read on `config.json` showed missing key.

## Executed Path
config.py:42

## Falsifier
N/A

## Root Cause
config.py:42

## Fix
Add null check

## Verification
Run pytest
"""
        rca_data["tool_events"] = [{"name": "Read"}]

        result = check(rca_data)
        assert result is not None
        assert result["decision"] == "block"

    def test_missing_falsifier_blocks(self, rca_data):
        """Missing Falsifier should block."""
        rca_data["assistant_response"] = """
## Symptom
The system crashed.

## Evidence
Read on `config.json` showed missing key.

## Executed Path
config.py:42

## Alternative Hypothesis
The config is missing a key.

## Root Cause
config.py:42

## Fix
Add null check

## Verification
Run pytest
"""
        rca_data["tool_events"] = [{"name": "Read"}]

        result = check(rca_data)
        assert result is not None
        assert result["decision"] == "block"

    def test_unlabeled_transcript_evidence_blocks(self, rca_data):
        rca_data["assistant_response"] = """
## Symptom
The system crashed.

## Evidence
The transcript shows the hook fired after stale state was loaded.

## Executed Path
Read on `config.py` showed the call path enters parse_config().

## Alternative Hypothesis
The config file was malformed.

## Falsifier
Read on `config.py` showed valid parsing before the stale-state branch.

## Root Cause
parse_config() consumes stale state without a guard.

## Fix
Add a guard before stale-state consumption.

## Verification
Run pytest tests/test_config.py
"""
        rca_data["tool_events"] = [{"name": "Read"}]
        result = check(rca_data)
        assert result is not None
        assert result["decision"] == "block"
        assert any("transcript" in reason.lower() for reason in result.get("block_reasons", []))

    def test_non_rca_turn_skipped(self, base_data):
        """Non-RCA turns should skip validation."""
        base_data["assistant_response"] = """
## Symptom
The system crashed.

## Evidence
Read on `config.json` showed missing key.
"""
        result = check(base_data)
        assert result is None  # None = allow (skipped)


# --- Dead Code Regression Test -----------------------------------------------


class TestDeadCodeRegression:
    """Regression test for dead-code TTL misdiagnosis pattern."""

    def test_dead_code_function_blocked(self, rca_data):
        """Naming dead code as root cause should block."""
        rca_data["assistant_response"] = """
## Symptom
The system crashed with a KeyError.

## Evidence
Read on `StopHook_skill_execution_gate.py` line 474.

## Executed Path
_stop_hook.py imports StopHook_skill_execution_gate.py

## Alternative Hypothesis
The function `_read_slash_command_intent_state()` at line 474 is the cause.

## Falsifier
The function is never called (0 callers).

## Root Cause
_read_slash_command_intent_state() at StopHook_skill_execution_gate.py:474

## Fix
Delete the dead function.

## Verification
Run the test suite.
"""
        rca_data["tool_events"] = [
            {"name": "Read"},
            {"name": "Grep"},
        ]

        result = check(rca_data)
        assert result is not None
        assert result["decision"] == "block"
        # The root cause is in the executed path (via imports), so this might pass
        # But ideally we should check if the function is actually called


# --- Run Interface Tests ----------------------------------------------------


class TestRunInterface:
    """Tests for the run() interface used by Stop_router."""

    def test_run_returns_block_dict(self, rca_data):
        """run() should return block dict when validation fails."""
        rca_data["assistant_response"] = "## Symptom\nCrash"
        rca_data["tool_events"] = []

        result = run(rca_data)
        assert result is not None
        assert result.get("block") is True
        assert "blocking_hook" in result

    def test_run_returns_none_when_allowed(self, rca_data):
        """run() should return None when validation passes."""
        rca_data["assistant_response"] = """
## Symptom
The system crashed.

## Evidence
Grep found showed the missing timeout key in the configuration.

## Executed Path
config.py:42

## Alternative Hypothesis
The config is missing a key.

## Falsifier
Adding timeout key does not fix it.

## Root Cause
config.py:42

## Fix
Add null check

## Verification
Run pytest
"""
        rca_data["tool_events"] = [{"name": "Read"}]

        result = run(rca_data)
        assert result is None  # None = allow


# --- Tool Events Tests -------------------------------------------------------


class TestToolEvents:
    """Tests for tool event detection."""

    def test_read_tool_detected(self):
        """Read tool should be detected as verification tool."""
        events = [{"name": "Read", "tool_name": "Read"}]
        tools = _get_current_turn_tools(events)
        assert "Read" in tools

    def test_grep_tool_detected(self):
        """Grep tool should be detected as verification tool."""
        events = [{"name": "Grep"}]
        tools = _get_current_turn_tools(events)
        assert "Grep" in tools

    def test_bash_tool_detected(self):
        """Bash tool should be detected as verification tool."""
        events = [{"name": "Bash"}]
        tools = _get_current_turn_tools(events)
        assert "Bash" in tools

    def test_no_verification_tools(self):
        """Response without verification tools should block."""
        events = []  # No tools used
        is_valid, _ = _validate_rca_contract(
            "## Symptom\nCrash\n## Evidence\nNothing", events, True
        )
        # Without verification tools, evidence section should fail
        assert is_valid is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
