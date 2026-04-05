#!/usr/bin/env python3
"""
PreToolUse TDD-95 Gate Hook

Simplified TDD enforcement with auto-scaffold and characterization.

Core Philosophy:
- Test-first: No implementation without test
- Auto-scaffold: Automatically create test when missing
- Characterization: Run tests before editing to establish baseline
- Respect bypass env var (TDD_BYPASS=1)

Decision Flow:
1. TDD_BYPASS=1 -> Allow immediately
2. File exempt (docs, tests, config) -> Allow
3. File is test itself -> Allow
4. Critical hook without tests -> Block (must create manually)
5. No test file exists -> Auto-scaffold test, allow edit
6. Test exists but never run -> Block (run to characterize first)
7. Test ran >10 min ago BUT tests green (PASSING/COMPLETE) -> Allow (refactoring phase - Scenario #5)
8. Test ran >10 min ago AND tests NOT green -> Block (re-run to re-characterize)
9. Test ran recently -> Allow edit
10. MultiEdit: Each file checked individually - all must pass (Scenario #3)
11. SCENARIO #7: Function-level coverage - edited function must be tested
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Add hooks directory to path
hooks_dir = Path("P:/.claude/hooks")
if str(hooks_dir) not in sys.path:
    sys.path.insert(0, str(hooks_dir))

from tdd95_core import (
    TDD95State,
    TDD95StateManager,
    canonicalize_path,
    find_project_root,
    get_bypass_flag,
    get_critical_hook_tests,
    get_template_for_impl,
    get_test_candidates,
    in_maintenance_mode,
    is_critical_hook,
    is_exempt,
    is_in_maintenance_scope,
    is_test_file,
    load_config,
    path_from_posix,
)


def _extract_function_names_from_code(code: str) -> list[str]:
    """
    Extract function and method names from Python code using AST.

    Args:
        code: Python source code (can be partial or full)

    Returns:
        List of function/method names found in the code
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # Fall back to regex for partial code
        return _extract_function_names_regex(code)

    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append(node.name)
        elif isinstance(node, ast.AsyncFunctionDef):
            functions.append(node.name)
    return functions


def _extract_function_names_regex(code: str) -> list[str]:
    """
    Fallback regex-based function extraction for partial code.

    Args:
        code: Python source code (partial)

    Returns:
        List of function names found
    """
    # Match 'def function_name' and 'async def function_name'
    pattern = r"(?:async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\("
    matches = re.findall(pattern, code)
    return matches


def _extract_function_from_edit(edit_content: str) -> str | None:
    """
    Extract the primary function name being edited.

    For Edit operations, analyzes both old_string and new_string to determine
    which function is being modified.

    Args:
        edit_content: The new_string content from Edit tool

    Returns:
        Function name if detected, None otherwise
    """
    functions = _extract_function_names_from_code(edit_content)
    if functions:
        # Return the first function defined (most likely the one being edited)
        return functions[0]
    return None


def _get_functions_tested_by_file(test_path: Path) -> set[str]:
    """
    Parse a test file and find which implementation functions it tests.

    Uses AST to find test function names, then maps them to impl function names.
    E.g., test_foo_bar() -> tests foo, bar, or both

    Args:
        test_path: Path to the test file

    Returns:
        Set of implementation function names that have corresponding tests
    """
    if not test_path.exists():
        return set()

    try:
        content = test_path.read_text(encoding="utf-8")
        tree = ast.parse(content)
    except (SyntaxError, OSError):
        return set()

    tested_functions = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_name = node.name
            # Standard pytest pattern: test_foo_* or test_foo_bar
            if func_name.startswith("test_"):
                # Extract the base name after 'test_'
                # test_foo_bar_baz -> foo, foo_bar, foo_bar_baz
                parts = func_name.split("_")[1:]  # Remove 'test_' prefix
                if parts:
                    # Add all progressively joined names
                    # e.g., test_foo_bar_baz -> {"foo", "foo_bar", "foo_bar_baz"}
                    for i in range(len(parts)):
                        tested_functions.add("_".join(parts[: i + 1]))

            # Alternative pattern: testfoo or testFoo
            elif func_name.lower().startswith("test"):
                base = func_name[4:] if len(func_name) > 4 else func_name[4:]
                if base:
                    tested_functions.add(base.lower())

    return tested_functions


