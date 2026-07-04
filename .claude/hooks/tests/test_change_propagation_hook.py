"""Tests for source-aware structural-change detection (no mocks).

Two layers, per the test-strategy contract:
  - UNIT: structural_change pure functions (mention-vs-operation, symbol removal).
  - REGRESSION/INTEGRATION: ChangePropagationHook.process() over realistic
    tool payloads. The historical false positive lived at the tool-input
    boundary (a Write whose *body* contained "rm old.py" was flagged as deleting
    old.py); a pure-logic unit test would miss that the hook fed it file content.
    The integration layer proves the real payload no longer creates a pending.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

_HOOKS = Path(__file__).resolve().parent.parent  # .claude/hooks
for _p in (str(_HOOKS), str(_HOOKS / "__lib")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import structural_change as sc  # noqa: E402


# ── UNIT: structural_change ──────────────────────────────────────────────────

@pytest.mark.parametrize("cmd,expected", [
    ("rm old.py", ["old.py"]),
    ("rm -rf build/", ["build/"]),
    ("cd a && rm -f x.py", ["x.py"]),
    ("git rm mod.py", ["mod.py"]),
])
def test_real_deletions_detected(cmd, expected):
    assert sc.deletions_in_command(cmd) == expected


@pytest.mark.parametrize("cmd", [
    'grep "rm old.py" log.txt',          # mention in a search
    'echo "to clean, run rm x.py"',       # mention in echo
    "python -c \"s = 'rm old.py'\"",      # mention as a string literal
    "cat a | grep rm",                     # the word rm, not a deletion
    "ls | xargs rm",                       # real deletion but no nameable target
])
def test_mentions_and_unnamed_return_empty(cmd):
    assert sc.deletions_in_command(cmd) == []


def test_removed_symbols():
    assert sc.removed_symbols("def foo():\n  pass\ndef bar(): pass", "def bar(): pass") == [("def", "foo")]
    assert sc.removed_symbols("def a(): pass", "def a(): pass\ndef b(): pass") == []


def test_lines_removed():
    assert sc.lines_removed("a\nb\nc\nd", "a") == 3
    assert sc.lines_removed("a", "a\nb\nc") == 0


# ── REGRESSION/INTEGRATION: the hook over real payloads ──────────────────────

@pytest.fixture
def hook(tmp_path, monkeypatch):
    # State now lives under the canonical contract at
    # {PROJECT_ROOT}/.claude/state/sessions/{session_id}/. Redirect the contract
    # root to tmp via PROJECT_ROOT and reload the module the hook actually imports
    # (__lib.state_paths) so STATE_DIR is recomputed under tmp.
    monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))
    import __lib.state_paths as sp
    importlib.reload(sp)
    sp.clear_path_cache()
    sys.modules.pop("posttooluse.change_propagation_hook", None)
    mod = importlib.import_module("posttooluse.change_propagation_hook")
    mod = importlib.reload(mod)
    return mod.ChangePropagationHook(), mod


def _pending(mod, session_id: str = "unknown"):
    """Read pending verifications for a session (default 'unknown' = direct
    process() calls that bypass run())."""
    h = mod.ChangePropagationHook()
    h._session_id = session_id
    return h._load_state().get("pending_verifications", [])


def test_write_with_deletion_string_in_body_creates_no_pending(hook):
    """REGRESSION: the exact failure — deletion-shaped string in a file body."""
    h, mod = hook
    h.process("Write", {"file_path": "t.py", "content": "cmd = 'rm old.py'  # fixture\n"}, {})
    assert _pending(mod) == []


def test_bash_grep_mention_creates_no_pending(hook):
    h, mod = hook
    h.process("Bash", {"command": 'grep "rm old.py" log.txt'}, {})
    assert _pending(mod) == []


def test_bash_real_rm_creates_pending(hook):
    """True positive preserved: a real rm still records a verification."""
    h, mod = hook
    h.process("Bash", {"command": "rm real_module.py"}, {})
    p = _pending(mod)
    assert len(p) == 1
    assert p[0]["type"] == "file_deletion" and p[0]["affected"] == "real_module.py"


def test_edit_removing_def_creates_pending(hook):
    h, mod = hook
    h.process("Edit", {"file_path": "m.py", "old_string": "def foo():\n    return 1\n", "new_string": "\n"}, {})
    p = _pending(mod)
    assert len(p) == 1
    assert p[0]["type"] == "function_removal" and p[0]["affected"] == "foo"


def test_edit_adding_code_creates_no_pending(hook):
    h, mod = hook
    h.process("Edit", {"file_path": "m.py", "old_string": "x = 1", "new_string": "x = 1\ndef bar(): pass"}, {})
    assert _pending(mod) == []


# ── ISOLATION / STALENESS REGRESSION ─────────────────────────────────────────
# These pin the fix for the bug that bit twice: state was written to ONE shared
# file (CSF_STATE_DIR), so concurrent terminals clobbered each other and a prior
# session's records bled in as "stale false positives". State is now scoped to
# .claude/state/sessions/{session_id}/, driven by run() resolving the session id.

def test_two_sessions_are_isolated(hook):
    """A deletion recorded in session A must not appear in session B."""
    h, mod = hook
    h.run({"tool_name": "Bash", "tool_input": {"command": "rm a_only.py"},
           "session_id": "sessionA"})
    assert _pending(mod, "sessionA") and _pending(mod, "sessionA")[0]["affected"] == "a_only.py"
    # A different concurrent session sees nothing from session A.
    assert _pending(mod, "sessionB") == []


def test_state_path_is_session_scoped_not_shared_root(hook):
    """The state file lives under sessions/{id}/, never at the shared state root."""
    h, mod = hook
    h._session_id = "sessionX"
    p = h._state_path()
    assert p.parent.name == "sessionX"
    assert p.parent.parent.name == "sessions"
    assert p.name == "propagation_state.json"


# ── AUTO-SATISFY TYPE-GATE REGRESSION ─────────────────────────────────────────
# Pins the fix for the over-broad auto-satisfy that dropped execution_test for
# change types whose `affected` is NOT a filesystem path. `function_removal`
# carries a symbol name; `large_deletion` carries "N lines". Neither resolves
# to a real path, so a type-agnostic `not Path(affected).exists()` cleared the
# WHOLE requirement set on the very next Bash — silently losing execution_test,
# the most important verification for those change types.

def test_function_removal_keeps_execution_test_after_unrelated_bash(hook):
    """REGRESSION: symbol-name `affected` must not auto-satisfy execution_test."""
    h, mod = hook
    h.process("Edit", {"file_path": "m.py",
                       "old_string": "def foo():\n    return 1\n",
                       "new_string": "\n"}, {})
    h.process("Bash", {"command": "ls"}, {})  # unrelated; no python/pytest
    p = _pending(mod)
    assert len(p) == 1 and p[0]["type"] == "function_removal"
    assert "execution_test" in p[0]["remaining"], (
        "execution_test was wrongly cleared — symbol name is not a path"
    )


def test_large_deletion_keeps_execution_test_after_unrelated_bash(hook):
    """REGRESSION: 'N lines' `affected` must not auto-satisfy execution_test."""
    h, mod = hook
    old = "\n".join(f"line{i}" for i in range(15)) + "\n"
    h.process("Edit", {"file_path": "big.py", "old_string": old, "new_string": ""}, {})
    h.process("Bash", {"command": "ls"}, {})
    p = _pending(mod)
    assert len(p) == 1 and p[0]["type"] == "large_deletion"
    assert "execution_test" in p[0]["remaining"], (
        "execution_test was wrongly cleared — 'N lines' is not a path"
    )


def test_file_deletion_still_auto_satisfies_when_path_gone(hook, tmp_path):
    """The #1059 fix must still work: deleted-file path gone → grep_references cleared."""
    h, mod = hook
    victim = tmp_path / "victim.py"
    victim.write_text("x = 1\n")
    h.process("Bash", {"command": f"rm {victim}"}, {})
    assert _pending(mod) and _pending(mod)[0]["type"] == "file_deletion"
    victim.unlink()  # ensure it's gone
    h.process("Bash", {"command": "ls"}, {})  # unrelated Bash
    # file gone → auto-satisfy cleared all reqs → pending removed
    assert _pending(mod) == [], "file_deletion should auto-satisfy when path is gone"
