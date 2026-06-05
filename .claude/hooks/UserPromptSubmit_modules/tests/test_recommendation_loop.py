"""Tests for the recommendation closed-loop system (scope-keyed, event-based staleness)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent.parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from UserPromptSubmit_modules import recommendation_loop as RL  # noqa: E402


# -- recall gate --
@pytest.mark.parametrize("prompt", [
    "what is the optimal solution?", "what's the best approach for caching?",
    "which option should we pick?", "what's the highest-roi path?",
    "should we consolidate these modules?", "is a whitelist better here?",
])
def test_gate_catches(prompt):
    assert RL._gate(prompt) is True


@pytest.mark.parametrize("prompt", ["please read this file", "run the test suite", ""])
def test_gate_skips(prompt):
    assert RL._gate(prompt) is False


# -- scope_key resolution (session_id-first, payload-based, no 'default') --
def test_scope_key_prefers_session_id():
    assert RL.scope_key({"session_id": "S1", "terminal_id": "T1"}) == "S1"

def test_scope_key_falls_back_to_terminal_id():
    assert RL.scope_key({"terminal_id": "T9"}) == "T9"

def test_scope_key_empty_when_no_identity(monkeypatch):
    monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
    monkeypatch.delenv("WT_SESSION", raising=False)
    assert RL.scope_key({}) == ""

def test_scope_key_sanitizes():
    assert "/" not in RL.scope_key({"session_id": "a/b:c-x"})


# -- parser --
def test_parse_reasoning_wrapped():
    v = RL._parse_judge('x {"is_recommendation": true, "compliant": false, "correction": "add an option"} y')
    assert v == {"is_recommendation": True, "compliant": False, "correction": "add an option"}

def test_parse_no_json():
    assert RL._parse_judge("nothing") is None


# -- state round-trip + single-use (no clock) --
def test_roundtrip_single_use():
    RL._write_correction("C", "keyA")
    assert RL.consume_pending_correction("keyA") == "C"
    assert RL.consume_pending_correction("keyA") is None  # single-use


def test_empty_key_noop():
    RL._write_correction("X", "")          # must not write
    assert RL.consume_pending_correction("") is None


# -- THE TWO FIXES --
def test_cross_session_isolation_no_clock():
    """A correction under one session's key is never readable by another session."""
    RL._write_correction("for-session-A", "sessA")
    assert RL.consume_pending_correction("sessB") is None  # different session -> never sees it
    assert RL.consume_pending_correction("sessA") == "for-session-A"


def test_terminal_isolation():
    RL._write_correction("A", "tA")
    RL._write_correction("B", "tB")
    assert RL.consume_pending_correction("tB") == "B"
    assert RL.consume_pending_correction("tA") == "A"


def test_supersede_newest_wins():
    """A newer correction for the same scope overwrites the older one (event-based, no TTL)."""
    RL._write_correction("old", "k")
    RL._write_correction("new", "k")
    assert RL.consume_pending_correction("k") == "new"


# -- fail-open --
def test_judge_fail_open_without_key(monkeypatch):
    monkeypatch.setattr(RL, "_load_key", lambda: None)
    assert RL.judge("what is optimal?", "answer") is None


# -- record_at_stop gating --
def _patch_popen(monkeypatch, counter):
    import subprocess
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: counter.__setitem__("n", counter["n"] + 1))

def test_record_skips_non_recommendation(monkeypatch):
    c = {"n": 0}; _patch_popen(monkeypatch, c)
    RL.record_at_stop({"session_id": "s", "prompt": "read the file", "response": "x" * 200})
    assert c["n"] == 0

def test_record_skips_without_identity(monkeypatch):
    """No session/terminal id -> cannot isolate -> never spawn (no shared bucket)."""
    monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
    monkeypatch.delenv("WT_SESSION", raising=False)
    c = {"n": 0}; _patch_popen(monkeypatch, c)
    RL.record_at_stop({"prompt": "what is the optimal fix?", "response": "x" * 200})
    assert c["n"] == 0

def test_record_disabled_flag(monkeypatch):
    monkeypatch.setenv("RECOMMENDATION_JUDGE_ENABLED", "false")
    c = {"n": 0}; _patch_popen(monkeypatch, c)
    RL.record_at_stop({"session_id": "s", "prompt": "what is optimal?", "response": "x" * 200})
    assert c["n"] == 0

def test_record_spawns_for_recommendation(monkeypatch):
    c = {"n": 0}; _patch_popen(monkeypatch, c)
    RL.record_at_stop({"session_id": "s", "prompt": "what is the optimal fix?", "response": "x" * 200})
    assert c["n"] == 1


# -- injector consumes scoped correction --
def test_injector_scoped(monkeypatch):
    from UserPromptSubmit_modules.recommendation_rubric_injector import recommendation_rubric_injector
    from UserPromptSubmit_modules.base import HookContext
    data = {"session_id": "inj_sess"}
    RL._write_correction("INJECT-ME", RL.scope_key(data))
    r = recommendation_rubric_injector(HookContext(prompt="x", data=data))
    assert "INJECT-ME" in (r.context or "")
    # different session does not see it
    RL._write_correction("OTHER", RL.scope_key({"session_id": "other"}))
    r2 = recommendation_rubric_injector(HookContext(prompt="x", data={"session_id": "inj_sess"}))
    assert not (r2.context or "")  # already consumed for inj_sess; other session's stays isolated
