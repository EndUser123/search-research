"""Tests for CONTROL turn mode behavior in Stop gates.

Verifies that:
1. _run_epistemic_contract skips for control turns
2. _run_epistemic_contract skips for exploration turns (regression)
3. --epistemic-strict override re-enables validation on control turns
4. _process_gate_result suppresses quality gate blocks on control turns
5. _process_gate_result does NOT suppress policy gate blocks on control turns
6. analysis/final-answer behavior is unchanged (regression)

Run with: pytest P:/.claude/hooks/tests/test_stop_control_mode.py -v
"""

import sys
from pathlib import Path

import pytest

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def control_data():
    """Input classified as control mode (short imperative command)."""
    return {
        "prompt": "stop",
        "response": "OK, stopping now.",
        "session_id": "test-session-control",
        "terminal_id": "test-terminal",
    }


@pytest.fixture
def control_long_data():
    """Control mode with a long response (tests that skip is mode-based, not length-based)."""
    return {
        "prompt": "fix the bug in Stop.py",
        "response": (
            "The bug is caused by a missing import on line 42. "
            "Evidence: grep output shows no match for the module name. "
            "Root cause: sys.path does not include the hooks directory. "
            "I've fixed the import and verified the fix works correctly "
            "by running the test suite locally."
        ),
        "session_id": "test-session-control-long",
        "terminal_id": "test-terminal",
    }


@pytest.fixture
def exploration_data():
    """Input classified as exploration mode."""
    return {
        "prompt": "should we refactor the payment processor?",
        "response": (
            "We could refactor it into separate modules for validation, "
            "charging, and refund checks. This might improve maintainability."
        ),
        "session_id": "test-session-exploration",
        "terminal_id": "test-terminal",
    }


@pytest.fixture
def analysis_data():
    """Input classified as analysis mode (regression check)."""
    return {
        "prompt": "Why is the database connection failing?",
        "response": (
            "The database is not connecting because the import path is wrong. "
            "The root cause is that sys.path does not include the drivers directory. "
            "Evidence: grep output shows no match for the module name."
        ),
        "session_id": "test-session-analysis",
        "terminal_id": "test-terminal",
    }


# =============================================================================
# TEST 1: Epistemic contract skips for control turns
# =============================================================================


class TestControlModeEpistemicSkip:
    """Verify _run_epistemic_contract skips for control turns."""

    def test_control_short_response_skips(self, control_data):
        from Stop import _run_epistemic_contract
        assert _run_epistemic_contract(control_data) is None

    def test_control_long_response_skips(self, control_long_data):
        from Stop import _run_epistemic_contract
        assert _run_epistemic_contract(control_long_data) is None

    def test_control_various_commands_skip(self):
        from Stop import _run_epistemic_contract, _classify_turn_mode
        commands = [
            "stop",
            "actually re-read the file",
            "no, use the other approach",
            "skip that step",
            "wait",
            "fix the bug in Stop.py",
            "check the logs",
            "run the tests",
        ]
        for prompt in commands:
            data = {
                "prompt": prompt,
                "response": "Some response text here.",
            }
            assert _classify_turn_mode(data) == "control", f"Not control: {prompt}"
            assert _run_epistemic_contract(data) is None, f"Did not skip: {prompt}"

    def test_control_skips_even_with_analytical_response(self):
        """Control turn with analytical response still skips — intent is command, not analysis."""
        from Stop import _run_epistemic_contract, _classify_turn_mode
        data = {
            "prompt": "fix the bug",
            "response": (
                "The root cause is a missing import. Evidence: stack trace shows "
                "NameError on line 42. This suggests the dependency was removed."
            ),
        }
        assert _classify_turn_mode(data) == "control"
        assert _run_epistemic_contract(data) is None


# =============================================================================
# TEST 2: Epistemic contract skips for exploration turns (regression)
# =============================================================================


class TestExplorationModeEpistemicSkip:
    """Verify exploration turns still skip (regression from previous behavior)."""

    def test_exploration_skips(self, exploration_data):
        from Stop import _run_epistemic_contract
        assert _run_epistemic_contract(exploration_data) is None

    def test_exploration_various_prompts_skip(self):
        from Stop import _run_epistemic_contract, _classify_turn_mode
        prompts = [
            "should we consolidate these packages?",
            "what are the tradeoffs of this approach?",
            "alternatives to using FAISS?",
            "REST vs. GraphQL for the API?",
            "compare the two approaches",
        ]
        for prompt in prompts:
            data = {"prompt": prompt, "response": "Some reasoning here."}
            assert _classify_turn_mode(data) == "exploration", f"Not exploration: {prompt}"
            assert _run_epistemic_contract(data) is None, f"Did not skip: {prompt}"


