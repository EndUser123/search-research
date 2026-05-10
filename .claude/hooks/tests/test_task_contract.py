"""Tests for task_contract helper and Stop task_contract_fit gate.

Covers:
1. Helper: save/load round-trip, overwrite preserves task_id, clear marks completed
2. Gate PASS: complete answer with all required outputs
3. Gate BLOCK: missing outputs → block with specific message
4. Gate silent: no contract, control turn, short response, exploration turn
5. Aggregator: task_contract_fit classified as task_incomplete/high

Run with: pytest P:/.claude/hooks/tests/test_task_contract.py -v
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure hooks directory is on sys.path for imports
HOOKS_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = HOOKS_DIR / "__lib"
for d in (str(HOOKS_DIR), str(LIB_DIR)):
    if d not in sys.path:
        sys.path.insert(0, d)


@pytest.fixture(autouse=True)
def _isolated_artifacts(tmp_path, monkeypatch):
    """Redirect _home() to a temp dir so contracts land in tmp_path/.claude/.artifacts/."""
    import __lib.task_contract as _tc
    monkeypatch.setattr(_tc, "_home", lambda: tmp_path)
    yield


# =============================================================================
# TEST 1: Helper round-trips
# =============================================================================

class TestTaskContractHelpers:
    def test_no_contract_returns_none(self):
        from __lib.task_contract import load_contract
        assert load_contract("terminal_nonexistent") is None

    def test_save_and_load_round_trip(self):
        from __lib.task_contract import load_contract, save_contract
        save_contract(
            "terminal_test",
            task_id="t-001",
            description="Fix the off-by-one in parser",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
        )
        loaded = load_contract("terminal_test")
        assert loaded is not None
        assert loaded["task_id"] == "t-001"
        assert loaded["status"] == "active"
        assert loaded["required_outputs"] == [
            "root_cause", "fix", "tests", "verification_commands"
        ]

    def test_overwrite_preserves_task_id_and_created_at(self):
        from __lib.task_contract import load_contract, save_contract
        save_contract(
            "terminal_test",
            task_id="t-001",
            description="Initial description",
            required_outputs=["root_cause", "fix"],
        )
        first = load_contract("terminal_test")

        save_contract(
            "terminal_test",
            task_id="t-001",
            description="Updated description",
            required_outputs=["root_cause", "fix", "tests"],
        )
        second = load_contract("terminal_test")

        assert second["task_id"] == first["task_id"]
        assert second["created_at"] == first["created_at"]
        assert second["last_updated_at"] != first["last_updated_at"]
        assert second["description"] == "Updated description"
        assert "tests" in second["required_outputs"]

    def test_clear_marks_completed(self):
        from __lib.task_contract import clear_contract, load_contract, save_contract
        save_contract(
            "terminal_test",
            task_id="t-002",
            description="Something",
            required_outputs=["fix"],
        )
        clear_contract("terminal_test")
        # load_contract only returns active contracts
        assert load_contract("terminal_test") is None

    def test_filters_invalid_outputs(self):
        from __lib.task_contract import load_contract, save_contract
        save_contract(
            "terminal_test",
            task_id="t-003",
            description="Test filtering",
            required_outputs=["root_cause", "invalid_output", "fix"],
        )
        loaded = load_contract("terminal_test")
        assert loaded["required_outputs"] == ["root_cause", "fix"]


# =============================================================================
# TEST 2: Gate PASS — complete answer
# =============================================================================

class TestGatePass:
    def test_complete_answer_all_outputs_present(self):
        from __lib.task_contract import save_contract
        from Stop import _run_task_contract_fit_gate

        save_contract(
            "terminal_pass",
            task_id="t-pass",
            description="Fix the bug",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
        )

        response = (
            "## Root Cause\n"
            "The bug is caused by an off-by-one error in the parser loop at line 42.\n"
            "The index variable starts at 1 instead of 0, skipping the first element.\n\n"
            "## Fix Applied\n"
            "Changed the initial index from 1 to 0 in parser.py:42.\n"
            "This fix ensures all elements are processed correctly.\n\n"
            "## Tests\n"
            "Added test_parser_full_coverage in test_parser.py.\n"
            "pytest tests/test_parser.py -v\n"
            "All 15 tests pass.\n\n"
            "## Verification Commands\n"
            "Run verification:\n"
            "```bash\n"
            "pytest tests/test_parser.py -v\n"
            "```\n"
        )

        data = {
            "response": response,
            "terminal_id": "terminal_pass",
            "session_id": "sess-1",
            "user_prompt": "Why does the parser crash on empty input? Diagnose and provide root cause, fix, tests, verification.",
        }
        result = _run_task_contract_fit_gate(data)
        assert result is None  # All outputs present → allow


# =============================================================================
# TEST 3: Gate BLOCK — missing outputs
# =============================================================================

class TestGateBlock:
    def test_missing_tests_and_verification(self):
        from __lib.task_contract import save_contract
        from Stop import _run_task_contract_fit_gate

        save_contract(
            "terminal_block",
            task_id="t-block",
            description="Fix the bug",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
        )

        # Response has root_cause and fix but NOT tests or verification_commands
        response = (
            "## Root Cause\n"
            "The bug is caused by a null pointer dereference in the handler.\n"
            "The pointer is never checked before being dereferenced.\n\n"
            "## Fix Applied\n"
            "Added a null check before dereferencing in handler.py:30.\n"
            "This prevents the crash when the pointer is null.\n\n"
            "The fix is straightforward and minimal. The handler now safely returns "
            "early when the pointer is null, avoiding any dereference. "
            "This change is backward-compatible and adds no new dependencies."
        )

        data = {
            "response": response,
            "terminal_id": "terminal_block",
            "session_id": "sess-2",
            # Use a prompt that classifies as analysis (not control)
            "user_prompt": "What is causing the null pointer in handler.py?",
        }
        result = _run_task_contract_fit_gate(data)
        assert result is not None
        assert result.get("decision") == "block"
        msg = result.get("systemMessage", "")
        assert "tests" in msg
        assert "verification_commands" in msg

    def test_missing_only_root_cause(self):
        from __lib.task_contract import save_contract
        from Stop import _run_task_contract_fit_gate

        save_contract(
            "terminal_rc",
            task_id="t-rc",
            description="Fix",
            required_outputs=["root_cause", "fix"],
        )

        response = (
            "I fixed the issue by adding a guard clause at the top of the function. "
            "The fix prevents the crash by checking the condition early. "
            "Tests: added test_guard_clause. "
            "Run verification: pytest tests/test_module.py\n"
            "This change is small and surgical — it adds a single if-statement "
            "that returns early when the input is invalid. No other code paths are affected."
        )

        data = {
            "response": response,
            "terminal_id": "terminal_rc",
            "session_id": "sess-3",
            "user_prompt": "Why is the handler crashing? Provide root cause and fix.",
        }
        result = _run_task_contract_fit_gate(data)
        assert result is not None
        assert result["decision"] == "block"
        assert "root_cause" in result["systemMessage"]


# =============================================================================
# TEST 4: Gate SILENT — no contract / non-completion turns
# =============================================================================

class TestGateSilent:
    def test_no_contract_present(self):
        from Stop import _run_task_contract_fit_gate

        data = {
            "response": "Some long analytical response " * 50,
            "terminal_id": "terminal_no_contract",
            "session_id": "sess-4",
            "user_prompt": "Explain the architecture",
        }
        result = _run_task_contract_fit_gate(data)
        assert result is None

    def test_control_turn_skipped(self):
        from __lib.task_contract import save_contract
        from Stop import _run_task_contract_fit_gate

        save_contract(
            "terminal_control",
            task_id="t-ctrl",
            description="Fix",
            required_outputs=["root_cause", "fix"],
        )

        data = {
            "response": "Done. " * 50,
            "terminal_id": "terminal_control",
            "session_id": "sess-5",
            "user_prompt": "stop",  # control turn
        }
        result = _run_task_contract_fit_gate(data)
        assert result is None

    def test_short_response_skipped(self):
        from __lib.task_contract import save_contract
        from Stop import _run_task_contract_fit_gate

        save_contract(
            "terminal_short",
            task_id="t-short",
            description="Fix",
            required_outputs=["root_cause"],
        )

        data = {
            "response": "I think the issue is in the parser.",  # < 300 chars
            "terminal_id": "terminal_short",
            "session_id": "sess-6",
            "user_prompt": "What's wrong with the parser?",
        }
        result = _run_task_contract_fit_gate(data)
        assert result is None

    def test_exploration_turn_skipped(self):
        from __lib.task_contract import save_contract
        from Stop import _run_task_contract_fit_gate

        save_contract(
            "terminal_explore",
            task_id="t-explore",
            description="Fix",
            required_outputs=["root_cause", "fix"],
        )

        response = (
            "There are several possible approaches to this problem. "
            "We could use approach A which is simple but limited. "
            "Or approach B which is more flexible but complex. "
            + "Let me think about this more carefully. " * 20
        )

        data = {
            "response": response,
            "terminal_id": "terminal_explore",
            "session_id": "sess-7",
            # "Should we..." classifies as exploration
            "user_prompt": "Should we refactor the auth module to use JWT?",
        }
        result = _run_task_contract_fit_gate(data)
        assert result is None

    def test_no_terminal_id_skipped(self):
        from Stop import _run_task_contract_fit_gate

        data = {
            "response": "Some response " * 50,
            "terminal_id": "",
            "session_id": "",
            "user_prompt": "Fix the bug",
        }
        result = _run_task_contract_fit_gate(data)
        assert result is None


# =============================================================================
# TEST 5: Aggregator classification
# =============================================================================

class TestAggregatorClassification:
    def test_task_contract_fit_classified(self):
        from Stop_aggregator import classify_result
        root_issue, confidence = classify_result("task_contract_fit", "block")
        assert root_issue == "task_incomplete"
        assert confidence == "high"

    def test_task_incomplete_priority_is_high(self):
        from Stop_aggregator import _ISSUE_PRIORITY
        assert "task_incomplete" in _ISSUE_PRIORITY
        # Should be between missing_verification (2) and empty_ack (3)
        assert _ISSUE_PRIORITY["task_incomplete"] == 2
