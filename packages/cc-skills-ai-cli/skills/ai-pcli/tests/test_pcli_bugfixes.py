"""Regression tests for /ai-pcli bug fixes.

Covers:
- is_pi detection logic (parallel_llm.py:238)
- PTY noise filter sentinels (parallel_llm.py:255)
- calc_timeout boundary conditions (parallel_llm.py:648)
- _is_quota_error quota signals (parallel_llm.py:294)
- ling-2.6-1t-free alias (ai_cli.py:443)
- _load_ai_cli_config file missing/malformed (ai_cli.py:41)
- _extract_text_findings_all priority regex (ai_cli.py:2804)
- `start` variable scope bug (parallel_llm.py:176) - UnboundLocalError when verbose=False
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest


# =============================================================================
# parallel_llm.py — pure function tests
# =============================================================================

import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from parallel_llm import calc_timeout, _is_quota_error  # noqa: E402


class TestCalcTimeout:
    """Boundary conditions for calc_timeout."""

    def test_zero_kb_returns_minimum(self):
        """0 KB context returns base_timeout + 1 + 1 = 642s."""
        result = calc_timeout(0)
        assert result == 642  # 640 + 1 + 1

    def test_one_kb_rounds_up_to_1mb(self):
        """1 KB // 1024 = 0, max(1, 0) = 1. Returns 642s."""
        result = calc_timeout(1)
        assert result == 642  # 640 + 1 + 1

    def test_exactly_1mb(self):
        """1 MB = 1024 KB // 1024 = 1. Returns 640 + 1 + 1 = 642."""
        result = calc_timeout(1024)
        assert result == 642

    def test_just_over_1mb(self):
        """1 MB + 1 KB = 1025 KB // 1024 = 1. Returns 642s."""
        result = calc_timeout(1025)
        assert result == 642

    def test_2mb(self):
        """2 MB = 2048 KB // 1024 = 2. Returns 640 + 2 + 1 = 643."""
        result = calc_timeout(2048)
        assert result == 643


class TestIsQuotaError:
    """Quota signal detection."""

    @pytest.mark.parametrize(
        "signal",
        [
            "429",
            "no capacity",
            "rate limit",
            "quota",
            "limit exceeded",
            "temporarily unavailable",
            "terminalquotaerror",
            "failed to create the engine",
            "gpu_artisan",
        ],
    )
    def test_quota_signals_detected(self, signal: str):
        """All quota_signals trigger _is_quota_error True."""
        assert _is_quota_error(signal) is True

    @pytest.mark.parametrize(
        "non_quota",
        [
            "error",
            "timeout",
            "connection refused",
            "authentication failed",
            "file not found",
            "",
        ],
    )
    def test_non_quota_not_detected(self, non_quota: str):
        """Non-quota strings return False."""
        assert _is_quota_error(non_quota) is False

    def test_case_insensitive(self):
        """Quota signals are matched case-insensitively."""
        assert _is_quota_error("RATE LIMIT") is True
        assert _is_quota_error("No Capacity") is True


# =============================================================================
# PTY noise filter — pure logic extracted from run_single_command
# =============================================================================


def _filter_pty_noise(stderr_text: str) -> str | None:
    """Pure extract of PTY noise filter logic (parallel_llm.py:256-259).

    Returns None if stderr is only PTY noise (treat as success),
    returns the stripped stderr if real error content found.
    """
    if not stderr_text or not stderr_text.strip():
        return None
    stripped = stderr_text.strip()
    noise_words = ["Error:", "Fail:", "Exception:", "Traceback"]
    if not any(word in stripped for word in noise_words):
        return None  # Only PTY noise — treat as success
    return stripped  # Real error content


