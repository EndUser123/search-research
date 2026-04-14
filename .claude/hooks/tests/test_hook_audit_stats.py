from __future__ import annotations

import sys
from pathlib import Path

HOOKS_DIR = Path("P:/.claude/hooks")
sys.path.insert(0, str(HOOKS_DIR))

import hook_audit_dashboard


def test_hook_audit_stats_prints_turn_scoped_summary(monkeypatch, capsys) -> None:
    sample_rows = [
        {
            "timestamp": "2026-04-13T12:00:00+00:00",
            "session_id": "session-a",
            "terminal_id": "terminal-a",
            "turn_id": "turn-123",
            "hook_name": "behavior_contract",
            "event_type": "UserPromptSubmit",
            "action": "inject",
            "reason": "behavior_contract_injection",
        },
        {
            "timestamp": "2026-04-13T12:01:00+00:00",
            "session_id": "session-a",
            "terminal_id": "terminal-a",
            "turn_id": "turn-123",
            "hook_name": "Stop.py:behavior_audit",
            "event_type": "Stop",
            "action": "block",
            "reason": "UNVERIFIED CLAIMS",
        },
    ]

    monkeypatch.setattr(hook_audit_dashboard, "query_hook_invocations", lambda **kwargs: sample_rows)

    hook_audit_dashboard.stats(days=7, turn_id="turn-123", limit=10)

    output = capsys.readouterr().out

    assert "Hook Database Stats" in output
    assert "turn: turn-123" in output
    assert "Events: 2" in output
    assert "Injects: 1 | Blocks: 1" in output
    assert "/hook-audit stats --turn <turn-id>" in output
