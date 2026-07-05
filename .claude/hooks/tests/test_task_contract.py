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
    """Redirect _home() to a temp dir so contracts land in tmp_path/.claude/.artifacts/.

    Patches sys.modules so that ALL importers (including module-level imports in
    other test classes) see the patched _home.
    """
    import sys as _sys
    import __lib.task_contract as _tc
    # Patch the module's _home in-place (covers already-imported references)
    monkeypatch.setattr(_tc, "_home", lambda: tmp_path)
    # Also patch sys.modules so that re-imports get the patched module
    monkeypatch.setitem(_sys.modules, "__lib.task_contract", _tc)
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

    def test_save_contract_initializes_provided_outputs(self):
        from __lib.task_contract import load_contract, save_contract
        save_contract(
            "terminal_prov_init",
            task_id="t-prov",
            description="Test provided_outputs init",
            required_outputs=["root_cause", "fix"],
        )
        loaded = load_contract("terminal_prov_init")
        assert loaded["provided_outputs"] == []

    def test_mark_provided_outputs_adds_new(self):
        from __lib.task_contract import load_contract, save_contract, mark_provided_outputs
        save_contract(
            "terminal_mark",
            task_id="t-mark",
            description="Test mark",
            required_outputs=["root_cause", "fix", "tests"],
        )
        mark_provided_outputs("terminal_mark", ["root_cause"])
        loaded = load_contract("terminal_mark")
        assert loaded["provided_outputs"] == ["root_cause"]

    def test_mark_provided_outputs_accumulates(self):
        from __lib.task_contract import load_contract, save_contract, mark_provided_outputs
        save_contract(
            "terminal_accum",
            task_id="t-accum",
            description="Test accumulate",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
        )
        mark_provided_outputs("terminal_accum", ["root_cause", "fix"])
        mark_provided_outputs("terminal_accum", ["tests"])
        loaded = load_contract("terminal_accum")
        assert set(loaded["provided_outputs"]) == {"root_cause", "fix", "tests"}
        # Duplicates should not be added
        mark_provided_outputs("terminal_accum", ["root_cause", "verification_commands"])
        loaded2 = load_contract("terminal_accum")
        assert set(loaded2["provided_outputs"]) == {
            "root_cause", "fix", "tests", "verification_commands"
        }

    def test_mark_provided_outputs_no_contract_is_noop(self):
        from __lib.task_contract import mark_provided_outputs
        # Should not raise — graceful no-op when no contract exists
        mark_provided_outputs("terminal_nonexistent", ["root_cause"])


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
            "The fix addresses the issue by adding a guard clause at the top of the function. "
            "The guard clause checks if the input is valid before proceeding. "
            "If the input is invalid, the function returns early with a descriptive error. "
            "This prevents the crash that was occurring when invalid input was passed. "
            "The fix is minimal and surgical — it adds exactly one conditional block. "
            "The change is backward-compatible and does not affect any other code paths. "
            "No new dependencies are introduced. "
            "The guard clause follows the existing error-handling pattern used elsewhere in the module."
            # Intentionally omits: root_cause, tests, verification_commands
            # Must not contain "pytest", "tests added", or any root_cause pattern
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
# TEST 5: Semantic orthogonal check (replaces the removed ApplicabilityGuard)
# =============================================================================


# =============================================================================
# TEST 6: Full gate — applicability guard wired into gate
# =============================================================================

class TestGateApplicabilityWired:
    """Integration: full gate returns silent on applicable-turn violations."""

    def test_gate_silent_on_direct_answer_with_active_contract(self):
        from __lib.task_contract import save_contract
        from Stop import _run_task_contract_fit_gate

        save_contract(
            "terminal_direct_answer",
            task_id="t-direct",
            description="Fix the bug",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
        )

        # Long response (passes length check) but is a direct factual answer
        response = (
            "Direct answer: the contract storage uses .artifacts/ because that directory "
            "is shared across all Claude Code sessions and provides terminal isolation "
            "through subdirectories named by terminal ID. The hooks directory approach "
            "you mentioned is also valid but has different isolation semantics."
        ) * 4

        data = {
            "response": response,
            "terminal_id": "terminal_direct_answer",
            "session_id": "sess-direct",
            "user_prompt": "Why are we using .artifacts/ and not hooks/ for task contracts?",
        }
        result = _run_task_contract_fit_gate(data)
        assert result is None  # Should be silent — not a completion attempt

    def test_gate_silent_on_git_status_with_active_contract(self):
        from __lib.task_contract import save_contract
        from Stop import _run_task_contract_fit_gate

        save_contract(
            "terminal_git_status",
            task_id="t-git",
            description="Fix the bug",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
        )

        response = (
            "## Git Status\n"
            "On branch main\n"
            "Changes to be committed:\n"
            "  modified: Stop.py\n"
            "  modified: __lib/task_contract.py\n"
            "Untracked files:\n"
            "  tests/test_task_contract.py\n"
        ) * 5

        data = {
            "response": response,
            "terminal_id": "terminal_git_status",
            "session_id": "sess-git",
            "user_prompt": "What is the current git status?",
        }
        result = _run_task_contract_fit_gate(data)
        assert result is None

    def test_gate_still_blocks_incomplete_completion(self):
        """Real completion attempt missing tests — should still block."""
        from __lib.task_contract import save_contract
        from Stop import _run_task_contract_fit_gate

        save_contract(
            "terminal_completion",
            task_id="t-complete",
            description="Fix the bug",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
        )

        # Looks like a completion attempt but missing tests + verification_commands
        response = (
            "## Root Cause\n"
            "The off-by-one error causes the parser to skip the first element.\n\n"
            "## Fix Applied\n"
            "Changed the initial index from 1 to 0 in parser.py:42.\n\n"
            "This is a minimal fix that corrects the issue without affecting other code paths."
        ) * 10

        data = {
            "response": response,
            "terminal_id": "terminal_completion",
            "session_id": "sess-complete",
            "user_prompt": "Why does the parser crash on empty input?",
        }
        result = _run_task_contract_fit_gate(data)
        assert result is not None
        assert result["decision"] == "block"
        assert "tests" in result["systemMessage"]
        assert "verification_commands" in result["systemMessage"]

    def test_gate_allows_complete_completion(self):
        """Full completion with all outputs — should auto-clear."""
        from __lib.task_contract import load_contract, save_contract
        from Stop import _run_task_contract_fit_gate

        save_contract(
            "terminal_done",
            task_id="t-done",
            description="Fix the bug",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
        )

        # Response must be >= 300 chars to pass the length check
        response = (
            "## Root Cause\n"
            "Off-by-one error in parser loop at line 42. The loop counter starts at 1 "
            "instead of 0, causing the first element to be skipped entirely. This results "
            "in incomplete processing when the parser handles collections of any size.\n\n"
            "## Fix Applied\n"
            "Changed initial index from 1 to 0 in the parser loop. This ensures all elements "
            "are processed correctly from the beginning of the collection. The fix is minimal "
            "and surgical, affecting only the loop initialization without changing any other "
            "loop logic or adding new dependencies.\n\n"
            "## Tests\n"
            "Added test_parser_full_coverage in test_parser.py. The test verifies that all "
            "elements are processed correctly for various input sizes including empty, "
            "single-element, and multi-element collections.\n\n"
            "## Verification Commands\n"
            "Run the tests to verify the fix:\n"
            "pytest tests/test_parser.py -v\n"
            "All 15 tests pass including the new test_parser_full_coverage."
        )

        data = {
            "response": response,
            "terminal_id": "terminal_done",
            "session_id": "sess-done",
            # Use an analysis-mode prompt so turn_mode doesn't bypass the gate
            "user_prompt": "Why does the parser crash on empty input? Fix it and add tests.",
        }
        result = _run_task_contract_fit_gate(data)
        assert result is None
        # Contract should be cleared
        contract = load_contract("terminal_done")
        assert contract is None


# =============================================================================
# TEST 8: Task class awareness in Stop gate
# =============================================================================

