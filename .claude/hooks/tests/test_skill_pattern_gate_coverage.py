#!/usr/bin/env python3
"""
Comprehensive test suite for skill pattern gate coverage.

Tests legitimate bash commands to ensure they are NOT blocked.
This addresses RISK:9 from pre-mortem: "No test coverage for legitimate bash commands"

Test Categories:
1. Common bash commands (ls, cd, cat, grep, find, etc.)
2. File operations (cp, mv, rm, mkdir, etc.)
3. Python operations (python -c, pip, pytest, etc.)
4. Git operations (git status, git log, etc.)
5. Text processing (sed, awk, sort, uniq, etc.)
6. System operations (ps, top, kill, etc.)
7. Network operations (curl, wget, ssh, etc.)
8. Test execution (pytest, npm test, cargo test, etc.)
9. Build operations (npm build, make, cargo build, etc.)
10. Edge cases (empty commands, comments, etc.)
"""

import json
import subprocess
import sys
from pathlib import Path


def run_hook(test_input: dict) -> dict:
    """Run the skill pattern gate hook with test input.

    Args:
        test_input: Hook input dict with tool_name and input fields

    Returns:
        Hook result dict (block decision + reason if blocked)
    """
    hook_path = Path("P:/packages/skill-guard/src/skill_guard/PreToolUse/PreToolUse_skill_pattern_gate.py")

    # Run hook with test input
    env = {
        "SKILL_PATTERN_ENFORCEMENT_ENABLED": "true",
        "SKILL_INTENT_DAEMON_ENABLED": "false",  # Disable for faster tests
        "FIRST_TOOL_COHERENCE_ENABLED": "true",
    }

    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(test_input),
        capture_output=True,
        text=True,
        env={**subprocess.os.environ, **env},
        timeout=10
    )

    # Parse output
    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        return {"block": False, "parse_error": True}


# =============================================================================
# NEGATIVE TEST CASES: Legitimate commands that should NOT be blocked
# =============================================================================

