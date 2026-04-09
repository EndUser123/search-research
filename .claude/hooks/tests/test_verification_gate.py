#!/usr/bin/env python3
"""Test suite for Stop_verification_gate.py hook."""

import subprocess
from pathlib import Path

import pytest


def run_hook(response_text: str) -> dict:
    """Helper to run hook and capture output."""
    hook_path = Path("P:/.claude/hooks/stop/Stop_verification_gate.py")

    process = subprocess.run(
        ["python", str(hook_path)],
        input=response_text,
        capture_output=True,
        text=True,
        cwd="P:/"
    )

    return {
        "exit_code": process.returncode,
        "stdout": process.stdout,
        "stderr": process.stderr
    }


class TestVerificationGateBasicPatterns:
    """Test basic claim detection patterns."""

    def test_empty_response_allowed(self):
        """Empty responses should pass through."""
        result = run_hook("")
        assert result["exit_code"] == 0

    def test_code_only_response_allowed(self):
        """Code-only responses (starting with #) should pass."""
        result = run_hook("# Python code\nprint('hello')")
        assert result["exit_code"] == 0

    def test_claim_without_test_blocked(self):
        """Claims without testing evidence should be blocked."""
        # "The problem is X" matches CLAIM_PATTERNS[1] without test evidence
        response = "The problem is the configuration file."
        result = run_hook(response)
        assert result["exit_code"] == 1
        assert "Verification Gate" in result["stdout"]

    def test_premature_solution_blocked(self):
        """Premature solution jumps should be blocked."""
        response = "Let's fix this by updating the config."
        result = run_hook(response)
        assert result["exit_code"] == 1
        assert "BEHAV-001" in result["stdout"]


class TestVerificationGateWithEvidence:
    """Test that responses with verification evidence pass."""

    def test_claim_with_test_allowed(self):
        """Claims backed by test evidence should pass."""
        response = """
        Hypothesis: The issue is in config.py

        Test: python -m pytest tests/test_config.py -v
        Result: PASSED

        Conclusion: Config module is working correctly
        """
        result = run_hook(response)
        assert result["exit_code"] == 0

    def test_diagnostic_with_evidence_allowed(self):
        """Structured diagnostic with evidence should pass."""
        response = """
        ## Diagnostic Investigation

        **Hypotheses**:
        H1: Plugin interference
        H2: Missing module

        **Test Results**:
        H1: pytest -v -p no:plugin → Tests pass → RULED OUT
        H2: grep -r module → Not found → CONFIRMED

        **Conclusion**: H2 confirmed
        """
        result = run_hook(response)
        assert result["exit_code"] == 0


class TestVerificationGatePatterns:
    """Test specific pattern detection."""

    def test_single_hypothesis_blocked(self):
        """Single hypothesis without testing should be blocked."""
        # Uses hypothesis table format with single hypothesis + root cause
        response = "| ✓ | H1: The root cause is the plugin | Tests confirm |\nThe problem is the test plugin."
        result = run_hook(response)
        assert result["exit_code"] == 1
        assert "BEHAV-002" in result["stdout"]

    def test_diagnostic_jumping_blocked(self):
        """Jumping between diagnostic approaches should be blocked."""
        # 6 diagnostic approaches triggers BEHAV-004 (>3)
        response = """Let's try checking the logs.
Actually, let's try the config file.
Wait, let's look at the test output.
Maybe we should check dependencies.
Let's also examine the environment.
And let's verify the setup."""
        result = run_hook(response)
        assert result["exit_code"] == 1
        assert "BEHAV-004" in result["stdout"]

    def test_unverified_claim_blocked(self):
        """Unverified claims should be blocked."""
        # "Probably a bug" matches CLAIM_PATTERNS[4] without test evidence
        response = "Probably a bug in the code."
        result = run_hook(response)
        assert result["exit_code"] == 1
        assert "BEHAV-003" in result["stdout"]


class TestVerificationGateOutputFormat:
    """Test that hook produces helpful output."""

    def test_violation_message_format(self):
        """Violation messages should be well-formatted."""
        # "The problem is X" triggers CLAIM_PATTERNS without test evidence
        response = "The problem is misconfigured."
        result = run_hook(response)
        assert result["exit_code"] == 1
        assert "Verification Gate" in result["stdout"]
        assert "BEHAV-003" in result["stdout"]
        assert "MEMORY.md" in result["stdout"]

    def test_multiple_violations_listed(self):
        """Multiple violations should all be listed."""
        # Triggers both BEHAV-003 (claim) and BEHAV-001 (solution jump)
        response = "The problem is the config. Let's fix it now."
        result = run_hook(response)
        assert result["exit_code"] == 1
        violations = result["stdout"].count("BEHAV-")
        assert violations >= 2


@pytest.mark.parametrize("response,should_block", [
    ("The problem is X.", True),
    ("Let's fix the bug.", True),
    ("Test output shows error in line 42.", False),
    ("# Code comment", False),
    ("", False),
])
def test_verification_gate_decision_matrix(response, should_block):
    """Parametrized test for various response types."""
    result = run_hook(response)
    if should_block:
        assert result["exit_code"] == 1
    else:
        assert result["exit_code"] == 0