def _check_function_coverage(
    impl_path: Path, test_path: Path, edited_function: str
) -> tuple[bool, str | None]:
    """
    Check if a specific function has test coverage.

    Args:
        impl_path: Path to the implementation file
        test_path: Path to the test file
        edited_function: Name of the function being edited

    Returns:
        (has_coverage, message_if_no_coverage)
    """
    tested_functions = _get_functions_tested_by_file(test_path)

    # Normalize the edited function name
    edited_normalized = edited_function.lower()

    # Check if any tested function matches the edited function
    for tested in tested_functions:
        if tested.lower() == edited_normalized:
            return True, None

    # Check for partial matches (e.g., edited_function = "foo_bar_baz" but tests check "foo")
    # Be more lenient - only block if NO overlap at all
    if tested_functions:
        # Check if edited function contains any tested function or vice versa
        for tested in tested_functions:
            if tested.lower() in edited_normalized or edited_normalized in tested.lower():
                return True, None

    # No coverage found
    # Generate helpful message
    if tested_functions:
        suggestion = f"Tests exist but don't cover '{edited_function}'. Tested functions: {', '.join(sorted(tested_functions))}"
    else:
        suggestion = f"Test file doesn't detect any function tests. Add test_{edited_function}() to cover this function."

    return False, suggestion


def _find_best_test_path(impl_path: Path, config: dict) -> Path | None:
    """
    Find the best test path for scaffolding.

    Priority:
    1. Primary test directory (tests/) with existing parent
    2. Hooks test directory (for hooks/)
    3. First writable location

    Returns:
        Path object or None if no valid location
    """
    candidates = get_test_candidates(impl_path, config)

    if not candidates:
        return None

    project_root = find_project_root(impl_path)
    if project_root:
        valid_candidates = []
        for c in candidates:
            if c.parent.exists() or c.parent == project_root:
                valid_candidates.append(c)

        if valid_candidates:
            return valid_candidates[0]

    return candidates[0]


def _scaffold_test_for_impl(impl_path: Path, config: dict) -> dict[str, Any]:
    """
    Create a test file for the given implementation file.

    Returns:
        Dict with result info: {action, test_file, message}
    """
    test_path = _find_best_test_path(impl_path, config)

    if not test_path:
        return {
            "action": "error",
            "reason": "No valid test path found",
            "impl_file": str(impl_path),
        }

    if test_path.exists():
        return {
            "action": "skip",
            "reason": "Test file already exists",
            "impl_file": str(impl_path),
            "test_file": str(test_path),
        }

    test_path.parent.mkdir(parents=True, exist_ok=True)
    template_type = config.get("autoscaffold", {}).get("template", "minimal")
    template = get_template_for_impl(impl_path, template_type)

    try:
        test_path.write_text(template, encoding="utf-8")
        # Note: state update happens when test runs, not at scaffold time

        return {
            "action": "scaffolded",
            "impl_file": str(impl_path),
            "test_file": str(test_path),
            "template_type": template_type,
            "message": f"Auto-scaffolded test: {test_path}",
        }
    except OSError as e:
        return {
            "action": "error",
            "impl_file": str(impl_path),
            "test_file": str(test_path),
            "error": str(e),
        }


