"""
Quota-fallback regression tests for parallel_llm.py.

Tests the gemini quota detection + model fallback chain:
1. Primary command succeeds → no fallback
2. Primary hits quota → fallback to next model → success
3. All models in chain hit quota → return last result with _used_fallback flag
4. Non-quota error → no fallback

These are REGRESSION TESTS: reproduce the exact failure path (quota not triggering
fallback chain) then prove the same path now works.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "packages" / "cc-skills-ai-cli" / "skills" / "ai-pcli"))


# =============================================================================
# Unit tests: _is_quota_error
# =============================================================================

class TestIsQuotaError:
    """Unit tests for quota signal detection."""

    @pytest.mark.parametrize("error", [
        "429 Too Many Requests",
        "no capacity left",
        "rate limit exceeded",
        "quota exceeded",
        "limit exceeded",
        "service temporarily unavailable",
        "TerminalQuotaError: You have exhausted your capacity",
        "RESOURCE_EXHAUSTED: quota limit",
    ])
    def test_quota_signals(self, error):
        from parallel_llm import _is_quota_error
        assert _is_quota_error(error) is True, f"Should detect quota in: {error}"

    @pytest.mark.parametrize("error", [
        "connection refused",
        "file not found",
        "syntax error",
        "authentication failed",
        "invalid request",
        "",
    ])
    def test_non_quota_signals(self, error):
        from parallel_llm import _is_quota_error
        assert _is_quota_error(error) is False, f"Should not flag as quota: {error}"


# =============================================================================
# Unit tests: _check_gemini_quota_file
# =============================================================================

class TestCheckGeminiQuotaFile:
    """Unit tests for gemini error file detection (filesystem boundary)."""

    def test_no_files_returns_false(self, tmp_path):
        """No error files exist → False."""
        with patch("parallel_llm.glob.glob", return_value=[]):
            from parallel_llm import _check_gemini_quota_file
            result = _check_gemini_quota_file()
        assert result is False

    def test_stale_file_older_than_4h_returns_false(self, tmp_path):
        """Error file exists but is older than 4 hours → False."""
        stale_mtime = time.time() - 14401

        def fake_glob(pattern):
            f = tmp_path / "gemini-client-error-old.json"
            f.write_text(json.dumps({"error": {"message": "exhausted"}}), encoding="utf-8")
            return [str(f)]

        def fake_getmtime(path):
            return stale_mtime

        with patch("parallel_llm.glob.glob", fake_glob):
            with patch("os.path.getmtime", fake_getmtime):
                from parallel_llm import _check_gemini_quota_file
                result = _check_gemini_quota_file()
        assert result is False

    def test_recent_quota_file_returns_true(self, tmp_path):
        """Recent error file with quota signal → True."""
        recent_mtime = time.time()

        def fake_glob(pattern):
            f = tmp_path / "gemini-client-error-recent.json"
            f.write_text(json.dumps({
                "error": {
                    "message": "You have exhausted your capacity on this model. Your quota will reset after 9h8m26s."
                }
            }), encoding="utf-8")
            return [str(f)]

        def fake_getmtime(path):
            return recent_mtime

        with patch("parallel_llm.glob.glob", fake_glob):
            with patch("os.path.getmtime", fake_getmtime):
                from parallel_llm import _check_gemini_quota_file
                result = _check_gemini_quota_file()
        assert result is True

    def test_recent_non_quota_file_returns_false(self, tmp_path):
        """Recent error file without quota signal → False."""
        recent_mtime = time.time()

        def fake_glob(pattern):
            f = tmp_path / "gemini-client-error-non-quota.json"
            f.write_text(json.dumps({"error": {"message": "connection refused"}}), encoding="utf-8")
            return [str(f)]

        def fake_getmtime(path):
            return recent_mtime

        with patch("parallel_llm.glob.glob", fake_glob):
            with patch("os.path.getmtime", fake_getmtime):
                from parallel_llm import _check_gemini_quota_file
                result = _check_gemini_quota_file()
        assert result is False


# =============================================================================
# Integration tests: run_parallel_commands with fallback chain
# =============================================================================

class TestRunParallelCommandsFallback:
    """Regression tests for quota → fallback chain via run_parallel_commands.

    run_with_fallback is a nested function inside run_parallel_commands, so we
    test it through run_parallel_commands by mocking run_single_command.
    """

    @pytest.mark.asyncio
    async def test_primary_succeeds_no_fallback(self):
        """Primary succeeds → no fallback, result returned."""
        from parallel_llm import run_parallel_commands

        async def mock_run_single(cmd, input_text=None, timeout=120, verbose=False, cwd=None):
            return {"output": "primary success", "error": ""}

        with patch("parallel_llm.run_single_command", mock_run_single):
            commands = [("gemini", ["gemini", "-m", "gemini-2.5-flash", "echo", "test"])]
            fallback_commands = {
                "gemini": [("gemini-3.1-pro-preview", ["gemini", "-m", "gemini-3.1-pro-preview", "echo", "test"])]
            }
            result = await run_parallel_commands(
                commands, fallback_commands=fallback_commands, verbose=False
            )
        assert result["gemini"]["output"] == "primary success"
        assert result["gemini"].get("_used_fallback") is not True

    @pytest.mark.asyncio
    async def test_quota_triggers_fallback_chain(self):
        """Primary hits quota → fallback to next model → success."""
        from parallel_llm import run_parallel_commands

        call_count = 0

        async def mock_run_single(cmd, input_text=None, timeout=120, verbose=False, cwd=None):
            nonlocal call_count
            call_count += 1
            # First call: quota error. Second call (fallback): success.
            if call_count == 1:
                return {"output": "", "error": "429 quota exhausted"}
            return {"output": "fallback worked", "error": ""}

        with patch("parallel_llm.run_single_command", mock_run_single):
            commands = [("gemini", ["gemini", "-m", "gemini-2.5-flash", "echo", "test"])]
            fallback_commands = {
                "gemini": [("gemini-3.1-pro-preview", ["gemini", "-m", "gemini-3.1-pro-preview", "echo", "test"])]
            }
            result = await run_parallel_commands(
                commands, fallback_commands=fallback_commands, verbose=False
            )
        assert result["gemini"]["output"] == "fallback worked"
        assert result["gemini"]["_used_fallback"] is True
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_all_fallbacks_quota_exhausted(self):
        """All fallbacks hit quota → return last result, _used_fallback=True."""
        from parallel_llm import run_parallel_commands

        async def mock_run_single(cmd, input_text=None, timeout=120, verbose=False, cwd=None):
            return {"output": "", "error": "429 quota exhausted"}

        with patch("parallel_llm.run_single_command", mock_run_single):
            commands = [("gemini", ["gemini", "-m", "gemini-2.5-flash", "echo", "test"])]
            fallback_commands = {
                "gemini": [
                    ("gemini-3.1-pro-preview", ["gemini", "-m", "gemini-3.1-pro-preview", "echo", "test"]),
                    ("gemini-3-flash-preview", ["gemini", "-m", "gemini-3-flash-preview", "echo", "test"]),
                ]
            }
            result = await run_parallel_commands(
                commands, fallback_commands=fallback_commands, verbose=False
            )
        assert result["gemini"]["_used_fallback"] is True
        assert result["gemini"]["error"] == "429 quota exhausted"

    @pytest.mark.asyncio
    async def test_non_quota_error_no_fallback(self):
        """Non-quota error (e.g., syntax error) → no fallback, result returned as-is."""
        from parallel_llm import run_parallel_commands

        async def mock_run_single(cmd, input_text=None, timeout=120, verbose=False, cwd=None):
            return {"output": "", "error": "syntax error in prompt"}

        with patch("parallel_llm.run_single_command", mock_run_single):
            commands = [("gemini", ["gemini", "-m", "gemini-2.5-flash", "echo", "test"])]
            fallback_commands = {
                "gemini": [("gemini-3.1-pro-preview", ["gemini", "-m", "gemini-3.1-pro-preview", "echo", "test"])]
            }
            result = await run_parallel_commands(
                commands, fallback_commands=fallback_commands, verbose=False
            )
        assert result["gemini"]["error"] == "syntax error in prompt"
        assert "_used_fallback" not in result["gemini"]

    @pytest.mark.asyncio
    async def test_gemini_quota_via_json_file(self):
        """Gemini reports quota via JSON file (not stderr) → fallback triggered."""
        from parallel_llm import run_parallel_commands

        call_count = 0

        async def mock_run_single(cmd, input_text=None, timeout=120, verbose=False, cwd=None):
            nonlocal call_count
            call_count += 1
            # gemini shows quota via JSON file, not stderr - so stderr has a non-quota message
            if call_count == 1:
                return {"output": "", "error": "non-quota stderr message"}
            return {"output": "fallback via JSON detection", "error": ""}

        # Patch _check_gemini_quota_file to return True (simulating recent quota JSON)
        with patch("parallel_llm.run_single_command", mock_run_single):
            with patch("parallel_llm._check_gemini_quota_file", return_value=True):
                commands = [("gemini", ["gemini", "-m", "gemini-2.5-flash", "echo", "test"])]
                fallback_commands = {
                    "gemini": [("gemini-3.1-pro-preview", ["gemini", "-m", "gemini-3.1-pro-preview", "echo", "test"])]
                }
                result = await run_parallel_commands(
                    commands, fallback_commands=fallback_commands, verbose=False
                )
        assert call_count == 2
        assert result["gemini"]["output"] == "fallback via JSON detection"
        assert result["gemini"]["_used_fallback"] is True

    @pytest.mark.asyncio
    async def test_no_fallback_configured_always_returns_primary(self):
        """No fallback_commands → primary result returned regardless of quota."""
        from parallel_llm import run_parallel_commands

        async def mock_run_single(cmd, input_text=None, timeout=120, verbose=False, cwd=None):
            return {"output": "", "error": "429 quota exhausted"}

        with patch("parallel_llm.run_single_command", mock_run_single):
            commands = [("gemini", ["gemini", "-m", "gemini-2.5-flash", "echo", "test"])]
            result = await run_parallel_commands(
                commands, fallback_commands=None, verbose=False
            )
        assert result["gemini"]["error"] == "429 quota exhausted"
        assert "_used_fallback" not in result["gemini"]


# =============================================================================
# Model substitution test
# =============================================================================

class TestSubstituteGeminiModel:
    """Test that _substitute_gemini_model correctly swaps the -m flag."""

    def test_substitutes_second_arg_m(self):
        """Command [gemini, -m, old-model, echo, test] → new-model substituted."""
        from ai_cli import _substitute_gemini_model
        cmd = ["gemini", "-m", "gemini-2.5-flash", "echo", "test"]
        result = _substitute_gemini_model(cmd, "gemini-3.1-pro-preview")
        assert result == ["gemini", "-m", "gemini-3.1-pro-preview", "echo", "test"]

    def test_no_m_flag_unchanged(self):
        """Command without -m flag is returned unchanged."""
        from ai_cli import _substitute_gemini_model
        cmd = ["gemini", "echo", "test"]
        result = _substitute_gemini_model(cmd, "gemini-3.1-pro-preview")
        assert result == ["gemini", "echo", "test"]

    def test_non_list_coerces_to_list(self):
        """String command is coerced via list() and -m not found → returned as char list."""
        from ai_cli import _substitute_gemini_model
        cmd = "gemini -m gemini-2.5-flash echo test"
        result = _substitute_gemini_model(cmd, "gemini-3.1-pro-preview")
        # list(cmd) iterates the string into chars, -m not found as list element, returns char list
        assert result == list(cmd)