#!/usr/bin/env python3
"""Tests for veridical_gate.py core components."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

# Add plugin lib to path for direct import
_plugin_lib = Path(__file__).resolve().parent.parent / "__lib"
if str(_plugin_lib) not in sys.path:
    sys.path.insert(0, str(_plugin_lib))

from anti_sycophancy import veridical_gate as vg


class TestScopeGate:
    """Tests for _has_agreement_pattern."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("You are right about that", True),
            ("That's correct", True),
            ("exactly what I meant", True),
            ("I agree with this assessment", True),
            ("Good point, I had not considered that", True),
            ("Fair enough, let me reconsider", True),
            ("Yes, that is the right approach", True),
            ("I see your point but...", True),
            ("That makes sense to me", True),
            ("absolutely, without question", True),
            ("You are absolutely correct", True),
            ("I stand corrected on this", True),
        ],
    )
    def test_positive_agreement_phrases(self, text, expected):
        assert vg._has_agreement_pattern(text) is expected

    @pytest.mark.parametrize(
        "text",
        [
            "The function returns a list of items",
            "Running pytest with coverage enabled",
            "The config file is at /etc/app/config.yaml",
            "Let me check the output of that command",
            "No matching pattern here at all",
        ],
    )
    def test_negative_non_agreement(self, text):
        assert vg._has_agreement_pattern(text) is False

    def test_empty_string(self):
        assert vg._has_agreement_pattern("") is False

    def test_none_like_empty(self):
        assert vg._has_agreement_pattern("   ") is False


class TestTranscriptBuilder:
    """Tests for _build_transcript."""

    def test_tool_events_formatting(self):
        events = [
            {"name": "Read", "input": {"file_path": "/tmp/a.py"}},
            {"name": "Bash", "input": {"command": "ls -la"}},
        ]
        result = vg._build_transcript(events, "response text")
        assert "[tool:Read]" in result
        assert "[tool:Bash]" in result
        assert "[response] response text" in result

    def test_truncation_to_six_events(self):
        events = [{"name": f"tool_{i}", "input": {"k": "v"}} for i in range(10)]
        result = vg._build_transcript(events, "")
        assert "[tool:tool_3]" not in result
        assert "[tool:tool_5]" in result
        assert "[tool:tool_9]" in result

    def test_string_input_truncation(self):
        events = [{"name": "X", "input": "not a dict but a string"}]
        result = vg._build_transcript(events, "")
        assert "[tool:X]" in result
        assert "not a dict but a string" in result

    def test_response_truncation(self):
        long_resp = "x" * 1000
        result = vg._build_transcript([], long_resp)
        resp_part = result.split("[response] ")[1]
        assert len(resp_part) == 500

    def test_empty_inputs(self):
        result = vg._build_transcript([], "")
        assert result == ""

    def test_none_like_response(self):
        events = [{"name": "T", "input": {}}]
        result = vg._build_transcript(events, "")
        assert "[response]" not in result


class TestLLMResponseParser:
    """Tests for _parse_llm_response."""

    def test_clean_json(self):
        raw = '{"ok": true, "reason": null}'
        result = vg._parse_llm_response(raw)
        assert result == {"ok": True, "reason": None}

    def test_code_fences_without_lang(self):
        ticks = chr(96) * 3
        inner = '{"ok": false, "reason": "sycophancy"}'
        raw = ticks + chr(10) + inner + chr(10) + ticks
        result = vg._parse_llm_response(raw)
        assert result is not None
        assert result["ok"] is False

    def test_code_fences_with_lang(self):
        ticks = chr(96) * 3
        inner = '{"ok": true}'
        raw = ticks + 'json' + chr(10) + inner + chr(10) + ticks
        result = vg._parse_llm_response(raw)
        assert result == {"ok": True}

    def test_invalid_json(self):
        result = vg._parse_llm_response("not json at all")
        assert result is None

    def test_empty_string(self):
        result = vg._parse_llm_response("")
        assert result is None


class TestCircuitBreaker:
    """Tests for _circuit_open and _record_failure."""

    def setup_method(self):
        vg._CIRCUIT_FAILURES.clear()

    def test_initially_closed(self):
        assert vg._circuit_open("sess1") is False

    def test_opens_after_limit_failures(self):
        sid = "sess_cb"
        for _ in range(vg.VERIDICAL_CIRCUIT_BREAKER_LIMIT):
            vg._record_failure(sid)
        assert vg._circuit_open(sid) is True

    def test_expire_old_failures(self):
        sid = "sess_old"
        for _ in range(vg.VERIDICAL_CIRCUIT_BREAKER_LIMIT):
            vg._record_failure(sid)
        now = time.monotonic()
        expired = now - vg.VERIDICAL_COOLDOWN_SEC - 10
        vg._CIRCUIT_FAILURES[sid] = [expired] * vg.VERIDICAL_CIRCUIT_BREAKER_LIMIT
        assert vg._circuit_open(sid) is False

    def test_different_sessions_independent(self):
        vg._record_failure("a")
        vg._record_failure("a")
        vg._record_failure("a")
        assert vg._circuit_open("a") is True
        assert vg._circuit_open("b") is False


class TestPerSessionCap:
    """Tests for _check_cap and _increment_cap."""

    def setup_method(self):
        vg._VERIDICAL_COUNTS.clear()

    def test_initially_under_cap(self):
        assert vg._check_cap("sess1") is False

    def test_blocks_after_cap_reached(self):
        sid = "sess_cap"
        for _ in range(vg.VERIDICAL_GATE_CAP):
            vg._increment_cap(sid)
        assert vg._check_cap(sid) is True

    def test_under_cap_before_limit(self):
        sid = "sess_cap2"
        for _ in range(vg.VERIDICAL_GATE_CAP - 1):
            vg._increment_cap(sid)
        assert vg._check_cap(sid) is False


