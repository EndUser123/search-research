#!/usr/bin/env python3
"""Tests for external_judge.py Phase 4 integration."""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add hooks dir to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))


class TestJudgeConfig:
    """Test JudgeConfig and configuration loading."""

    def test_default_config_values(self):
        from __lib.external_judge import get_config, JudgeConfig

        with patch.dict("os.environ", {}, clear=False):
            config = get_config()

        assert config.enabled is True
        assert config.model == "sonnet"
        assert config.timeout_seconds == 30.0
        assert config.min_confidence_threshold == 0.7

    def test_env_var_override(self):
        from __lib.external_judge import get_config

        with patch.dict("os.environ", {
            "EXTERNAL_JUDGE_ENABLED": "false",
            "EXTERNAL_JUDGE_MODEL": "opus",
            "EXTERNAL_JUDGE_TIMEOUT": "60.0",
            "EXTERNAL_JUDGE_THRESHOLD": "0.8",
        }):
            config = get_config()

        assert config.enabled is False
        assert config.model == "opus"
        assert config.timeout_seconds == 60.0
        assert config.min_confidence_threshold == 0.8


class TestVerdict:
    """Test Verdict dataclass."""

    def test_verdict_creation(self):
        from __lib.external_judge import Verdict

        v = Verdict(
            score=0.85,
            passes=True,
            issues=["Minor hedging"],
            suggestions=["Be more direct"],
            confidence=0.9,
            model_used="sonnet",
            latency_ms=150.5,
        )

        assert v.score == 0.85
        assert v.passes is True
        assert len(v.issues) == 1
        assert v.confidence == 0.9
        assert v.model_used == "sonnet"
        assert v.latency_ms == 150.5
        assert v.error is None


class TestLoadRubric:
    """Test rubric loading."""

    def test_load_rubric_success(self):
        from __lib.external_judge import load_rubric

        rubric = load_rubric()
        # Rubric exists and has content
        assert len(rubric) > 0
        assert "Directness" in rubric
        assert "Evidence" in rubric

    def test_load_rubric_missing_file(self):
        from __lib.external_judge import load_rubric, RUBRIC_PATH

        # Temporarily rename file
        backup = None
        if RUBRIC_PATH.exists():
            backup = RUBRIC_PATH.with_suffix(".bak")
            RUBRIC_PATH.rename(backup)

        try:
            rubric = load_rubric()
            assert rubric == ""  # Fail-open returns empty
        finally:
            if backup and backup.exists():
                backup.rename(RUBRIC_PATH)


class TestTerminalIsolation:
    """Test terminal-scoped state isolation."""

    def test_terminal_id_detection(self):
        from __lib.external_judge import _get_terminal_id

        # Mock WT_SESSION
        with patch.dict("os.environ", {"WT_SESSION": "test-session-123"}):
            terminal_id = _get_terminal_id()
            assert terminal_id == "console_test-session-123"

    def test_terminal_id_fallback(self):
        from __lib.external_judge import _get_terminal_id

        with patch.dict("os.environ", {}, clear=True):
            terminal_id = _get_terminal_id()
            assert terminal_id == "unknown"

    def test_state_path_is_terminal_scoped(self):
        from __lib.external_judge import _get_state_path

        with patch.dict("os.environ", {"WT_SESSION": "abc123"}):
            path = _get_state_path()
            assert "console_abc123" in str(path)
            assert "judge_state_" in str(path)


