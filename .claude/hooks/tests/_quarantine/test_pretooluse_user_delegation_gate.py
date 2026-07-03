#!/usr/bin/env python3
"""
Tests for PreToolUse_user_delegation_gate.

Covers ask-user-before-investigate enforcement on PreToolUse.
"""

import json as _json
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HOOKS_DIR))

from PreToolUse_user_delegation_gate import (
    _has_user_delegation_signal,
    run,
)
from __lib.anti_lazy_policy import (
    is_diagnostic_topic as _is_diagnostic_topic,
    extract_topic_keywords as _extract_topic_keywords,
    check_topic_relevant_investigation as _check_topic_relevant_investigation,
)

# Minimal mock for run() to test ledger-less logic
class MockLedger:
    def __init__(self, files_read=None, searches=None):
        self.files_read = files_read or []
        self.searches = searches or []


class TestIsDiagnosticTopic:
    """Tests for _is_diagnostic_topic."""

    def test_debug_keyword(self):
        assert _is_diagnostic_topic("debug why the hook is blocking") is True

    def test_investigate_keyword(self):
        assert _is_diagnostic_topic("investigate the Stop.py behavior") is True

    def test_diagnose_keyword(self):
        assert _is_diagnostic_topic("diagnose the error") is True

    def test_error_keyword(self):
        assert _is_diagnostic_topic("there's an error in the output") is True

    def test_issue_keyword(self):
        assert _is_diagnostic_topic("what's the issue with this hook") is True

    def test_hook_keyword(self):
        assert _is_diagnostic_topic("the hook is not firing") is True

    def test_root_cause_keyword(self):
        assert _is_diagnostic_topic("find the root cause") is True

    def test_rca_keyword(self):
        assert _is_diagnostic_topic("do an RCA on this failure") is True

    def test_non_diagnostic_plain_question(self):
        assert _is_diagnostic_topic("what time is it") is False

    def test_non_diagnostic_implementation(self):
        assert _is_diagnostic_topic("add a feature to handle this") is False

    def test_non_diagnostic_planning(self):
        assert _is_diagnostic_topic("plan the next sprint") is False

    def test_non_diagnostic_help(self):
        assert _is_diagnostic_topic("can you help me with this task") is False

    def test_why_question_not_diagnostic(self):
        # "why" alone is noise — requires diagnostic context
        assert _is_diagnostic_topic("why did you choose this approach") is False

    def test_empty_prompt(self):
        assert _is_diagnostic_topic("") is False
        assert _is_diagnostic_topic(None) is False  # type: ignore


class TestExtractTopicKeywords:
    """Tests for _extract_topic_keywords."""

    def test_extracts_file_path_components(self):
        keywords = _extract_topic_keywords(
            "debug Stop.py lazy closure detector"
        )
        assert "stop" in keywords or "Stop" in keywords

    def test_filters_short_tokens(self):
        keywords = _extract_topic_keywords("the file is in src/lib")
        assert "the" not in keywords
        assert "is" not in keywords
        assert "in" not in keywords

    def test_filters_common_noise(self):
        keywords = _extract_topic_keywords(
            "what is test_foo.py and tests/test_bar.py"
        )
        assert "what" not in keywords
        assert "is" not in keywords
        assert "and" not in keywords

    def test_returns_empty_for_short_prompt(self):
        assert _extract_topic_keywords("hi") == set()
        assert _extract_topic_keywords("ok") == set()
        assert _extract_topic_keywords("") == set()

    def test_extracts_alphanumeric_only(self):
        keywords = _extract_topic_keywords("fix bug in filename123.py")
        # Should extract "bug" and "fix" (not filtered as noise) and "filename123" (has digits)
        assert "bug" in keywords or "fix" in keywords or "filename123" in keywords


class TestHasUserDelegationSignal:
    """Tests for _has_user_delegation_signal."""

    def test_can_you_show_me_the_log(self):
        assert _has_user_delegation_signal("can you show me the log") is True

    def test_could_you_show_me_output(self):
        assert _has_user_delegation_signal("could you show me the output") is True

    def test_please_share_log(self):
        assert _has_user_delegation_signal("please share the log") is True

    def test_show_me_the_error(self):
        assert _has_user_delegation_signal("show me the error") is True

    def test_what_is_in_the_log(self):
        assert _has_user_delegation_signal("what's in the log") is True

    def test_what_does_the_log_say(self):
        assert _has_user_delegation_signal("what does the log say") is True

    def test_non_delegation_question(self):
        assert _has_user_delegation_signal("can you explain the design") is False

    def test_non_delegation_help(self):
        assert _has_user_delegation_signal("please help me") is False

    def test_non_delegation_plan(self):
        assert _has_user_delegation_signal("can you plan the next steps") is False

    def test_implementation_request(self):
        assert _has_user_delegation_signal("can you implement this fix") is False


