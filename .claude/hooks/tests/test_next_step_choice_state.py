#!/usr/bin/env python3

from __future__ import annotations

from __lib.next_step_choice_state import (
    detect_number_choice,
    resolve_choice_to_command,
)


def test_detect_number_choice():
    assert detect_number_choice("0") == "0"
    assert detect_number_choice(" 1 ") == "1"
    assert detect_number_choice("A") is None
    assert detect_number_choice("0 - /commit") is None


def test_resolve_choice_to_command():
    state = {
        "pending": True,
        "options": [
            {"label": "0", "command": "/task-unresolved", "display": "/task-unresolved - Scan unresolved"},
            {"label": "1", "command": "/commit", "display": "/commit - Commit changes"},
        ],
    }
    assert resolve_choice_to_command(state, "0") == (
        "/task-unresolved",
        "/task-unresolved - Scan unresolved",
    )
    assert resolve_choice_to_command(state, "1") == ("/commit", "/commit - Commit changes")
    assert resolve_choice_to_command(state, "2") is None