class TestEvaluateResponse:
    """Test evaluate_response function."""

    def test_disabled_judge_passes(self):
        from __lib.external_judge import evaluate_response

        with patch.dict("os.environ", {"EXTERNAL_JUDGE_ENABLED": "false"}):
            result = evaluate_response(
                response="Test response",
                user_prompt="Test prompt",
                turn_mode="analysis"
            )

        assert result.passes is True
        assert result.model_used == "disabled"

    def test_empty_response_returns_fail(self):
        from __lib.external_judge import evaluate_response

        result = evaluate_response("", "prompt", "analysis")

        assert result.passes is False
        assert result.score == 0.0
        assert "Empty response" in result.issues

    def test_short_response_scored_low(self):
        from __lib.external_judge import evaluate_response

        # Response is short but not empty - should get low score from heuristic
        result = evaluate_response(
            response="This is a somewhat short answer to the question.",
            user_prompt="What is the answer?",
            turn_mode="analysis"
        )

        # Short response gets low score from heuristic
        assert result.score < 0.7

    def test_turn_mode_affects_evaluation(self):
        from __lib.external_judge import evaluate_response

        response = "The fix is to add error handling."

        # Different modes may have different expectations
        result_control = evaluate_response(response, "prompt", "control")
        result_analysis = evaluate_response(response, "prompt", "analysis")

        # Both should return valid verdicts
        assert result_control.score is not None
        assert result_analysis.score is not None

    def test_model_used_is_heuristic_when_no_subprocess(self):
        from __lib.external_judge import evaluate_response

        with patch.dict("os.environ", {"EXTERNAL_JUDGE_ENABLED": "true"}):
            result = evaluate_response(
                response="A" * 100,  # Long enough to avoid short-response block
                user_prompt="Test",
                turn_mode="analysis"
            )

        # Should use heuristic fallback (no subprocess available in test)
        assert result.model_used in ("heuristic", "error")


class TestStatePersistence:
    """Test state save/load."""

    def test_save_and_load_state(self):
        from __lib.external_judge import save_state, load_state, _get_state_path

        with patch.dict("os.environ", {"WT_SESSION": "test-state-456"}):
            test_state = {
                "stats": {"total": 10, "passed": 8, "failed": 2},
                "last_verdict": {
                    "score": 0.8,
                    "passes": True,
                    "model": "sonnet"
                }
            }

            save_state(test_state)
            loaded = load_state()

            assert loaded["stats"]["total"] == 10
            assert loaded["last_verdict"]["score"] == 0.8

    def test_load_state_nonexistent_returns_empty_dict(self):
        from __lib.external_judge import load_state, _get_state_path

        with patch.dict("os.environ", {"WT_SESSION": "nonexistent-state-789"}):
            state = load_state()

        assert state == {}

    def test_get_stats(self):
        from __lib.external_judge import get_stats, save_state

        with patch.dict("os.environ", {"WT_SESSION": "stats-test-123"}):
            # Initialize with some data
            save_state({
                "stats": {"total": 5, "passed": 4, "failed": 1}
            })

            stats = get_stats()
            assert stats["total"] == 5
            assert stats["passed"] == 4
            assert stats["failed"] == 1


class TestHeuristicEvaluation:
    """Test heuristic evaluation fallback."""

    def test_text_too_short_gets_low_score(self):
        from __lib.external_judge import _heuristic_evaluate

        result = _heuristic_evaluate("Short", "prompt")

        assert result.score == 0.4
        assert "Response too short" in result.issues

    def test_empty_text_returns_zero(self):
        from __lib.external_judge import _heuristic_evaluate

        result = _heuristic_evaluate(None, "prompt")

        assert result.score == 0.0
        assert "Empty or unavailable response" in result.issues

    def test_deflection_pattern_penalty(self):
        from __lib.external_judge import _heuristic_evaluate

        text = "Let me check, but I didn't find anything."
        result = _heuristic_evaluate(text, "prompt")

        assert result.score < 0.8  # Should be penalized
        assert any("investigate" in issue.lower() for issue in result.issues)

    def test_filler_start_penalty(self):
        from __lib.external_judge import _heuristic_evaluate

        text = "well, the answer is simple."
        result = _heuristic_evaluate(text, "prompt")

        # Should have filler penalty applied
        assert any("filler" in issue.lower() for issue in result.issues)

    def test_error_included_in_suggestions(self):
        from __lib.external_judge import _heuristic_evaluate

        result = _heuristic_evaluate("Some text", "prompt", error="test error")

        assert any("test error" in s for s in result.suggestions)