class TestCheckTopicRelevantInvestigation:
    """Tests for _check_topic_relevant_investigation using mock ledger."""

    def test_no_ledger_returns_false(self, monkeypatch):
        """No ledger at all → False (no investigation)."""
        monkeypatch.setattr(
            "__lib.anti_lazy_policy.load_investigation_ledger",
            lambda: {},
        )
        result = _check_topic_relevant_investigation("debug Stop.py")
        assert result is False

    def test_empty_ledger_returns_false(self, monkeypatch):
        """Ledger with no files_read or searches → False."""
        monkeypatch.setattr(
            "__lib.anti_lazy_policy.load_investigation_ledger",
            lambda: {"files_read": [], "searches": [], "executions": []},
        )
        result = _check_topic_relevant_investigation("debug Stop.py")
        assert result is False

    def test_relevant_file_read_returns_true(self, monkeypatch):
        """File read matching topic keyword → True."""
        monkeypatch.setattr(
            "__lib.anti_lazy_policy.load_investigation_ledger",
            lambda: {"files_read": ["P:/.claude/hooks/Stop.py"], "searches": [], "executions": []},
        )
        result = _check_topic_relevant_investigation("debug Stop.py blocking")
        assert result is True

    def test_relevant_search_returns_true(self, monkeypatch):
        """Search matching topic keyword → True."""
        monkeypatch.setattr(
            "__lib.anti_lazy_policy.load_investigation_ledger",
            lambda: {"files_read": [], "searches": ["lazy_closure_detector"], "executions": []},
        )
        result = _check_topic_relevant_investigation("debug lazy closure")
        assert result is True

    def test_irrelevant_investigation_returns_false(self, monkeypatch):
        """Irrelevant files_read → False (topic-scoped correctly)."""
        monkeypatch.setattr(
            "__lib.anti_lazy_policy.load_investigation_ledger",
            lambda: {"files_read": ["P:/some/unrelated/file.py"], "searches": [], "executions": []},
        )
        result = _check_topic_relevant_investigation("debug Stop.py")
        assert result is False

    def test_no_topic_keywords_returns_true(self, monkeypatch):
        """No scorable keywords + non-empty ledger → True (nothing to scope against)."""
        # "hi" has no 3+ char alphanumeric parts → returns True
        monkeypatch.setattr(
            "__lib.anti_lazy_policy.load_investigation_ledger",
            lambda: {"files_read": ["P:/.claude/hooks/Stop.py"], "searches": [], "executions": []},
        )
        result = _check_topic_relevant_investigation("hi")
        assert result is True

    def test_fail_open_on_error(self, monkeypatch):
        """Exception in check → True (fail open)."""
        monkeypatch.setattr(
            "__lib.anti_lazy_policy.load_investigation_ledger",
            lambda: (_err for _err in [RuntimeError("test")]),
        )
        result = _check_topic_relevant_investigation("debug Stop.py")
        assert result is True