NEGATIVE_TEST_CASES = {
    # Category 1: Common bash commands
    "ls_simple": {
        "tool_name": "Bash",
        "input": {"command": "ls"},
        "description": "Simple ls command"
    },
    "ls_with_path": {
        "tool_name": "Bash",
        "input": {"command": "ls P:/.claude/hooks"},
        "description": "ls with path (CURRENT BUG: blocks this)"
    },
    "ls_with_flags": {
        "tool_name": "Bash",
        "input": {"command": "ls -la"},
        "description": "ls with flags"
    },
    "cd_simple": {
        "tool_name": "Bash",
        "input": {"command": "cd P:/packages"},
        "description": "Change directory"
    },
    "cat_file": {
        "tool_name": "Bash",
        "input": {"command": "cat README.md"},
        "description": "Display file content"
    },
    "grep_simple": {
        "tool_name": "Bash",
        "input": {"command": "grep 'pattern' file.txt"},
        "description": "Search for pattern"
    },
    "find_simple": {
        "tool_name": "Bash",
        "input": {"command": "find . -name '*.py'"},
        "description": "Find files"
    },

    # Category 2: File operations
    "cp_simple": {
        "tool_name": "Bash",
        "input": {"command": "cp file1.txt file2.txt"},
        "description": "Copy file"
    },
    "mv_simple": {
        "tool_name": "Bash",
        "input": {"command": "mv old.txt new.txt"},
        "description": "Move file"
    },
    "rm_simple": {
        "tool_name": "Bash",
        "input": {"command": "rm temp.txt"},
        "description": "Remove file"
    },
    "mkdir_simple": {
        "tool_name": "Bash",
        "input": {"command": "mkdir new_dir"},
        "description": "Create directory"
    },
    "touch_simple": {
        "tool_name": "Bash",
        "input": {"command": "touch new_file.txt"},
        "description": "Create file"
    },

    # Category 3: Python operations (non-skill)
    "python_simple": {
        "tool_name": "Bash",
        "input": {"command": "python script.py"},
        "description": "Run Python script"
    },
    "python_module": {
        "tool_name": "Bash",
        "input": {"command": "python -m pytest"},
        "description": "Run Python module"
    },
    "python_check": {
        "tool_name": "Bash",
        "input": {"command": "python --version"},
        "description": "Check Python version"
    },
    "pip_install": {
        "tool_name": "Bash",
        "input": {"command": "pip install requests"},
        "description": "Install package"
    },
    "pip_list": {
        "tool_name": "Bash",
        "input": {"command": "pip list"},
        "description": "List packages"
    },

    # Category 4: Git operations
    "git_status": {
        "tool_name": "Bash",
        "input": {"command": "git status"},
        "description": "Check git status"
    },
    "git_log": {
        "tool_name": "Bash",
        "input": {"command": "git log --oneline"},
        "description": "Show git log"
    },
    "git_diff": {
        "tool_name": "Bash",
        "input": {"command": "git diff"},
        "description": "Show git diff"
    },
    "git_branch": {
        "tool_name": "Bash",
        "input": {"command": "git branch"},
        "description": "List branches"
    },

    # Category 5: Text processing
    "sed_simple": {
        "tool_name": "Bash",
        "input": {"command": "sed 's/old/new/g' file.txt"},
        "description": "Text replacement"
    },
    "awk_simple": {
        "tool_name": "Bash",
        "input": {"command": "awk '{print $1}' file.txt"},
        "description": "Text processing"
    },
    "sort_simple": {
        "tool_name": "Bash",
        "input": {"command": "sort file.txt"},
        "description": "Sort lines"
    },
    "uniq_simple": {
        "tool_name": "Bash",
        "input": {"command": "uniq file.txt"},
        "description": "Remove duplicates"
    },
    "wc_simple": {
        "tool_name": "Bash",
        "input": {"command": "wc -l file.txt"},
        "description": "Count lines"
    },

    # Category 6: System operations
    "ps_simple": {
        "tool_name": "Bash",
        "input": {"command": "ps aux"},
        "description": "List processes"
    },
    "top_simple": {
        "tool_name": "Bash",
        "input": {"command": "top -n 1"},
        "description": "Show processes"
    },
    "kill_simple": {
        "tool_name": "Bash",
        "input": {"command": "kill 12345"},
        "description": "Kill process"
    },
    "df_simple": {
        "tool_name": "Bash",
        "input": {"command": "df -h"},
        "description": "Disk usage"
    },
    "du_simple": {
        "tool_name": "Bash",
        "input": {"command": "du -sh dir"},
        "description": "Directory size"
    },

    # Category 7: Network operations
    "curl_simple": {
        "tool_name": "Bash",
        "input": {"command": "curl https://example.com"},
        "description": "HTTP request"
    },
    "wget_simple": {
        "tool_name": "Bash",
        "input": {"command": "wget https://example.com/file.txt"},
        "description": "Download file"
    },
    "ping_simple": {
        "tool_name": "Bash",
        "input": {"command": "ping -c 1 example.com"},
        "description": "Ping host"
    },

    # Category 8: Test execution (legitimate testing)
    "pytest_simple": {
        "tool_name": "Bash",
        "input": {"command": "pytest tests/"},
        "description": "Run pytest"
    },
    "pytest_verbose": {
        "tool_name": "Bash",
        "input": {"command": "pytest -v tests/test_file.py"},
        "description": "Run pytest verbose"
    },
    "npm_test": {
        "tool_name": "Bash",
        "input": {"command": "npm test"},
        "description": "Run npm tests"
    },
    "cargo_test": {
        "tool_name": "Bash",
        "input": {"command": "cargo test"},
        "description": "Run cargo tests"
    },

    # Category 9: Build operations
    "npm_build": {
        "tool_name": "Bash",
        "input": {"command": "npm run build"},
        "description": "Build with npm"
    },
    "make_build": {
        "tool_name": "Bash",
        "input": {"command": "make"},
        "description": "Build with make"
    },
    "cargo_build": {
        "tool_name": "Bash",
        "input": {"command": "cargo build"},
        "description": "Build with cargo"
    },
    "gcc_build": {
        "tool_name": "Bash",
        "input": {"command": "gcc -o program program.c"},
        "description": "Compile with gcc"
    },

    # Category 10: Edge cases
    "empty_command": {
        "tool_name": "Bash",
        "input": {"command": ""},
        "description": "Empty command"
    },
    "whitespace_only": {
        "tool_name": "Bash",
        "input": {"command": "   "},
        "description": "Whitespace only"
    },
    "comment_only": {
        "tool_name": "Bash",
        "input": {"command": "# this is a comment"},
        "description": "Comment only"
    },
    "echo_simple": {
        "tool_name": "Bash",
        "input": {"command": "echo 'hello'"},
        "description": "Echo command"
    },
    "pwd_simple": {
        "tool_name": "Bash",
        "input": {"command": "pwd"},
        "description": "Print working directory"
    },

    # Additional: Complex legitimate commands
    "pipeline": {
        "tool_name": "Bash",
        "input": {"command": "cat file.txt | grep pattern | sort"},
        "description": "Command pipeline"
    },
    "redirection": {
        "tool_name": "Bash",
        "input": {"command": "ls > output.txt"},
        "description": "Output redirection"
    },
    "background": {
        "tool_name": "Bash",
        "input": {"command": "sleep 10 &"},
        "description": "Background job"
    },
    "variable": {
        "tool_name": "Bash",
        "input": {"command": "VAR=value python script.py"},
        "description": "Environment variable"
    },
}


