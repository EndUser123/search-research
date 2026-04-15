#!/usr/bin/env python3
"""
PreToolUse Hook: Git Remote Check Order Guard

Blocks remote-ref inspection commands until the current repository has first
checked local HEAD or the current branch in the same session.

This prevents a repeat of the failure mode where `origin/main` was inspected
before confirming the checked-out branch locally.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from __lib.hook_base import hook_main

_STATE_FILE = "git_remote_check_order_state.json"
_LOCAL_CHECK_PATTERNS = (
    re.compile(r"\bgit\s+branch\s+--show-current\b", re.IGNORECASE),
    re.compile(r"\bgit\s+rev-parse\s+--abbrev-ref\s+HEAD\b", re.IGNORECASE),
    re.compile(r"\bgit\s+rev-parse\s+HEAD\b", re.IGNORECASE),
    re.compile(r"\bgit\s+symbolic-ref\s+--short\s+HEAD\b", re.IGNORECASE),
)
_REMOTE_MARKER_PATTERNS = (
    re.compile(r"\borigin/", re.IGNORECASE),
    re.compile(r"@\{u\}", re.IGNORECASE),
    re.compile(r"\b--remotes\b", re.IGNORECASE),
    re.compile(r"\s-r\b", re.IGNORECASE),
)
_REMOTE_INSPECTION_SUBCOMMANDS = {
    "branch",
    "describe",
    "diff",
    "log",
    "merge-base",
    "reflog",
    "rev-list",
    "rev-parse",
    "show",
}
_STATE_INVALIDATING_SUBCOMMANDS = {
    "checkout",
    "commit",
    "merge",
    "pull",
    "rebase",
    "reset",
    "switch",
}


def _env_value(name: str, fallback: str) -> str:
    value = os.environ.get(name, "").strip()
    return value or fallback


def _session_id() -> str:
    return _env_value("CLAUDE_SESSION_ID", "default")


def _terminal_id() -> str:
    return _env_value("CLAUDE_TERMINAL_ID", "terminal")


def _state_dir() -> Path:
    state_dir = Path(os.environ.get("CSF_STATE_DIR", "P:/.claude/state"))
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def _session_state_path() -> Path:
    digest = hashlib.sha1(f"{_terminal_id()}:{_session_id()}".encode("utf-8")).hexdigest()[:12]
    return _state_dir() / f"{_STATE_FILE}.{digest}"


def _load_state() -> dict:
    path = _session_state_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(state: dict) -> None:
    path = _session_state_path()
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def _repo_root(cwd: str) -> str | None:
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=creationflags,
        )
    except Exception:
        return None

    if result.returncode != 0:
        return None
    repo_root = result.stdout.strip()
    return repo_root or None


def _repo_key(repo_root: str) -> str:
    normalized = repo_root.replace("\\", "/").lower()
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:12]


def _git_subcommand(command: str) -> str:
    parts = command.strip().split()
    if len(parts) < 2:
        return ""
    if parts[0].lower() != "git":
        return ""
    return parts[1].lower()


def _first_pattern_index(command: str, patterns: tuple[re.Pattern[str], ...]) -> int:
    indices = [match.start() for pattern in patterns if (match := pattern.search(command))]
    return min(indices) if indices else -1


def _is_local_head_check(command: str) -> bool:
    return _first_pattern_index(command, _LOCAL_CHECK_PATTERNS) != -1


def _is_state_invalidating(command: str) -> bool:
    subcommand = _git_subcommand(command)
    return subcommand in _STATE_INVALIDATING_SUBCOMMANDS


def _is_remote_inspection(command: str) -> bool:
    if not command.strip().lower().startswith("git "):
        return False

    subcommand = _git_subcommand(command)
    if subcommand not in _REMOTE_INSPECTION_SUBCOMMANDS:
        return False

    return _first_pattern_index(command, _REMOTE_MARKER_PATTERNS) != -1


def _mark_repo_verified(state: dict, repo_root: str, command: str) -> None:
    repos = state.setdefault("repos", {})
    repos[_repo_key(repo_root)] = {
        "repo_root": repo_root,
        "verified": True,
        "last_command": command,
    }


def _clear_repo_verification(state: dict, repo_root: str) -> None:
    repos = state.get("repos", {})
    repos.pop(_repo_key(repo_root), None)


def _repo_is_verified(state: dict, repo_root: str) -> bool:
    repos = state.get("repos", {})
    repo_state = repos.get(_repo_key(repo_root), {})
    return bool(repo_state.get("verified"))


def _block_reason(repo_root: str, command: str) -> str:
    return (
        "Git remote-first check blocked.\n\n"
        f"Repo: {repo_root}\n"
        f"Command: {command}\n\n"
        "Check local HEAD or the current branch first, then inspect the remote.\n"
        "Run one of these before touching `origin/*`:\n"
        "  git branch --show-current\n"
        "  git rev-parse HEAD\n"
        "  git rev-parse --abbrev-ref HEAD"
    )


def run(data: dict) -> dict | None:
    """Block remote-ref inspection before local branch verification."""
    if data.get("tool_name") != "Bash":
        return None

    tool_input = data.get("tool_input", {}) or {}
    command = str(tool_input.get("command", "")).strip()
    if not command:
        return None

    if not command.lower().startswith("git "):
        return None

    cwd = tool_input.get("cwd", "") or os.getcwd()
    repo_root = _repo_root(cwd)
    if not repo_root:
        return None

    state = _load_state()

    # Commands that explicitly verify the checked-out branch/HEAD.
    if _is_local_head_check(command):
        _mark_repo_verified(state, repo_root, command)
        _save_state(state)
        return None

    # If a command changes HEAD/branch state, clear the previous verification.
    if _is_state_invalidating(command):
        _clear_repo_verification(state, repo_root)
        _save_state(state)
        return None

    remote_index = _first_pattern_index(command, _REMOTE_MARKER_PATTERNS)
    local_index = _first_pattern_index(command, _LOCAL_CHECK_PATTERNS)

    # Allow a same-command sequence like:
    #   git branch --show-current && git show origin/main
    if remote_index != -1 and local_index != -1 and local_index < remote_index:
        _mark_repo_verified(state, repo_root, command)
        _save_state(state)
        return None

    if _is_remote_inspection(command) and not _repo_is_verified(state, repo_root):
        return {
            "decision": "block",
            "reason": _block_reason(repo_root, command),
            "blocking_hook": "PreToolUse_git_remote_check_order_guard.py",
        }

    return None


@hook_main
def main() -> None:
    data = json.load(sys.stdin)
    result = run(data)
    if result:
        print(json.dumps(result))
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
