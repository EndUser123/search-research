"""Tests for Stop_correction_followthrough_gate."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure hooks dir is on path
_HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))


def _run_gate(data: dict) -> dict | None:
    """Import and call _run_gate from Stop_correction_followthrough_gate."""
    import importlib

    import Stop_correction_followthrough_gate
    importlib.reload(Stop_correction_followthrough_gate)
    return Stop_correction_followthrough_gate._run_gate(data)


class TestNoCorrectionNoop:
    """Gate should do nothing when no correction is detected."""

    def test_no_correction_in_user_prompt(self):
        """No correction in user prompt, no transcript — no-op."""
        data = {
            "user_prompt": "Can you explain how the gate works?",
            "response": "The gate checks for corrections and requires follow-through.",
            "transcript_path": "",
            "tool_events": [],
        }
        result = _run_gate(data)
        assert result is None

    def test_no_correction_in_transcript(self):
        """No correction in transcript path — no-op."""
        data = {
            "user_prompt": "What files were changed?",
            "response": "Three files were modified.",
            "transcript_path": "P:/fake/nonexistent_transcript.txt",
            "tool_events": [],
        }
        # Transcript read will fail (file doesn't exist) — should gracefully skip
        result = _run_gate(data)
        assert result is None

    def test_empty_response(self):
        """Empty response should be no-op."""
        data = {
            "user_prompt": "You're wrong about that",
            "response": "",
            "tool_events": [],
        }
        result = _run_gate(data)
        assert result is None


class TestPureAckBlocked:
    """Pure acknowledgments without re-check evidence should be blocked."""

    def test_understood_acknowledged_blocked(self):
        """'Understood' without re-check should block."""
        data = {
            "user_prompt": "You're wrong — that hook is in PreToolUse, not Stop.",
            "response": "Understood, thanks for the correction.",
            "tool_events": [],
        }
        result = _run_gate(data)
        assert result is not None
        assert result["decision"] == "block"
        assert "CORRECTION WITHOUT FOLLOW-THROUGH" in result["systemMessage"]

    def test_got_it_blocked(self):
        """'Got it' without re-check should block."""
        data = {
            "user_prompt": "No, that's incorrect. The critical hooks are set at import time.",
            "response": "Got it.",
            "tool_events": [],
        }
        result = _run_gate(data)
        assert result is not None
        assert result["decision"] == "block"

    def test_thanks_acknowledge_blocked(self):
        """'Thanks for the correction' without re-check should block."""
        data = {
            "user_prompt": "I didn't say that — you're misquoting me.",
            "response": "Thanks for the clarification!",
            "tool_events": [],
        }
        result = _run_gate(data)
        assert result is not None
        assert result["decision"] == "block"

    def test_acknowledged_with_evidence_of_tool_use_still_blocked(self):
        """Pure ack even with tool events but no re-check language should block."""
        data = {
            "user_prompt": "No, you're wrong about the threshold value.",
            "response": "Acknowledged.",
            "tool_events": [
                {"name": "Bash", "command": "echo test", "output": "test output"},
            ],
        }
        result = _run_gate(data)
        # Tool event exists but no re-check language in response
        assert result is not None
        assert result["decision"] == "block"

    def test_apology_dismissal_blocked(self):
        """Apology + dismissal pattern should block."""
        data = {
            "user_prompt": "No, you're wrong. The gate uses regex, not AST.",
            "response": "I apologize, but that is incorrect — the gate uses regex as documented. Working as designed.",
            "tool_events": [],
        }
        result = _run_gate(data)
        assert result is not None
        assert result["decision"] == "block"


class TestRecheckAllowed:
    """Responses with re-check evidence should be allowed."""

    def test_re_read_block_allows(self):
        """'I re-read' should allow."""
        data = {
            "user_prompt": "No, that's wrong. The CRITICAL_HOOKS set is in PreToolUse.py.",
            "response": "You're right. I re-read PreToolUse.py and confirmed CRITICAL_HOOKS is defined at line 95.",
            "tool_events": [],
        }
        result = _run_gate(data)
        assert result is None

    def test_ran_pytest_allows(self):
        """'I ran pytest' should allow."""
        data = {
            "user_prompt": "That's not correct — the test should pass, not fail.",
            "response": "You're right. I ran pytest and all 15 tests passed. I had a stale cache.",
            "tool_events": [],
        }
        result = _run_gate(data)
        assert result is None

    def test_could_not_verify_allows(self):
        """'I could not verify' with attempt description should allow."""
        data = {
            "user_prompt": "You're wrong — the gate doesn't use that env var.",
            "response": "I could not verify whether that env var is used. I grep'd for it in Stop.py but found no match, and checking the verification engine as well.",
            "tool_events": [],
        }
        result = _run_gate(data)
        assert result is None

    def test_tool_event_allows(self):
        """Tool events this turn should allow even without explicit re-check language."""
        data = {
            "user_prompt": "No, that function doesn't exist. Check again.",
            "response": "I see. Let me look at the file directly.",
            "tool_events": [
                {"name": "Read", "command": "P:/.claude/hooks/Stop.py", "output": "def _run_gate..."},
            ],
        }
        result = _run_gate(data)
        assert result is None

    def test_after_reading_allows(self):
        """'After reading' followed by conclusion should allow."""
        data = {
            "user_prompt": "Wrong. The gate is in Stop_router.py, not Stop.py.",
            "response": "After reading Stop_router.py, I can confirm the gate is registered there. I'll update my understanding.",
            "tool_events": [],
        }
        result = _run_gate(data)
        assert result is None

    def test_confirms_allows(self):
        """Response with 'confirms' should allow."""
        data = {
            "user_prompt": "No, that's not how it works.",
            "response": "Checking the code confirms that the gate runs at Stop phase, not PreToolUse.",
            "tool_events": [],
        }
        result = _run_gate(data)
        assert result is None


class TestWarnMode:
    """Warn mode should allow but emit systemMessage."""

    def test_pure_ack_warns_in_warn_mode(self, monkeypatch):
        """In warn mode, pure ack should allow but emit systemMessage."""
        import os
        monkeypatch.setenv("CORRECTION_FOLLOWTHROUGH_MODE", "warn")

        import importlib
        import Stop_correction_followthrough_gate
        importlib.reload(Stop_correction_followthrough_gate)

        data = {
            "user_prompt": "You're wrong about that.",
            "response": "Understood.",
            "tool_events": [],
        }
        result = Stop_correction_followthrough_gate._run_gate(data)
        assert result is not None
        assert result["decision"] == "allow"
        assert "CORRECTION WITHOUT FOLLOW-THROUGH" in result["systemMessage"]


class TestNoTranscriptPath:
    """When transcript_path is empty, gate should still detect this-turn corrections."""

    def test_this_turn_correction_no_transcript(self):
        """Correction in user_prompt without transcript should still fire."""
        data = {
            "user_prompt": "No, that's wrong. The CRITICAL_HOOKS is in PreToolUse.py.",
            "response": "Understood. I'll check the file.",
            "tool_events": [],
        }
        result = _run_gate(data)
        assert result is not None
        assert result["decision"] == "block"

    def test_this_turn_correction_with_recheck_allowed(self):
        """Correction in user_prompt with re-check should allow."""
        data = {
            "user_prompt": "No — that's not right. The gate is registered in Stop_router.py.",
            "response": "You're right. I re-read Stop_router.py and see it at line 289.",
            "tool_events": [],
        }
        result = _run_gate(data)
        assert result is None