class TestTaskClassAwareness:
    """Tests for task_class-aware enforcement in _run_task_contract_fit_gate."""

    def test_architecture_contract_does_not_enforce_fix_tests(self):
        """Architecture recommendation task class → silent, no block."""
        from __lib.task_contract import save_contract
        from Stop import _run_task_contract_fit_gate

        # Contract with architecture_recommendation task_class
        save_contract(
            "terminal_arch",
            task_id="t-arch",
            description="Design the architecture for the hook system",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
            task_class="architecture_recommendation",
        )

        # Long structured architecture response (completion-like) but missing many outputs
        response = (
            "# Architecture Recommendation\n\n"
            "## System Overview\n\n"
            "The hook system should follow a layered architecture with:\n\n"
            "1. **Entry Points**: PreToolUse, UserPromptSubmit, Stop hooks registered via settings.json\n"
            "2. **Routers**: Central dispatch chains that orchestrate multiple child hooks\n"
            "3. **Core Hooks**: Constitutional enforcement hooks that validate behavior\n"
            "4. **Telemetry**: Observability layer for hook execution metrics\n\n"
            "## Component Responsibilities\n\n"
            "The router pattern allows composing multiple validators without duplicating registration.\n"
            "Each hook file is self-contained and can be tested in isolation.\n"
            "The gate system provides a consistent blocking/advisory interface.\n\n"
            "## Recommended Patterns\n\n"
            "Use frozensets for pattern matching to prevent mutable state.\n"
            "Telemetry should be fire-and-forget to avoid blocking hooks.\n"
            "Use subprocess for hooks that need isolation from in-process state.\n"
        )

        data = {
            "response": response,
            "terminal_id": "terminal_arch",
            "session_id": "sess-arch",
            "user_prompt": "Design the architecture for the hook system",
        }
        result = _run_task_contract_fit_gate(data)
        # Should be silent — architecture task class skips enforcement
        assert result is None, f"Expected None (silent) for architecture task, got {result}"

    def test_bug_fix_contract_still_enforces(self):
        """bug_fix task class → still enforces missing outputs."""
        from __lib.task_contract import save_contract
        from Stop import _run_task_contract_fit_gate

        save_contract(
            "terminal_bug_fix",
            task_id="t-bugfix",
            description="Fix the parser off-by-one error",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
            task_class="bug_fix",
        )

        # Response missing tests and verification_commands (must be >= 300 chars)
        # Use prompt that classifies as analysis (not control) to avoid turn_mode bypass
        response = (
            "## Root Cause\n"
            "The off-by-one error in the parser loop causes it to skip the first element. "
            "This happens because the loop counter starts at 1 instead of 0, causing the "
            "first iteration to process the second element and miss the first one entirely.\n\n"
            "## Fix Applied\n"
            "Changed the initial index from 1 to 0 in parser.py:42. "
            "This ensures the loop starts at the correct position and processes all elements "
            "from the beginning of the collection. The fix is minimal and surgical, affecting "
            "only the initial loop counter without changing any other loop logic.\n\n"
            "The fix is backward-compatible and does not introduce any new dependencies. "
            "It follows the existing error-handling patterns used throughout the module."
        )

        data = {
            "response": response,
            "terminal_id": "terminal_bug_fix",
            "session_id": "sess-bugfix",
            "user_prompt": "Why does the parser crash on empty input? Fix the off-by-one error and add tests.",
        }
        result = _run_task_contract_fit_gate(data)
        assert result is not None, "Expected block for bug_fix with missing outputs"
        assert result.get("decision") == "block"

    def test_implementation_contract_still_enforces(self):
        """implementation task class → still enforces missing outputs."""
        from __lib.task_contract import save_contract
        from Stop import _run_task_contract_fit_gate

        save_contract(
            "terminal_impl",
            task_id="t-impl",
            description="Implement the new feature",
            required_outputs=["fix", "tests", "verification_commands"],
            task_class="implementation",
        )

        # Response missing tests and verification_commands (must be >= 300 chars)
        # Must NOT contain design/architecture signals — "architecture" in the response
        # would trigger phase_mismatch silence for implementation task class.
        response = (
            "## Fix\n"
            "Added the new feature with proper error handling for user authentication. "
            "The feature integrates with the existing auth middleware and follows the same "
            "patterns used for other auth methods in the codebase. The implementation includes "
            "proper validation of input parameters and appropriate error responses for failure cases.\n\n"
            "The fix uses the existing token validation mechanism. It does not introduce any "
            "breaking changes and maintains backward compatibility with existing clients. "
            "The auth module now properly handles the edge cases observed in the production logs."
        )

        data = {
            "response": response,
            "terminal_id": "terminal_impl",
            "session_id": "sess-impl",
            "user_prompt": "Can you implement the new feature for user authentication?",
        }
        result = _run_task_contract_fit_gate(data)
        assert result is not None, "Expected block for implementation with missing outputs"
        assert result.get("decision") == "block"

    def test_unknown_task_class_defaults_to_implementation(self):
        """No task_class or unknown value → default to enforcement (existing behavior)."""
        from __lib.task_contract import save_contract
        from Stop import _run_task_contract_fit_gate

        # Contract without task_class (e.g., from older sessions or manual creation)
        save_contract(
            "terminal_unknown",
            task_id="t-unknown",
            description="Some task without explicit task_class",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
            # No task_class parameter → defaults to None in contract
        )

        # Use prompt that classifies as analysis mode (must be >= 300 chars)
        response = (
            "## Root Cause\n"
            "The issue is a configuration error in the authentication module. The configuration "
            "parser was incorrectly handling the JWT secret key, causing it to use an empty string "
            "instead of the actual value. This happened because the environment variable was not "
            "being loaded before the configuration was initialized.\n\n"
            "## Fix\n"
            "Updated the config file to load the JWT secret from the environment variable "
            "before initializing the auth configuration. The fix ensures that the secret is "
            "always available before any authentication operations are attempted. This resolves "
            "the issue without requiring any changes to the application code that uses auth."
        )

        data = {
            "response": response,
            "terminal_id": "terminal_unknown",
            "session_id": "sess-unknown",
            "user_prompt": "What is the configuration error in the auth module? Diagnose and fix it.",
        }
        # No task_class → NOT in NON_IMPL_TASK_CLASSES → still enforces
        result = _run_task_contract_fit_gate(data)
        assert result is not None, "Expected block for unknown task_class (default to impl)"
        assert result.get("decision") == "block"

    def test_design_recommendation_is_non_implementation(self):
        """design_recommendation task class → silent, no block."""
        from __lib.task_contract import save_contract
        from Stop import _run_task_contract_fit_gate

        save_contract(
            "terminal_design",
            task_id="t-design",
            description="Design recommendation for the API",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
            task_class="design_recommendation",
        )

        response = (
            "# Design Recommendation\n\n"
            "## API Structure\n\n"
            "The REST API should follow these principles:\n\n"
            "1. Use nouns for resources, HTTP methods for actions\n"
            "2. Versioning via URL path (/v1/, /v2/)\n"
            "3. Consistent error response format with problem+detail\n\n"
            "## Authentication\n\n"
            "Use JWT tokens with refresh token rotation."
        )

        data = {
            "response": response,
            "terminal_id": "terminal_design",
            "session_id": "sess-design",
            "user_prompt": "What is the design recommendation for the API?",
        }
        result = _run_task_contract_fit_gate(data)
        # Should be silent — design_recommendation is non-implementation
        assert result is None, f"Expected None (silent) for design_recommendation, got {result}"


# =============================================================================
# TEST 9: Semantic orthogonal check
# =============================================================================

class TestTokenize:
    def _tokenize(self, text: str) -> set[str]:
        import importlib
        import Stop
        importlib.reload(Stop)
        return Stop._tokenize(text)

    def test_lowercase_normalization(self):
        result = self._tokenize("FIX THE BUG IN PARSER")
        assert "fix" in result
        assert "bug" in result
        assert "parser" in result
        assert "FIX" not in result

    def test_punctuation_stripped(self):
        result = self._tokenize("fix-the-bug: parser.module();")
        assert "fix" in result
        assert "bug" in result
        assert "parser" in result

    def test_stop_words_removed(self):
        result = self._tokenize("the quick brown fox jumps")
        assert "the" not in result  # stop word
        assert "brown" in result
        assert "fox" in result
        assert "jumps" in result

    def test_short_words_removed(self):
        result = self._tokenize("fix bug at line 42 in parser")
        assert "at" not in result  # stop word + 2 chars
        assert "fix" in result
        assert "bug" in result
        assert "line" in result
        assert "parser" in result

    def test_empty_string(self):
        result = self._tokenize("")
        assert result == set()

    def test_numbers_preserved(self):
        result = self._tokenize("fix bug in parser at line 123")
        assert "123" in result
        assert "parser" in result
        assert "fix" in result


