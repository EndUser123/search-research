#!/usr/bin/env python3
"""Tests for Stop_fix_verification_enforcer.py

Tests the fix verification enforcer gate.
"""

from Stop_fix_verification_enforcer import run


class TestBlockTopicTransitionWithoutVerification:
    """Block topic transitions without verification evidence."""

    def test_moving_on_without_verification_blocks(self):
        """Must block when 'moving on' without verification evidence."""
        data = {"response_text": "The fix is applied. Moving on to the next issue."}
        result = run(data)
        assert result["allow"] is False
        assert "TOPIC TRANSITION WITHOUT VERIFICATION" in result["reason"]

    def test_next_issue_without_verification_blocks(self):
        """Must block 'next issue' without verification."""
        data = {"response_text": "Let me address that. Next issue: the timeout problem."}
        result = run(data)
        assert result["allow"] is False

    def test_lets_move_to_without_verification_blocks(self):
        """Must block 'let's move to' without verification."""
        data = {"response_text": "The hook is fixed. Let's move to the next topic."}
        result = run(data)
        assert result["allow"] is False

    def test_changing_subject_without_verification_blocks(self):
        """Must block 'changing subject' without verification."""
        data = {"response_text": "That issue is resolved. Changing subject to the CLI."}
        result = run(data)
        assert result["allow"] is False

    def test_moving_on_uppercase_blocks(self):
        """Must block uppercase 'MOVING ON' without verification."""
        data = {"response_text": "The fix works. MOVING ON to the next problem."}
        result = run(data)
        assert result["allow"] is False

    def test_lets_talk_about_blocks(self):
        """Must block 'let's talk about' without verification."""
        data = {"response_text": "That bug is fixed. Let's talk about the timeout issue."}
        result = run(data)
        assert result["allow"] is False


class TestAllowWithVerificationEvidence:
    """Allow transitions when verification evidence is present."""

    def test_pytest_output_before_transition_allows(self):
        """Must allow when pytest results shown before transition."""
        data = {"response_text": "Test results: 12 passed, 0 failed. Moving on to the next issue."}
        result = run(data)
        assert result["allow"] is True

    def test_tool_output_before_transition_allows(self):
        """Must allow when tool output shown before transition."""
        data = {
            "response_text": "Tool output shows the fix is working correctly. Let's move to the next topic."
        }
        result = run(data)
        assert result["allow"] is True

    def test_code_block_before_transition_allows(self):
        """Must allow when code block appears before transition."""
        data = {"response_text": "```\nAll tests passing\n```\nNext issue: the timeout."}
        result = run(data)
        assert result["allow"] is True

    def test_test_passed_before_transition_allows(self):
        """Must allow when 'test passed' appears before transition."""
        data = {"response_text": "Test passed successfully. Moving on to the next issue."}
        result = run(data)
        assert result["allow"] is True

    def test_file_read_before_transition_allows(self):
        """Must allow when file read evidence appears before transition."""
        data = {
            "response_text": "file: settings.json shows the hook is registered. Let's move to the next topic."
        }
        result = run(data)
        assert result["allow"] is True

    def test_error_output_before_transition_allows(self):
        """Must allow when error/traceback evidence appears before transition."""
        data = {
            "response_text": "Error: connection refused - but the fix is applied. Changing subject."
        }
        result = run(data)
        assert result["allow"] is True


class TestEdgeCases:
    """Edge cases."""

    def test_empty_response_allows(self):
        """Empty response should be allowed."""
        data = {"response_text": ""}
        result = run(data)
        assert result["allow"] is True

    def test_short_response_allows(self):
        """Very short response should be allowed."""
        data = {"response_text": "Hi"}
        result = run(data)
        assert result["allow"] is True

    def test_no_transition_phrase_allows(self):
        """Response without transition phrase should be allowed."""
        data = {"response_text": "The fix is working correctly."}
        result = run(data)
        assert result["allow"] is True

    def test_gate_disabled_allows(self, monkeypatch):
        """When gate is disabled, should allow everything."""
        monkeypatch.setenv("FIX_VERIFICATION_ENFORCER_ENABLED", "false")
        data = {"response_text": "Moving on to the next issue."}
        result = run(data)
        assert result["allow"] is True
        assert "Gate disabled" in result["reason"]

    def test_transition_at_end_with_verification_allows(self):
        """Transition at end with prior verification should be allowed."""
        data = {"response_text": "The test ran successfully and passed. Moving on."}
        result = run(data)
        assert result["allow"] is True