# =============================================================================
# POSITIVE TEST CASES: Skill invocations that SHOULD be blocked
# =============================================================================

POSITIVE_TEST_CASES = {
    "ask_cli_direct": {
        "tool_name": "Bash",
        "input": {"command": "python P:/.claude/skills/cli/ask_cli.py --qwen-only 'prompt'"},
        "description": "Direct ask_cli.py invocation (should block)",
        "expected_skill": "ask-olymp"
    },
    "rca_direct": {
        "tool_name": "Bash",
        "input": {"command": "python -c 'from src.rca import SimpleRCAEngine; SimpleRCAEngine().run()'"},
        "description": "Direct RCA import (should block)",
        "expected_skill": "rca"
    },
    "research_cli": {
        "tool_name": "Bash",
        "input": {"command": "python -m research.cli 'query'"},
        "description": "Research CLI invocation (should block)",
        "expected_skill": "research"
    },
}


def test_negative_cases():
    """Test that legitimate bash commands are NOT blocked."""
    print("\n" + "="*70)
    print("NEGATIVE TESTS: Legitimate commands (should NOT block)")
    print("="*70)

    passed = 0
    failed = 0
    failures = []

    for test_name, test_case in NEGATIVE_TEST_CASES.items():
        result = run_hook(test_case)

        # Check if command was blocked
        if result.get("block"):
            failed += 1
            reason = result.get("reason", "Unknown reason")
            failures.append({
                "test": test_name,
                "description": test_case["description"],
                "command": test_case["input"]["command"],
                "reason": reason
            })
            print(f"✗ FAIL: {test_name} - {test_case['description']}")
            print(f"  Command: {test_case['input']['command']}")
            print(f"  Blocked: {reason[:200]}")
        else:
            passed += 1
            print(f"✓ PASS: {test_name} - {test_case['description']}")

    print("\n" + "-"*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70)

    if failed > 0:
        print("\n🚨 FALSE POSITIVE DETECTED!")
        print("\nSummary of failures:")
        for failure in failures:
            print(f"\n{failure['test']}: {failure['description']}")
            print(f"  Command: {failure['command']}")
            print(f"  Reason: {failure['reason'][:200]}")

    return failed == 0