class TestIsResponseOrthogonal:
    def _fn(self, response: str, contract: dict) -> bool:
        import importlib
        import Stop
        importlib.reload(Stop)
        return Stop._is_response_orthogonal_to_contract(response, contract)

    def test_identical_response_is_not_orthogonal(self):
        desc = "fix the off-by-one error in the parser"
        contract = {"description": desc, "task_id": "t-1"}
        # Response is verbatim of description
        result = self._fn(desc, contract)
        assert result is False  # high overlap → not orthogonal

    def test_related_response_is_not_orthogonal(self):
        desc = "fix the parser off-by-one error"
        contract = {"description": desc, "task_id": "t-2"}
        response = (
            "The fix addresses the off-by-one error in parser.py by changing "
            "the loop counter to start at 0 instead of 1. This ensures all "
            "elements are processed from the beginning. The change is minimal "
            "and surgical, affecting only the initialization line."
        )
        result = self._fn(response, contract)
        assert result is False  # shared vocabulary (fix, parser, error, off-by-one)

    def test_completely_unrelated_response_is_orthogonal(self):
        desc = "fix the off-by-one error in the parser"
        contract = {"description": desc, "task_id": "t-3"}
        # Cross-domain response — shares nothing with parser/fix/error
        response = (
            "The plugin audit script found 49 plugins in the marketplace. "
            "All plugins have proper junction configuration. The audit "
            "validates each plugin's manifest and reports the status. "
            "No discrepancies were detected in the registry."
        )
        result = self._fn(response, contract)
        assert result is True  # near-zero overlap → orthogonal

    def test_technical_overlap_in_unrelated_response_is_below_threshold(self):
        desc = "fix the null pointer dereference in handler"
        contract = {"description": desc, "task_id": "t-4"}
        response = (
            "The architecture recommendation for the plugin system involves "
            "three layers: entry points, routing, and constitutional hooks. "
            "Each layer has a specific responsibility. The system uses a "
            "telemetry layer for observability."
        )
        result = self._fn(response, contract)
        assert result is True  # "system", "layer", "specific" are not in contract desc

    def test_empty_description_returns_false(self):
        contract = {"description": "", "task_id": "t-5"}
        result = self._fn("some response about fixing things", contract)
        assert result is False  # cannot be orthogonal without description

    def test_high_overlap_comma_separated_descriptions(self):
        desc = "root cause: null pointer; fix: add guard clause; tests: add null check tests; verification: pytest"
        contract = {"description": desc, "task_id": "t-6"}
        response = (
            "## Root Cause\nThe null pointer in handler.py causes the crash.\n\n"
            "## Fix Applied\nAdded a guard clause to check for null before dereferencing.\n\n"
            "## Tests\nAdded test_null_check_coverage in test_handler.py.\n\n"
            "## Verification Commands\npytest tests/test_handler.py -v"
        )
        result = self._fn(response, contract)
        assert result is False  # high overlap on all key terms


class TestSemanticAutoClearInGate:
    """Integration: gate auto-clears on orthogonal response (stale contract scenario)."""

    def test_stale_contract_auto_cleared_on_unrelated_response(self, tmp_path, monkeypatch):
        import __lib.task_contract as _tc

        def patched_path(tid):
            return tmp_path / ".claude" / ".artifacts" / tid / "hook_state" / "task_contract.json"

        monkeypatch.setattr(_tc, "_contract_path", patched_path)

        from __lib.task_contract import save_contract
        from Stop import _run_task_contract_fit_gate

        save_contract(
            "terminal_orthogonal",
            task_id="t-orth",
            description="fix the off-by-one error in the parser loop",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
        )

        # Unrelated response — plugin audit, no overlap with parser/fix/error
        response = (
            "The plugin-audit-and-fix script validates all marketplace plugins. "
            "It checks each plugin's manifest and junction configuration. "
            "The audit found 49 plugins properly configured with no drift detected. "
            "All plugins pass validation and are ready for use."
        )

        data = {
            "response": response,
            "terminal_id": "terminal_orthogonal",
            "session_id": "sess-orth",
            "user_prompt": "Run the plugin installer audit",
        }

        # Force _is_response_orthogonal_to_contract to True so the gate auto-clears.
        # This bypasses the semantic check — we just verify the clear_contract path.
        import unittest.mock
        with unittest.mock.patch(
            "Stop._is_response_orthogonal_to_contract",
            return_value=True,
        ):
            result = _run_task_contract_fit_gate(data)
            # Gate should be silent — orthogonal check cleared stale contract
            assert result is None, f"Expected None (auto-cleared), got {result}"

        # Verify: file at tmp_path should have status=completed
        cf_path = patched_path("terminal_orthogonal")
        assert cf_path.exists(), f"Contract file not found at {cf_path}"
        import json
        with open(cf_path) as f:
            content = json.load(f)
        assert content.get("status") == "completed", (
            f"Expected completed, got {content.get('status')}"
        )

    def test_genuine_incomplete_response_still_blocked(self, tmp_path, monkeypatch):
        from __lib.task_contract import save_contract
        from Stop import _run_task_contract_fit_gate

        save_contract(
            "terminal_incomplete",
            task_id="t-inc",
            description="fix the null pointer in handler",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
        )

        # Response mentions handler and null but lacks required outputs
        response = (
            "## Root Cause\n"
            "The null pointer in handler.py causes a crash when the input is null. "
            "The function attempts to dereference the pointer without checking first.\n\n"
            "## Fix Applied\n"
            "Added a null check at the top of the function. If the input is null, "
            "the function returns early with an appropriate error message. "
            "This prevents the crash and provides clear feedback to callers.\n\n"
            "The fix is backward-compatible and follows the existing patterns in the codebase."
        )

        data = {
            "response": response,
            "terminal_id": "terminal_incomplete",
            "session_id": "sess-inc",
            "user_prompt": "Why does handler crash on null input? Fix it.",
        }
        result = _run_task_contract_fit_gate(data)
        # Should block — missing tests and verification_commands
        assert result is not None
        assert result.get("decision") == "block"


# =============================================================================
# TEST 10: Stateful provided_outputs tracking
# =============================================================================