class TestRunGate:
    """End-to-end tests for run() using mock ledger."""

    def test_non_ask_user_tool_passes(self):
        """Non-AskUserQuestion tools always pass."""
        result = run({"tool_name": "Bash", "prompt": "debug Stop.py", "user_prompt": "debug Stop.py"})
        assert result is None

    def test_non_diagnostic_prompt_passes(self):
        """Non-diagnostic prompts pass even with delegation signal."""
        result = run({
            "tool_name": "AskUserQuestion",
            "prompt": "can you show me the log",
            "user_prompt": "can you show me the log",
        })
        assert result is None

    def test_diagnostic_without_delegation_signal_passes(self):
        """Diagnostic prompt without delegation signal passes."""
        result = run({
            "tool_name": "AskUserQuestion",
            "prompt": "debug the hook",
            "user_prompt": "debug the hook",
        })
        assert result is None

    def test_diagnostic_with_delegation_no_investigation_blocks(self, monkeypatch):
        """Diagnostic + delegation signal + no relevant investigation → BLOCK."""
        monkeypatch.setattr(
            "__lib.anti_lazy_policy.load_investigation_ledger",
            lambda: {"files_read": [], "searches": [], "executions": []},
        )
        result = run({
            "tool_name": "AskUserQuestion",
            "prompt": "debug Stop.py — can you show me the log",
            "user_prompt": "debug Stop.py — can you show me the log",
        })
        assert result is not None
        assert result["decision"] == "block"
        assert "ASK-USER-DELEGATION BLOCKED" in result["reason"]
        assert "blocking_hook" in result

    def test_diagnostic_with_delegation_with_relevant_investigation_passes(self, monkeypatch):
        """Diagnostic + delegation + relevant investigation → PASS."""
        monkeypatch.setattr(
            "__lib.anti_lazy_policy.load_investigation_ledger",
            lambda: {"files_read": ["P:/.claude/hooks/Stop.py"], "searches": [], "executions": []},
        )
        result = run({
            "tool_name": "AskUserQuestion",
            "prompt": "debug Stop.py — can you show me the log",
            "user_prompt": "debug Stop.py — can you show me the log",
        })
        assert result is None

    def test_diagnostic_with_delegation_stale_unrelated_investigation_blocks(self, monkeypatch):
        """Diagnostic + delegation + stale unrelated investigation → BLOCK."""
        monkeypatch.setattr(
            "__lib.anti_lazy_policy.load_investigation_ledger",
            lambda: {"files_read": ["P:/some/completely/unrelated/path.py"], "searches": [], "executions": []},
        )
        result = run({
            "tool_name": "AskUserQuestion",
            "prompt": "debug Stop.py — can you show me the log",
            "user_prompt": "debug Stop.py — can you show me the log",
        })
        assert result is not None
        assert result["decision"] == "block"

    def test_plan_control_framing_does_not_bypass(self, monkeypatch):
        """PLAN framing on diagnostic task does not bypass gate."""
        monkeypatch.setattr(
            "__lib.anti_lazy_policy.load_investigation_ledger",
            lambda: {"files_read": [], "searches": [], "executions": []},
        )
        result = run({
            "tool_name": "AskUserQuestion",
            "prompt": "[PLAN] debug Stop.py — can you show me the log",
            "user_prompt": "[PLAN] debug Stop.py — can you show me the log",
        })
        assert result is not None
        assert result["decision"] == "block"

    def test_control_framing_does_not_bypass(self, monkeypatch):
        """CONTROL framing on diagnostic task does not bypass gate."""
        monkeypatch.setattr(
            "__lib.anti_lazy_policy.load_investigation_ledger",
            lambda: {"files_read": [], "searches": [], "executions": []},
        )
        result = run({
            "tool_name": "AskUserQuestion",
            "prompt": "[CONTROL] debug Stop.py — can you show me the log",
            "user_prompt": "[CONTROL] debug Stop.py — can you show me the log",
        })
        assert result is not None
        assert result["decision"] == "block"

    def test_empty_user_prompt_passes(self):
        """Empty prompt passes (no signal to evaluate)."""
        result = run({"tool_name": "AskUserQuestion", "prompt": ""})
        assert result is None

    def test_missing_prompt_passes(self):
        """Missing prompt field passes (graceful)."""
        result = run({"tool_name": "AskUserQuestion"})
        assert result is None


class TestPreToolUseAskUserQuestionBlocking:
    """Tests confirming PreToolUse gate blocks AskUserQuestion (no regression)."""

    def test_ask_user_on_diagnostic_without_investigation_blocks(self, monkeypatch):
        """AskUserQuestion on diagnostic topic with no prior relevant investigation → block."""
        monkeypatch.setattr(
            "__lib.anti_lazy_policy.load_investigation_ledger",
            lambda: {"files_read": [], "searches": [], "executions": []},
        )
        result = run({
            "tool_name": "AskUserQuestion",
            "prompt": "debug Stop.py — can you show me the log",
            "user_prompt": "debug Stop.py — can you show me the log",
        })
        assert result is not None
        assert result["decision"] == "block"
        assert "ASK-USER-DELEGATION BLOCKED" in result["reason"]

    def test_ask_user_with_relevant_investigation_passes(self, monkeypatch):
        """AskUserQuestion when ledger has relevant investigation → pass."""
        monkeypatch.setattr(
            "__lib.anti_lazy_policy.load_investigation_ledger",
            lambda: {"files_read": ["P:/.claude/hooks/Stop.py"], "searches": [], "executions": []},
        )
        result = run({
            "tool_name": "AskUserQuestion",
            "prompt": "debug Stop.py — can you show me the log",
            "user_prompt": "debug Stop.py — can you show me the log",
        })
        assert result is None

    def test_non_diagnostic_ask_user_passes(self, monkeypatch):
        """AskUserQuestion on non-diagnostic topic always passes."""
        monkeypatch.setattr(
            "__lib.anti_lazy_policy.load_investigation_ledger",
            lambda: {"files_read": [], "searches": [], "executions": []},
        )
        result = run({
            "tool_name": "AskUserQuestion",
            "prompt": "can you plan the next sprint",
            "user_prompt": "can you plan the next sprint",
        })
        assert result is None


