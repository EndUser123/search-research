#!/usr/bin/env python3
"""Tests for Stop_hypothesis_enforcement.py

Tests the hypothesis-before-root-cause enforcement gate.
"""

import pytest
from Stop_hypothesis_enforcement import run


class TestBlockRootCauseWithoutHypothesis:
    """Block 'root cause:' without preceding 'Hypothesis:'"""

    def test_root_cause_without_hypothesis(self):
        """Must block root cause statement without any hypothesis."""
        data = {
            "response_text": "The issue is that the file is missing. Root cause: the file was never created."
        }
        result = run(data)
        assert result["allow"] is False
        assert "UNVERIFIED HYPOTHESIS DETECTED" in result["reason"]

    def test_root_cause_capitalized(self):
        """Must block 'Root Cause:' (capitalized) without hypothesis."""
        data = {
            "response_text": "The issue is that the file is missing. Root Cause: the file was never created."
        }
        result = run(data)
        assert result["allow"] is False
        assert "UNVERIFIED HYPOTHESIS DETECTED" in result["reason"]

    def test_root_cause_lowercase(self):
        """Must block 'root cause:' (lowercase) without hypothesis."""
        data = {
            "response_text": "The issue is that the file is missing. root cause: the file was never created."
        }
        result = run(data)
        assert result["allow"] is False

    def test_root_cause_with_space(self):
        """Must block 'root cause :' (with space) without hypothesis."""
        data = {
            "response_text": "The issue is that the file is missing. root cause : the file was never created."
        }
        result = run(data)
        assert result["allow"] is False


class TestAllowRootCauseWithHypothesisAndEvidence:
    """Allow 'root cause:' after 'Hypothesis:' + verification evidence."""

    def test_hypothesis_with_tool_output_before_root_cause(self):
        """Must allow when hypothesis exists and tool output shown."""
        data = {
            "response_text": (
                "Hypothesis: The file might be missing because it was never created.\n"
                "Tool output shows the directory is empty.\n"
                "Root cause: the file was never created."
            )
        }
        result = run(data)
        assert result["allow"] is True
        assert "Hypothesis structure verified" in result["reason"]

    def test_hypothesis_with_test_results_before_root_cause(self):
        """Must allow when hypothesis exists and test results shown."""
        data = {
            "response_text": (
                "Hypothesis: The hook might not be registered.\n"
                "Test results: 0 tests passed, hook did not fire.\n"
                "Root cause: the hook registration failed."
            )
        }
        result = run(data)
        assert result["allow"] is True

    def test_hypothesis_with_pytest_output(self):
        """Must allow when pytest output shown between hypothesis and root cause."""
        data = {
            "response_text": (
                "Hypothesis: The function might be returning None.\n"
                "pytest shows FAILED test_my_function\n"
                "Root cause: missing return statement."
            )
        }
        result = run(data)
        assert result["allow"] is True

    def test_hypothesis_with_code_block(self):
        """Must allow when code block shown between hypothesis and root cause."""
        data = {
            "response_text": (
                "Hypothesis: The regex pattern might be incorrect.\n"
                "```\n"
                "re.compile(r'pattern['\"]')\n"
                "```\n"
                "Root cause: the regex has a syntax error."
            )
        }
        result = run(data)
        assert result["allow"] is True

    def test_hypothesis_with_error_keyword(self):
        """Must allow when error/exception shown between hypothesis and root cause."""
        data = {
            "response_text": (
                "Hypothesis: The import might be failing.\n"
                "Exception: ModuleNotFoundError: No module named 'requests'\n"
                "Root cause: missing dependency."
            )
        }
        result = run(data)
        assert result["allow"] is True

    def test_hypothesis_with_file_reference(self):
        """Must allow when file reference shown between hypothesis and root cause."""
        data = {
            "response_text": (
                "Hypothesis: The settings might be incorrect.\n"
                "file: settings.json shows empty hooks list\n"
                "Root cause: hooks not configured."
            )
        }
        result = run(data)
        assert result["allow"] is True


