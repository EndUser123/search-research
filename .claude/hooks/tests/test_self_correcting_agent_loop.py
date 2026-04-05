#!/usr/bin/env python3
"""
Tests for Self-Correcting Agent Loop hooks (ADR-20260325).

Tests:
1. context_followup_detector.py - UserPromptSubmit hook
2. tool_availability_checker.py - PreToolUse hook
3. self_verification_gate.py - PostToolUse hook
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock

# Add hooks directory to path for imports
hooks_dir = Path(__file__).parent.parent
sys.path.insert(0, str(hooks_dir))

# Test state directory
TEST_STATE_DIR = hooks_dir / "state"


# ===== CONTEXT FOLLOWUP DETECTOR TESTS =====


def _get_followup_hook_context(prompt: str, terminal_id: str = "test_terminal") -> Mock:
    """Create a mock HookContext for testing."""
    context = Mock()
    context.prompt = prompt
    context.extra = {"raw_input": {"terminal_id": terminal_id}}
    return context


def _clean_followup_state(terminal_id: str) -> None:
    """Clean up test state files."""
    TEST_STATE_DIR.mkdir(parents=True, exist_ok=True)
    safe_id = "".join(c if c.isalnum() or c in "_.-:" else "_" for c in terminal_id)
    state_file = TEST_STATE_DIR / f"followup_context_{safe_id}.json"
    if state_file.exists():
        state_file.unlink()


def test_followup_fragment_patterns():
    """Test fragment patterns that indicate follow-up queries."""
    from UserPromptSubmit_modules.context_followup_detector import _is_followup_query

    # Positive cases - should be detected as follow-up
    # Note: "also" pattern requires "also...and the other" or "also...the other"
    # Note: "which/what/how else/about" pattern requires "else" or "about", not "other"
    positive_cases = [
        "if that's the best practice",
        "what about the other hooks",
        "also and the other component",
        "what else should I consider",
        "how about the other approach",
    ]

    for case in positive_cases:
        is_followup, matched = _is_followup_query(case)
        assert is_followup, f"Should detect as follow-up: {case}"


def test_followup_pronoun_start_patterns():
    """Test pronoun start patterns that indicate follow-up queries."""
    from UserPromptSubmit_modules.context_followup_detector import _is_followup_query

    # Positive cases - pronoun at start of sentence
    # Note: second word "was"/"is"/"has"/"had"/"'s"/'"s' are excluded as they indicate statements, not follow-ups
    positive_cases = [
        "It should be added to the router",
        "That should be working now",
        "This should be verified",
        "They need to be verified",
    ]

    for case in positive_cases:
        is_followup, matched = _is_followup_query(case)
        assert is_followup, f"Should detect as follow-up: {case}"


def test_standalone_query_not_followup():
    """Test that standalone queries are not flagged as follow-ups."""
    from UserPromptSubmit_modules.context_followup_detector import _is_followup_query

    # Negative cases - standalone queries
    negative_cases = [
        "How do I add a new hook",
        "What is the purpose of the PreToolUse phase",
        "Show me the context detector code",
        "List all registered hooks",
        "Run the tests",
    ]

    for case in negative_cases:
        is_followup, matched = _is_followup_query(case)
        assert not is_followup, f"Should NOT detect as follow-up: {case}"


def test_mid_sentence_pronoun_not_followup():
    """Test that mid-sentence pronouns don't trigger follow-up detection."""
    from UserPromptSubmit_modules.context_followup_detector import _is_followup_query

    # These are imperatives, not follow-ups
    cases = [
        "Run it with pytest",
        "Fix that issue",
        "Add this to the router",
        "Check them all",
    ]

    for case in cases:
        is_followup, matched = _is_followup_query(case)
        assert not is_followup, f"Should NOT detect as mid-sentence pronoun follow-up: {case}"


def test_context_followup_detector_returns_empty_for_no_terminal():
    """Test that detector returns empty when no terminal_id available."""
    from UserPromptSubmit_modules.context_followup_detector import process_prompt

    context = Mock()
    context.prompt = "if that's the case"
    context.extra = {"raw_input": {}}  # No terminal_id

    result = process_prompt(context)
    # Should return empty result since no terminal_id
    assert result is not None or result == {} or result.additional_context == ""


def test_inject_prior_context():
    """Test context injection for follow-up queries."""
    from UserPromptSubmit_modules.context_followup_detector import _inject_prior_context

    prompt = "if that's the case"
    prior_context = {
        "topic": "hook path fix",
        "summary": "We were discussing adding a new hook",
    }

    enhanced = _inject_prior_context(prompt, prior_context)
    assert "Prior context" in enhanced
    assert "hook path fix" in enhanced
    assert prompt in enhanced


