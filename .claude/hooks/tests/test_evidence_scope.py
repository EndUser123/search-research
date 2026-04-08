from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import evidence_scope as scope


def test_turn_strict_uses_explicit_turn_scoping(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_load_tool_events_for_context(
        session_id: str,
        terminal_id: str,
        limit: int = 500,
        within_seconds: int | None = None,
        use_turn_scoping: bool | None = None,
    ) -> list[dict]:
        captured["use_turn_scoping"] = use_turn_scoping
        return [{"id": 1, "name": "Read", "command": "a.py", "terminal_id": terminal_id}]

    monkeypatch.setattr(scope, "load_tool_events_for_context", fake_load_tool_events_for_context)

    events = scope.load_scoped_tool_events(
        session_id="11111111-1111-1111-1111-111111111111",
        terminal_id="term-1",
        scope=scope.SCOPE_TURN_STRICT,
    )

    assert captured["use_turn_scoping"] is True
    assert len(events) == 1


def test_session_fresh_merges_current_turn_events(monkeypatch) -> None:
    monkeypatch.setattr(
        scope,
        "load_tool_events_for_context",
        lambda session_id, terminal_id, limit=500, within_seconds=None, use_turn_scoping=None: [
            {"id": 10, "name": "Read", "command": "persisted.py", "terminal_id": terminal_id}
        ],
    )

    events = scope.load_scoped_tool_events(
        session_id="22222222-2222-2222-2222-222222222222",
        terminal_id="term-2",
        scope=scope.SCOPE_SESSION_FRESH,
        current_turn_events=[{"id": 1, "name": "Bash", "command": "pytest", "terminal_id": "term-2"}],
    )

    assert [event["name"] for event in events] == ["Bash", "Read"]


def test_session_fresh_mutation_safe_filters_invalidated_artifacts(monkeypatch) -> None:
    monkeypatch.setattr(
        scope,
        "load_tool_events_for_context",
        lambda session_id, terminal_id, limit=500, within_seconds=None, use_turn_scoping=None: [
            {"id": 1, "name": "Read", "command": "P:/repo/stale.py", "terminal_id": terminal_id},
            {"id": 2, "name": "Read", "command": "P:/repo/fresh.py", "terminal_id": terminal_id},
        ],
    )
    monkeypatch.setattr(
        scope,
        "is_file_invalidated",
        lambda path: path.endswith("stale.py"),
    )

    events = scope.load_scoped_tool_events(
        session_id="33333333-3333-3333-3333-333333333333",
        terminal_id="term-3",
        scope=scope.SCOPE_SESSION_FRESH_MUTATION_SAFE,
    )

    assert [event["command"] for event in events] == ["P:/repo/fresh.py"]
