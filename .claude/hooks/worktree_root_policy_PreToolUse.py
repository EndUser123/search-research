#!/usr/bin/env python3
"""PreToolUse guard: enforce that `git worktree add` lands under P:/.worktrees/.

Generic worktree-root policy hook. Lives in P:/.claude/hooks/ (not in any
plugin, not project-local) so it survives the upstream bugs that bound the
project-level and plugin-level surfaces:

  - #79111 (subdirectory launches fail-open for project-root settings.json)
  - #16288 / #78936 (plugin hooks.json unreliable without `version` field)

Wired in ~/.claude/settings.json hooks.PreToolUse matcher Bash.

Behavior:
  - Bash command contains `git worktree add` (case-insensitive) AND the target
    path is NOT under the configured allowed root (default P:/.worktrees/)
    -> deny with redirect hint to the managed CLI.
  - Bash command contains any other `git worktree` subcommand (list, remove,
    prune, move, lock, unlock) -> allow (this hook only gates `add`).
  - Non-worktree commands -> allow.
  - GO_WORKTREE_SAFETY_BYPASS=1 env var -> allow with stderr advisory.

Fail-safe: malformed payload or unparseable input => allow (return 0). We
never want a hook parse error to silently block legitimate work.

Known upstream gaps that bound the threat model (see wiki page
worktree-root-policy-hook-design-2026-07):
  - #78970 (PreToolUse Bash hook is NOT invoked for subagent tool calls).
    This hook only enforces on the main thread.

Replaces the yt-is-specific package-local hook
P:/packages/yt-is/.claude/hooks/worktree_policy_PreToolUse.py, which was
defeated by #79111 (worktree ops happen in subdirectories, exactly when
project-level settings.json fail-open).
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path, PureWindowsPath

# Default allowed root. Override via env var for per-machine customization
# without code edits (settings.json wiring stays identical).
_DEFAULT_ALLOWED_ROOT = Path("P:/.worktrees")
ALLOWED_ROOT = Path(os.environ.get("WORKTREE_ALLOWED_ROOT", str(_DEFAULT_ALLOWED_ROOT)))

# `git worktree add` — allow flags/args between `git` and `worktree`
# (e.g. `git -C P:/foo worktree add ...`, `git -b feat worktree add ...`).
# Case-insensitive, word-boundary anchored.
_GIT_WT_ADD_PATTERN = re.compile(r"\bgit\b(?:\s+\S+)*\s+worktree\s+add\b", re.IGNORECASE)


def _is_under_allowed_root(path_str: str) -> bool:
    """True if path_str resolves to a location under ALLOWED_ROOT."""
    if not path_str:
        return False
    try:
        # Pure paths (no resolve): worktree-add targets may not exist yet.
        # is_relative_to handles drive + parent containment lexically.
        candidate = PureWindowsPath(path_str)
        allowed = PureWindowsPath(str(ALLOWED_ROOT))
        return candidate == allowed or candidate.is_relative_to(allowed)
    except (ValueError, TypeError, OSError):
        return False


def _extract_target_path(command: str) -> str | None:
    """Pull the path arg out of `git worktree add ... <path>`. Best-effort.

    Returns the first plausible non-flag token after `git worktree add`.
    Returns None if no candidate path is found (caller denies).
    """
    m = _GIT_WT_ADD_PATTERN.search(command)
    if not m:
        return None
    tail = command[m.end():]

    tokens = re.findall(r"""(?:[^\s'"]+|'[^']*'|"[^"]*")+""", tail)

    # Flags that take a separate argument (the arg is therefore NOT the path).
    _TAKES_ARG = {"-b", "-B", "--branch"}

    skip_next = False
    for tok in tokens:
        if (tok.startswith("'") and tok.endswith("'")) or (
            tok.startswith('"') and tok.endswith('"')
        ):
            tok = tok[1:-1]
        if skip_next:
            skip_next = False
            continue
        if tok in _TAKES_ARG:
            skip_next = True
            continue
        if tok.startswith("-"):
            # Bool flags (-f, --force, --detach, ...): skip the flag only.
            continue
        if tok in {"add", "list", "remove", "prune", "move", "lock", "unlock"}:
            continue
        # First non-flag, non-arg, non-subcommand token is the path.
        return tok
    return None


def _deny(reason: str) -> None:
    # hookSpecificOutput wrapper required — bare top-level permissionDecision
    # is ignored by the harness (confirmed vs PreToolUse_existence_gate /
    # PreToolUse_search_before_create, 2026-07-19).
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        return 0

    tool_name = payload.get("tool_name", "")
    if tool_name != "Bash":
        return 0

    tool_input = payload.get("tool_input", {})
    command = tool_input.get("command", "")
    if not command:
        return 0

    if not _GIT_WT_ADD_PATTERN.search(command):
        return 0

    if os.environ.get("GO_WORKTREE_SAFETY_BYPASS", "").strip() == "1":
        print(
            "WORKTREE_ROOT_POLICY: bypassing git worktree-add guard "
            "(GO_WORKTREE_SAFETY_BYPASS=1). Worktrees created outside "
            f"{ALLOWED_ROOT} will not be tracked by /go cleanup.",
            file=sys.stderr,
        )
        return 0

    target = _extract_target_path(command)
    if target is None:
        _deny(
            "WORKTREE_ROOT_POLICY: could not parse a path argument from "
            "`git worktree add`. Either pass an explicit path under "
            f"{ALLOWED_ROOT}, or set GO_WORKTREE_SAFETY_BYPASS=1 to override."
        )
        return 0

    if _is_under_allowed_root(target):
        return 0

    _deny(
        f"WORKTREE_ROOT_POLICY: git worktree add target `{target}` is not "
        f"under the allowed root `{ALLOWED_ROOT}`. Use the managed path "
        f"({ALLOWED_ROOT}/<branch>) so /go can find and clean it up. To "
        "acknowledge a one-off bypass, set GO_WORKTREE_SAFETY_BYPASS=1 for "
        "the duration of this command."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
