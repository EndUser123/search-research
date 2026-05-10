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
        # Use prompt that classifies as analysis mode
        response = (
            "## Fix\n"
            "Added the new feature with proper error handling for user authentication. "
            "The feature integrates with the existing auth middleware and follows the same "
            "patterns used for other auth methods in the codebase. The implementation includes "
            "proper validation of input parameters and appropriate error responses for failure cases.\n\n"
            "The implementation follows the existing patterns and integrates seamlessly with "
            "the current architecture. It does not introduce any breaking changes and maintains "
            "backward compatibility with existing clients. The feature is designed to be extensible "
            "for future authentication methods."
        )

        data = {
            "response": response,
            "terminal_id": "terminal_impl",
            "session_id": "sess-impl",
            "user_prompt": "Implement the new feature for user authentication.",
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
        # Force both __lib.task_contract and Stop.py to use tmp_path for contracts.
        # Stop.py imports load_contract/clear_contract at runtime inside the gate,
        # so patching _home directly on the module ensures all path resolution uses tmp_path.
        import __lib.task_contract as _tc
        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)

        from __lib.task_contract import load_contract, save_contract
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
        result = _run_task_contract_fit_gate(data)
        # Should be silent — orthogonal check clears stale contract
        assert result is None, f"Expected None (auto-cleared), got {result}"
        # Contract is cleared: load_contract returns None (completed contracts are filtered)
        assert load_contract("terminal_orthogonal") is None
        # Verify the file was written as completed (not deleted)
        cf_path = _tc._contract_path("terminal_orthogonal")
        assert cf_path.exists()
        import json
        with open(cf_path) as f:
            content = json.load(f)
        assert content.get("status") == "completed", f"Expected completed, got {content.get('status')}"

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