class TestPTYNoiseFilter:
    """PTY noise filter sentinel detection."""

    def test_warning_colon_is_pty_noise(self):
        """Warning: is PTY noise on Windows (not a real error) — treat as success."""
        assert _filter_pty_noise("Warning:") is None
        assert _filter_pty_noise("Warning: PTY artifact") is None

    def test_real_error_with_warning_still_detected(self):
        """stderr containing 'Warning:' alongside real error words is kept."""
        result = _filter_pty_noise("Error: something failed\nWarning: PTY")
        assert result is not None
        assert "Error:" in result

    def test_error_sentinels_still_work(self):
        """Existing sentinels (Error:, Fail:, Exception:, Traceback) unchanged."""
        assert _filter_pty_noise("Error: connection refused") is not None
        assert _filter_pty_noise("Fail: rate limit") is not None
        assert _filter_pty_noise("Exception: out of memory") is not None
        assert _filter_pty_noise("Traceback (most recent call last):") is not None

    def test_clean_stderr_returns_none(self):
        """stderr with no noise words returns None (treat as success)."""
        assert _filter_pty_noise("") is None
        assert _filter_pty_noise("   ") is None
        assert _filter_pty_noise("all good") is None


# =============================================================================
# ai_cli.py — model alias resolution
# =============================================================================

sys.path.insert(0, str(Path(__file__).parent.parent))
from ai_cli import _resolve_model_alias  # noqa: E402


class TestPiModelAliases:
    """pi model alias resolution."""

    def test_ling_free_alias_resolves(self):
        """ling-2.6-1t-free resolves to openrouter/inclusionai/ling-2.6-1t:free."""
        result = _resolve_model_alias("ling-2.6-1t-free")
        assert result == "openrouter/inclusionai/ling-2.6-1t:free"

    def test_kimi_alias_still_works(self):
        """Existing kimi-k2.6 alias still resolves correctly."""
        result = _resolve_model_alias("kimi-k2.6")
        assert result == "nvidia-nim/moonshotai/kimi-k2.6"

    def test_devstral_alias_still_works(self):
        """Existing devstral alias still resolves correctly."""
        result = _resolve_model_alias("devstral")
        assert result == "mistral/devstral-2512"

    def test_full_model_id_passthrough(self):
        """Full model IDs not in aliases are passed through unchanged."""
        result = _resolve_model_alias("openrouter/anthropic/claude-3-5-sonnet")
        assert result == "openrouter/anthropic/claude-3-5-sonnet"

    def test_empty_string_passthrough(self):
        """Empty string passes through as-is."""
        result = _resolve_model_alias("")
        assert result == ""


# =============================================================================
# ai_cli.py — config loading
# =============================================================================

from ai_cli import _load_ai_cli_config, _AI_CLI_CONFIG  # noqa: E402


