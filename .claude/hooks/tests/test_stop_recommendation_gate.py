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


# ---------------------------------------------------------------------------
# Dismissal patterns — positive (should clear nag)
# ---------------------------------------------------------------------------


def test_dismissal_patterns_clear_nag(monkeypatch, tmp_path: Path) -> None:
    """Responses with completion signals should clear the persistent nag."""
    monkeypatch.setenv("CSF_STATE_DIR", str(tmp_path))
    monkeypatch.setattr(gate, "prompt_session_state", _no_prompt_state())

    data = {"session_id": "session-d1", "terminal_id": "terminal-d1"}
    gate.check_recommendation(BREACH_RESPONSE, data)

    cases = [
        "Here's what I added to GTO. Tests pass.",
        "I've completed the update. All tests pass.",
        "Cleanup done, now back to bf diagnostic.",
        "I didn't stop — I answered fully above.",
        "already done.",
        "Tests pass.",
        "all 10 tests pass.",
    ]
    for response in cases:
        result = gate.check_recommendation(response, data)
        assert result is None, f"Expected None for: {response!r}"


def test_dismissal_with_open_question_does_not_clear(monkeypatch, tmp_path: Path) -> None:
    """Dismissal signal but also an open question — nag stays."""
    monkeypatch.setenv("CSF_STATE_DIR", str(tmp_path))
    monkeypatch.setattr(gate, "prompt_session_state", _no_prompt_state())

    data = {"session_id": "session-d2", "terminal_id": "terminal-d2"}
    gate.check_recommendation(BREACH_RESPONSE, data)

    # "Here's what I added" is dismissal, but "should I also...?" is open question
    response = "Here's what I added. Should I add tests too?"
    result = gate.check_recommendation(response, data)
    assert result is not None
    assert "pending" in result["systemMessage"].lower()


# ---------------------------------------------------------------------------
# Dismissal patterns — negative (should NOT clear nag)
# ---------------------------------------------------------------------------


def test_open_questions_keep_nag(monkeypatch, tmp_path: Path) -> None:
    """Responses that are purely open questions should NOT clear the nag."""
    monkeypatch.setenv("CSF_STATE_DIR", str(tmp_path))
    monkeypatch.setattr(gate, "prompt_session_state", _no_prompt_state())

    data = {"session_id": "session-d3", "terminal_id": "terminal-d3"}
    gate.check_recommendation(BREACH_RESPONSE, data)

    cases = [
        "Should I add dismissal patterns?",
        "What do you want me to do next?",
        "Which would you prefer?",
        "Do you want me to proceed?",
    ]
    for response in cases:
        result = gate.check_recommendation(response, data)
        assert result is not None, f"Expected nag for: {response!r}"


# ---------------------------------------------------------------------------
# Persistence — nag clears and stays cleared across turns
# ---------------------------------------------------------------------------


def test_dismissal_clears_and_stays_cleared(monkeypatch, tmp_path: Path) -> None:
    """After dismissal, subsequent turns stay clear (no lingering state)."""
    monkeypatch.setenv("CSF_STATE_DIR", str(tmp_path))
    monkeypatch.setattr(gate, "prompt_session_state", _no_prompt_state())

    data = {"session_id": "session-p1", "terminal_id": "terminal-p1"}
    gate.check_recommendation(BREACH_RESPONSE, data)

    result1 = gate.check_recommendation("Here's what I added.", data)
    assert result1 is None

    # 3 more turns without re-offending
    result2 = gate.check_recommendation("Continuing the analysis.", data)
    assert result2 is None
    result3 = gate.check_recommendation("Next step is done.", data)
    assert result3 is None
    result4 = gate.check_recommendation("Wrapping up.", data)
    assert result4 is None


def test_check_dismissal_function(monkeypatch) -> None:
    """Unit test for the _check_dismissal helper."""
    # Positive dismissals (using curly apostrophes like real LLM output)
    assert gate._check_dismissal("Here's what I added to GTO.") is True
    assert gate._check_dismissal("I've completed the update.") is True
    assert gate._check_dismissal("Cleanup done, now back to work.") is True
    assert gate._check_dismissal("I didn't stop — I answered fully.") is True
    assert gate._check_dismissal("Tests pass.") is True
    assert gate._check_dismissal("all 10 tests pass.") is True
    assert gate._check_dismissal("Already done.") is True

    # Negative — too short
    assert gate._check_dismissal("Done.") is False
    assert gate._check_dismissal("") is False

    # Negative — open question present
    assert gate._check_dismissal("Here's what I added. Should I add tests?") is False
    assert gate._check_dismissal("Which option should I choose?") is False

    # Negative — no dismissal pattern
    assert gate._check_dismissal("The implementation looks good.") is False
    assert gate._check_dismissal("Let me think about this.") is False
