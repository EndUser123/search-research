"""Tests for language_lock UserPromptSubmit module."""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.language_lock import language_lock, _is_enabled, _INJECTION


def _ctx(prompt: str, **kwargs) -> HookContext:
    return HookContext(prompt=prompt, data=kwargs, session_id="test", terminal_id="test")


class TestLanguageLock:
    def test_enabled_by_default(self):
        assert _is_enabled() is True

    def test_injects_on_substantive_prompt(self):
        result = language_lock(_ctx("What is the schema for stop hooks?"))
        assert not result.is_empty()
        assert _INJECTION in result.context

    def test_injects_on_action_prompt(self):
        result = language_lock(_ctx("Fix the bug in Stop.py"))
        assert not result.is_empty()

    def test_injects_on_medium_prompt(self):
        result = language_lock(_ctx("Why did the test fail and what can we do about it?"))
        assert not result.is_empty()

    def test_skips_casual_responses(self):
        for casual in ("ok", "okay", "thanks", "yes", "no", "got it", "done", "continue", "go ahead", "proceed"):
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
