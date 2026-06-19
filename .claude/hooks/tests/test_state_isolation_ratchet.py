"""Ratchet test: prevent recurrence of the un-scoped shared-state bug class.

WHY THIS EXISTS
  `change_propagation_hook` wrote its state to `CSF_STATE_DIR/propagation_state.json`
  — a single file shared by every terminal. That broke multi-terminal isolation
  (terminals clobbered each other) and let a prior session's records survive as
  "stale false positives". The canonical fix is the state contract in
  __lib/state_paths.py (session/terminal/shared-scoped paths).

  Reading CSF_STATE_DIR as a literal state directory is the exact anti-pattern
  that caused the bug. This test FREEZES the set of files that still do it and
  fails the build if a NEW file joins them. The allowlist is technical debt: it
  should only ever SHRINK. When it reaches empty, delete this test (or repoint it
  at a different anti-pattern).

  Scope is deliberately narrow and precise — it matches actual env ACCESS
  (os.environ[...] / os.environ.get(...)), never a docstring/comment mention, so
  it cannot false-positive on the very kind of string-literal mention that the
  change_propagation fix was about. It does not attempt to detect every possible
  un-scoped-state bug; it nails the specific vector that recurred.

  Migration backlog tracked at: state-contract adoption (see project tasks).
"""
from __future__ import annotations

import re
from pathlib import Path

_HOOKS = Path(__file__).resolve().parent.parent  # .claude/hooks

# Files that still read CSF_STATE_DIR as a state directory. KNOWN DEBT — shrink
# only. Paths are relative to .claude/hooks/, POSIX separators.
_ALLOWLIST: frozenset[str] = frozenset({
    "PreToolUse_git_remote_check_order_guard.py",
    "SessionStart_memory_cks_auto.py",
    "Stop_meta_conversation_loop.py",
    "Stop_recommendation_gate.py",
    "UserPromptSubmit_modules/recommendation_loop.py",
    "__lib/enforcement_rate_limiter.py",
    "_cks_cache.py",
    "csftracker.py",
    "shared_utils.py",
})

# Matches real access of the env var, not a bare mention in a comment/docstring.
_ENV_ACCESS = re.compile(r"""environ(?:\.get\(|\[)\s*['"]CSF_STATE_DIR""")


def _current_users() -> set[str]:
    users: set[str] = set()
    for path in _HOOKS.rglob("*.py"):
        parts = set(path.parts)
        if "__pycache__" in parts or "tests" in parts or ".archive" in parts:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if _ENV_ACCESS.search(text):
            users.add(path.relative_to(_HOOKS).as_posix())
    return users


def test_no_new_csf_state_dir_users():
    """No file outside the frozen allowlist may read CSF_STATE_DIR as a state dir."""
    new_users = _current_users() - _ALLOWLIST
    assert not new_users, (
        "New hook(s) read CSF_STATE_DIR as a state directory instead of using "
        "the state contract (__lib/state_paths.py: get_session_state_path / "
        f"get_terminal_state_path / get_shared_state_path): {sorted(new_users)}"
    )


def test_allowlist_has_no_stale_entries():
    """Keep the backlog honest: every allowlisted file must still exist and still
    use the anti-pattern. When an entry is migrated, remove it from _ALLOWLIST."""
    stale = _ALLOWLIST - _current_users()
    assert not stale, (
        f"Allowlist entries no longer read CSF_STATE_DIR (migrated?). "
        f"Remove them from _ALLOWLIST: {sorted(stale)}"
    )
