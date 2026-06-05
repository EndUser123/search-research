"""Tests for the dual injector-skip in registry.py.

Two independent cuts:
  - CEREMONY skip: model-INDEPENDENT (the `message.model` label is unreliable under
    CLI aliasing), applied every turn unless CEREMONY_SKIP_HOOKS="".
  - WEAK extras: added only when a literal non-Claude model is positively detected AND
    tier gating is available + enabled.

No mocks: model tier is resolved from a real temp transcript JSONL.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parents[2]
for _p in (str(_HOOKS_DIR), str(_HOOKS_DIR / "__lib")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

registry = importlib.import_module("UserPromptSubmit_modules.registry")


def _write_transcript(tmp_path: Path, model: str) -> str:
    p = tmp_path / "transcript.jsonl"
    rows = [
        {"type": "user", "message": {"role": "user", "content": "hi"}},
        {"type": "assistant", "message": {"role": "assistant", "model": model}},
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return str(p)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.setenv("MODEL_TIER_GATING_ENABLED", "true")
    monkeypatch.delenv("CEREMONY_SKIP_HOOKS", raising=False)
    monkeypatch.delenv("WEAK_MODEL_SKIP_HOOKS", raising=False)
    yield


def test_claude_label_gets_ceremony_only(tmp_path):
    # A claude-* label (real OR CLI-aliased — indistinguishable) → ceremony, no weak extras.
    data = {"transcript_path": _write_transcript(tmp_path, "claude-opus-4-8")}
    skip = registry._tier_skip_set(data)
    assert skip == registry._DEFAULT_CEREMONY_SKIP
    assert "behavior_contract" not in skip  # weak-only extra, not applied
    assert "recommendation_rubric_injector" not in skip


def test_weak_model_gets_ceremony_plus_weak(tmp_path):
    data = {"transcript_path": _write_transcript(tmp_path, "MiniMax-M3")}
    skip = registry._tier_skip_set(data)
    assert registry._DEFAULT_CEREMONY_SKIP <= skip          # ceremony always
    assert registry._DEFAULT_WEAK_MODEL_SKIP <= skip        # plus weak extras
    assert "behavior_contract" in skip


def test_gating_disabled_keeps_ceremony_drops_weak(tmp_path, monkeypatch):
    # Ceremony is independent of tier gating; weak extras require it.
    monkeypatch.setenv("MODEL_TIER_GATING_ENABLED", "false")
    strong = {"transcript_path": _write_transcript(tmp_path, "claude-opus-4-8")}
    weak = {"transcript_path": _write_transcript(tmp_path, "MiniMax-M3")}
    assert registry._tier_skip_set(strong) == registry._DEFAULT_CEREMONY_SKIP
    assert registry._tier_skip_set(weak) == registry._DEFAULT_CEREMONY_SKIP


def test_no_transcript_gets_ceremony_only(tmp_path):
    # Unknown model (fail-open) → ceremony, no weak extras.
    assert registry._tier_skip_set({}) == registry._DEFAULT_CEREMONY_SKIP


def test_ceremony_env_override_custom(tmp_path, monkeypatch):
    monkeypatch.setenv("CEREMONY_SKIP_HOOKS", "think_trigger , cognitive_enhancers")
    data = {"transcript_path": _write_transcript(tmp_path, "claude-sonnet-4-6")}
    assert registry._tier_skip_set(data) == frozenset({"think_trigger", "cognitive_enhancers"})


def test_ceremony_empty_disables_for_claude(tmp_path, monkeypatch):
    monkeypatch.setenv("CEREMONY_SKIP_HOOKS", "")
    data = {"transcript_path": _write_transcript(tmp_path, "claude-opus-4-8")}
    assert registry._tier_skip_set(data) == frozenset()


def test_ceremony_empty_weak_still_gets_weak_extras(tmp_path, monkeypatch):
    # Disabling ceremony must not disable the weak extras path.
    monkeypatch.setenv("CEREMONY_SKIP_HOOKS", "")
    data = {"transcript_path": _write_transcript(tmp_path, "glm-5.1")}
    assert registry._tier_skip_set(data) == registry._DEFAULT_WEAK_MODEL_SKIP


def test_log_tier_skip_writes_only_registered(tmp_path, monkeypatch):
    log = tmp_path / "ups_tier_skip.jsonl"
    monkeypatch.setattr(registry, "_TIER_SKIP_LOG", log)
    ctx = registry.HookContext(prompt="x", data={}, session_id="s1", terminal_id="t1")
    registry._log_tier_skip(ctx, frozenset({"think_trigger", "__not_a_real_hook__"}))
    if "think_trigger" in registry.HOOKS:
        assert log.exists()
        rec = json.loads(log.read_text(encoding="utf-8").strip())
        assert rec["skipped"] == ["think_trigger"]
    else:
        assert not log.exists()
