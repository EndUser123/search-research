#!/usr/bin/env python3
"""Tests for judge_feedback.py Session Start and First-Query Advisory."""

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent
# Add hooks/__lib to path for judge_feedback module
sys.path.insert(0, str(HOOKS_DIR / "__lib"))
# Add hooks dir for judge_first_query_advisory module
sys.path.insert(0, str(HOOKS_DIR))


class TestLoadRecentVerdicts:
    """Test load_recent_judge_verdicts function."""

    def test_no_file_returns_empty(self):
        from judge_feedback import load_recent_judge_verdicts

        with patch("judge_feedback._JUDGE_VERDICTS_PATH", Path("/nonexistent/path.jsonl")):
            result = load_recent_judge_verdicts(hours=24)
            assert result == []

    def test_filters_by_timestamp(self):
        from judge_feedback import load_recent_judge_verdicts
        import tempfile
        import os

        # Create temp file with verdicts
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            old_verdict = {
                "timestamp": 1000000000.0,  # Old timestamp
                "score": 0.9,
                "passes": True,
            }
            f.write(json.dumps(old_verdict) + "\n")
            new_verdict = {
                "timestamp": float(os.path.getmtime(__file__)),  # Recent timestamp
                "score": 0.7,
                "passes": True,
            }
            f.write(json.dumps(new_verdict) + "\n")
            temp_path = f.name

        try:
            with patch("judge_feedback._JUDGE_VERDICTS_PATH", Path(temp_path)):
                result = load_recent_judge_verdicts(hours=24)
                # Should only get the recent verdict
                assert len(result) == 1
                assert result[0]["score"] == 0.7
        finally:
            os.unlink(temp_path)

    def test_handles_invalid_json(self):
        from judge_feedback import load_recent_judge_verdicts
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            f.write('{"timestamp": 9999999999.0, "score": 0.9}\n')
            f.write("invalid json\n")
            f.write('{"timestamp": 9999999999.0, "score": 0.8}\n')
            temp_path = f.name

        try:
            with patch("judge_feedback._JUDGE_VERDICTS_PATH", Path(temp_path)):
                result = load_recent_judge_verdicts(hours=24)
                # Should get 2 valid verdicts, skip invalid
                assert len(result) == 2
        finally:
            import os
            os.unlink(temp_path)


class TestSummarizeJudgeActivity:
    """Test summarize_judge_activity function."""

    def test_empty_verdicts_returns_zeros(self):
        from judge_feedback import summarize_judge_activity

        result = summarize_judge_activity([])
        assert result["total"] == 0
        assert result["blocks"] == 0
        assert result["avg_score"] == 0.0
        assert result["top_issues"] == []

    def test_calculates_correct_metrics(self):
        from judge_feedback import summarize_judge_activity

        verdicts = [
            {"score": 0.8, "passes": True, "issues": ["issue1"]},
            {"score": 0.6, "passes": True, "issues": ["issue1", "issue2"]},
            {"score": 0.4, "passes": False, "issues": ["issue3"]},
        ]

        result = summarize_judge_activity(verdicts)
        assert result["total"] == 3
        assert result["blocks"] == 1
        assert result["avg_score"] == pytest.approx(0.6)
        assert result["top_issues"][0] == ("issue1", 2)

    def test_handles_missing_fields(self):
        from judge_feedback import summarize_judge_activity

        verdicts = [
            {"score": 0.8},
            {},  # Missing fields
            {"passes": False},
        ]

        result = summarize_judge_activity(verdicts)
        assert result["total"] == 3


class TestFormatSessionStartSummary:
    """Test format_session_start_judge_summary function."""

    def test_none_when_too_few_verdicts(self):
        from judge_feedback import format_session_start_judge_summary

        summary = {"total": 2, "blocks": 0, "avg_score": 0.9}
        result = format_session_start_judge_summary(summary)
        assert result is None

    def test_all_good_returns_minimal_output(self):
        from judge_feedback import format_session_start_judge_summary

        summary = {"total": 5, "blocks": 0, "avg_score": 0.8, "top_issues": []}
        result = format_session_start_judge_summary(summary)
        assert result is not None
        assert "0 blocks" in result
        assert "✓" in result

    def test_blocks_shows_issue_summary(self):
        from judge_feedback import format_session_start_judge_summary

        summary = {
            "total": 5,
            "blocks": 2,
            "avg_score": 0.6,
            "top_issues": [("investigate before asking", 3)],
        }
        result = format_session_start_judge_summary(summary)
        assert result is not None
        assert "2 blocks" in result
        assert "investigate" in result.lower()

    def test_issue_suggestions_mapped(self):
        from judge_feedback import format_session_start_judge_summary

        # Test evidence issue
        summary = {
            "total": 5,
            "blocks": 1,
            "avg_score": 0.7,
            "top_issues": [("missing evidence", 2)],
        }
        result = format_session_start_judge_summary(summary)
        assert "file paths and line numbers" in result