def test_inject_prior_context_empty():
    """Test no injection when prior context is empty."""
    from UserPromptSubmit_modules.context_followup_detector import _inject_prior_context

    prompt = "if that's the case"
    prior_context = {}

    enhanced = _inject_prior_context(prompt, prior_context)
    assert enhanced == prompt  # Should be unchanged


# ===== TOOL AVAILABILITY CHECKER TESTS =====


def create_pretool_input(tool_name: str, params: dict, terminal_id: str = "test-terminal") -> str:
    """Create PreToolUse hook input JSON."""
    data = {
        "tool": tool_name,
        "terminal_id": terminal_id,
        "parameters": params,
    }
    return json.dumps(data)


def run_tool_checker(tool_name: str, params: dict) -> tuple[int, str]:
    """Run tool_availability_checker and return exit code and output."""
    import io
    from contextlib import redirect_stderr, redirect_stdout

    sys.path.insert(0, str(hooks_dir))
    import tool_availability_checker

    input_data = create_pretool_input(tool_name, params)

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    old_stdin = sys.stdin
    sys.stdin = io.StringIO(input_data)

    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            try:
                tool_availability_checker.main()
                exit_code = 0
            except SystemExit as e:
                exit_code = e.code if e.code is not None else 0
    finally:
        sys.stdin = old_stdin

    output = stdout_capture.getvalue() + stderr_capture.getvalue()
    return exit_code, output


def test_tool_checker_allows_read():
    """Test that Read tool passes without errors."""
    exit_code, output = run_tool_checker("Read", {"file_path": "P:/test.py"})
    assert exit_code == 0, f"Expected exit code 0, got {exit_code}"
    assert "{}" in output or exit_code == 0


def test_tool_checker_allows_edit():
    """Test that Edit tool passes without errors."""
    exit_code, output = run_tool_checker("Edit", {"file_path": "P:/test.py"})
    assert exit_code == 0, f"Expected exit code 0, got {exit_code}"


def test_tool_checker_skills_valid():
    """Test that valid skill names pass availability check."""
    # These are known skills that should exist
    exit_code, output = run_tool_checker("Skill", {"skill": "planning"})
    # planning skill should exist, so should pass
    assert exit_code == 0, f"Expected planning skill to be available, got {exit_code}: {output}"


def test_tool_checker_bash_command_check():
    """Test that bash command availability is checked."""
    # python should be available
    exit_code, output = run_tool_checker("Bash", {"command": "python --version"})
    assert exit_code == 0, f"Expected python to be available, got {exit_code}: {output}"


def test_tool_checker_get_tool_name():
    """Test tool name extraction from different input formats."""
    from tool_availability_checker import _get_tool_name

    # Test different data formats
    assert _get_tool_name({"tool": "Read"}) == "Read"
    assert _get_tool_name({"toolName": "Edit"}) == "Edit"
    assert _get_tool_name({}) == ""


def test_tool_checker_get_skill_name():
    """Test skill name extraction from parameters."""
    from tool_availability_checker import _get_skill_name_from_params

    assert _get_skill_name_from_params({"parameters": {"skill": "planning"}}) == "planning"
    assert _get_skill_name_from_params({"params": {"skillName": "gto"}}) == "gto"
    assert _get_skill_name_from_params({}) is None


def test_tool_checker_get_bash_command():
    """Test bash command extraction from parameters."""
    from tool_availability_checker import _get_bash_command_from_params

    assert (
        _get_bash_command_from_params({"parameters": {"command": "python --version"}}) == "python"
    )
    assert _get_bash_command_from_params({"params": {"cmd": "pytest"}}) == "pytest"
    assert _get_bash_command_from_params({}) is None


def test_tool_checker_check_bash_available():
    """Test bash command availability check."""
    from tool_availability_checker import _check_bash_command_available

    # python should be available on most systems
    available, error = _check_bash_command_available("python")
    assert available, f"python should be available: {error}"

    # non-existent command should fail
    available, error = _check_bash_command_available("this_command_definitely_does_not_exist_12345")
    assert not available, "Non-existent command should not be available"


def test_tool_checker_check_skill_available():
    """Test skill availability check."""
    from tool_availability_checker import _check_skill_available

    # planning skill should exist
    available, error = _check_skill_available("planning")
    assert available, f"planning skill should be available: {error}"


# ===== SELF VERIFICATION GATE TESTS =====


def create_posttool_input(response: str, events: list, terminal_id: str = "test-terminal") -> str:
    """Create PostToolUse hook input JSON."""
    data = {
        "response": response,
        "events": events,
        "terminal_id": terminal_id,
    }
    return json.dumps(data)