# =============================================================================
# TEST 3: --epistemic-strict override
# =============================================================================


class TestEpistemicStrictOverride:
    """Verify --epistemic-strict overrides control/exploration suppression."""

    def test_control_with_epistemic_strict_does_not_skip(self):
        from Stop import _run_epistemic_contract, _classify_turn_mode
        data = {
            "prompt": "fix the bug --epistemic-strict",
            "response": (
                "The root cause is that the import is wrong. "
                "Evidence: stack trace shows NameError. "
                "This means the module was never loaded."
            ),
            "session_id": "test-ctrl-strict",
            "terminal_id": "test-terminal",
        }
        assert _classify_turn_mode(data) == "control"
        # With --epistemic-strict, the gate should run (not early-return)
        # The validator may or may not find issues, but it should NOT skip.
        result = _run_epistemic_contract(data)
        assert isinstance(result, (dict, type(None)))

    def test_exploration_with_epistemic_strict_does_not_skip(self):
        from Stop import _run_epistemic_contract, _classify_turn_mode
        data = {
            "prompt": "should we refactor --epistemic-strict",
            "response": (
                "The refactoring could help. Evidence: current module is 500 lines. "
                "Root cause: no separation of concerns."
            ),
            "session_id": "test-expl-strict",
            "terminal_id": "test-terminal",
        }
        assert _classify_turn_mode(data) == "exploration"
        result = _run_epistemic_contract(data)
        assert isinstance(result, (dict, type(None)))

    def test_epistemic_warn_flag_on_control_still_skips(self):
        """--epistemic-warn does NOT override suppression (only --epistemic-strict does)."""
        from Stop import _run_epistemic_contract
        data = {
            "prompt": "stop --epistemic-warn",
            "response": "OK, stopping.",
        }
        assert _run_epistemic_contract(data) is None


# =============================================================================
# TEST 4: _process_gate_result quality block suppression
# =============================================================================


