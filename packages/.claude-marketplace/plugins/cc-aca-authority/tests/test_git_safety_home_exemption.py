"""Regression test for the home-drive exemption in PreToolUse_git_safety.

Root cause fixed: user-home tool config (CCR ~/.claude-code-router, MCP
~/.claude.json, ~/.pi, ~/.gemini, ~/.claude) was misclassified as cross-worktree
access and blocked on every Edit, because the exemption only covered ~/.claude
specifically. The fix exempts any path under Path.home() when the current
worktree is NOT itself under home.

Drives the REAL hook via subprocess (its bootstrap sets up __lib paths that an
importlib load misses) — same contract as Claude Code's PreToolUse dispatch.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_HOOK = Path(__file__).resolve().parent.parent / "hooks" / "pretool" / "PreToolUse_git_safety.py"
_PY = sys.executable


def _run(file_path: str) -> tuple[int, dict]:
    payload = json.dumps({
        "tool_name": "Edit",
        "tool_input": {"file_path": file_path},
        "transcript_path": "",
    })
    proc = subprocess.run(
        [_PY, str(_HOOK)], input=payload, capture_output=True, text=True, timeout=20,
    )
    out = proc.stdout.strip()
    try:
        parsed = json.loads(out) if out else {}
    except json.JSONDecodeError:
        parsed = {"_raw": out}
    return proc.returncode, parsed


def test_ccr_config_edit_is_allowed() -> None:
    """The reported false positive: ~/.claude-code-router/config.json."""
    target = str(Path.home() / ".claude-code-router" / "config.json")
    rc, parsed = _run(target)
    assert rc == 0, f"expected allow (exit 0), got {rc}: {parsed}"
    assert parsed.get("decision") != "block", parsed


def test_generic_sibling_under_home_allowed() -> None:
    """Any sibling tool config under home is exempted (not just ~/.claude)."""
    for sub in (".claude", ".claude.json", ".pi", ".gemini", ".config"):
        rc, parsed = _run(str(Path.home() / sub))
        assert rc == 0, f"{sub}: expected allow, got {rc}: {parsed}"
        assert parsed.get("decision") != "block", f"{sub}: {parsed}"


def test_home_exemption_never_fires_for_non_home_path() -> None:
    """A path NOT under home must never be allowed via the home-exemption branch.
    Pin via the reason string so the exemption can't silently widen."""
    rc, parsed = _run("Z:/foreign/not_under_home.py")
    reason = json.dumps(parsed)
    assert "User-home path" not in reason, parsed