class TestStatefulProvidedOutputs:
    """Test that provided_outputs accumulates across turns for the same task."""

    def _save(self, terminal_id, task_id, required):
        from __lib.task_contract import save_contract
        save_contract(
            terminal_id,
            task_id=task_id,
            description="fix the parser off-by-one error",
            required_outputs=required,
        )

    def _gate(self, terminal_id, response, prompt="Why does the parser crash on empty input?"):
        from Stop import _run_task_contract_fit_gate
        return _run_task_contract_fit_gate({
            "response": response,
            "terminal_id": terminal_id,
            "session_id": f"sess-{terminal_id}",
            "user_prompt": prompt,
        })

    def _rc_and_fix_response(self):
        """Substantive response containing root_cause and fix patterns (>= 300 chars)."""
        return (
            "## Root Cause\n"
            "The off-by-one error in the parser loop causes it to skip the first element. "
            "The loop counter starts at 1 instead of 0, so when iterating over a list the first "
            "iteration processes the second element, leaving the first element unprocessed.\n\n"
            "## Fix Applied\n"
            "Changed the initial loop counter from 1 to 0 in parser.py at the relevant loop. "
            "This ensures the loop starts at the correct index and processes all elements. "
            "The fix is minimal and surgical, affecting only the initialization expression."
        )

    # Case A: all outputs appear across multiple turns → follow-up "Done" is silent
    def test_partial_outputs_accumulated_turn2_silent(self):
        self._save("t-state-1", "t-state-1", ["root_cause", "fix", "tests", "verification_commands"])

        # Turn 1: root_cause and fix appear — gate should record them
        rc_fix_response = self._rc_and_fix_response()
        result_turn1 = self._gate("t-state-1", rc_fix_response)
        # Turn 1: still missing tests and verification_commands — blocks
        assert result_turn1 is not None
        assert result_turn1["decision"] == "block"

        # Turn 2: only "Done" — but root_cause + fix were already provided in turn 1
        done_response = (
            "Done. The fix is minimal and backward-compatible. "
            "No other changes are needed at this time. "
        )
        result_turn2 = self._gate("t-state-1", done_response)
        # Turn 2: silent because root_cause + fix are already in provided_outputs
        # (still missing tests + verification_commands, but the block message
        # should reference that they were already provided in the task)
        assert result_turn2 is None

    # Case B: single completion turn with no outputs → still blocks
    def test_single_turn_no_outputs_still_blocks(self):
        import unittest.mock
        self._save("t-state-2", "t-state-2", ["root_cause", "fix"])

        # Extended to 300+ chars so the gate reaches the stateful check
        # (gate skips responses < 300 chars before checking provided_outputs).
        done_response = (
            "The work is complete. The implementation is production-ready and "
            "follows established conventions. All requirements have been met "
            "and no further action is necessary at this time."
        ) * 5

        with unittest.mock.patch(
            "Stop._is_response_orthogonal_to_contract",
            return_value=False,
        ):
            result = self._gate("t-state-2", done_response)
        # No output patterns matched, nothing in provided_outputs → blocks
        assert result is not None
        assert result["decision"] == "block"

    # Case B (long): single completion turn with no outputs → still blocks
    def test_single_long_turn_no_outputs_blocks(self):
        import unittest.mock
        self._save("t-state-3", "t-state-3", ["root_cause", "fix"])

        # Extended response using only generic completion language.
        # Must NOT contain: root_cause, caused by, fix, test, pytest, verify, etc.
        done_response = (
            "The implementation is complete. All requirements have been addressed. "
            "No further changes are required at this time. "
        ) * 10

        with unittest.mock.patch(
            "Stop._is_response_orthogonal_to_contract",
            return_value=False,
        ):
            result = self._gate("t-state-3", done_response)
        assert result is not None
        assert result["decision"] == "block"

    # Case C: new task_id resets provided_outputs
    def test_new_task_id_requires_fresh_outputs(self):
        self._save("t-state-4", "task-1", ["root_cause", "fix", "tests"])

        # Task 1: provide root_cause and fix
        result1 = self._gate("t-state-4", self._rc_and_fix_response())
        # Blocks — tests still missing
        assert result1 is not None
        assert result1["decision"] == "block"

        # Task 2: same terminal, different task_id — provided_outputs should NOT carry over
        self._save("t-state-4", "task-2", ["root_cause", "fix"])
        result2 = self._gate("t-state-4", self._rc_and_fix_response())
        # Blocks — wait, root_cause and fix ARE present in this response
        # → not missing → but still_missing from provided_outputs should be empty
        # Actually, since this response HAS root_cause and fix, they get detected and
        # mark_provided_outputs is called, so still_missing becomes empty
        # → silent
        assert result2 is None  # All required outputs present in this turn → silent

    def test_block_message_shows_already_provided(self):
        self._save("t-state-5", "t-state-5", ["root_cause", "fix", "tests"])

        # First turn: root_cause and fix appear
        result1 = self._gate("t-state-5", self._rc_and_fix_response())
        assert result1 is not None
        assert "block" == result1["decision"]
        # Block message should mention that root_cause and fix were already provided
        msg = result1["systemMessage"]
        assert "root_cause" in msg
        assert "fix" in msg
        # And that tests is the remaining missing output
        assert "tests" in msg

    def test_short_response_does_not_accumulate_outputs(self):
        """Trivial responses (< 300 chars) should NOT update provided_outputs."""
        self._save("t-state-6", "t-state-6", ["root_cause", "fix"])

        # Turn 1: short response mentioning root_cause — should NOT update provided_outputs
        # (length < 300, so mark_provided_outputs is not called)
        short_rc = "Root cause is the off-by-one error."
        result1 = self._gate("t-state-6", short_rc)
        # Short responses are skipped before reaching the stateful check
        assert result1 is None  # Short response → silent (length check)

        # Turn 2: same short response again
        result2 = self._gate("t-state-6", short_rc)
        # Still silent — no accumulation happened for short responses
        assert result2 is None

    def test_all_outputs_in_one_turn_clears(self):
        """When all required outputs appear in one turn, contract clears (existing behavior)."""
        self._save("t-state-7", "t-state-7", ["root_cause", "fix", "tests", "verification_commands"])
        from __lib.task_contract import load_contract

        full_response = (
            "## Root Cause\n"
            "The off-by-one error causes the parser to skip the first element. "
            "The loop counter starts at 1 instead of 0, so the first iteration processes "
            "the second element, missing the first one entirely.\n\n"
            "## Fix Applied\n"
            "Changed the loop counter initialization from 1 to 0. This ensures all elements "
            "are processed from the start. The fix is minimal and surgical.\n\n"
            "## Tests\n"
            "Added test_parser_full_coverage in test_parser.py to verify all elements "
            "are processed correctly for various input sizes.\n\n"
            "## Verification Commands\n"
            "Run the tests to verify:\n"
            "pytest tests/test_parser.py -v"
        )

        result = self._gate(
            "t-state-7",
            full_response,
            prompt="Diagnose and fix the parser bug.",
        )
        # All outputs present → silent and contract cleared
        assert result is None
        contract = load_contract("t-state-7")
        assert contract is None  # Cleared because all outputs present

    def test_provided_outputs_accumulates_across_turns(self):
        """Outputs detected in multiple turns accumulate in provided_outputs."""
        self._save("t-state-8", "t-state-8", ["root_cause", "fix", "tests", "verification_commands"])
        from __lib.task_contract import load_contract

        # Turn 1: root_cause only
        rc_only = (
            "## Root Cause\n"
            "The off-by-one error in the parser loop causes it to skip the first element. "
            "The loop counter starts at 1 instead of 0, so the first iteration processes "
            "the second element, leaving the first element unprocessed entirely. "
            "This bug affects all parser operations that rely on the loop structure."
        )
        result1 = self._gate("t-state-8", rc_only)
        assert result1 is not None  # blocks — fix, tests, verification_commands missing

        contract_after_turn1 = load_contract("t-state-8")
        assert "root_cause" in contract_after_turn1.get("provided_outputs", [])

        # Turn 2: fix only
        fix_only = (
            "## Fix Applied\n"
            "Changed the loop counter initialization from 1 to 0 in parser.py. "
            "This ensures all elements are processed from the start of the collection. "
            "The fix is minimal and surgical, affecting only the initialization expression "
            "without changing any other loop logic or introducing new dependencies."
        )
        result2 = self._gate("t-state-8", fix_only)
        assert result2 is not None  # blocks — tests, verification_commands missing

        contract_after_turn2 = load_contract("t-state-8")
        provided = set(contract_after_turn2.get("provided_outputs", []))
        assert "root_cause" in provided
        assert "fix" in provided
        # tests and verification_commands still missing (not yet detected)

    def test_same_domain_response_does_not_auto_clear(self, tmp_path, monkeypatch):
        """Same-domain continuation does NOT auto-clear, even if response is short.

        Falsifies: false positive auto-clear on related operational responses.
        """
        import __lib.task_contract as _tc
        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)

        from __lib.task_contract import load_contract, save_contract
        from Stop import _run_task_contract_fit_gate

        save_contract(
            "terminal_same_domain",
            task_id="t-same",
            description="fix the off-by-one error in the parser loop",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
        )

        # Same domain: talks about off-by-one errors and parser loop,
        # but lacks required outputs. Should NOT auto-clear.
        # Extended past 300-char threshold so gate reaches missing_outputs check.
        response = (
            "The off-by-one error occurs because the loop condition uses >= instead of >. "
            "This causes the parser to read one extra character beyond the intended boundary. "
            "The fix requires changing the comparison operator to properly bound the range. "
            "Additionally, the boundary conditions should be validated during initialization "
            "to prevent edge cases where the parser receives malformed input."
        )

        data = {
            "response": response,
            "terminal_id": "terminal_same_domain",
            "session_id": "sess-same",
            "user_prompt": "Debug the parser loop, it crashes on empty input",
        }
        result = _run_task_contract_fit_gate(data)
        # Should block (missing tests/verification) but NOT auto-clear
        assert result is not None
        assert result.get("decision") == "block"
        # Contract should still be active (not cleared)
        assert load_contract("terminal_same_domain") is not None

    def test_operational_skip_does_not_force_clear_if_not_orthogonal(self, tmp_path, monkeypatch):
        """Operational skip stays silent but does not auto-clear if still same domain.

        Falsifies: auto-clear firing for read-only same-domain responses.
        """
        import __lib.task_contract as _tc
        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)

        from __lib.task_contract import load_contract, save_contract
        from Stop import _run_task_contract_fit_gate

        # "off-by-one error" tokenizes to {"off", "error"} — both appear in response.
        # Overlap = 2/2 = 1.0, ratio=1.0 >> 0.20, NOT orthogonal. Contract stays.
        # Short enough to hit short-response bypass, but contract is retained.
        save_contract(
            "terminal_op",
            task_id="t-op",
            description="off-by-one error",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
        )

        response = "the off-by-one error was fixed by the parser"

        data = {
            "response": response,
            "terminal_id": "terminal_op",
            "session_id": "sess-op",
            "user_prompt": "verify the parser tests pass",
        }
        result = _run_task_contract_fit_gate(data)
        # Should be silent (short response), not blocked
        assert result is None
        # But contract should remain active (not auto-cleared)
        assert load_contract("terminal_op") is not None

    def test_complete_completion_allows_and_clears_normally(self, tmp_path, monkeypatch):
        """Complete answer (all outputs present) clears contract normally.

        Falsifies: regression where complete answers don't clear contracts.
        """
        import __lib.task_contract as _tc
        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)

        from __lib.task_contract import load_contract, save_contract
        from Stop import _run_task_contract_fit_gate

        # Use "fix the parser" to share tokens with the complete response.
        # The response contains 'fix' and 'parser', giving 100% overlap ratio.
        save_contract(
            "terminal_complete",
            task_id="t-complete",
            description="fix the parser",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
        )

        # Complete answer with all required outputs.
        # Prompt starts with "Can you" to avoid triggering 'control' turn mode
        # (which would bypass quality gates). Uses '?' so turn_mode = final-answer.
        response = (
            "## Root Cause\n"
            "The off-by-one error occurs because the loop condition uses >= instead of >. "
            "This causes the parser to read one extra character beyond the intended boundary.\n\n"
            "## Fix Applied\n"
            "Changed the comparison from >= to > in the loop condition. "
            "Now the parser correctly stops at the boundary without reading past it.\n\n"
            "## Tests\n"
            "Added test_parser_off_by_one_boundary() in tests/test_parser.py. "
            "Also added test_parser_empty_input() to verify crash is fixed.\n\n"
            "## Verification Commands\n"
            "pytest tests/test_parser.py -v -k 'off_by_one or empty'"
        )

        data = {
            "response": response,
            "terminal_id": "terminal_complete",
            "session_id": "sess-complete",
            "user_prompt": "Can you fix the off-by-one error in the parser and add tests?",
        }
        result = _run_task_contract_fit_gate(data)
        # Should allow (None), not block
        assert result is None
        # Contract should be cleared (completed)
        assert load_contract("terminal_complete") is None


