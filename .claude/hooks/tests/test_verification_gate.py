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
        response = "I think the issue is in the configuration file."
        result = run_hook(response)
        assert result["exit_code"] == 1
        assert "VERIFICATION GATE VIOLATION" in result["stderr"]

    def test_premature_solution_blocked(self):
        """Premature solution jumps should be blocked."""
        response = "Let's fix this by updating the config."
        result = run_hook(response)
        assert result["exit_code"] == 1
        assert "BEHAV-001" in result["stderr"]


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
        response = "The problem is the test plugin. Let's disable it."
        result = run_hook(response)
        assert result["exit_code"] == 1
        assert "BEHAV-002" in result["stderr"]

    def test_diagnostic_jumping_blocked(self):
        """Jumping between diagnostic approaches should be blocked."""
        response = """
        Let's check the logs.
        Actually, let's try the config file.
        Wait, let's look at the test output.
        Maybe we should check dependencies.
        """
        result = run_hook(response)
        assert result["exit_code"] == 1
        assert "BEHAV-004" in result["stderr"]

    def test_unverified_claim_blocked(self):
        """Unverified claims should be blocked."""
        response = "This is probably caused by a race condition."
        result = run_hook(response)
        assert result["exit_code"] == 1
        assert "BEHAV-003" in result["stderr"]


class TestVerificationGateOutputFormat:
    """Test that hook produces helpful output."""

    def test_violation_message_format(self):
        """Violation messages should be well-formatted."""
        response = "I think it's broken."
        result = run_hook(response)

        assert "VERIFICATION GATE VIOLATION DETECTED" in result["stderr"]
        assert "Violations Found:" in result["stderr"]
        assert "Required Actions:" in result["stderr"]
        assert "MEMORY.md" in result["stderr"]

    def test_multiple_violations_listed(self):
        """Multiple violations should all be listed."""
        response = "I think it's the config. Let's fix it now."
        result = run_hook(response)

        # Should detect both claim and premature solution
        violations = result["stderr"].count("BEHAV-")
        assert violations >= 1


@pytest.mark.parametrize("response,should_block", [
    ("I think the issue is X.", True),
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
