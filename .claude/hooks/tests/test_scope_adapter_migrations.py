from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_unverified_stance_context_loader_uses_session_fresh(monkeypatch) -> None:
    import StopHook_unverified_stance as hook

    captured: dict[str, object] = {}

    def fake_load_scoped_tool_events(**kwargs):
        captured.update(kwargs)
        return [{"id": 1, "name": "Read"}]

    monkeypatch.setattr(hook, "load_scoped_tool_events", fake_load_scoped_tool_events)

    result = hook.load_tool_events_for_context(
        session_id="session-1",
        terminal_id="terminal-1",
        limit=321,
    )

    assert result == [{"id": 1, "name": "Read"}]
    assert captured == {
        "session_id": "session-1",
        "terminal_id": "terminal-1",
        "scope": "session_fresh",
        "limit": 321,
    }


def test_unverified_stance_runtime_loader_uses_session_fresh(monkeypatch) -> None:
    import StopHook_unverified_stance as hook

    captured: dict[str, object] = {}

    def fake_load_scoped_tool_events(**kwargs):
        captured.update(kwargs)
        return [{"id": 2, "name": "Bash"}]

    monkeypatch.setattr(hook, "load_scoped_tool_events", fake_load_scoped_tool_events)

    result = hook.load_tool_events("session-2", limit=111)

    assert result == [{"id": 2, "name": "Bash"}]
    assert captured == {
        "session_id": "session-2",
        "scope": "session_fresh",
        "limit": 111,
    }


@pytest.mark.parametrize(
    ("module_name", "limit"),
    [
        ("Stop_completion_verification_guard", 500),
        ("Stop_negative_existence_guard", 200),
        ("Stop_unverified_existence_gate", 200),
    ],
)
def test_turn_scoped_adapters_use_turn_strict_for_uuid_sessions(
    monkeypatch, module_name: str, limit: int
) -> None:
    module = __import__(module_name)
    captured: dict[str, object] = {}

    def fake_load_scoped_tool_events(**kwargs):
        captured.update(kwargs)
        return [{"id": 10, "name": "Read", "command": "foo.py"}]

    monkeypatch.setattr(module, "load_scoped_tool_events", fake_load_scoped_tool_events)

    result = module._load_turn_events(
        "11111111-1111-1111-1111-111111111111",
        "terminal-3",
    )

    assert result == [{"id": 10, "name": "Read", "command": "foo.py"}]
    assert captured == {
        "session_id": "11111111-1111-1111-1111-111111111111",
        "terminal_id": "terminal-3",
        "scope": "turn_strict",
        "limit": limit,
    }