def test_positive_cases():
    """Test that direct skill invocations ARE blocked."""
    print("\n" + "="*70)
    print("POSITIVE TESTS: Skill invocations (SHOULD block)")
    print("="*70)

    passed = 0
    failed = 0
    failures = []

    for test_name, test_case in POSITIVE_TEST_CASES.items():
        result = run_hook(test_case)

        # Check if command was blocked (expected)
        if result.get("block"):
            passed += 1
            print(f"✓ PASS: {test_name} - {test_case['description']}")
        else:
            failed += 1
            failures.append({
                "test": test_name,
                "description": test_case["description"],
                "command": test_case["input"]["command"],
            })
            print(f"✗ FAIL: {test_name} - {test_case['description']}")
            print(f"  Command: {test_case['input']['command']}")
            print("  Expected: BLOCK, Got: ALLOW")

    print("\n" + "-"*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70)

    if failed > 0:
        print("\n⚠️  BLOCKING FAILURE!")
        print("\nSummary of failures (commands that should be blocked but weren't):")
        for failure in failures:
            print(f"\n{failure['test']}: {failure['description']}")
            print(f"  Command: {failure['command']}")

    return failed == 0


def test_edge_cases():
    """Test edge cases that could cause misclassification or security gaps."""
    print("\n" + "="*70)
    print("EDGE CASE TESTS: Boundary conditions and security gaps")
    print("="*70)

    # Clean up any existing state first
    from skill_guard.skill_execution_state import clear_state
    clear_state()

    passed = 0
    failed = 0
    failures = []

    # Edge Case 1: Malformed state file (JSON decode error)
    print("\nEdge Case 1: Malformed state file")
    test_input = {
        "tool_name": "Bash",
        "input": {"command": "ls"}
    }

    # Create malformed state file
    from pathlib import Path

    state_file = Path("P:/.claude/state/skill_execution_edge_test/skill_execution_pending.json")
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text("{invalid json content")

    try:
        result = run_hook(test_input)

        # Should fail open (allow) when state is malformed
        if result.get("block"):
            failed += 1
            failures.append({
                "test": "malformed_state_file",
                "reason": "Should fail open when state is malformed"
            })
            print("✗ FAIL: Should allow when state file is malformed")
        else:
            passed += 1
            print("✓ PASS: Fails open when state file is malformed")
    finally:
        # Cleanup
        state_file.unlink(missing_ok=True)
        state_file.parent.rmdir()

    # Edge Case 2: Empty state file (exists but empty)
    print("\nEdge Case 2: Empty state file")
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text("")

    try:
        result = run_hook(test_input)

        # Should fail open (allow) when state is empty
        if result.get("block"):
            failed += 1
            failures.append({
                "test": "empty_state_file",
                "reason": "Should allow when state file is empty"
            })
            print("✗ FAIL: Should allow when state file is empty")
        else:
            passed += 1
            print("✓ PASS: Fails open when state file is empty")
    finally:
        state_file.unlink(missing_ok=True)
        state_file.parent.rmdir()

    # Edge Case 3: State with execution intent but empty required_tools
    # (This tests RISK:4 from pre-mortem)
    print("\nEdge Case 3: State with empty required_tools")

    # Recreate directory for edge case 3
    state_file.parent.mkdir(parents=True, exist_ok=True)

    # Write state with empty required_tools
    state_file.write_text(json.dumps({
        "skill": "test-skill",
        "required_tools": [],  # EMPTY
        "pattern": "",
        "first_tool_validated": False
    }))

    try:
        result = run_hook(test_input)

        # Should allow (knowledge skill behavior)
        if result.get("block"):
            failed += 1
            failures.append({
                "test": "empty_required_tools",
                "reason": "Should allow when required_tools is empty"
            })
            print("✗ FAIL: Should allow when required_tools is empty")
        else:
            passed += 1
            print("✓ PASS: Allows when required_tools is empty (knowledge skill)")
    finally:
        state_file.unlink(missing_ok=True)
        state_file.parent.rmdir()

    # Edge Case 4: Registry skill with empty required_tools (tests validation warning)
    print("\nEdge Case 4: Registry skill with empty required_tools (validation)")

    # This tests the RISK:9 mitigation we just added
    # Use plugin path for skill-guard hooks (single source of truth)
    _plugin_src = Path("P:/packages/skill-guard/src")
    if str(_plugin_src) not in sys.path:
        sys.path.insert(0, str(_plugin_src))
    from skill_guard.PreToolUse.PreToolUse_skill_pattern_gate import SKILL_EXECUTION_REGISTRY

    # Save original registry
    original_registry = SKILL_EXECUTION_REGISTRY.get("edge_test_skill", None)

    # Add malformed skill to registry
    SKILL_EXECUTION_REGISTRY["edge_test_skill"] = {
        "tools": [],  # EMPTY - misconfigured
        "pattern": "",
        "hint": "Test"
    }

    try:
        import contextlib
        import io

        # Call set_skill_loaded to trigger validation
        from skill_guard.skill_execution_state import set_skill_loaded

        stderr_capture = io.StringIO()
        with contextlib.redirect_stderr(stderr_capture):
            set_skill_loaded("edge_test_skill")

        stderr_output = stderr_capture.getvalue()

        if 'WARNING' in stderr_output and 'empty required_tools' in stderr_output:
            passed += 1
            print("✓ PASS: Validation warning logged for registry skill with empty tools")
        else:
            failed += 1
            failures.append({
                "test": "registry_validation_warning",
                "reason": "Should log warning for registry skill with empty tools"
            })
            print("✗ FAIL: No warning logged for misconfigured registry skill")
    finally:
        # Restore registry
        if original_registry:
            SKILL_EXECUTION_REGISTRY["edge_test_skill"] = original_registry
        elif "edge_test_skill" in SKILL_EXECUTION_REGISTRY:
            del SKILL_EXECUTION_REGISTRY["edge_test_skill"]

        # Clean up any state
        from skill_guard.skill_execution_state import clear_state
        clear_state()

    print("\n" + "-"*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70)

    if failed > 0:
        print("\n🚨 EDGE CASE FAILURES DETECTED!")
        print("\nSummary of failures:")
        for failure in failures:
            print(f"\n{failure['test']}: {failure['reason']}")

    return failed == 0