class TestShouldInjectFirstQueryAdvisory:
    """Test should_inject_first_query_advisory function."""

    def test_false_when_already_shown(self):
        from judge_feedback import should_inject_first_query_advisory

        with patch(
            "judge_feedback._STATE_DIR",
            Path(tempfile.gettempdir()),
        ):
            # Create state file to simulate already shown
            state_file = (
                Path(tempfile.gettempdir()) / "judge_advisory_test-session.json"
            )
            state_file.write_text('{"session_id": "test-session"}')

            try:
                summary = {"total": 5, "blocks": 2, "avg_score": 0.7}
                result = should_inject_first_query_advisory(summary, "test-session")
                assert result is False
            finally:
                if state_file.exists():
                    state_file.unlink()

    def test_false_when_too_few_verdicts(self):
        from judge_feedback import should_inject_first_query_advisory

        summary = {"total": 2, "blocks": 0, "avg_score": 0.9}
        result = should_inject_first_query_advisory(summary, "test-session")
        assert result is False

    def test_true_when_block_rate_high(self):
        from judge_feedback import should_inject_first_query_advisory

        summary = {"total": 10, "blocks": 2, "avg_score": 0.7}  # 20% block rate
        result = should_inject_first_query_advisory(summary, "new-session")
        assert result is True

    def test_true_when_avg_score_low(self):
        from judge_feedback import should_inject_first_query_advisory

        summary = {"total": 10, "blocks": 0, "avg_score": 0.65}  # Below 0.72
        result = should_inject_first_query_advisory(summary, "new-session")
        assert result is True

    def test_true_when_same_issue_repeats(self):
        from judge_feedback import should_inject_first_query_advisory

        summary = {
            "total": 10,
            "blocks": 1,
            "avg_score": 0.8,
            "top_issues": [("investigate before asking", 4)],  # 4x
        }
        result = should_inject_first_query_advisory(summary, "new-session")
        assert result is True


class TestBuildFirstQueryAdvisory:
    """Test build_first_query_advisory function."""

    def test_none_when_no_top_issues(self):
        from judge_feedback import build_first_query_advisory

        summary = {"total": 10, "blocks": 1, "avg_score": 0.7, "top_issues": []}
        result = build_first_query_advisory(summary)
        assert result is None

    def test_returns_advisory_with_issue(self):
        from judge_feedback import build_first_query_advisory

        summary = {
            "total": 10,
            "blocks": 2,
            "avg_score": 0.7,
            "top_issues": [("investigate before asking", 3)],
        }
        result = build_first_query_advisory(summary)
        assert result is not None
        assert "investigate" in result.lower()
        assert "Tip:" in result

    def test_tip_mapped_to_issue_type(self):
        from judge_feedback import build_first_query_advisory

        test_cases = [
            ("evidence", "file paths and line numbers"),
            ("short", "more detail"),
            ("hedg", "Lead with the answer"),  # hedging maps to "Lead with the answer"
        ]

        for issue_part, expected_tip in test_cases:
            summary = {
                "total": 10,
                "blocks": 1,
                "avg_score": 0.7,
                "top_issues": [(f"{issue_part} issue", 3)],
            }
            result = build_first_query_advisory(summary)
            assert expected_tip in result, f"Failed for issue: {issue_part}"


class TestMarkAdvisoryShown:
    """Test mark_advisory_shown function."""

    def test_creates_state_file(self):
        from judge_feedback import mark_advisory_shown

        with patch(
            "judge_feedback._STATE_DIR",
            Path(tempfile.gettempdir()),
        ):
            state_file = (
                Path(tempfile.gettempdir()) / "judge_advisory_test-session.json"
            )

            try:
                mark_advisory_shown("test-session")
                assert state_file.exists()
                data = json.loads(state_file.read_text())
                assert data["session_id"] == "test-session"
                assert "timestamp" in data
            finally:
                if state_file.exists():
                    state_file.unlink()


