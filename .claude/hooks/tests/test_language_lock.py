"""Tests for language_lock UserPromptSubmit module."""

import json
import os
from pathlib import Path

import pytest

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.language_lock import (
    _CASUAL,
    _counter_path,
    _DEFAULT_INTERVAL,
    _increment_and_check,
    _INJECTION,
    language_lock,
)


def _ctx(prompt: str, terminal_id: str = "test", **kwargs) -> HookContext:
    return HookContext(prompt=prompt, data=kwargs, session_id="test", terminal_id=terminal_id)


@pytest.fixture(autouse=True)
def _tmp_artifacts(monkeypatch, tmp_path):
    """Redirect artifacts dir to tmp_path for isolation."""
    import UserPromptSubmit_modules.language_lock as mod

    def _fake_artifacts_dir(terminal_id: str) -> Path:
        d = tmp_path / ".artifacts" / terminal_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    monkeypatch.setattr(mod, "_artifacts_dir", _fake_artifacts_dir)


class TestLanguageLock:
    def test_enabled_by_default(self):
        result = language_lock(_ctx("What is the schema for stop hooks?"))
        assert not result.is_empty()

    def test_injects_on_first_substantive_prompt(self):
        result = language_lock(_ctx("Fix the bug in Stop.py"))
        assert not result.is_empty()
        assert _INJECTION in result.context

    def test_skips_casual_responses(self):
        for casual in _CASUAL:
            result = language_lock(_ctx(casual))
            assert result.is_empty(), f"Should skip casual '{casual}'"

    def test_skips_slash_commands(self):
        result = language_lock(_ctx("/wiki query hooks"))
        assert result.is_empty()

    def test_skips_empty_prompt(self):
        result = language_lock(_ctx(""))
        assert result.is_empty()

    def test_respects_env_disable(self, monkeypatch):
        monkeypatch.setenv("LANGUAGE_LOCK_ENABLED", "false")
        result = language_lock(_ctx("What is the schema?"))
        assert result.is_empty()

    def test_priority_is_high(self):
        result = language_lock(_ctx("Analyze the root cause"))
        assert result.priority == 2.0

    def test_injection_text_is_english_only(self):
        result = language_lock(_ctx("Test prompt"))
        assert "English only" in result.context
        assert "SESSION CONSTRAINT" in result.context


class TestIntervalBehavior:
    """Test that injection fires every Nth turn, not every turn."""

    def test_injects_on_turn_1(self):
        result = language_lock(_ctx("Turn one prompt", terminal_id="interval-1"))
        assert not result.is_empty()

    def test_skips_on_turn_2(self):
        tid = "interval-2"
        language_lock(_ctx("Turn one", terminal_id=tid))
        result = language_lock(_ctx("Turn two", terminal_id=tid))
        assert result.is_empty()

    def test_injects_again_on_turn_6(self):
        """With N=5, turn 6 should inject (6 % 5 == 1)."""
        tid = "interval-6"
        for i in range(5):
            language_lock(_ctx(f"Turn {i+1}", terminal_id=tid))
        result = language_lock(_ctx("Turn six prompt", terminal_id=tid))
        assert not result.is_empty()

    def test_full_cycle_with_default_interval(self):
        """Verify the 5-turn cycle: inject, skip x4, inject."""
        tid = "cycle-test"
        results = []
        for i in range(11):
            r = language_lock(_ctx(f"Turn {i+1}", terminal_id=tid))
            results.append(not r.is_empty())
        assert results == [True, False, False, False, False, True, False, False, False, False, True]

    def test_custom_interval_via_env(self, monkeypatch):
        monkeypatch.setenv("LANGUAGE_LOCK_INTERVAL", "3")
        tid = "custom-interval"
        results = []
        for i in range(7):
            r = language_lock(_ctx(f"Turn {i+1}", terminal_id=tid))
            results.append(not r.is_empty())
        assert results == [True, False, False, True, False, False, True]

    def test_different_terminals_independent(self):
        """Two terminals should have independent counters."""
        r1 = language_lock(_ctx("T1 turn 1", terminal_id="term-a"))
        r2 = language_lock(_ctx("T2 turn 1", terminal_id="term-b"))
        assert not r1.is_empty()
        assert not r2.is_empty()

        r1_t2 = language_lock(_ctx("T1 turn 2", terminal_id="term-a"))
        assert r1_t2.is_empty()


class TestCounterState:
    """Unit tests for the per-terminal counter file."""

    def test_returns_true_on_first_call(self):
        assert _increment_and_check("fresh-terminal", 5) is True

    def test_returns_false_for_middle_turns(self):
        _increment_and_check("mid-terminal", 5)  # 1 → True
        assert _increment_and_check("mid-terminal", 5) is False  # 2
        assert _increment_and_check("mid-terminal", 5) is False  # 3
        assert _increment_and_check("mid-terminal", 5) is False  # 4
        assert _increment_and_check("mid-terminal", 5) is False  # 5
        assert _increment_and_check("mid-terminal", 5) is True   # 6

    def test_counter_file_created_in_artifacts(self, tmp_path):
        _increment_and_check("file-test", 5)
        path = _counter_path("file-test")
        assert path.exists()
        assert str(path).startswith(str(tmp_path / ".artifacts"))
        data = json.loads(path.read_text())
        assert data["count"] == 1

    def test_corrupted_state_recovers(self, tmp_path):
        artifacts = tmp_path / ".artifacts" / "corrupted"
        artifacts.mkdir(parents=True, exist_ok=True)
        (artifacts / "language_lock_counter.json").write_text("not json", encoding="utf-8")
        result = _increment_and_check("corrupted", 5)
        assert result is True

    def test_interval_1_always_injects(self):
        for _ in range(5):
            assert _increment_and_check("every-turn", 1) is True
