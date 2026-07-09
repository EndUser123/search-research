"""Regression test for the home-drive exemption in PreToolUse_git_safety.

Root cause fixed: user-home tool config (CCR ~/.claude-code-router, MCP
~/.claude.json, ~/.pi, ~/.gemini, ~/.claude) was misclassified as cross-worktree
access and blocked on every Edit, because the exemption only covered ~/.claude
specifically. The fix exempts any path under Path.home() when the current
worktree is NOT itself under home (so a repo under home keeps real enforcement).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_HOOK = Path(__file__).resolve().parent.parent / "hooks" / "pretool" / "PreToolUse_git_safety.py"


def _load():
    spec = importlib.util.spec_from_file_location("ptu_git_safety", _HOOK)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["ptu_git_safety"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_ccr_config_edit_is_allowed() -> None:
    """The reported false positive: ~/.claude-code-router/config.json."""
    mod = _load()
    target = Path.home() / ".claude-code-router" / "config.json"
    result = mod.check_worktree_cross_contamination(
        "Edit", {"file_path": str(target)}, {}
    )
    assert result["decision"] == "allow", result
    assert "User-home path" in result.get("reason", "")


def test_generic_sibling_under_home_allowed() -> None:
    """Any sibling tool config under home is exempted (not just ~/.claude)."""
    mod = _load()
    for sub in (".claude", ".claude.json", ".pi", ".gemini", ".config"):
        target = Path.home() / sub
        result = mod.check_worktree_cross_contamination(
            "Edit", {"file_path": str(target)}, {}
        )
        assert result["decision"] == "allow", f"{sub}: {result}"
        assert "User-home path" in result.get("reason", "")


def test_home_exemption_never_fires_for_non_home_path() -> None:
    """Regression guard: a path NOT under home must never take the home-exemption
    branch. (Whether it then blocks or fails open depends on the worktree
    resolver + drive layout; this test only pins that the home reason is absent,
    so the exemption can't silently widen to arbitrary paths.)"""
    mod = _load()
    # A path on a foreign drive letter (not C:\Users\.. = not home; not P:\).
    result = mod.check_worktree_cross_contamination(
        "Edit", {"file_path": "Z:/foreign/not_under_home.py"}, {}
    )
    assert "User-home path" not in result.get("reason", ""), result