class TestJudgeFirstQueryAdvisoryModule:
    """Test judge_first_query_advisory UserPromptSubmit module."""

    def test_process_prompt_returns_empty_on_later_messages(self):
        from UserPromptSubmit_modules.judge_first_query_advisory import (
            _process_prompt_impl,
        )
        from UserPromptSubmit_modules.base import HookContext

        data = {
            "session_id": "test-session",
            "messages": [
                {"role": "user", "content": "First message"},
                {"role": "assistant", "content": "Response"},
                {"role": "user", "content": "Second message"},
            ],
        }

        context = HookContext(
            prompt="Second message",
            data=data,
            session_id="test-session",
            terminal_id="test-terminal",
        )

        result = _process_prompt_impl(context)
        assert result.is_empty()

    def test_process_prompt_returns_advisory_on_first_query(self):
        from UserPromptSubmit_modules.judge_first_query_advisory import (
            _process_prompt_impl,
        )
        from UserPromptSubmit_modules.base import HookContext

        with patch(
            "judge_feedback._STATE_DIR",
            Path(tempfile.gettempdir()),
        ):
            # Clean up any existing state file
            state_file = (
                Path(tempfile.gettempdir()) / "judge_advisory_test-session.json"
            )
            if state_file.exists():
                state_file.unlink()

            try:
                data = {
                    "session_id": "test-session",
                    "messages": [{"role": "user", "content": "First message"}],
                }

                context = HookContext(
                    prompt="First message",
                    data=data,
                    session_id="test-session",
                    terminal_id="test-terminal",
                )

                # Mock the judge_feedback functions to return triggering conditions
                with patch(
                    "UserPromptSubmit_modules.judge_first_query_advisory.load_recent_judge_verdicts",
                    return_value=[{"score": 0.5, "passes": False}]
                ), patch(
                    "UserPromptSubmit_modules.judge_first_query_advisory.summarize_judge_activity",
                    return_value={
                        "total": 10,
                        "blocks": 2,
                        "avg_score": 0.65,
                        "top_issues": [("test issue", 3)],
                    }
                ):
                    result = _process_prompt_impl(context)
                    assert not result.is_empty()
                    assert result.context is not None
                    assert "test issue" in result.context
            finally:
                if state_file.exists():
                    state_file.unlink()

    def test_process_prompt_returns_empty_when_no_trigger(self):
        from UserPromptSubmit_modules.judge_first_query_advisory import (
            _process_prompt_impl,
        )
        from UserPromptSubmit_modules.base import HookContext

        data = {
            "session_id": "test-session",
            "messages": [{"role": "user", "content": "First message"}],
        }

        context = HookContext(
            prompt="First message",
            data=data,
            session_id="test-session",
            terminal_id="test-terminal",
        )

        with patch(
            "UserPromptSubmit_modules.judge_first_query_advisory.load_recent_judge_verdicts",
            return_value=[{"score": 0.9, "passes": True}]
        ), patch(
            "UserPromptSubmit_modules.judge_first_query_advisory.summarize_judge_activity",
            return_value={"total": 10, "blocks": 0, "avg_score": 0.9, "top_issues": []}
        ):
            result = _process_prompt_impl(context)
            assert result.is_empty()


class TestHookRegistrationInRegistry:
    """Integration test: verify judge_first_query_advisory is in HOOKS registry.

    This test would have caught the original registration bug where the module
    was listed in core_hook_modules but lacked @register_hook decorator and had
    the wrong function signature. The hook only works when:
    1. _try_import_hook finds and imports the module
    2. The module calls register_hook() at import time
    3. The registered function has the correct (context: HookContext) signature
    """

    def test_judge_first_query_advisory_registered_in_hooks(self):
        # Import the registry — this triggers _load_hooks() via module-level code
        from UserPromptSubmit_modules import registry

        # Force hook loading if not already done
        if not registry.HOOKS:
            registry._load_hooks()

        # Verify the hook is registered with correct priority
        assert "judge_first_query_advisory" in registry.HOOKS, (
            "judge_first_query_advisory not found in HOOKS registry. "
            "This means the module was not properly registered via @register_hook."
        )
        assert registry.HOOK_PRIORITY["judge_first_query_advisory"] == 7.0, (
            f"Expected priority 7.0, got {registry.HOOK_PRIORITY.get('judge_first_query_advisory')}"
        )

    def test_judge_first_query_advisory_function_has_correct_signature(self):
        from UserPromptSubmit_modules import registry

        if not registry.HOOKS:
            registry._load_hooks()

        hook_func = registry.HOOKS.get("judge_first_query_advisory")
        assert hook_func is not None, "Hook not registered"

        # Verify it accepts HookContext and returns HookResult
        import inspect
        sig = inspect.signature(hook_func)
        params = list(sig.parameters.keys())
        assert len(params) == 1, f"Expected 1 param, got {len(params)}: {params}"
        assert params[0] == "context", f"Expected param 'context', got {params[0]}"


class TestSummarizeGracefulDegradation:
    """Test that summarize_judge_activity handles missing issues field gracefully."""

    def test_top_issues_empty_when_issues_field_absent(self):
        """Real telemetry (judge_verdicts.jsonl) has n_issues but no issues list.

        The system must not crash or produce malformed top_issues when the issues
        field is absent — it should gracefully degrade to empty top_issues.
        """
        from judge_feedback import summarize_judge_activity

        # Real telemetry shape: has n_issues, passes, score — but no issues list
        verdicts_real_schema = [
            {"timestamp": 1778643093.0, "score": 0.75, "passes": True,
             "confidence": 0.85, "model_used": "sonnet", "latency_ms": 100.0,
             "turn_mode": "analysis", "n_issues": 1, "n_suggestions": 1, "error": None},
            {"timestamp": 1778643094.0, "score": 0.6, "passes": False,
             "confidence": 0.7, "model_used": "sonnet", "latency_ms": 150.0,
             "turn_mode": "analysis", "n_issues": 2, "n_suggestions": 0, "error": None},
        ]

        result = summarize_judge_activity(verdicts_real_schema)

        # Should compute total/blocks/score correctly
        assert result["total"] == 2
        assert result["blocks"] == 1
        assert result["avg_score"] == pytest.approx(0.675)

        # top_issues must be empty when issues field is absent (not crash, not partial)
        assert result["top_issues"] == [], (
            "top_issues should be empty when verdict lacks 'issues' field. "
            f"Got: {result['top_issues']}"
        )

    def test_top_issues_populated_when_issues_field_present(self):
        """Verify top_issues works normally when issues field is properly populated."""
        from judge_feedback import summarize_judge_activity

        verdicts_with_issues = [
            {"score": 0.8, "passes": True, "issues": ["investigate before asking"]},
            {"score": 0.6, "passes": True, "issues": ["investigate before asking", "missing evidence"]},
            {"score": 0.5, "passes": False, "issues": ["investigate before asking"]},
        ]

        result = summarize_judge_activity(verdicts_with_issues)

        assert result["total"] == 3
        assert result["top_issues"][0] == ("investigate before asking", 3)