class TestStopPyIntegration:
    """Test integration with Stop.py gate registration."""

    def test_external_judge_in_gate_classes(self):
        """Verify external_judge is registered in GATE_CLASSES."""
        # Read Stop.py and check GATE_CLASSES
        stop_py = (HOOKS_DIR / "Stop.py").read_text()

        assert '"external_judge": "quality"' in stop_py

    def test_external_judge_in_in_process_gates(self):
        """Verify external_judge is registered in IN_PROCESS_GATES."""
        stop_py = (HOOKS_DIR / "Stop.py").read_text()

        assert '("external_judge", _run_judge_evaluation)' in stop_py

    def test_judge_evaluation_function_exists(self):
        """Verify _run_judge_evaluation function exists in Stop.py."""
        stop_py = (HOOKS_DIR / "Stop.py").read_text()

        assert "def _run_judge_evaluation(data: dict)" in stop_py

    def test_log_judge_verdict_function_exists(self):
        """Verify _log_judge_verdict function exists in Stop.py."""
        stop_py = (HOOKS_DIR / "Stop.py").read_text()

        assert "def _log_judge_verdict(verdict, turn_mode: str)" in stop_py

    def test_judge_evaluation_uses_quality_suppression(self):
        """Verify judge evaluation respects quality mode suppression."""
        stop_py = (HOOKS_DIR / "Stop.py").read_text()

        # Should check is_quality_mode_suppressed before running
        assert "is_quality_mode_suppressed(turn_mode, \"stop\")" in stop_py

    def test_phase_4_comment_present(self):
        """Verify Phase 4 section comment is present."""
        stop_py = (HOOKS_DIR / "Stop.py").read_text()

        assert "# Phase 4: External Judge Evaluation Gate" in stop_py


class TestTelemetry:
    """Test telemetry logging."""

    def test_log_verdict_creates_file(self, tmp_path):
        """Verify _log_judge_verdict writes to log file."""
        from __lib.external_judge import Verdict

        verdict = Verdict(
            score=0.75,
            passes=True,
            issues=["Minor issue"],
            suggestions=["Be clearer"],
            confidence=0.85,
            model_used="sonnet",
            latency_ms=100.0,
        )

        # Patch HOOKS_DIR in Stop module before calling
        import Stop

        original_hooks_dir = Stop.HOOKS_DIR
        try:
            Stop.HOOKS_DIR = tmp_path
            Stop._log_judge_verdict(verdict, "analysis")

            log_file = tmp_path / "logs" / "diagnostics" / "judge_verdicts.jsonl"
            assert log_file.exists()

            # Parse and verify entry
            content = log_file.read_text()
            entry = json.loads(content.strip())

            assert entry["score"] == 0.75
            assert entry["passes"] is True
            assert entry["turn_mode"] == "analysis"
            assert entry["gate"] == "external_judge"
            assert entry["issues"] == ["Minor issue"]
            assert entry["n_issues"] == 1
        finally:
            Stop.HOOKS_DIR = original_hooks_dir

    def test_log_verdict_with_multiple_issues(self, tmp_path):
        """Verify _log_judge_verdict records multiple issues."""
        from __lib.external_judge import Verdict

        verdict = Verdict(
            score=0.55,
            passes=False,
            issues=["Missing Investigation", "Unverified Claim", "Lazy Delegation"],
            suggestions=["Read files first", "Cite sources"],
            confidence=0.7,
            model_used="sonnet",
            latency_ms=150.0,
        )

        import Stop

        original_hooks_dir = Stop.HOOKS_DIR
        try:
            Stop.HOOKS_DIR = tmp_path
            Stop._log_judge_verdict(verdict, "analysis")

            log_file = tmp_path / "logs" / "diagnostics" / "judge_verdicts.jsonl"
            content = log_file.read_text()
            entry = json.loads(content.strip())

            assert entry["issues"] == ["Missing Investigation", "Unverified Claim", "Lazy Delegation"]
            assert entry["n_issues"] == 3
            assert entry["score"] == 0.55
            assert entry["passes"] is False
        finally:
            Stop.HOOKS_DIR = original_hooks_dir


if __name__ == "__main__":
    pytest.main([__file__, "-v"])