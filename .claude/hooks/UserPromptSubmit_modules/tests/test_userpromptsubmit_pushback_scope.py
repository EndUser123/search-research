"""Tests for UserPromptSubmit pushback marker scoping."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_userpromptsubmit_module():  # type: ignore[no-untyped-def]
    hooks_dir = Path(__file__).resolve().parent.parent.parent
    module_path = hooks_dir / "UserPromptSubmit.py"
    spec = importlib.util.spec_from_file_location("userpromptsubmit_entry", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pushback_marker_paths_are_session_terminal_scoped() -> None:
    module = _load_userpromptsubmit_module()
    data_a = {"session_id": "session-A", "terminal_id": "terminal-1"}
    data_b = {"session_id": "session-A", "terminal_id": "terminal-2"}

    scoped_a, legacy_a = module._get_challenge_marker_paths(data_a)
    scoped_b, legacy_b = module._get_challenge_marker_paths(data_b)

    assert scoped_a != scoped_b
    assert scoped_a.name.startswith("last_blocked_claim_session-A_terminal-1")
    assert scoped_b.name.startswith("last_blocked_claim_session-A_terminal-2")
    assert legacy_a == legacy_b


def test_safe_id_sanitizes_filesystem_unsafe_characters() -> None:
    module = _load_userpromptsubmit_module()
    value = "session:abc/def*ghi?"
    assert module._safe_id(value) == "session_abc_def_ghi_"