class TestCheckTelemetrySchemaHealth:
    """Test check_telemetry_schema_health function."""

    def test_no_note_when_issues_field_present(self):
        """Normal case: all verdicts have issues list → no maintenance note."""
        from judge_feedback import check_telemetry_schema_health

        verdicts = [
            {"score": 0.8, "passes": True, "issues": ["investigate before asking"]},
            {"score": 0.6, "passes": True, "issues": ["missing evidence"]},
            {"score": 0.5, "passes": False, "issues": ["short responses"]},
            {"score": 0.7, "passes": True, "issues": ["investigate before asking"]},
        ]

        result = check_telemetry_schema_health(verdicts)
        assert result is None

    def test_note_appears_when_issues_missing_above_threshold(self):
        """Warn case: issues missing in 7/8 verdicts (87.5%) → note appears."""
        from judge_feedback import check_telemetry_schema_health

        verdicts = [
            {"score": 0.8, "passes": True},  # missing issues
            {"score": 0.6, "passes": True},  # missing issues
            {"score": 0.5, "passes": False},  # missing issues
            {"score": 0.7, "passes": True},  # missing issues
            {"score": 0.8, "passes": True},  # missing issues
            {"score": 0.6, "passes": True},  # missing issues
            {"score": 0.5, "passes": False},  # missing issues
            {"score": 0.7, "passes": True, "issues": ["investigate before asking"]},  # has issues
        ]

        result = check_telemetry_schema_health(verdicts)
        assert result is not None
        assert "missing `issues` field" in result
        assert "7/8" in result

    def test_no_note_when_issues_missing_below_threshold(self):
        """Below threshold: issues missing in 5/8 verdicts (62.5%) → no note."""
        from judge_feedback import check_telemetry_schema_health

        verdicts = [
            {"score": 0.8, "passes": True},  # missing
            {"score": 0.6, "passes": True},  # missing
            {"score": 0.5, "passes": False},  # missing
            {"score": 0.7, "passes": True},  # missing
            {"score": 0.7, "passes": True},  # missing
            {"score": 0.9, "passes": True, "issues": ["good"]},  # has issues
            {"score": 0.8, "passes": True, "issues": ["good"]},  # has issues
            {"score": 0.9, "passes": True, "issues": ["good"]},  # has issues
        ]

        result = check_telemetry_schema_health(verdicts)
        assert result is None

    def test_no_note_when_sample_size_below_minimum(self):
        """Small sample: only 2 verdicts → no note regardless of missing rate."""
        from judge_feedback import check_telemetry_schema_health

        verdicts = [
            {"score": 0.8, "passes": True},  # missing issues
            {"score": 0.6, "passes": False},  # missing issues
        ]

        result = check_telemetry_schema_health(verdicts)
        assert result is None

    def test_malformed_issues_noted_separately(self):
        """Malformed: issues field present but not a list → counted as unusable."""
        from judge_feedback import check_telemetry_schema_health

        verdicts = [
            {"score": 0.8, "passes": True, "issues": "not a list"},  # malformed
            {"score": 0.6, "passes": True},  # missing
            {"score": 0.5, "passes": False, "issues": 42},  # malformed
            {"score": 0.7, "passes": True},  # missing
        ]

        result = check_telemetry_schema_health(verdicts)
        assert result is not None
        assert "2 malformed" in result

    def test_all_missing_triggers_note(self):
        """All missing: 10/10 verdicts without issues → note clearly."""
        from judge_feedback import check_telemetry_schema_health

        verdicts = [
            {"score": 0.8, "passes": True},
            {"score": 0.6, "passes": True},
            {"score": 0.5, "passes": False},
            {"score": 0.7, "passes": True},
            {"score": 0.8, "passes": True},
        ]

        result = check_telemetry_schema_health(verdicts)
        assert result is not None
        assert "5/5" in result
        assert "5/5 verdicts" in result