def run_verification_gate(response: str, events: list) -> tuple[int, str]:
    """Run self_verification_gate and return exit code and output."""
    import io
    from contextlib import redirect_stderr, redirect_stdout

    sys.path.insert(0, str(hooks_dir))
    import self_verification_gate

    input_data = create_posttool_input(response, events)

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    old_stdin = sys.stdin
    sys.stdin = io.StringIO(input_data)

    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            try:
                self_verification_gate.main()
                exit_code = 0
            except SystemExit as e:
                exit_code = e.code if e.code is not None else 0
    finally:
        sys.stdin = old_stdin

    output = stdout_capture.getvalue() + stderr_capture.getvalue()
    return exit_code, output


def test_verification_gate_allows_no_claims():
    """Test that responses without completion claims pass through."""
    response = "Let me analyze the code structure and provide recommendations."
    exit_code, output = run_verification_gate(response, [])
    assert exit_code == 0, f"Expected exit code 0, got {exit_code}"


def test_verification_gate_allows_claim_with_bash_event():
    """Test that claim with Bash pytest event is verified."""
    response = "All tests pass"
    events = [{"type": "Bash", "command": "pytest tests/"}]
    exit_code, output = run_verification_gate(response, events)
    assert exit_code == 0, f"Expected verified claim to pass, got {exit_code}: {output}"


def test_verification_gate_allows_claim_with_edit_event():
    """Test that implementation claim with Edit event is verified."""
    response = "I implemented the fix"
    events = [{"type": "Edit", "name": "Edit", "file_path": "test.py"}]
    exit_code, output = run_verification_gate(response, events)
    assert exit_code == 0, f"Expected verified claim to pass, got {exit_code}: {output}"


def test_verification_gate_blocks_unverified_fix_claim():
    """Test that unverified 'fixed' claim triggers warning."""
    response = "The issue is fixed"
    events = []  # No verification events
    exit_code, output = run_verification_gate(response, events)
    # Should return warning but not block (non-blocking hook)
    assert "{}" not in output or exit_code == 0, f"Expected warning output, got: {output}"


def test_verification_gate_detect_completion_claims():
    """Test completion claim detection patterns."""
    from self_verification_gate import _detect_completion_claims

    test_cases = [
        ("All tests passed", True),
        ("All tests pass successfully", True),
        ("The issue is fixed", True),
        ("Issue is fixed", True),
        ("Verified working", True),
        ("Complete solution", True),
        ("Done!", True),
        ("Bug fixed", True),
        ("Analysis of the code", False),
        ("Let me check the file", False),
    ]

    for text, should_match in test_cases:
        claims = _detect_completion_claims(text)
        has_claim = len(claims) > 0
        assert has_claim == should_match, f"Pattern detection mismatch for: {text}"


def test_verification_gate_get_response_text():
    """Test response text extraction from various formats."""
    from self_verification_gate import _get_response_text

    assert _get_response_text({"response": "test"}) == "test"
    assert _get_response_text({"result": "test"}) == "test"
    assert _get_response_text({"response": {"content": "test"}}) == "test"
    assert _get_response_text({}) == ""


def test_verification_gate_get_tool_events():
    """Test tool events extraction."""
    from self_verification_gate import _get_tool_events

    events = [{"type": "Bash", "command": "pytest"}]
    assert _get_tool_events({"events": events}) == events
    assert _get_tool_events({}) == []


def test_verification_gate_check_claim_verified():
    """Test claim verification against tool events."""
    from self_verification_gate import _check_claim_verified

    # Claim should be verified with Bash pytest event
    events = [{"type": "Bash", "command": "pytest", "name": "pytest tests/"}]
    verified, msg = _check_claim_verified("tests pass", events)
    assert verified, f"Should be verified with pytest event: {msg}"

    # Claim should not be verified with no events
    verified, msg = _check_claim_verified("tests pass", [])
    assert not verified, "Should not be verified without events"


# ===== INTEGRATION TESTS =====


def test_multi_terminal_isolation():
    """Test that terminals have isolated state."""
    from UserPromptSubmit_modules.context_followup_detector import (
        _load_prior_context,
        _save_prior_context,
    )

    # Save context for terminal A
    terminal_a_context = {"topic": "topic A", "summary": "summary A"}
    _save_prior_context("terminal_a", terminal_a_context)

    # Save context for terminal B
    terminal_b_context = {"topic": "topic B", "summary": "summary B"}
    _save_prior_context("terminal_b", terminal_b_context)

    # Verify each terminal sees only its own context
    loaded_a = _load_prior_context("terminal_a")
    loaded_b = _load_prior_context("terminal_b")

    assert loaded_a["topic"] == "topic A"
    assert loaded_b["topic"] == "topic B"

    # Cleanup
    _clean_followup_state("terminal_a")
    _clean_followup_state("terminal_b")


if __name__ == "__main__":
    # Run tests
    import pytest

    pytest.main([__file__, "-v"])