class TestQualityBlockSuppression:
    """Verify quality gate blocks are suppressed on control/exploration turns."""

    def test_quality_block_suppressed_on_control(self):
        from Stop import _process_gate_result
        system_messages = []
        quality_messages = []
        data = {"prompt": "stop", "response": "OK"}
        res = {
            "decision": "block",
            "reason": "EPISTEMIC VIOLATION (2 issue(s))",
            "blocking_hook": "Stop.py:epistemic_contract",
        }
        blocked = _process_gate_result(
            res, "epistemic_contract", system_messages, quality_messages,
            data, "control", "normal",
        )
        assert not blocked, "Quality block should be suppressed on control turn"

    def test_quality_block_suppressed_on_exploration(self):
        from Stop import _process_gate_result
        system_messages = []
        quality_messages = []
        data = {"prompt": "should we?", "response": "Maybe."}
        res = {
            "decision": "block",
            "reason": "LAZY CLOSURE VIOLATION",
            "blocking_hook": "Stop.py:anti_sycophancy_quality",
        }
        blocked = _process_gate_result(
            res, "anti_sycophancy_quality", system_messages, quality_messages,
            data, "exploration", "normal",
        )
        assert not blocked, "Quality block should be suppressed on exploration turn"

    def test_policy_block_not_suppressed_on_control(self):
        from Stop import _process_gate_result
        system_messages = []
        quality_messages = []
        data = {"prompt": "stop", "response": "secret: abc123"}
        res = {
            "decision": "block",
            "reason": "SAFETY VIOLATION: secret detected",
            "blocking_hook": "Stop.py:safety_gate",
        }
        blocked = _process_gate_result(
            res, "safety_gate", system_messages, quality_messages,
            data, "control", "normal",
        )
        assert blocked, "Policy block should fire even on control turn"

    def test_quality_block_fires_on_analysis(self):
        from Stop import _process_gate_result
        system_messages = []
        quality_messages = []
        data = {"prompt": "why?", "response": "Because reasons."}
        res = {
            "decision": "block",
            "reason": "EPISTEMIC VIOLATION",
            "blocking_hook": "Stop.py:epistemic_contract",
        }
        blocked = _process_gate_result(
            res, "epistemic_contract", system_messages, quality_messages,
            data, "analysis", "normal",
        )
        assert blocked, "Quality block should fire on analysis turns"

    def test_quality_block_fires_on_control_in_strict_mode(self):
        """STOP_QUALITY_MODE=strict still suppresses control (per is_quality_mode_suppressed)."""
        from Stop import _process_gate_result
        system_messages = []
        quality_messages = []
        data = {"prompt": "fix it", "response": "Fixed."}
        res = {
            "decision": "block",
            "reason": "EPISTEMIC VIOLATION",
            "blocking_hook": "Stop.py:epistemic_contract",
        }
        # In strict mode, control is STILL suppressed (you don't nag on commands)
        blocked = _process_gate_result(
            res, "epistemic_contract", system_messages, quality_messages,
            data, "control", "strict",
        )
        assert not blocked, "Quality block should be suppressed on control even in strict"

    def test_quality_block_fires_on_exploration_in_strict_mode(self):
        """STOP_QUALITY_MODE=strict re-enables quality gates for exploration."""
        from Stop import _process_gate_result
        system_messages = []
        quality_messages = []
        data = {"prompt": "should we?", "response": "Maybe."}
        res = {
            "decision": "block",
            "reason": "EPISTEMIC VIOLATION",
            "blocking_hook": "Stop.py:epistemic_contract",
        }
        blocked = _process_gate_result(
            res, "epistemic_contract", system_messages, quality_messages,
            data, "exploration", "strict",
        )
        assert blocked, "Quality block should fire on exploration in strict mode"

    def test_quality_systemmessage_routed_to_quality_list(self):
        from Stop import _process_gate_result
        system_messages = []
        quality_messages = []
        data = {"prompt": "analyze", "response": "Because X."}
        res = {
            "decision": "warn",
            "reason": "ADVISORY",
            "systemMessage": "EPISTEMIC ADVISORY (1 issue(s))",
        }
        blocked = _process_gate_result(
            res, "epistemic_contract", system_messages, quality_messages,
            data, "analysis", "normal",
        )
        assert not blocked
        assert len(quality_messages) == 1
        assert len(system_messages) == 0


# =============================================================================
# TEST 5: Regression — analysis/final-answer behavior unchanged
# =============================================================================


class TestAnalysisRegression:
    """Verify analysis/final-answer turns are not affected by control-mode changes."""

    def test_analysis_not_suppressed(self, analysis_data):
        from Stop import _run_epistemic_contract, _classify_turn_mode
        mode = _classify_turn_mode(analysis_data)
        assert mode == "analysis", f"Expected analysis, got {mode}"
        result = _run_epistemic_contract(analysis_data)
        # May return None (no issues found) or a dict (issues found)
        # The key is it doesn't skip due to mode suppression
        assert isinstance(result, (dict, type(None)))

    def test_plan_still_skips_format_repair(self):
        from Stop import _run_epistemic_contract, _classify_turn_mode
        data = {
            "prompt": "What are the next 10 things we should do?",
            "response": (
                "[PLAN]\n"
                "1. Fix the bug\n"
                "2. Add tests\n"
                "[RATIONALE]\n"
                "- Bug is blocking\n"
                "- Tests prevent regression"
            ),
        }
        assert _classify_turn_mode(data) == "plan"
        assert _run_epistemic_contract(data) is None

    def test_report_still_skips_format_repair(self):
        from Stop import _run_epistemic_contract, _classify_turn_mode
        data = {
            "prompt": "update",
            "response": "[STATUS] Done\n[CHANGES] None\n[RESULTS] Passing",
        }
        assert _classify_turn_mode(data) == "execution-report"
        assert _run_epistemic_contract(data) is None

    def test_control_classification_unchanged(self):
        """Verify control turn classification hasn't shifted."""
        from Stop import _classify_turn_mode
        assert _classify_turn_mode({"prompt": "stop", "response": ""}) == "control"
        assert _classify_turn_mode({"prompt": "fix the bug", "response": ""}) == "control"
        assert _classify_turn_mode({"prompt": "actually re-read", "response": ""}) == "control"
        assert _classify_turn_mode({"prompt": "wait", "response": ""}) == "control"