class TestLazyClosureEscalationStop:
    """Tests for Stop._lazy_closure_escalation cooperative reset and topic isolation."""

    def test_same_topic_escalation_returns_1_then_2(self, monkeypatch):
        """Same topic escalation returns 1 on first block, 2 on repeated."""
        monkeypatch.setattr(
            "__lib.anti_lazy_policy.check_topic_relevant_investigation",
            lambda p: False,
        )
        import Stop
        # Use a unique session to avoid state pollution
        import uuid
        sid = f"test-{uuid.uuid4().hex[:8]}"
        tid = "test-term"
        path = Path.home() / ".claude" / ".artifacts" / sid / "lazy_closure_escalation.json"
        if path.exists():
            path.unlink()

        r1 = Stop._lazy_closure_escalation(sid, tid, "sample-escal", "diagnose log issue")
        r2 = Stop._lazy_closure_escalation(sid, tid, "sample-escal", "diagnose log issue")
        assert r1 == 1, f"first call should be 1, got {r1}"
        assert r2 == 2, f"second call should be 2, got {r2}"

        if path.exists():
            path.unlink()

    def test_different_topics_do_not_share_counter(self, monkeypatch):
        """Different topics maintain separate counters."""
        monkeypatch.setattr(
            "__lib.anti_lazy_policy.check_topic_relevant_investigation",
            lambda p: False,
        )
        import Stop
        import uuid
        sid = f"test-{uuid.uuid4().hex[:8]}"
        tid = "test-term"
        path = Path.home() / ".claude" / ".artifacts" / sid / "lazy_closure_escalation.json"
        if path.exists():
            path.unlink()

        r1 = Stop._lazy_closure_escalation(sid, tid, "sample-a", "diagnose log issue")
        r2 = Stop._lazy_closure_escalation(sid, tid, "sample-b", "diagnose config issue")
        assert r1 == 1, f"first topic should be 1, got {r1}"
        assert r2 == 1, f"different topic should also be 1, got {r2}"

        if path.exists():
            path.unlink()

    def test_cooperative_reset_clears_counter_after_investigation(self, monkeypatch):
        """When check_topic_relevant_investigation returns True, counter clears and returns 1."""
        call_count = [0]
        def fake_ctri(prompt):
            call_count[0] += 1
            return True  # Always indicate investigation exists
        monkeypatch.setattr(
            "__lib.anti_lazy_policy.check_topic_relevant_investigation",
            fake_ctri,
        )
        import Stop
        import uuid
        sid = f"test-{uuid.uuid4().hex[:8]}"
        tid = "test-term"
        path = Path.home() / ".claude" / ".artifacts" / sid / "lazy_closure_escalation.json"
        if path.exists():
            path.unlink()

        # First call - should reset and return 1
        r1 = Stop._lazy_closure_escalation(sid, tid, "sample-reset", "diagnose log issue")
        # Second call - cooperative reset fires again, counter stays cleared
        r2 = Stop._lazy_closure_escalation(sid, tid, "sample-reset", "diagnose log issue")
        assert r1 == 1, f"with reset, first call should be 1, got {r1}"
        assert r2 == 1, f"with reset, second call should also be 1, got {r2}"

        if path.exists():
            path.unlink()

    def test_save_lazy_escalation_state_overwrites_existing_file(self, monkeypatch):
        """Regression: tmp.replace(target) must atomically overwrite on Windows.

        On Windows, os.rename() raises FileExistsError when the target already exists,
        causing every second save to silently drop state.  os.replace() atomically
        overwrites regardless of whether the target exists.
        """
        import Stop
        import uuid
        sid = f"test-{uuid.uuid4().hex[:8]}"
        tid = "test-term"
        path = Path.home() / ".claude" / ".artifacts" / sid / "lazy_closure_escalation.json"
        if path.exists():
            path.unlink()

        # Write initial state (v1)
        Stop._save_lazy_escalation_state(sid, {"counter": 1})
        assert path.exists(), "first write must succeed"
        assert _json.loads(path.read_text())["counter"] == 1

        # Overwrite with new state (v2) — this is where rename() would fail silently
        Stop._save_lazy_escalation_state(sid, {"counter": 2})
        assert path.exists(), "second write must also succeed"
        assert _json.loads(path.read_text())["counter"] == 2, \
            "replace() must atomically overwrite; rename() would leave stale v1 content"

        if path.exists():
            path.unlink()


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))