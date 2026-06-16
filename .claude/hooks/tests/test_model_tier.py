#!/usr/bin/env python3
"""Tests for __lib/model_tier.py — strong/weak model classification.

Uses real temp JSONL transcripts (no mocks, per project anti-mock policy).
Fixtures mirror the empirically observed transcript shapes: assistant entries
carry ``message.model`` with the true provider string (Bifrost does not
masquerade as a Claude alias), and ``<synthetic>`` marks compaction/injected
entries.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "__lib"))
import model_tier  # noqa: E402


def _write_transcript(tmp_path: Path, models: list[str | None]) -> str:
    """Write a JSONL transcript; each entry is an assistant turn with given model.

    A model of None emits an entry with no ``model`` key (e.g., a user turn).
    Returns the transcript path as a string.
    """
    p = tmp_path / "session.jsonl"
    with p.open("w", encoding="utf-8") as fh:
        for m in models:
            if m is None:
                entry = {"type": "user", "message": {"role": "user", "content": "hi"}}
            else:
                entry = {"type": "assistant", "message": {"role": "assistant", "model": m, "content": "x"}}
            fh.write(json.dumps(entry) + "\n")
    return str(p)


# ── active_model ─────────────────────────────────────────────────────────────

def test_active_model_returns_last_assistant_model(tmp_path):
    path = _write_transcript(tmp_path, ["claude-opus-4-8", "MiniMax-M3"])
    assert model_tier.active_model({"transcript_path": path}) == "MiniMax-M3"


def test_active_model_skips_synthetic(tmp_path):
    path = _write_transcript(tmp_path, ["claude-opus-4-8", "<synthetic>"])
    assert model_tier.active_model({"transcript_path": path}) == "claude-opus-4-8"


def test_active_model_none_when_no_path():
    assert model_tier.active_model({}) is None


def test_active_model_none_when_file_missing(tmp_path):
    assert model_tier.active_model({"transcript_path": str(tmp_path / "nope.jsonl")}) is None


def test_active_model_none_on_empty_file(tmp_path):
    p = tmp_path / "empty.jsonl"
    p.write_text("", encoding="utf-8")
    assert model_tier.active_model({"transcript_path": str(p)}) is None


def test_active_model_ignores_malformed_lines(tmp_path):
    p = tmp_path / "session.jsonl"
    p.write_text(
        'not json at all\n'
        + json.dumps({"type": "assistant", "message": {"model": "glm-5.1"}}) + "\n"
        + '{"broken": \n',
        encoding="utf-8",
    )
    assert model_tier.active_model({"transcript_path": str(p)}) == "glm-5.1"


# ── model_tier / is_weak_model ───────────────────────────────────────────────

@pytest.mark.parametrize("model,expected", [
    ("claude-opus-4-8", "strong"),
    ("claude-sonnet-4-6", "strong"),
    ("claude-haiku-4-5-20251001", "strong"),
    ("MiniMax-M3", "weak"),
    ("MiniMax-M2.7", "weak"),
    ("glm-5.1", "weak"),
    ("glm-4.7", "weak"),
])
def test_model_tier_classification(tmp_path, model, expected):
    path = _write_transcript(tmp_path, [model])
    assert model_tier.model_tier({"transcript_path": path}) == expected


def test_model_tier_fails_open_strong_on_missing():
    assert model_tier.model_tier({}) == "strong"


def test_is_weak_model_true_for_minimax(tmp_path, monkeypatch):
    monkeypatch.delenv("MODEL_TIER_GATING_ENABLED", raising=False)
    path = _write_transcript(tmp_path, ["MiniMax-M3"])
    assert model_tier.is_weak_model({"transcript_path": path}) is True


def test_is_weak_model_false_for_claude(tmp_path):
    path = _write_transcript(tmp_path, ["claude-opus-4-8"])
    assert model_tier.is_weak_model({"transcript_path": path}) is False


def test_is_weak_model_reflects_current_turn_not_history(tmp_path):
    # User switched away from Claude mid-session → latest turn governs.
    path = _write_transcript(tmp_path, ["claude-opus-4-8", "claude-opus-4-8", "MiniMax-M3"])
    assert model_tier.is_weak_model({"transcript_path": path}) is True


# ── env switches ─────────────────────────────────────────────────────────────

def test_gating_disabled_suppresses_weak_detection(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_TIER_GATING_ENABLED", "false")
    path = _write_transcript(tmp_path, ["MiniMax-M3"])
    assert model_tier.is_weak_model({"transcript_path": path}) is False


def test_strong_prefixes_override(tmp_path, monkeypatch):
    # Treat glm-5.1 as strong via override; M3 stays weak.
    monkeypatch.setenv("STRONG_MODEL_PREFIXES", "claude-,glm-")
    strong = _write_transcript(tmp_path, ["glm-5.1"])
    assert model_tier.model_tier({"transcript_path": strong}) == "strong"
    # M3 stays weak even with the override.
    weak = tmp_path / "weak.jsonl"
    weak.write_text(json.dumps({"type": "assistant", "message": {"model": "MiniMax-M3"}}) + "\n", encoding="utf-8")
    assert model_tier.model_tier({"transcript_path": str(weak)}) == "weak"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