def main():
    """Run all tests and report results."""
    print("\n" + "="*70)
    print("SKILL PATTERN GATE COMPREHENSIVE COVERAGE TEST")
    print("="*70)
    print(f"Total negative tests: {len(NEGATIVE_TEST_CASES)}")
    print(f"Total positive tests: {len(POSITIVE_TEST_CASES)}")

    # Run negative tests (legitimate commands should NOT be blocked)
    negative_pass = test_negative_cases()

    # Run positive tests (skill invocations SHOULD be blocked)
    positive_pass = test_positive_cases()

    # Run edge case tests (boundary conditions and security gaps)
    edge_case_pass = test_edge_cases()

    # Overall result
    print("\n" + "="*70)
    print("OVERALL RESULTS")
    print("="*70)
    print(f"Negative tests (legitimate commands): {'PASS ✓' if negative_pass else 'FAIL ✗'}")
    print(f"Positive tests (skill invocations): {'PASS ✓' if positive_pass else 'FAIL ✗'}")
    print(f"Edge case tests: {'PASS ✓' if edge_case_pass else 'FAIL ✗'}")

    if negative_pass and positive_pass and edge_case_pass:
        print("\n✅ ALL TESTS PASSED")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        if not negative_pass:
            print("\n⚠️  False positives detected - legitimate commands are being blocked!")
            print("   This is the RISK:9 issue from the pre-mortem analysis.")
        if not positive_pass:
            print("\n⚠️  Blocking failures - skill invocations are not being blocked!")
            print("   The gate is not providing security value.")
        if not edge_case_pass:
            print("\n⚠️  Edge case failures - boundary conditions or security gaps detected!")
            print("   These are the RISK:6 and RISK:9 issues from pre-mortem analysis.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
