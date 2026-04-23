from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

import Stop_recommendation_gate as gate  # type: ignore


BREACH_RESPONSE = (
    "1. Option A: keep current flow and monitor.\n"
    "2. Option B: switch immediately to a stricter mode.\n"
    "Which option would you like me to implement?"
)


def _no_prompt_state() -> SimpleNamespace:
    return SimpleNamespace(read_latest_prompt=lambda payload: ("", "not_found"))


def test_persistent_reminder_repeats_until_direction(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CSF_STATE_DIR", str(tmp_path))
    monkeypatch.setattr(gate, "prompt_session_state", _no_prompt_state())

    data = {"session_id": "session-1", "terminal_id": "terminal-1"}

    first = gate.check_recommendation(BREACH_RESPONSE, data)
    assert first is not None
    assert "persistent" in first["systemMessage"].lower()

    follow_up = gate.check_recommendation("Acknowledged.", data)
    assert follow_up is not None
    assert "still pending" in follow_up["systemMessage"].lower()


def test_direction_clears_pending_state(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CSF_STATE_DIR", str(tmp_path))
    monkeypatch.setattr(gate, "prompt_session_state", _no_prompt_state())

    data = {"session_id": "session-2", "terminal_id": "terminal-2"}
    gate.check_recommendation(BREACH_RESPONSE, data)

    monkeypatch.setattr(
        gate,
        "prompt_session_state",
        SimpleNamespace(read_latest_prompt=lambda payload: ("go with option b", "ok")),
    )

    result = gate.check_recommendation("Thanks, continuing with analysis.", data)
    assert result is None


def test_question_does_not_count_as_direction(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CSF_STATE_DIR", str(tmp_path))
    monkeypatch.setattr(gate, "prompt_session_state", _no_prompt_state())

    data = {"session_id": "session-3", "terminal_id": "terminal-3"}
    gate.check_recommendation(BREACH_RESPONSE, data)

    monkeypatch.setattr(
        gate,
        "prompt_session_state",
        SimpleNamespace(read_latest_prompt=lambda payload: ("which option should I choose?", "ok")),
    )

    result = gate.check_recommendation("Continuing.", data)
    assert result is not None
    assert "still pending" in result["systemMessage"].lower()