def check_file_path(
    file_path_str: str, tool_input: dict[str, Any]
) -> tuple[bool, str, dict[str, Any] | None]:
    """
    Check if a file edit should be allowed.

    Returns:
        (allow, reason, context)
        - allow: True if edit should proceed
        - reason: Message if blocking/warning
        - context: Additional context for resolution
    """
    # Normalize path
    file_path = canonicalize_path(file_path_str)

    # Load config
    config = load_config()

    # Check 1: TDD_BYPASS
    if get_bypass_flag():
        return True, "TDD_BYPASS=1", {"bypassed": True, "tdd_state": "BYPASS"}

    # Check 1.5: Maintenance mode
    if in_maintenance_mode() and is_in_maintenance_scope(file_path, config):
        # Record maintenance edit for later tracking
        state_mgr = TDD95StateManager()
        state_mgr.record_maintenance_edit(file_path)
        # Do NOT block; only warn and log context
        return (
            True,
            "maintenance mode - TDD relaxed for this file",
            {
                "maintenance_mode": True,
                "file": str(file_path),
                "tdd_state": "MAINTENANCE",
            },
        )

    # Check 2: Is file exempt?
    if is_exempt(file_path, config):
        return True, "file exempt", {"exempt": True, "tdd_state": "EXEMPT"}

    # Check 3: Is this a test file?
    if is_test_file(file_path, config):
        return True, "editing test file", {"is_test": True, "tdd_state": "TEST"}

    # Check 4: Critical hook requirements
    if is_critical_hook(file_path, config):
        hook_tests = get_critical_hook_tests(file_path.stem)

        if hook_tests and hook_tests.required_tests:
            # Check if required tests exist
            missing_tests = []
            for test_path_str in hook_tests.required_tests:
                test_path = path_from_posix(test_path_str)
                if not test_path.exists():
                    missing_tests.append(str(test_path))

            if missing_tests:
                # Block critical hook edits without tests
                actions = []
                for test_path in missing_tests:
                    actions.append(f"- Create test: {test_path}")

                context = {
                    "critical_hook": True,
                    "missing_tests": missing_tests,
                    "suggested_action": "scaffold_tests",
                    "tdd_state": "BLOCKED",
                }
                return (
                    False,
                    ("Critical hook requires tests. Create them first:\n" + "\n".join(actions)),
                    context,
                )

    # Check 5: Characterization requirement - tests must exist AND have been run
    state_mgr = TDD95StateManager()
    file_state = state_mgr.get_state_for_impl(file_path)
    test_candidates = get_test_candidates(file_path, config)
    existing_tests = [t for t in test_candidates if t.exists()]

    if not existing_tests:
        # No test file exists - auto-scaffold test, then allow edit
        scaffold_result = _scaffold_test_for_impl(file_path, config)

        if scaffold_result["action"] == "scaffolded":
            return (
                True,
                f"Auto-scaffolded test: {scaffold_result['test_file']}",
                {
                    "scaffolded": True,
                    "test_file": scaffold_result["test_file"],
                    "impl_file": str(file_path),
                    "tdd_state": "AUTO",
                },
            )
        else:
            return (
                False,
                f"No test found for {file_path.name}. Auto-scaffold failed: {scaffold_result.get('reason', 'unknown')}. Create test manually.",
                {
                    "block_reason": "no_tests",
                    "scaffold_error": scaffold_result,
                    "tdd_state": "BLOCKED",
                },
            )

    # Test file exists - check if it's been run (characterization requirement)
    if file_state is None or not file_state.last_test_run:
        # Tests exist but never run - block until characterized
        return (
            False,
            f"Tests exist but never run. Run tests first to characterize: pytest {existing_tests[0]}",
            {"block_reason": "never_run", "tdd_state": "NEVER_RUN"},
        )

    # Check recency - tests must have been run recently
    # SCENARIO #5: Refactoring phase - if tests are green (PASSING/COMPLETE), skip stale check
    recency_minutes = config.get("gate", {}).get("check_test_recency_minutes", 10)
    try:
        last_run = datetime.fromisoformat(file_state.last_test_run)
        stale_threshold = datetime.now() - timedelta(minutes=recency_minutes)

        if last_run < stale_threshold:
            # Check if we're in refactoring phase (tests are green)
            current_state = TDD95State.from_string(file_state.state)
            if current_state in (TDD95State.PASSING, TDD95State.COMPLETE):
                # Refactoring phase - tests passed, allow edit without re-running
                return (
                    True,
                    "refactoring phase - tests green",
                    {"refactoring": True, "characterized": True, "tdd_state": "REFACTORING"},
                )
            # Not in refactoring phase - block for stale tests
            return (
                False,
                f"Tests stale ({recency_minutes}+ min). Re-run to re-characterize: pytest {existing_tests[0]}",
                {"block_reason": "stale_tests", "tdd_state": "STALE"},
            )
    except (ValueError, TypeError) as e:
        # Invalid timestamp in state file - surface error for visibility
        # but still treat as "never run" to guide user toward re-characterization
        return (
            False,
            f"Tests exist but never run. Run tests first to characterize: pytest {existing_tests[0]}",
            {
                "block_reason": "never_run",
                "tdd_state": "NEVER_RUN",
                "warning": f"Invalid timestamp in state file: {e}",
            },
        )

    # Tests exist and have been run recently - allow edit
    # SCENARIO #7: Function-level coverage check
    # Check if the specific function being edited has test coverage
    if tool_input:
        edited_function = _extract_function_from_edit_content(tool_input)
        if edited_function and existing_tests:
            # Check coverage against the first (primary) test file
            test_path = existing_tests[0]
            has_coverage, coverage_msg = _check_function_coverage(
                file_path, test_path, edited_function
            )
            if not has_coverage:
                return (
                    False,
                    f"Function-level coverage gap: {coverage_msg}",
                    {
                        "block_reason": "function_not_tested",
                        "edited_function": edited_function,
                        "test_file": str(test_path),
                        "suggested_action": f"Add test_{edited_function}() to {test_path.name}",
                        "tdd_state": "NO_COVERAGE",
                    },
                )

    return True, "tests characterized", {"characterized": True, "tdd_state": "CHARACTERIZED"}