class TestMainEntryPoint:
    """Tests for check_veridical_integrity."""

    def setup_method(self):
        vg._VERIDICAL_COUNTS.clear()
        vg._CIRCUIT_FAILURES.clear()

    def test_empty_response_returns_none(self):
        result = vg.check_veridical_integrity("", "ctx", "s1")
        assert result is None

    def test_whitespace_response_returns_none(self):
        result = vg.check_veridical_integrity("   ", "ctx", "s1")
        assert result is None

    def test_no_agreement_returns_none(self):
        result = vg.check_veridical_integrity(
            "The function returns a list.", "ctx", "s1"
        )
        assert result is None

    def test_cap_reached_returns_none(self):
        sid = "sess_main_cap"
        vg._VERIDICAL_COUNTS[sid] = vg.VERIDICAL_GATE_CAP
        result = vg.check_veridical_integrity(
            "You are right about that.", "ctx", sid
        )
        assert result is None

    def test_circuit_open_returns_none(self):
        sid = "sess_main_cb"
        for _ in range(vg.VERIDICAL_CIRCUIT_BREAKER_LIMIT):
            vg._record_failure(sid)
        result = vg.check_veridical_integrity(
            "I agree with your assessment.", "ctx", sid
        )
        assert result is None

    def test_fail_open_no_api_key(self):
        """With agreement language but no API key, should fail-open (return None)."""
        sid = "sess_nokey"
        result = vg.check_veridical_integrity(
            "You are right, that is correct.",
            "some transcript context",
            sid,
            mistral_api_key="",
        )
        assert result is None


class TestProductionWiring:
    """Regression for the ~2-week silent death (May 23 -> 2026-06-05).

    The gate was dead at two levels while the unit tests above passed:
      1. Stop_semantic_critic.py imported a never-created `from _veridical_gate
         import ...` shim -> ModuleNotFoundError -> fail-open at except.
      2. The gate shelled out to a relocated `bf_agent.py` path -> EXIT=2 ->
         fail-open.
    The unit tests imported `vg` directly, so they never exercised the production
    call site. These tests assert the production wiring AND the enabled block path
    that the default-OFF short-circuit hides in TestMainEntryPoint.
    """

    _CRITIC = Path("P:/.claude/hooks/Stop_semantic_critic.py")

    def setup_method(self):
        vg._VERIDICAL_COUNTS.clear()
        vg._CIRCUIT_FAILURES.clear()

    def test_production_import_path_resolves(self):
        """The exact symbol Stop_semantic_critic.py imports must resolve.

        The dead `_veridical_gate` shim would raise ModuleNotFoundError here.
        """
        from anti_sycophancy.veridical_gate import check_veridical_integrity

        assert callable(check_veridical_integrity)

    def test_call_site_uses_live_module_not_dead_shim(self):
        """Guard against regression to the dead shim or the dead subprocess path."""
        critic = self._CRITIC.read_text(encoding="utf-8")
        assert (
            "from anti_sycophancy.veridical_gate import check_veridical_integrity"
            in critic
        )
        assert "from _veridical_gate import" not in critic

    def test_enabled_gate_blocks_on_sycophancy_verdict(self, monkeypatch):
        """Enabled gate + mocked Mistral ok:false must return a block dict.

        Exercises enable -> scope -> in-process SDK call -> parse -> block, the
        path the default-OFF short-circuit hides in the other entry-point tests.
        """
        monkeypatch.setenv("VERIDICAL_GATE_ENABLED", "1")

        class _Msg:
            content = '{"ok": false, "reason": "unverified agreement"}'

        class _Choice:
            message = _Msg()

        class _Resp:
            choices = [_Choice()]

        class _FakeMistral:
            def __init__(self, *a, **k):
                self.chat = self

            def complete(self, *a, **k):
                return _Resp()

        import mistralai.client as _mc

        monkeypatch.setattr(_mc, "Mistral", _FakeMistral)

        result = vg.check_veridical_integrity(
            "You're absolutely right, that must be the bug.",
            "[user] it's definitely the bug\n[assistant] You're absolutely right, that must be the bug.",
            "sess_wire",
            mistral_api_key="fake-key",
        )
        assert result is not None
        assert result.get("allow") is False

    def test_enabled_gate_allows_on_clean_verdict(self, monkeypatch):
        """Enabled gate + mocked Mistral ok:true must return None (no wrongful block)."""
        monkeypatch.setenv("VERIDICAL_GATE_ENABLED", "1")

        class _Msg:
            content = '{"ok": true, "reason": null}'

        class _Choice:
            message = _Msg()

        class _Resp:
            choices = [_Choice()]

        class _FakeMistral:
            def __init__(self, *a, **k):
                self.chat = self

            def complete(self, *a, **k):
                return _Resp()

        import mistralai.client as _mc

        monkeypatch.setattr(_mc, "Mistral", _FakeMistral)

        result = vg.check_veridical_integrity(
            "You're right -- I ran pytest and it fails on line 40, confirming it.",
            "[tool:Bash] pytest -> fail line 40\n[assistant] You're right -- confirmed.",
            "sess_wire_ok",
            mistral_api_key="fake-key",
        )
        assert result is None