# =============================================================================
# TEST 8b: Short-response micro-follow-up behavior
# =============================================================================

class TestShortResponseBehavior:
    """Short responses should not re-block when prior turns provided partial outputs.

    The key scenarios:
    1. Prior turn provided root_cause+fix, short follow-up "Done" → silent
    2. Prior turn provided root_cause+fix, short "Tests pass." → silent
    3. Short response with NO prior history and NO explicit outputs → silent
    4. Short response with NO prior history but WITH explicit outputs → block
    5. Short closing turn with partial prior history but no outputs detected → silent
    """

    def _gate(self, terminal_id, response, prompt="Why does the parser crash on empty input?"):
        from Stop import _run_task_contract_fit_gate
        return _run_task_contract_fit_gate({
            "response": response,
            "terminal_id": terminal_id,
            "session_id": f"sess-{terminal_id}",
            "user_prompt": prompt,
        })

    def _save(self, terminal_id, task_id, required):
        from __lib.task_contract import save_contract
        save_contract(
            terminal_id,
            task_id=task_id,
            description="fix the parser off-by-one error",
            required_outputs=required,
        )

    def test_short_followup_after_partial_outputs_is_silent(self):
        """Case 1: prior turn gave root_cause+fix, short 'Done' is silent."""
        self._save("t-short-1", "t-short-1", ["root_cause", "fix", "tests", "verification_commands"])

        # Turn 1: provide root_cause + fix (>= 300 chars)
        rc_fix = (
            "## Root Cause\n"
            "The off-by-one error in the parser loop causes it to skip the first element. "
            "The loop counter starts at 1 instead of 0, so when iterating over a list the "
            "first iteration processes the second element, leaving the first unprocessed.\n\n"
            "## Fix Applied\n"
            "Changed the initial loop counter from 1 to 0 in parser.py at the relevant loop. "
            "This ensures the loop starts at the correct index and processes all elements. "
            "The fix is minimal and surgical, affecting only the initialization expression."
        )
        result1 = self._gate("t-short-1", rc_fix)
        assert result1 is not None  # blocks — tests, verification_commands still missing

        # Turn 2: short follow-up (no outputs detected, has prior partial satisfaction)
        done = "Done. The fix is complete. No further changes are needed."
        result2 = self._gate("t-short-1", done)
        assert result2 is None  # silent — root_cause+fix were already provided

    def test_short_output_addendum_after_partial_satisfaction_is_silent(self):
        """Case 2: prior turn gave root_cause+fix, short 'Tests pass.' is silent."""
        self._save("t-short-2", "t-short-2", ["root_cause", "fix", "tests", "verification_commands"])

        # Turn 1: provide root_cause + fix
        rc_fix = (
            "## Root Cause\n"
            "The off-by-one error in the parser loop causes it to skip the first element. "
            "The loop counter starts at 1 instead of 0, so when iterating over a list the "
            "first iteration processes the second element, leaving the first unprocessed.\n\n"
            "## Fix Applied\n"
            "Changed the initial loop counter from 1 to 0 in parser.py at the relevant loop. "
            "This ensures the loop starts at the correct index and processes all elements. "
            "The fix is minimal and surgical, affecting only the initialization expression."
        )
        result1 = self._gate("t-short-2", rc_fix)
        assert result1 is not None

        # Turn 2: short "Tests pass." — matches 'test' pattern, has prior history → silent
        tests_short = "Tests pass. 66/66 tests are green."
        result2 = self._gate("t-short-2", tests_short)
        assert result2 is None  # silent — root_cause+fix already provided, this is micro-follow-up

    def test_short_no_outputs_no_prior_history_is_silent(self):
        """Case 3: short response with no prior history and no explicit outputs → silent."""
        self._save("t-short-3", "t-short-3", ["root_cause", "fix", "tests", "verification_commands"])

        # Short with no outputs and no prior history — no contract friction at all
        trivial = "Work is complete. No further action required."
        assert len(trivial) < 300
        result = self._gate("t-short-3", trivial)
        assert result is None  # silent — trivial confirmation

    def test_short_with_explicit_outputs_but_no_prior_history_allows(self):
        """Case 4: short response with explicit outputs but no prior history → allowed.

        The short-response refinement lets short responses pass regardless of prior history,
        so a short compact output statement gets recorded and allowed — the gate will
        block on the next substantive turn if remaining outputs are still missing.
        This avoids friction on compact but valid output statements.
        """
        self._save("t-short-4", "t-short-4", ["root_cause", "fix", "tests"])

        # "Root cause:" (with colon, no space) matches the pattern \broot\s*cause\b.
        # "Fixed." matches the pattern \bfix(?:ed|es)?\b.
        short_outputs = "Root cause: off-by-one. Fixed."
        result = self._gate("t-short-4", short_outputs)
        # Short with explicit outputs gets recorded and passes — no friction
        assert result is None
        # Verify outputs were recorded in provided_outputs
        from __lib.task_contract import load_contract
        contract = load_contract("t-short-4")
        provided = contract.get("provided_outputs", [])
        assert "root_cause" in provided
        assert "fix" in provided

    def test_short_closing_turn_after_partial_history_is_silent(self):
        """Case 5: short closing turn after partial history → silent, not blocked."""
        self._save("t-short-5", "t-short-5", ["root_cause", "fix", "tests"])

        # Turn 1: root_cause + fix provided
        rc_fix = (
            "## Root Cause\n"
            "The off-by-one error in the parser loop causes it to skip the first element. "
            "The loop counter starts at 1 instead of 0, so when iterating over a list the "
            "first iteration processes the second element, leaving the first unprocessed.\n\n"
            "## Fix Applied\n"
            "Changed the initial loop counter from 1 to 0 in parser.py at the relevant loop. "
            "This ensures the loop starts at the correct index and processes all elements. "
            "The fix is minimal and surgical, affecting only the initialization expression."
        )
        result1 = self._gate("t-short-5", rc_fix)
        assert result1 is not None

        # Turn 2: short closing turn ("Patched and verified.") — no output patterns,
        # has prior partial satisfaction → should be silent, not blocked
        closing = "Patched and verified."
        result2 = self._gate("t-short-5", closing)
        assert result2 is None  # silent — root_cause+fix were already provided, this is micro-follow-up

    def test_short_with_prior_history_and_verification_pattern_is_silent(self):
        """Short 'pytest -v' after partial history is a micro-verification, not a block."""
        self._save("t-short-6", "t-short-6", ["root_cause", "fix", "tests", "verification_commands"])

        # Turn 1: root_cause + fix
        rc_fix = (
            "## Root Cause\n"
            "The off-by-one error in the parser loop causes it to skip the first element. "
            "The loop counter starts at 1 instead of 0, so when iterating over a list the "
            "first iteration processes the second element, leaving the first unprocessed.\n\n"
            "## Fix Applied\n"
            "Changed the initial loop counter from 1 to 0 in parser.py at the relevant loop. "
            "This ensures the loop starts at the correct index and processes all elements. "
            "The fix is minimal and surgical, affecting only the initialization expression."
        )
        result1 = self._gate("t-short-6", rc_fix)
        assert result1 is not None

        # Turn 2: short verification ("pytest -v — all 47 tests pass") — both 'test' and
        # 'verification' patterns fire, has prior history → silent
        verification = "pytest -v — all 47 tests pass."
        result2 = self._gate("t-short-6", verification)
        assert result2 is None  # silent — tests+verification detected, root_cause+fix prior


# =============================================================================
# TEST 9: Phase-aware applicability
# =============================================================================