def _extract_function_from_edit_content(tool_input: dict[str, Any]) -> str | None:
    """
    Extract the function name being edited from tool_input.

    For Edit operations, checks new_string for function definitions.
    For Write operations, checks the content being written.

    Args:
        tool_input: The tool input dict containing new_string or content

    Returns:
        Function name if detected, None otherwise
    """
    # For Edit operations
    new_string = tool_input.get("new_string", "")
    if new_string:
        return _extract_function_from_edit(new_string)

    # For Write operations, check content
    content = tool_input.get("content", "")
    if content:
        return _extract_function_from_edit(content)

    return None


def process_hook(input_data: dict[str, Any]) -> tuple[bool, str | None, dict[str, Any] | None]:
    """
    Process the hook and decide whether to allow the action.

    Returns:
        (allow, reason, context)
    """
    tool_name = input_data.get("name", "")
    tool_input = input_data.get("tool_input", {})

    # Only process Write/Edit operations
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return True, None, None

    # Check if TDD-95 is enabled
    config = load_config()
    if not config.get("enabled", True):
        return True, "TDD-95 disabled", {"disabled": True}

    # SCENARIO #3: MultiEdit handling - check each file in the edit
    if tool_name == "MultiEdit":
        edits = tool_input.get("edits", [])
        if not edits:
            return True, None, None

        # Check each file in the MultiEdit
        blocked_files = []
        for edit in edits:
            file_path_str = edit.get("file_path", "")
            if not file_path_str:
                continue

            allow, reason, _context = check_file_path(file_path_str, edit)
            if not allow:
                blocked_files.append((file_path_str, reason))

        if blocked_files:
            # At least one file in MultiEdit is blocked
            first_file, first_reason = blocked_files[0]
            total_blocked = len(blocked_files)
            if total_blocked == 1:
                return (
                    False,
                    first_reason,
                    {
                        "block_reason": "multiedit_blocked",
                        "blocked_file": first_file,
                        "tdd_state": "BLOCKED",
                    },
                )
            else:
                return (
                    False,
                    f"MultiEdit blocked: {total_blocked} files fail TDD check. First: {first_file} - {first_reason}",
                    {
                        "block_reason": "multiedit_blocked",
                        "blocked_files": [f for f, _ in blocked_files],
                        "tdd_state": "BLOCKED",
                    },
                )

        # All files pass TDD check
        return (
            True,
            "MultiEdit all files TDD-compliant",
            {"multiedit_checked": True, "tdd_state": "PASS"},
        )

    # Single file operations (Write/Edit)
    # Get file path from various sources
    file_path_str = (
        tool_input.get("file_path", "")
        or tool_input.get("path", "")
        or os.environ.get("CLAUDE_TOOL_EDIT_FILE", "")
        or os.environ.get("CLAUDE_TOOL_WRITE_FILE", "")
    )

    if not file_path_str:
        return True, None, None

    # Main check
    return check_file_path(file_path_str, tool_input)


def main():
    """
    Hook entry point.

    stdin: JSON hook input
    stdout: JSON decision
    exit code: 0 for allow, 1 for block
    """
    # Read hook input
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        # No valid input, allow
        print(json.dumps({"continue": True}))
        return

    allow, reason, context = process_hook(input_data)

    if allow:
        output: dict[str, Any] = {"continue": True}
        # Only emit TDD state for actionable states - suppress noise
        ACTIONABLE_TDD_STATES = {
            "BLOCKED",
            "STALE",
            "NEVER_RUN",
            "NO_COVERAGE",
            "REFACTORING",
            "BYPASS",
            "MAINTENANCE",
        }
        if context and "tdd_state" in context:
            tdd_state = context["tdd_state"]
            if tdd_state in ACTIONABLE_TDD_STATES:
                output["info"] = f"[TDD: {tdd_state}]"
                if reason and reason not in ("default allow", "editing test file", "file exempt"):
                    output["info"] = f"[TDD: {tdd_state}] {reason}"
        elif reason and reason not in ("default allow", "editing test file", "file exempt"):
            output["info"] = reason
        if context:
            output["context"] = context
        print(json.dumps(output))
    else:
        # Block with reason - include TDD state if available
        error_output: dict[str, Any] = {
            "continue": False,
            "error": {"message": reason or "TDD gate blocked this action"},
        }
        if context and "tdd_state" in context:
            error_output["error"]["tdd_state"] = context["tdd_state"]
        print(json.dumps(error_output))
        sys.exit(1)  # Exit with error code to block


if __name__ == "__main__":
    main()