class TestCheckAutomationEffectiveness:
    """Test check_automation_effectiveness function."""

    def _window_ts(self, days_ago: int) -> float:
        """Return approximate timestamp N days ago."""
        return time.time() - (days_ago * 86400)

    def test_healthy_metrics_no_note(self):
        """Normal case: healthy metrics → no note."""
        from judge_feedback import check_automation_effectiveness

        now = self._window_ts(0)
        verdicts = [
            {"timestamp": now, "score": 0.85, "passes": True},
            {"timestamp": now, "score": 0.80, "passes": True},
            {"timestamp": now, "score": 0.90, "passes": True},
        ]
        result = check_automation_effectiveness(verdicts)
        assert result is None

    def test_single_degraded_window_warning(self):
        """Degraded case: current window degraded, first occurrence → compact warning."""
        from judge_feedback import check_automation_effectiveness

        now = self._window_ts(0)
        verdicts = []
        # window 0 (today) - degraded
        verdicts.append({"timestamp": now - 0 * 86400, "score": 0.68, "passes": False})
        verdicts.append({"timestamp": now - 0 * 86400, "score": 0.65, "passes": False})
        # window 1 (1 day ago) - healthy
        verdicts.append({"timestamp": now - 1 * 86400, "score": 0.85, "passes": True})
        verdicts.append({"timestamp": now - 1 * 86400, "score": 0.82, "passes": True})
        # window 2 (2 days ago) - healthy
        verdicts.append({"timestamp": now - 2 * 86400, "score": 0.88, "passes": True})
        verdicts.append({"timestamp": now - 2 * 86400, "score": 0.84, "passes": True})
        result = check_automation_effectiveness(verdicts)
        assert result is not None
        assert "degraded this window" in result
        assert "Not yet persistent" in result

    def test_persistent_degradation_escalation(self):
        """Persistent case: 3+ degraded windows → escalation with remediation."""
        from judge_feedback import check_automation_effectiveness

        # Build 5 windows, 3 degraded
        now = self._window_ts(0)
        verdicts = []
        # window 0 (today) - degraded
        verdicts.append({"timestamp": now - 0 * 86400, "score": 0.68, "passes": False})
        verdicts.append({"timestamp": now - 0 * 86400, "score": 0.65, "passes": False})
        # window 1 (1 day ago) - degraded
        verdicts.append({"timestamp": now - 1 * 86400, "score": 0.69, "passes": False})
        verdicts.append({"timestamp": now - 1 * 86400, "score": 0.66, "passes": False})
        # window 2 (2 days ago) - degraded
        verdicts.append({"timestamp": now - 2 * 86400, "score": 0.67, "passes": False})
        verdicts.append({"timestamp": now - 2 * 86400, "score": 0.64, "passes": False})
        # window 3 (3 days ago) - healthy
        verdicts.append({"timestamp": now - 3 * 86400, "score": 0.85, "passes": True})
        verdicts.append({"timestamp": now - 3 * 86400, "score": 0.82, "passes": True})
        # window 4 (4 days ago) - healthy
        verdicts.append({"timestamp": now - 4 * 86400, "score": 0.88, "passes": True})

        result = check_automation_effectiveness(verdicts)
        assert result is not None
        assert "degraded" in result
        assert "3 of last 3" in result
        assert "Action:" in result
        assert "self-investigation mode" in result or "advisory thresholds" in result

    def test_insufficient_windows_returns_none(self):
        """Not enough windows for persistence check → None."""
        from judge_feedback import check_automation_effectiveness

        now = self._window_ts(0)
        verdicts = [
            {"timestamp": now, "score": 0.65, "passes": False},
            {"timestamp": now, "score": 0.62, "passes": False},
        ]
        result = check_automation_effectiveness(verdicts)
        assert result is None

    def test_score_only_low_no_block_not_degraded(self):
        """Score low but block rate OK → not degraded (needs both conditions)."""
        from judge_feedback import check_automation_effectiveness

        now = self._window_ts(0)
        verdicts = [
            {"timestamp": now, "score": 0.60, "passes": True},
            {"timestamp": now, "score": 0.58, "passes": True},
            {"timestamp": now, "score": 0.55, "passes": True},
        ]
        result = check_automation_effectiveness(verdicts)
        # Score is below threshold but blocks are 0, so not degraded
        # With 3+ verdicts all healthy (passes=True), there's not block_rate >= 0.15
        # This would produce no note
        assert result is None

    def test_threshold_customization(self):
        """Custom thresholds respected."""
        from judge_feedback import check_automation_effectiveness

        now = self._window_ts(0)
        verdicts = []
        # window 0 (today) - degraded with lower threshold
        verdicts.append({"timestamp": now - 0 * 86400, "score": 0.55, "passes": False})
        verdicts.append({"timestamp": now - 0 * 86400, "score": 0.52, "passes": False})
        # window 1 (1 day ago) - degraded
        verdicts.append({"timestamp": now - 1 * 86400, "score": 0.54, "passes": False})
        verdicts.append({"timestamp": now - 1 * 86400, "score": 0.51, "passes": False})
        # window 2 (2 days ago) - degraded
        verdicts.append({"timestamp": now - 2 * 86400, "score": 0.53, "passes": False})
        verdicts.append({"timestamp": now - 2 * 86400, "score": 0.50, "passes": False})
        # With higher threshold (0.60), should trigger degraded
        result = check_automation_effectiveness(verdicts, score_threshold=0.60)
        assert result is not None