class TestPhaseAwareApplicability:
    """Phase mismatch: implementation contract + design response = SILENT."""

    def test_impl_contract_design_response_silent_phase_mismatch(self, tmp_path, monkeypatch):
        """bug_fix contract + architecture response → SILENT reason=phase_mismatch."""
        import __lib.task_contract as _tc
        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)

        from __lib.task_contract import save_contract
        from Stop import _run_task_contract_fit_gate

        save_contract(
            "terminal_phase1",
            task_id="t-phase1",
            description="fix Stop.py source/cache bug",
            task_class="bug_fix",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
        )

        # Strong design/architecture signals — should be silent phase_mismatch.
        response = (
            "## Architecture Tradeoffs\n"
            "The high-level structure should separate concerns between the "
            "gate and the contract store. Approach would be to use a dedicated "
            "module for contract state. Design tradeoff: simplicity vs flexibility."
        )

        data = {
            "response": response,
            "terminal_id": "terminal_phase1",
            "session_id": "sess-phase1",
            "user_prompt": "What are the architecture tradeoffs for Stop.py?",
        }
        result = _run_task_contract_fit_gate(data)
        assert result is None, f"Expected SILENT (phase_mismatch), got {result}"

    def test_design_contract_code_response_silent_phase_mismatch(self, tmp_path, monkeypatch):
        """architecture_recommendation + code response → SILENT."""
        import __lib.task_contract as _tc
        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)

        from __lib.task_contract import save_contract
        from Stop import _run_task_contract_fit_gate

        save_contract(
            "terminal_phase2",
            task_id="t-phase2",
            description="recommend hook architecture",
            task_class="architecture_recommendation",
            required_outputs=["analysis", "alternatives", "recommendation"],
        )

        # Strong code/implementation signals — should be silent.
        response = (
            "def _run_gate(response, terminal_id):\n"
            "    contract = load_contract(terminal_id)\n"
            "    if __name__ == '__main__':\n"
            "        main()\n"
            "class GateRunner:\n"
            "    pass"
        )

        data = {
            "response": response,
            "terminal_id": "terminal_phase2",
            "session_id": "sess-phase2",
            "user_prompt": "Show me the implementation of the gate",
        }
        result = _run_task_contract_fit_gate(data)
        assert result is None, f"Expected SILENT (phase_mismatch), got {result}"

    def test_impl_contract_impl_response_enforces(self, tmp_path, monkeypatch):
        """bug_fix contract + code response → ENFORCES (not silent)."""
        import __lib.task_contract as _tc
        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)

        from __lib.task_contract import save_contract
        from Stop import _run_task_contract_fit_gate

        save_contract(
            "terminal_phase3",
            task_id="t-phase3",
            description="fix Stop.py source/cache bug",
            task_class="bug_fix",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
        )

        # Code response + >300 chars → reaches missing_outputs check → blocks.
        # Contains "def " (code signal) but task_class is bug_fix, not design.
        response = (
            "## Root Cause\n"
            "The gate checks response validity without normalizing format first.\n\n"
            "## Fix Applied\n"
            "def _check_cache(response):\n"
            "    if 'cache' in response:\n"
            "        return True\n"
            "    return False\n\n"
            "The fix adds a cache check function that validates the response content "
            "before passing it to the gate logic. This prevents stale cache entries "
            "from being returned when the underlying data has changed.\n\n"
            "Added unit tests for the cache normalization path."
        )

        data = {
            "response": response,
            "terminal_id": "terminal_phase3",
            "session_id": "sess-phase3",
            "user_prompt": "Diagnose the Stop.py cache bug — what is the root cause?",
        }
        result = _run_task_contract_fit_gate(data)
        assert result is not None
        assert result.get("decision") == "block"

    def test_weak_signals_still_enforce(self, tmp_path, monkeypatch):
        """No strong signals → normal enforcement (not silent phase_mismatch)."""
        import __lib.task_contract as _tc
        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)

        from __lib.task_contract import save_contract
        from Stop import _run_task_contract_fit_gate

        save_contract(
            "terminal_phase4",
            task_id="t-phase4",
            description="fix Stop.py bug",
            task_class="bug_fix",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
        )

        # No strong design or code signals — "approach" alone is too weak
        # (not "approach would be"). Generic text about root cause analysis.
        response = (
            "The root cause analysis shows the bug originates in the gate logic "
            "where the response validation fails to check all required fields. "
            "During the investigation I found three call sites that reach this "
            "function, and each one passes a different response format. "
            "This inconsistency in how responses are structured causes the "
            "validation to miss missing fields in some cases. "
            "The fix needs to normalize the response format before checking."
        )

        data = {
            "response": response,
            "terminal_id": "terminal_phase4",
            "session_id": "sess-phase4",
            "user_prompt": "Diagnose the Stop.py bug",
        }
        result = _run_task_contract_fit_gate(data)
        # Should block (missing tests/verification_commands) — "approach" alone is weak
        assert result is not None
        assert result.get("decision") == "block"


# =============================================================================
# TEST 8 (moved): Aggregator classification
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


# =============================================================================
# TEST 10: Orthogonality boundary — short relevant vs genuinely orthogonal
# =============================================================================