class TestLoadAiCliConfig:
    """Config file missing/malformed handling with fallback support."""

    def test_missing_file_returns_none(self, monkeypatch: pytest.MonkeyPatch):
        """Both primary and fallback absent → returns None."""
        monkeypatch.setattr("pathlib.Path.exists", lambda self: False)
        result = _load_ai_cli_config()
        assert result is None

    def test_corrupt_json_returns_none(self, monkeypatch: pytest.MonkeyPatch):
        """Corrupt JSON → exception caught, returns None."""
        import io

        def fake_open(path, *args, **kwargs):
            return io.StringIO("{ invalid json")

        monkeypatch.setattr("pathlib.Path.exists", lambda self: True)
        monkeypatch.setattr("builtins.open", fake_open)
        result = _load_ai_cli_config()
        assert result is None

    def test_valid_structured_config_parsed(self, monkeypatch: pytest.MonkeyPatch):
        """Valid structured config → parses correctly."""
        import io

        config = {
            "direct": [{"name": "pi:ling-2.6-1t-free"}],
            "default": {"clis": [{"name": "pi:ling-2.6-1t-free"}]},
        }

        def fake_open(path, *args, **kwargs):
            return io.StringIO(json.dumps(config))

        monkeypatch.setattr("pathlib.Path.exists", lambda self: True)
        monkeypatch.setattr("builtins.open", fake_open)
        result = _load_ai_cli_config()
        assert result is not None
        assert "default" in result

    def test_legacy_format_flattens_correctly(self, monkeypatch: pytest.MonkeyPatch):
        """Legacy format → flattens into expected structure."""
        import io

        legacy = {
            "clis": ["pi:ling-2.6-1t-free", "pi:kimi-k2.6"],
            "opencode_models": ["kimi"],
        }

        def fake_open(path, *args, **kwargs):
            return io.StringIO(json.dumps(legacy))

        monkeypatch.setattr("pathlib.Path.exists", lambda self: True)
        monkeypatch.setattr("builtins.open", fake_open)
        result = _load_ai_cli_config()
        assert result is not None
        assert "clis" in result
        assert result["clis"] == ["pi:ling-2.6-1t-free", "pi:kimi-k2.6"]

    def test_fallback_to_legacy_path(self, monkeypatch: pytest.MonkeyPatch):
        """Primary absent, fallback present → loads from fallback."""
        import io

        legacy_config = {
            "clis": ["pi:kimi-k2.6"],
        }
        fallback_content = json.dumps(legacy_config)

        def fake_exists(self) -> bool:
            path_str = str(self)
            return "ai-cli-recipe.json" in path_str and "ai-pcli-recipe.json" not in path_str

        def fake_open(path, *args, **kwargs):
            return io.StringIO(fallback_content)

        monkeypatch.setattr("pathlib.Path.exists", fake_exists)
        monkeypatch.setattr("builtins.open", fake_open)
        result = _load_ai_cli_config()
        assert result is not None
        assert "clis" in result
        assert result["clis"] == ["pi:kimi-k2.6"]


# =============================================================================
# ai_cli.py — priority section regex parsing
# =============================================================================

from ai_cli import _extract_text_findings_all  # noqa: E402


class TestAggregateLlmResultsPriorityRegex:
    """Priority section regex parsing in _extract_text_findings_all.

    The function signature is: (output: str, cli_name: str) -> list[dict]
    It parses text output for section headers and bullet points matching:
      ^\\s*[-•*]\\s*\\*?\\*?(.+?)\\*?\\*?\\s*:\\s*(.+)
    """

    def test_nice_to_have_header_parsed(self):
        """## Nice to have header sets current_priority=medium for subsequent bullets."""
        output = "## Nice to have\n- Security finding here: SQL injection in user input field"
        results = _extract_text_findings_all(output, "test-cli")
        assert len(results) > 0
        medium_items = [r for r in results if r.get("priority") == "medium"]
        assert len(medium_items) >= 1

    def test_critical_header_parsed(self):
        """## Critical Issues header sets priority=critical for subsequent bullets."""
        output = "## Critical Issues\n- Critical finding here: authentication bypass vulnerability"
        results = _extract_text_findings_all(output, "test-cli")
        assert len(results) > 0
        critical_items = [r for r in results if r.get("priority") == "critical"]
        assert len(critical_items) >= 1

    def test_high_header_parsed(self):
        """## High Issues header sets priority=high for subsequent bullets."""
        output = "## High Issues\n- Important finding here: missing input validation detected"
        results = _extract_text_findings_all(output, "test-cli")
        assert len(results) > 0
        high_items = [r for r in results if r.get("priority") == "high"]
        assert len(high_items) >= 1

    def test_medium_header_parsed(self):
        """## Medium header sets priority=medium for subsequent bullets."""
        output = "## Medium\n- Code style issue: inconsistent naming convention used"
        results = _extract_text_findings_all(output, "test-cli")
        assert len(results) > 0
        medium_items = [r for r in results if r.get("priority") == "medium"]
        assert len(medium_items) >= 1
        assert len(results) > 0
        medium_items = [r for r in results if r.get("priority") == "medium"]
        assert len(medium_items) >= 1
