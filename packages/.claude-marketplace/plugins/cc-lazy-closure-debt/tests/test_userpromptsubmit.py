"""Tests for the cc-lazy-closure-debt UserPromptSubmit hook.

We bypass the hook's bootstrap (which requires a real hooks_resolver chain)
by stubbing the `debt_store` module that the hook imports.
"""
from __future__ import annotations

import importlib
import re
import sys
import time
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "userpromptsubmit"))


@pytest.fixture
def hook(monkeypatch):
    """Re-import the hook with mocked debt_store + gate_residue dependencies."""
    fake = types.ModuleType("debt_store")
    fake_review = types.ModuleType("workflow_review")
    fake_residue = types.ModuleType("gate_residue")

    def recent_deferrals(terminal_id, max_age_h=24.0, max_count=5, state_root=None):
        return fake._items

    def record_workflow_review(data, review, state_root=None):
        fake._records.append((data, review))

    def summarize_workflow_reviews(terminal_id, max_age_h=24.0, state_root=None):
        return {
            "terminal_id": terminal_id,
            "total": len(fake._records),
            "counts": {"local": 1, "subagent": 0, "external_llm": 0},
        }

    def classify_workflow(data, debt_items=None):
        return {"recommendation": "local", "summary": "Keep it local.", "signals": ["test"]}

    def format_workflow_review(review):
        return f"[cc-lazy-closure-debt review] Suggested executor: {review['recommendation']}. {review['summary']} Signals: {'; '.join(review.get('signals', []))}."

    def _safe_id(value):
        if not value:
            return "unknown"
        return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)

    fake.recent_deferrals = recent_deferrals
    fake.record_workflow_review = record_workflow_review
    fake.summarize_workflow_reviews = summarize_workflow_reviews
    fake.format_workflow_review_stats = lambda summary: "[cc-lazy-closure-debt stats] last 24h: local=1, subagent=0, external_llm=0."
    fake._safe_id = _safe_id
    fake._items = []
    fake._records = []
    fake_review.classify_workflow = classify_workflow
    fake_review.format_workflow_review = format_workflow_review
    fake_review.record_workflow_review = record_workflow_review
    fake_review.summarize_workflow_reviews = summarize_workflow_reviews
    fake_review.format_workflow_review_stats = fake.format_workflow_review_stats
    # gate_residue stubs (return empty — existing tests don't exercise residues).
    fake_residue.ingest_new_blocks = lambda terminal_id, state_root=None: []
    fake_residue.classify_block = lambda block, tools, text: ("unresolved", None)
    fake_residue.record_classification = lambda *a, **kw: None
    fake_residue.mark_promoted = lambda *a, **kw: None
    fake_residue.promoted_ledger_ids = lambda terminal_id, state_root=None: set()
    fake_residue.recent_residue = lambda terminal_id, max_age_h=24.0, max_count=5, state_root=None: []
    sys.modules["debt_store"] = fake
    sys.modules["workflow_review"] = fake_review
    sys.modules["gate_residue"] = fake_residue
    sys.modules.pop("cc_lazy_closure_debt_UserPromptSubmit", None)
    return importlib.import_module("cc_lazy_closure_debt_UserPromptSubmit"), fake


class TestUserPromptSubmitHook:
    def test_empty_store_returns_no_context(self, hook):
        mod, fake = hook
        fake._items = []
        result = mod.run({"terminal_id": "t1"})
        assert result == {"continue": True}
        assert "hookSpecificOutput" not in result

    def test_with_items_returns_additional_context(self, hook):
        mod, fake = hook
        now = int(time.time())
        fake._items = [
            {"ts": now - 7200, "terminal_id": "t1", "phrase": "defer that", "transcript_excerpt": ""},
            {"ts": now - 18000, "terminal_id": "t1", "phrase": "defer this", "transcript_excerpt": ""},
        ]
        result = mod.run({"terminal_id": "t1"})
        assert result["continue"] is True
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert "[cc-lazy-closure-debt]" in ctx
        assert "2 pending deferral items" in ctx
        assert "defer that" in ctx
        assert "defer this" in ctx
        assert "2h ago" in ctx
        assert "5h ago" in ctx
        assert "[cc-lazy-closure-debt stats]" not in ctx

    def test_with_items_instructs_task_create(self, hook):
        # Phase 1: surfaced debt must instruct the model to call TaskCreate
        # (one task per unique phrase), replacing the old 'Run /debt' manual
        # workflow. The auto-promote path keeps the JSONL as an audit log.
        mod, fake = hook
        now = int(time.time())
        fake._items = [
            {"ts": now - 60, "terminal_id": "t1",
             "phrase": "defer that", "transcript_excerpt": ""},
        ]
        result = mod.run({"terminal_id": "t1"})
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert "TaskCreate" in ctx, (
            "UserPromptSubmit context must instruct the model to call TaskCreate"
        )
        assert "Run /debt to review" not in ctx

    def test_review_prompt_includes_stats(self, hook):
        mod, fake = hook
        now = int(time.time())
        fake._items = [
            {"ts": now - 60, "terminal_id": "t1", "phrase": "defer that", "transcript_excerpt": ""}
        ]
        result = mod.run({"terminal_id": "t1", "prompt": "/debt review"})
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert "[cc-lazy-closure-debt review]" in ctx
        assert "[cc-lazy-closure-debt stats]" in ctx

    def test_singular_item_grammar(self, hook):
        mod, fake = hook
        now = int(time.time())
        fake._items = [
            {"ts": now - 60, "terminal_id": "t1", "phrase": "defer this", "transcript_excerpt": ""},
        ]
        result = mod.run({"terminal_id": "t1"})
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert "1 pending deferral item " in ctx
        assert "1 pending deferral items" not in ctx

    def test_terminal_id_resolution_no_data(self, hook):
        mod, fake = hook
        fake._items = []
        result = mod.run({})
        assert result == {"continue": True}

    def test_session_nested_terminal_id(self, hook):
        mod, fake = hook
        now = int(time.time())
        fake._items = [
            {"ts": now, "terminal_id": "nested", "phrase": "defer that", "transcript_excerpt": ""},
        ]
        result = mod.run({"session": {"terminal_id": "nested"}})
        assert "additionalContext" in result["hookSpecificOutput"]
        assert "defer that" in result["hookSpecificOutput"]["additionalContext"]