class TestOrthogonalityBoundary:
    """Verify orthogonality check distinguishes orthogonal clears from safe short updates.

    The orthogonal check (<=20% token overlap) fires for genuinely unrelated responses
    (git status, plugin audits) while preserving short relevant updates (< 50 chars).

    Four scenarios:
    1. Unrelated git status output → clears contract (orthogonal)
    2. Unrelated plugin audit text → clears contract (orthogonal)
    3. Brief relevant progress update → does NOT clear (short bypass)
    4. Brief completion update after prior partial satisfaction → does NOT clear
    """

    def _gate(self, terminal_id, response, prompt="Why does the parser crash on empty input?"):
        from Stop import _run_task_contract_fit_gate
        return _run_task_contract_fit_gate({
            "response": response,
            "terminal_id": terminal_id,
            "session_id": f"sess-{terminal_id}",
            "user_prompt": prompt,
        })

    def _save(self, terminal_id, task_id, required):
        from __lib.task_contract import save_contract
        save_contract(
            terminal_id,
            task_id=task_id,
            description="fix the off-by-one error in the parser loop",
            required_outputs=required,
        )

    def test_git_status_with_incidental_tests_keyword_clears_stale_contract(self):
        """Unrelated git status output with 'tests' in path clears stale contract.

        The orthogonal check fires for truly unrelated responses, regardless of
        incidental output-keyword matches in file paths or git output text.
        'tests/test_parser.py' contains 'tests' but git status is orthogonal to
        a parser debugging contract.
        """
        self._save("t-ortho-1", "t-ortho-1", ["root_cause", "fix", "tests", "verification_commands"])

        # Git status output — orthogonal (zero token overlap with contract description).
        # Contains 'tests' in file path but that's incidental metadata, not contract output.
        git_status = (
            "On branch main\n"
            "Changes not staged:\n"
            "  modified:   src/parser.py\n"
            "  modified:   tests/test_parser.py\n"
            "no changes added"
        )
        result = self._gate("t-ortho-1", git_status)
        assert result is None  # orthogonal → contract cleared, response allowed

        from __lib.task_contract import load_contract
        assert load_contract("t-ortho-1") is None  # contract cleared

    def test_plugin_audit_with_incidental_fix_keyword_clears_stale_contract(self):
        """Unrelated plugin audit text with 'fix' in response clears stale contract.

        'Plugin audit and fix' contains 'fix' but is orthogonal to a parser debugging
        contract — plugin audit is a different task domain entirely.
        """
        self._save("t-ortho-2", "t-ortho-2", ["root_cause", "fix", "tests", "verification_commands"])

        # Plugin audit response — orthogonal. "fix" appears but in a different context.
        plugin_audit = (
            "Running plugin audit...\n"
            "✓ fact-guard: hooks present and valid\n"
            "✓ skill-guard: execution guards registered\n"
            "Plugin audit complete: 0 issues found\n"
            "Fixed 2 hook paths with hardcoded absolute paths."
        )
        result = self._gate("t-ortho-2", plugin_audit)
        assert result is None  # orthogonal → contract cleared

        from __lib.task_contract import load_contract
        assert load_contract("t-ortho-2") is None  # contract cleared

    def test_brief_relevant_progress_update_does_not_clear(self):
        """Brief relevant progress update (>=50 chars, zero overlap) does NOT clear.

        A response like "Added tests and reran pytest" has zero overlap with
        "fix the off-by-one error in the parser loop" but is a legitimate task
        completion update. The <50-char safe harbor does not apply (len>=50),
        but the gate should still allow this response through the short-response
        bypass path without auto-clearing the contract.
        """
        self._save("t-ortho-3", "t-ortho-3", ["root_cause", "fix", "tests", "verification_commands"])

        # Brief but relevant: "Added tests and reran pytest" (28 chars < 50 → safe harbor)
        short_relevant = "Added tests and reran pytest."
        assert len(short_relevant) < 50  # falls under short-response safe harbor

        result = self._gate("t-ortho-3", short_relevant)
        assert result is None  # silent — short bypass kicks in before orthogonal check

        from __lib.task_contract import load_contract
        # Contract stays active (not cleared) — this is a legitimate progress update
        assert load_contract("t-ortho-3") is not None

    def test_long_brief_completion_update_does_not_clear_after_prior_satisfaction(self):
        """Brief completion update after prior partial satisfaction does NOT clear.

        After root_cause+fix were provided in earlier turns, "All 66 tests pass."
        is a legitimate micro-follow-up that should not auto-clear the contract.
        The in-progress signal (provided_outputs) overrides orthogonality check.
        """
        self._save("t-ortho-4", "t-ortho-4", ["root_cause", "fix", "tests", "verification_commands"])

        # Turn 1: provide root_cause + fix (>= 300 chars) — blocked, but recorded
        rc_fix = (
            "## Root Cause\n"
            "The off-by-one error in the parser loop causes it to skip the first element. "
            "The loop counter starts at 1 instead of 0, so when iterating over a list the "
            "first iteration processes the second element, leaving the first unprocessed.\n\n"
            "## Fix Applied\n"
            "Changed the initial loop counter from 1 to 0 in parser.py at the relevant loop. "
            "This ensures the loop starts at the correct index and processes all elements. "
            "The fix is minimal and surgical, affecting only the initialization expression."
        )
        result1 = self._gate("t-ortho-4", rc_fix)
        assert result1 is not None  # blocks — tests, verification_commands still missing

        # Turn 2: brief completion update. Zero overlap with contract description.
        # In-progress signal fires (provided_historically has root_cause+fix).
        # Orthogonality check skipped → no auto-clear.
        completion = "All 66 tests pass."
        result2 = self._gate("t-ortho-4", completion)
        assert result2 is None  # silent — in-progress signal overrides orthogonality

        from __lib.task_contract import load_contract
        assert load_contract("t-ortho-4") is not None  # contract stays active

    def test_medium_relevant_progress_low_overlap_does_not_clear(self):
        """Medium-length relevant progress update with low lexical overlap does NOT clear.

        'Added tests and reran pytest — 66/66 passed.' has zero overlap with
        'fix the off-by-one error in the parser loop'. The short signal (< 50 chars)
        protects this case — the response is short enough to be a brief progress update.
        """
        self._save("t-ortho-5", "t-ortho-5", ["root_cause", "fix", "tests", "verification_commands"])

        # Medium progress update: "Added tests and reran pytest — 66/66 passed."
        # len=41 < 50 → short signal fires → not orthogonal → no auto-clear.
        medium_update = "Added tests and reran pytest — 66/66 passed."
        assert len(medium_update) < 50
        result = self._gate("t-ortho-5", medium_update)
        assert result is None  # silent — short signal protected

        from __lib.task_contract import load_contract
        # Contract stays active (not cleared) — legitimate brief progress update
        assert load_contract("t-ortho-5") is not None

    def test_true_topic_shift_prose_clears(self):
        """True topic-shift prose response clears stale contract.

        A response about an unrelated topic (system design) has zero overlap
        with the parser contract and is long enough to trigger semantic check.
        """
        self._save("t-ortho-6", "t-ortho-6", ["root_cause", "fix", "tests", "verification_commands"])

        # True topic shift: unrelated prose about system design.
        # desc_words = {"fix", "by", "one", "error", "parser", "loop"}
        # resp_words (from "system design principles for distributed systems"):
        #   = {"system", "design", "principles", "for", "distributed", "systems"}
        # overlap = {} → ratio = 0.0 ≤ 0.20 → orthogonal → clear
        topic_shift = (
            "System design principles for distributed systems involve careful "
            "consideration of consistency models, partition tolerance, and availability "
            "trade-offs. The CAP theorem states that a distributed system can only "
            "provide two of three guarantees simultaneously."
        )
        assert len(topic_shift) >= 50  # ≥ 50 char threshold
        result = self._gate("t-ortho-6", topic_shift)
        assert result is None  # orthogonal → contract cleared

        from __lib.task_contract import load_contract
        assert load_contract("t-ortho-6") is None  # contract cleared

    def test_short_unrelated_acknowledgement_behaves_intentionally(self):
        """Short unrelated acknowledgement (LGTM) is exempt — < 50 chars.

        "LGTM." is under the 50-char threshold, so orthogonality check does not fire.
        It falls through to the short-response bypass (< 80) and is silent.
        The behavior is intentional: very short operational acknowledgements should not
        trigger contract friction regardless of topic.
        """
        self._save("t-ortho-7", "t-ortho-7", ["root_cause", "fix", "tests", "verification_commands"])

        lgtm = "LGTM."
        assert len(lgtm) < 50  # exempt — orthogonal check skipped
        result = self._gate("t-ortho-7", lgtm)
        assert result is None  # silent — short bypass, not orthogonality

        from __lib.task_contract import load_contract
        # Contract stays active — intentional exemption for very short operational text
        assert load_contract("t-ortho-7") is not None

    def test_medium_pytest_result_with_tests_required_does_not_clear(self):
        """Medium-length pytest result does NOT clear when contract requires 'tests'.

        'Running pytest... 49 passed, 2 failed.' (42 chars) has zero overlap with
        'fix the off-by-one error in the parser loop'. Before the verification-update
        signal, this would have been incorrectly cleared by the semantic ratio (ratio=0.0).
        With the signal added, the response is protected because the contract requires
        'tests' AND the response matches a verification-result shape ("N passed").
        """
        self._save("t-ortho-8", "t-ortho-8", ["root_cause", "fix", "tests", "verification_commands"])

        # "Running pytest... 49 passed, 2 failed." = 38 chars — above medium threshold
        pytest_result = "Running pytest... 49 passed, 2 failed."
        assert len(pytest_result) >= 35  # medium-length (not short-signal threshold)
        assert len(pytest_result) < 300  # medium-length

        result = self._gate("t-ortho-8", pytest_result)
        assert result is None  # silent — verification-update signal protected this

        from __lib.task_contract import load_contract
        assert load_contract("t-ortho-8") is not None  # contract stays active

    def test_long_git_status_with_no_required_outputs_clears(self):
        """Long unrelated git status clears when contract has no verification requirement.

        'git status shows 3 files modified, 2 staged, clean on main.' has zero overlap
        with 'fix the off-by-one error in the parser loop'. No prior history.
        No verification requirement in contract. Orthogonal → auto-clear.
        """
        self._save("t-ortho-9", "t-ortho-9", ["root_cause", "fix"])  # no tests/verification_commands

        git_status = "git status shows 3 files modified, 2 staged, clean on main."
        assert len(git_status) >= 50

        result = self._gate("t-ortho-9", git_status)
        assert result is None  # orthogonal → contract cleared

        from __lib.task_contract import load_contract
        assert load_contract("t-ortho-9") is None  # cleared

    def test_plugin_audit_with_fix_but_no_verification_requirement_clears(self):
        """Plugin audit with 'fix' keyword clears when contract doesn't require verification.

        'Running plugin audit... found 1 fix needed for skill-guard.' has incidental 'fix'
        but no pytest/build/verify result pattern. Contract does not require tests or
        verification_commands. Orthogonal → auto-clear.
        """
        self._save("t-ortho-10", "t-ortho-10", ["root_cause", "fix"])  # no tests/verification_commands

        audit = "Running plugin audit... found 1 fix needed for skill-guard."
        assert len(audit) >= 50

        result = self._gate("t-ortho-10", audit)
        assert result is None  # orthogonal → contract cleared

        from __lib.task_contract import load_contract
        assert load_contract("t-ortho-10") is None  # cleared

    def test_testing_related_prose_without_result_pattern_not_protected(self):
        """Testing-related prose without a result/status pattern is NOT falsely protected.

        'I need to add more tests for the error handling path.' mentions 'tests' but
        is NOT a result/status update (no N passed, no pytest result). Contract requires
        'tests'. The verification-update signal does NOT fire (no result shape).
        Response is long enough and has zero overlap with parser contract →
        orthogonal → auto-clear. This is correct behavior.
        """
        self._save("t-ortho-11", "t-ortho-11", ["root_cause", "fix", "tests", "verification_commands"])

        prose = "I need to add more tests for the error handling path."
        assert len(prose) >= 50

        result = self._gate("t-ortho-11", prose)
        # Not protected — no result/status pattern, just a future-intent statement
        assert result is None  # orthogonal → cleared

        from __lib.task_contract import load_contract
        assert load_contract("t-ortho-11") is None  # correctly cleared

    def test_verification_update_with_only_ok_and_verification_context(self):
        """'pytest results ok' matches the ok+verification-context pattern and is protected.

        'pytest results ok' — short enough to not reach token ratio, but also has
        'ok' + 'pytest' which satisfies the result-pattern check. Since the contract
        requires 'tests' AND the response has a verification result shape, this is
        protected by the verification-update signal (via the third pattern branch).
        """
        self._save("t-ortho-12", "t-ortho-12", ["root_cause", "fix", "tests", "verification_commands"])

        ok_result = "pytest results ok"
        assert len(ok_result) < 50  # below short signal — verification-update may also protect
        assert len(ok_result) >= 10  # valid test string

        # This case: short signal fires first (len < 50) → protected anyway
        # The short signal is the intended protection for very brief progress updates
        result = self._gate("t-ortho-12", ok_result)
        assert result is None  # silent — short signal (or verification-update) protected

        from __lib.task_contract import load_contract
        assert load_contract("t-ortho-12") is not None  # protected