class TestCheckJudgeIntegrationHealth:
    """Test check_judge_integration_health function."""

    def _verdict(self, model: str, error: str | None = None, **overrides) -> dict:
        """Factory for test verdict dicts."""
        v = {
            "timestamp": time.time(),
            "score": 0.8,
            "passes": True,
            "confidence": 0.9,
            "model_used": model,
            "latency_ms": 100.0,
            "turn_mode": "analysis",
            "issues": [],
            "n_issues": 0,
            "n_suggestions": 0,
            "error": error,
        }
        v.update(overrides)
        return v

    def test_healthy_no_errors(self):
        """Normal case: no error verdicts → None."""
        from judge_feedback import check_judge_integration_health

        verdicts = [self._verdict("sonnet") for _ in range(10)]
        result = check_judge_integration_health(verdicts)
        assert result is None

    def test_healthy_heuristic_fallback_not_counted(self):
        """Heuristic fallback verdicts are normal, not integration failures."""
        from judge_feedback import check_judge_integration_health

        verdicts = [self._verdict("heuristic")] * 10
        result = check_judge_integration_health(verdicts)
        assert result is None

    def test_warning_tier_at_5_percent(self):
        """Exactly 1 error out of 20 (5.0%) → warning (error detail not included at this tier)."""
        from judge_feedback import check_judge_integration_health

        verdicts = [self._verdict("sonnet") for _ in range(19)]
        verdicts.append(self._verdict("error", "connection refused"))
        result = check_judge_integration_health(verdicts)
        assert result is not None
        assert "warning" in result
        assert "5.0%" in result
        assert "1/20" in result
        assert "connection refused" not in result  # error detail is escalation-only

    def test_warning_tier_above_5_percent(self):
        """2 errors out of 20 (10.0%) → escalation (above warn threshold lands here)."""
        from judge_feedback import check_judge_integration_health

        verdicts = [self._verdict("sonnet") for _ in range(18)]
        verdicts.append(self._verdict("error", "timeout"))
        verdicts.append(self._verdict("error", "connection refused"))
        result = check_judge_integration_health(verdicts)
        assert result is not None
        assert "degraded" in result
        assert "10.0%" in result
        assert "2/20" in result

    def test_escalation_tier_at_10_percent(self):
        """Exactly 2 errors out of 20 (10.0%) → escalation."""
        from judge_feedback import check_judge_integration_health

        verdicts = [self._verdict("sonnet") for _ in range(18)]
        verdicts.append(self._verdict("error", "timeout"))
        verdicts.append(self._verdict("error", "connection refused"))
        result = check_judge_integration_health(verdicts)
        assert result is not None
        assert "degraded" in result
        assert "10.0%" in result
        assert "Action:" in result

    def test_escalation_tier_above_10_percent(self):
        """3 errors out of 20 (15.0%) → escalation."""
        from judge_feedback import check_judge_integration_health

        verdicts = [self._verdict("sonnet") for _ in range(17)]
        verdicts.append(self._verdict("error", "timeout"))
        verdicts.append(self._verdict("error", "auth failure"))
        verdicts.append(self._verdict("error", "connection refused"))
        result = check_judge_integration_health(verdicts)
        assert result is not None
        assert "15.0%" in result
        assert "3/20" in result
        assert "degraded" in result
        assert "Action:" in result

    def test_all_errors_escalation(self):
        """All verdicts are errors (100%) → escalation."""
        from judge_feedback import check_judge_integration_health

        verdicts = [self._verdict("error", "catastrophic failure") for _ in range(5)]
        result = check_judge_integration_health(verdicts)
        assert result is not None
        assert "100.0%" in result
        assert "5/5" in result
        assert "catastrophic failure" in result

    def test_below_min_sample(self):
        """Fewer than 5 verdicts → None regardless of error rate."""
        from judge_feedback import check_judge_integration_health

        verdicts = [
            self._verdict("error", "timeout"),
            self._verdict("sonnet"),
            self._verdict("sonnet"),
        ]
        result = check_judge_integration_health(verdicts)
        assert result is None

    def test_missing_error_key_not_crash(self):
        """Verdict without error key is treated as non-error; no crash."""
        from judge_feedback import check_judge_integration_health

        verdicts = [
            {"timestamp": time.time(), "score": 0.8, "model_used": "sonnet"},
            {"timestamp": time.time(), "score": 0.7, "model_used": "sonnet"},
            {"timestamp": time.time(), "score": 0.6, "model_used": "error", "error": "fail"},
            {"timestamp": time.time(), "score": 0.9, "model_used": "sonnet"},
            {"timestamp": time.time(), "score": 0.85, "model_used": "sonnet"},
        ]
        result = check_judge_integration_health(verdicts)
        assert result is not None
        assert "20.0%" in result
        assert "1/5" in result

    def test_escalation_includes_truncated_error_text(self):
        """Escalation message includes first error string, truncated to 80 chars."""
        from judge_feedback import check_judge_integration_health

        long_error = "A" * 200
        verdicts = [self._verdict("sonnet") for _ in range(9)]
        verdicts.append(self._verdict("error", long_error))
        result = check_judge_integration_health(verdicts)
        assert result is not None
        assert "AAAA" in result  # truncated content appears
        assert len(result.split("Sample error: ")[1].split("\n")[0]) <= 83  # truncated

    def test_escalation_no_error_string(self):
        """Error verdict with null error still triggers escalation, no crash."""
        from judge_feedback import check_judge_integration_health

        verdicts = [self._verdict("sonnet") for _ in range(9)]
        verdicts.append(self._verdict("error", None))
        result = check_judge_integration_health(verdicts)
        assert result is not None
        assert "degraded" in result
        assert "10.0%" in result
        assert "Action:" in result

    def test_threshold_customization(self):
        """Custom thresholds respected."""
        from judge_feedback import check_judge_integration_health

        # 1 error in 10 = 10% — falls between 5% warn and 10% escalate
        verdicts = [self._verdict("sonnet") for _ in range(9)]
        verdicts.append(self._verdict("error", "x"))
        # At warn=5%, escalate=10%: 10% → escalation (meets escalate)
        result = check_judge_integration_health(verdicts, warn_threshold=0.05, escalate_threshold=0.10)
        assert result is not None
        assert "degraded" in result
        # At warn=5%, escalate=15%: 10% < 15% → below escalate, above warn → warning
        result2 = check_judge_integration_health(verdicts, warn_threshold=0.05, escalate_threshold=0.15)
        assert result2 is not None
        assert "warning" in result2


