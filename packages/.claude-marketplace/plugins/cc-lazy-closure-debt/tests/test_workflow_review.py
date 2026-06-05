"""Tests for cc-lazy-closure-debt workflow review helpers."""
from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "__lib"))

from __lib.workflow_review import (  # noqa: E402
    classify_workflow,
    format_workflow_review,
    format_workflow_review_stats,
    record_workflow_review,
    summarize_workflow_reviews,
)


def test_classify_subagent_when_multi_file_and_no_agent():
    review = classify_workflow(
        {
            "tool_events": [
                {"name": "Edit", "file_path": "a.py"},
                {"name": "Write", "file_path": "b.py"},
                {"name": "MultiEdit", "file_path": "c.py"},
            ]
        },
        [{"phrase": "leave that for later", "occurrences": 1}],
    )
    assert review["recommendation"] == "subagent"
    assert "subagent" in review["summary"].lower()


def test_classify_external_llm_for_comparative_prompt():
    review = classify_workflow(
        {"prompt": "what is the best approach for this trade-off?"},
        [],
    )
    assert review["recommendation"] == "external_llm"
    assert "decision-heavy" in review["summary"].lower() or "comparative" in review["summary"].lower()


def test_classify_local_for_repeated_single_item():
    review = classify_workflow(
        {},
        [{"phrase": "leave that for now", "occurrences": 3}],
    )
    assert review["recommendation"] == "local"
    assert "fix it once" in review["summary"].lower()


def test_format_review_includes_signals():
    review = {
        "recommendation": "subagent",
        "summary": "Split the work.",
        "signals": ["3 file ops", "unique debt item"],
    }
    rendered = format_workflow_review(review)
    assert "[cc-lazy-closure-debt review]" in rendered
    assert "Suggested executor: subagent" in rendered
    assert "3 file ops" in rendered


def test_review_metrics_log_round_trip(tmp_path):
    data = {"terminal_id": "term-metrics"}
    first = {"recommendation": "local", "signals": ["1 file op"]}
    second = {"recommendation": "subagent", "signals": ["3 file ops"]}
    third = {"recommendation": "external_llm", "signals": ["compare"]}

    record_workflow_review(data, first, state_root=tmp_path)
    record_workflow_review(data, second, state_root=tmp_path)
    record_workflow_review(data, third, state_root=tmp_path)

    summary = summarize_workflow_reviews("term-metrics", state_root=tmp_path)
    assert summary["total"] == 3
    assert summary["counts"]["local"] == 1
    assert summary["counts"]["subagent"] == 1
    assert summary["counts"]["external_llm"] == 1

    rendered = format_workflow_review_stats(summary)
    assert "local=1" in rendered
    assert "subagent=1" in rendered
    assert "external_llm=1" in rendered