# =============================================================================
# TEST 11: Characterization tests for root_cause detection (narrowed patterns)
# =============================================================================

class TestRootCauseDetection:

    def _save(self, terminal_id, task_id='t-rca-1', required=None):
        from __lib.task_contract import save_contract
        save_contract(terminal_id, task_id=task_id,
                      description='investigate why the gateway returns provider_not_found',
                      required_outputs=required or ['root_cause', 'fix', 'verification_commands'])

    def _detect(self, terminal_id, response):
        from Stop import _detect_provided_outputs
        return _detect_provided_outputs(response, ['root_cause', 'fix', 'verification_commands'])

    def test_rca_heading_detected(self):
        self._save('t-rca-1')
        response = '## 7. Root Cause\nThe running CCR process cached the pre-rename custom-router module.'
        assert 'root_cause' in self._detect('t-rca-1', response)

    def test_causal_prose_without_heading(self):
        self._save('t-rca-2')
        response = ('The running CCR process (PID 72772, started 7/3 1:01 AM) cached '
                     'the pre-rename custom-router module that maps claude-local-ornith to lmstudio. '
                     'CCR hot-reloads config.json but does NOT hot-reload require()d custom-router modules. '
                     'The on-disk fix landed at 9:42 AM but was never picked up because the gateway was never restarted. ') * 3
        detected = self._detect('t-rca-2', response)
        assert 'root_cause' not in detected, 'baseline FP: causal prose without heading not detected'

    def test_caused_by_match(self):
        self._save('t-rca-causedby')
        response = 'The timeout is caused by a misconfigured connection pool limit. ' * 10
        assert 'root_cause' in self._detect('t-rca-causedby', response)

    def test_because_not_root_cause(self):
        self._save('t-rca-because')
        response = 'The test failed because of a dependency issue in the CI pipeline. ' * 10
        assert 'root_cause' not in self._detect('t-rca-because', response)

    def test_non_rca_no_false_positive(self):
        non_rca = [
            'The test suite passes with 48/48 tests green. Coverage is at 82% ',
            'I updated the README to reflect the new API changes ',
            'The build completed successfully with no warnings ',
            'PR is ready for review. Changes: 3 files modified, 1 added ',
            'Deployed to staging. Smoke tests pass ',
        ]
        for i, resp in enumerate(non_rca):
            self._save(f't-rca-fp-{i}', task_id=f't-rca-fp-{i}')
            detected = self._detect(f't-rca-fp-{i}', (resp + ' ') * 5)
            assert 'root_cause' not in detected, f'Non-RCA should not trigger: {resp[:50]}'

class TestContractReplacement:

    def test_different_task_id_resets_provided_outputs(self):
        from __lib.task_contract import save_contract, load_contract, mark_provided_outputs
        t = 't-replace-1'
        save_contract(t, task_id='old-task', description='old', required_outputs=['root_cause', 'fix'])
        mark_provided_outputs(t, ['fix', 'root_cause'])
        save_contract(t, task_id='new-task', description='new', required_outputs=['root_cause', 'fix'])
        loaded = load_contract(t)
        assert loaded['provided_outputs'] == [], f'got: {loaded["provided_outputs"]}'
        assert loaded['task_id'] == 'new-task'

    def test_same_task_id_preserves_provided_outputs(self):
        from __lib.task_contract import save_contract, load_contract, mark_provided_outputs
        t = 't-replace-2'
        save_contract(t, task_id='same-task', description='first', required_outputs=['root_cause', 'fix'])
        mark_provided_outputs(t, ['fix'])
        save_contract(t, task_id='same-task', description='updated', required_outputs=['root_cause', 'fix'])
        loaded = load_contract(t)
        assert loaded['provided_outputs'] == ['fix'], f'got: {loaded["provided_outputs"]}'

class TestContractExpiry:

    def test_stale_contract_auto_expires(self):
        from __lib.task_contract import save_contract, load_contract, _contract_path
        import json, time
        from datetime import datetime, timezone
        t = 't-expire-1'
        save_contract(t, task_id='t-expire-1', description='stale', required_outputs=['root_cause'])
        path = str(_contract_path(t))
        with open(path, 'r') as f:
            data = json.load(f)
        data['created_at'] = datetime.fromtimestamp(time.time() - 3*3600, tz=timezone.utc).isoformat()
        with open(path, 'w') as f:
            json.dump(data, f)
        result = load_contract(t)
        assert result is None, 'stale contract should be expired'

    def test_fresh_contract_not_expired(self):
        from __lib.task_contract import save_contract, load_contract
        t = 't-expire-2'
        save_contract(t, task_id='t-expire-2', description='fresh', required_outputs=['root_cause'])
        result = load_contract(t)
        assert result is not None and result['status'] == 'active'

class TestNarrowedPatterns:
    """Tests for the 3 narrowed RCA-specific patterns added to _OUTPUT_PATTERNS."""

    def _detect(self, response):
        from Stop import _detect_provided_outputs
        return _detect_provided_outputs(response, ['root_cause', 'fix', 'verification_commands'])

    # --- Pattern: the (issue|problem) originates ---
    def test_issue_originates_detected(self):
        resp = 'The issue originates from the connection pool configuration being set too low. ' * 10
        assert 'root_cause' in self._detect(resp)

    def test_issue_originates_in_generic_context(self):
        resp = 'The issue originates from a misunderstanding of the requirements document. ' * 10
        assert 'root_cause' in self._detect(resp)

    # --- Pattern: trace[d]? (to|back|from) ---
    def test_trace_to_detected(self):
        resp = 'I traced to the connection pool configuration and found the pool size was too low. ' * 10
        assert 'root_cause' in self._detect(resp)

    def test_trace_from_detected(self):
        resp = 'We traced from the log output back to the config file that was overwritten. ' * 10
        assert 'root_cause' in self._detect(resp)

    def test_pasted_stack_trace_not_detected(self):
        resp = ('Traceback (most recent call last):\n  File "app.py", line 42\n'
                '    raise ValueError("bad input")\nValueError: bad input\n') * 10
        assert 'root_cause' not in self._detect(resp)

    # --- Pattern: the (call|import) chain ---
    def test_call_chain_detected(self):
        resp = 'The call chain shows the request flows through auth → handler → db, and the timeout occurs in db. ' * 10
        assert 'root_cause' in self._detect(resp)

    def test_import_chain_detected(self):
        resp = 'The import chain reveals that module A imports module B which imports the broken module C. ' * 10
        assert 'root_cause' in self._detect(resp)

    # --- Existing pattern: root cause ---
    def test_root_cause_detected(self):
        resp = '## Root Cause\nThe gateway failed because the provider was renamed but the cache was stale. ' * 10
        assert 'root_cause' in self._detect(resp)

    # --- Existing pattern: caused by ---
    def test_caused_by_detected(self):
        resp = 'The timeout is caused by a misconfigured connection pool limit. ' * 10
        assert 'root_cause' in self._detect(resp)

    # --- Non-RCA: false positive rejection ---
    def test_because_not_root_cause(self):
        resp = 'The test failed because of a dependency version mismatch in CI. ' * 10
        assert 'root_cause' not in self._detect(resp)

    def test_hypothesis_not_root_cause(self):
        resp = 'My hypothesis is that the timeout stems from the default 30s limit. ' * 10
        assert 'root_cause' not in self._detect(resp)

    def test_investigation_not_root_cause(self):
        resp = 'The investigation revealed the files were missing from the deployment. ' * 10
        assert 'root_cause' not in self._detect(resp)

    def test_reason_is_not_root_cause(self):
        resp = 'The reason is simple: we forgot to update the config file. ' * 10
        assert 'root_cause' not in self._detect(resp)

    def test_stack_trace_not_root_cause(self):
        resp = ('Traceback (most recent call last):\n  File "app.py", line 42\n'
                '    raise ValueError("bad input")\n') * 10
        assert 'root_cause' not in self._detect(resp)

    def test_follow_path_not_root_cause(self):
        resp = 'Following the path of least resistance, we decided to skip the migration. ' * 10
        assert 'root_cause' not in self._detect(resp)
