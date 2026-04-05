"""Integration-style tests for assumption_audit_v2 evidence scoping."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

import assumption_audit_v2 as audit  # noqa: E402
from tool_sequence_manager import ToolSequenceManager  # noqa: E402


def test_success_claim_allows_with_matching_scoped_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sample = {
        "session_id": "session_a",
        "tools": [
            {
                "name": "Read",
                "session_id": "session_a",
                "terminal_id": "term_1",
                "command": "foo.py",
            },
            {
                "name": "Read",
                "session_id": "session_b",
                "terminal_id": "term_1",
                "command": "bar.py",
            },
            {
                "name": "Read",
                "session_id": "session_a",
                "terminal_id": "term_2",
                "command": "baz.py",
            },
            {"name": "Read"},  # unscoped legacy entry should be dropped in strict mode
        ],
    }

    monkeypatch.setattr(ToolSequenceManager, "get_all", classmethod(lambda cls: sample))
    monkeypatch.setattr(audit, "load_tool_sequence_for_evidence", lambda: sample["tools"])
    monkeypatch.setattr(audit, "is_claim_cached", lambda claim: False)
    monkeypatch.setattr(audit, "cache_verified_claims", lambda claims, ts: None)
    monkeypatch.setenv("CLAUDE_SESSION_ID", "session_a")
    monkeypatch.setattr(audit, "TERMINAL_ID", "term_1")
    monkeypatch.setattr(audit, "UNIFIED_VERIFIER_ENABLED", False)
    monkeypatch.setattr(audit, "CLAIM_SCOPE_CHECK_ENABLED", True)

    result = audit.evaluate_response(
        response_text="The file foo.py is fixed.",
        tools_used=[],
        tool_sequence=None,
    )

    assert result["decision"] == "allow"


def test_success_claim_blocks_without_matching_scoped_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sample = {
        "session_id": "session_a",
        "tools": [
            {
                "name": "Read",
                "session_id": "session_b",
                "terminal_id": "term_1",
                "command": "bar.py",
            },
            {
                "name": "Read",
                "session_id": "session_a",
                "terminal_id": "term_2",
                "command": "baz.py",
            },
            {"name": "Read"},  # dropped in strict mode
        ],
    }

    monkeypatch.setattr(ToolSequenceManager, "get_all", classmethod(lambda cls: sample))
    monkeypatch.setattr(audit, "load_tool_sequence_for_evidence", lambda: sample["tools"])
    monkeypatch.setattr(audit, "is_claim_cached", lambda claim: False)
    monkeypatch.setattr(audit, "cache_verified_claims", lambda claims, ts: None)
    monkeypatch.setenv("CLAUDE_SESSION_ID", "session_a")
    monkeypatch.setattr(audit, "TERMINAL_ID", "term_1")
    monkeypatch.setattr(audit, "UNIFIED_VERIFIER_ENABLED", False)
    monkeypatch.setattr(audit, "CLAIM_SCOPE_CHECK_ENABLED", True)

    result = audit.evaluate_response(
        response_text="The file foo.py is fixed.",
        tools_used=[],
        tool_sequence=None,
    )

    assert result["decision"] == "block"
    assert "SCOPE_MISMATCH" in result["reason"]