class TestBlockHypothesisWithoutEvidence:
    """Block 'Hypothesis:' without verification evidence before 'root cause:'."""

    def test_hypothesis_without_evidence(self):
        """Must block when hypothesis exists but no evidence shown before root cause."""
        data = {
            "response_text": (
                "Hypothesis: The file might be missing.\nRoot cause: the file was never created."
            )
        }
        result = run(data)
        assert result["allow"] is False
        assert "MISSING VERIFICATION EVIDENCE" in result["reason"]

    def test_hypothesis_with_text_between_but_no_evidence(self):
        """Must block when only explanatory text exists between hypothesis and root cause."""
        data = {
            "response_text": (
                "Hypothesis: The file might be missing.\n"
                "I need to check if the file exists first.\n"
                "Root cause: the file was never created."
            )
        }
        result = run(data)
        assert result["allow"] is False


class TestEdgeCases:
    """Edge case handling."""

    def test_empty_response(self):
        """Must allow empty response (too short to analyze)."""
        data = {"response_text": ""}
        result = run(data)
        assert result["allow"] is True

    def test_short_response(self):
        """Must allow very short response (less than 20 chars)."""
        data = {"response_text": "Root cause: test"}
        result = run(data)
        assert result["allow"] is True

    def test_no_root_cause(self):
        """Must allow response without root cause statement."""
        data = {"response_text": "Hypothesis: The file might be missing."}
        result = run(data)
        assert result["allow"] is True
        assert "No root cause statement detected" in result["reason"]

    def test_hypothesis_only_no_root_cause(self):
        """Must allow hypothesis without root cause (normal reasoning)."""
        data = {
            "response_text": (
                "Hypothesis: The file might be missing.\nLet me check the directory first."
            )
        }
        result = run(data)
        assert result["allow"] is True

    def test_gate_disabled(self, monkeypatch):
        """Must allow when REASONING_HYGIENE_ENABLED=false."""
        monkeypatch.setenv("REASONING_HYGIENE_ENABLED", "false")
        data = {"response_text": "Root cause: test without hypothesis"}
        result = run(data)
        assert result["allow"] is True
        assert "Gate disabled" in result["reason"]

    def test_multiple_hypotheses_uses_last(self):
        """Must use the last hypothesis before root cause."""
        data = {
            "response_text": (
                "Hypothesis: The file might be at the wrong path.\n"
                "Hypothesis: The hook registration might have failed.\n"
                "Root cause: hook not registered."
            )
        }
        result = run(data)
        # Should block because second hypothesis has no evidence
        assert result["allow"] is False

    def test_hypothesis_after_root_cause_ignored(self):
        """Must only consider hypothesis BEFORE root cause."""
        data = {
            "response_text": (
                "Root cause: the file was never created.\n"
                "Hypothesis: Maybe I should create the file."
            )
        }
        result = run(data)
        assert result["allow"] is False


class TestRegexPatterns:
    """Test individual regex patterns."""

    def test_verification_evidence_tool_output(self):
        """Must detect 'tool output:' as verification evidence."""
        data = {
            "response_text": (
                "Hypothesis: The file might be missing.\n"
                "tool output: directory is empty\n"
                "Root cause: file not found."
            )
        }
        result = run(data)
        assert result["allow"] is True

    def test_verification_evidence_test_result(self):
        """Must detect 'test result:' as verification evidence."""
        data = {
            "response_text": (
                "Hypothesis: The hook might not fire.\n"
                "test result: hook did not trigger\n"
                "Root cause: registration failed."
            )
        }
        result = run(data)
        assert result["allow"] is True

    def test_verification_evidence_from_above_tool(self):
        """Must detect 'from the above tool output' as verification."""
        data = {
            "response_text": (
                "Hypothesis: The file might be missing.\n"
                "from the above tool output, I can see the directory is empty\n"
                "Root cause: file not found."
            )
        }
        result = run(data)
        assert result["allow"] is True

    def test_verification_evidence_bash_shows(self):
        """Must detect 'bash shows' as verification evidence."""
        data = {
            "response_text": (
                "Hypothesis: The directory might be empty.\n"
                "bash shows no files in the directory\n"
                "Root cause: directory is empty."
            )
        }
        result = run(data)
        assert result["allow"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