class TestCheckThresholdEffectivenessEscalation:
    """Test check_threshold_effectiveness_escalation and record_session_quality."""

    def _session_file(self, tmp_path):
        """Patch _SESSION_QUALITY_PATH to a temp location."""
        return tmp_path / "judge_session_quality.jsonl"

    def _write_sessions(self, path: Path, sessions: list[dict]) -> None:
        """Write a list of session dicts as JSONL."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for s in sessions:
                f.write(json.dumps(s) + "\n")

    def test_healthy_all_above_thresholds_none(self, tmp_path):
        """All sessions above thresholds → None."""
        from judge_feedback import check_threshold_effectiveness_escalation

        path = self._session_file(tmp_path)
        self._write_sessions(path, [
            {"session_id": "s1", "avg_score": 0.80, "block_rate": 0.05},
            {"session_id": "s2", "avg_score": 0.78, "block_rate": 0.08},
            {"session_id": "s3", "avg_score": 0.82, "block_rate": 0.10},
        ])

        with patch("judge_feedback._SESSION_QUALITY_PATH", path):
            result = check_threshold_effectiveness_escalation("s4", 0.80, 0.05)
        assert result is None

    def test_single_bad_session_resets_after_recovery(self, tmp_path):
        """One poor session, then recovery → None (streak broken)."""
        from judge_feedback import check_threshold_effectiveness_escalation

        path = self._session_file(tmp_path)
        self._write_sessions(path, [
            {"session_id": "s1", "avg_score": 0.65, "block_rate": 0.20},
            {"session_id": "s2", "avg_score": 0.80, "block_rate": 0.05},
        ])

        with patch("judge_feedback._SESSION_QUALITY_PATH", path):
            result = check_threshold_effectiveness_escalation("s3", 0.80, 0.05)
        assert result is None

    def test_exactly_3_consecutive_poor_warning(self, tmp_path):
        """Exactly 3 consecutive poor sessions → warning message.

        Two pre-existing poor sessions + current session (also poor) = 3 consecutive.
        record_session_quality appends current before counting, so we get exactly 3.
        """
        from judge_feedback import check_threshold_effectiveness_escalation

        path = self._session_file(tmp_path)
        self._write_sessions(path, [
            {"session_id": "s1", "avg_score": 0.65, "block_rate": 0.20},
            {"session_id": "s2", "avg_score": 0.68, "block_rate": 0.18},
        ])

        with patch("judge_feedback._SESSION_QUALITY_PATH", path):
            result = check_threshold_effectiveness_escalation("s3", 0.66, 0.19)
        assert result is not None
        assert "warning" in result
        assert "3 consecutive" in result

    def test_4_plus_consecutive_poor_escalation(self, tmp_path):
        """4+ consecutive poor sessions → escalation message.

        Three pre-existing poor sessions + current (poor) = 4 consecutive → escalation.
        """
        from judge_feedback import check_threshold_effectiveness_escalation

        path = self._session_file(tmp_path)
        self._write_sessions(path, [
            {"session_id": "s1", "avg_score": 0.65, "block_rate": 0.20},
            {"session_id": "s2", "avg_score": 0.68, "block_rate": 0.18},
            {"session_id": "s3", "avg_score": 0.66, "block_rate": 0.19},
        ])

        with patch("judge_feedback._SESSION_QUALITY_PATH", path):
            result = check_threshold_effectiveness_escalation("s4", 0.64, 0.22)
        assert result is not None
        assert "degraded" in result
        assert "4 consecutive" in result

    def test_mixed_criteria_all_count_as_poor(self, tmp_path):
        """Poor score OR high block rate — both count as poor.

        Two pre-existing poor sessions + current (poor) = 3 consecutive → warning.
        """
        from judge_feedback import check_threshold_effectiveness_escalation

        path = self._session_file(tmp_path)
        # s1: low score only
        # s2: high block rate only
        self._write_sessions(path, [
            {"session_id": "s1", "avg_score": 0.60, "block_rate": 0.05},
            {"session_id": "s2", "avg_score": 0.80, "block_rate": 0.20},
        ])

        with patch("judge_feedback._SESSION_QUALITY_PATH", path):
            result = check_threshold_effectiveness_escalation("s3", 0.60, 0.20)
        assert result is not None
        assert "3 consecutive" in result

    def test_missing_state_file_first_run(self, tmp_path):
        """No state file yet → None (first session, no history)."""
        from judge_feedback import check_threshold_effectiveness_escalation

        path = self._session_file(tmp_path)
        assert not path.exists()

        with patch("judge_feedback._SESSION_QUALITY_PATH", path):
            result = check_threshold_effectiveness_escalation("s1", 0.65, 0.20)
        assert result is None

    def test_malformed_jsonl_skipped(self, tmp_path):
        """Malformed JSON lines are skipped without crashing.

        Two pre-existing poor sessions + current (poor) = 3 consecutive → warning.
        """
        from judge_feedback import check_threshold_effectiveness_escalation

        path = self._session_file(tmp_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write('{"session_id": "s1", "avg_score": 0.65, "block_rate": 0.20}\n')
            f.write("NOT JSON\n")
            f.write('{"session_id": "s2", "avg_score": 0.60, "block_rate": 0.20}\n')

        with patch("judge_feedback._SESSION_QUALITY_PATH", path):
            result = check_threshold_effectiveness_escalation("s3", 0.65, 0.19)
        assert result is not None
        assert "3 consecutive" in result

    def test_record_session_quality_atomic_append(self, tmp_path):
        """record_session_quality writes atomically and prunes to 10."""
        from judge_feedback import record_session_quality

        path = self._session_file(tmp_path)

        with patch("judge_feedback._SESSION_QUALITY_PATH", path):
            for i in range(12):
                record_session_quality(f"s{i}", 0.70 - i * 0.01, 0.10 + i * 0.01)

        with open(path, encoding="utf-8") as f:
            lines = [json.loads(l) for l in f if l.strip()]
        assert len(lines) == 10
        # Oldest 2 pruned, newest 10 kept
        assert lines[0]["session_id"] == "s2"
        assert lines[-1]["session_id"] == "s11"

    def test_state_bounds_15_sessions_only_10_retained(self, tmp_path):
        """15 stored sessions → only 10 retained after pruning."""
        from judge_feedback import record_session_quality

        path = self._session_file(tmp_path)

        with patch("judge_feedback._SESSION_QUALITY_PATH", path):
            for i in range(15):
                record_session_quality(f"s{i}", 0.65, 0.20)

        with open(path, encoding="utf-8") as f:
            lines = [json.loads(l) for l in f if l.strip()]
        assert len(lines) == 10
        assert lines[0]["session_id"] == "s5"
        assert lines[-1]["session_id"] == "s14"

    def test_idempotent_session_recording(self, tmp_path):
        """Same session_id called twice → updates existing entry, not duplicate."""
        from judge_feedback import record_session_quality

        path = self._session_file(tmp_path)

        with patch("judge_feedback._SESSION_QUALITY_PATH", path):
            record_session_quality("session-X", 0.68, 0.18)
            record_session_quality("session-X", 0.70, 0.16)  # Same ID, different metrics

        with open(path, encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        assert len(lines) == 1, f"Expected 1 entry, got {len(lines)}"
        entry = json.loads(lines[0])
        assert entry["session_id"] == "session-X"
        assert entry["avg_score"] == 0.70
        assert entry["block_rate"] == 0.16

    def test_auto_fallback_session_id_format(self, tmp_path):
        """Empty session_id is handled gracefully (fallback generated in main(), not here)."""
        from judge_feedback import check_threshold_effectiveness_escalation

        path = self._session_file(tmp_path)

        with patch("judge_feedback._SESSION_QUALITY_PATH", path):
            # Empty string is accepted without crash (main() generates auto-* fallback)
            result = check_threshold_effectiveness_escalation("", 0.68, 0.18)
        # Should not crash — result depends on consecutive poor count
        assert result is None  # Only 1 session, below threshold

    def test_warning_message_includes_trend_line(self, tmp_path):
        """Warning message includes per-session trend breakdown."""
        from judge_feedback import check_threshold_effectiveness_escalation

        path = self._session_file(tmp_path)
        self._write_sessions(path, [
            {"session_id": "s1", "avg_score": 0.68, "block_rate": 0.18},
            {"session_id": "s2", "avg_score": 0.70, "block_rate": 0.16},
        ])

        with patch("judge_feedback._SESSION_QUALITY_PATH", path):
            result = check_threshold_effectiveness_escalation("s3", 0.69, 0.17)
        assert result is not None
        assert "warning" in result
        assert "[0.68/18%]" in result
        assert "[0.70/16%]" in result
        assert "[0.69/17%]" in result
        assert "Recent trend:" in result

    def test_escalation_message_includes_trend_line(self, tmp_path):
        """Escalation message includes per-session trend for all 4 sessions."""
        from judge_feedback import check_threshold_effectiveness_escalation

        path = self._session_file(tmp_path)
        self._write_sessions(path, [
            {"session_id": "s1", "avg_score": 0.68, "block_rate": 0.18},
            {"session_id": "s2", "avg_score": 0.70, "block_rate": 0.16},
            {"session_id": "s3", "avg_score": 0.69, "block_rate": 0.17},
        ])

        with patch("judge_feedback._SESSION_QUALITY_PATH", path):
            result = check_threshold_effectiveness_escalation("s4", 0.67, 0.19)
        assert result is not None
        assert "degraded" in result
        assert "4 consecutive" in result
        assert "[0.68/18%]" in result
        assert "[0.70/16%]" in result
        assert "[0.69/17%]" in result
        assert "[0.67/19%]" in result
        assert "Recent sessions:" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])