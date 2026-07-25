#!/usr/bin/env python3
"""Check all repos this workspace touches for uncommitted or unpushed state.

Runs after "commit and push" to catch the two failure modes:
1. Edits in ~/.grok (skills) not committed because the workflow only
   checked P:\\.
2. Submodule parent pointers not advanced after committing inside
   submodules.

Reports each repo with uncommitted files and/or commits ahead of origin.
Exit 0 if clean, exit 1 if any repo needs attention.

Stable location: P:/.agents/scripts/git_state_check.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Repos this workspace touches (add new ones here as they appear)
REPOS = [
    Path("P:/"),
    Path.home() / ".grok",
]

# Submodules under P:\ that have their own remotes
SUBMODULE_PREFIX = "P:/packages/.claude-marketplace/plugins/"
SUBMODULE_CANDIDATES = [
    SUBMODULE_PREFIX + "cc-skills-sdlc",
    SUBMODULE_PREFIX + "cc-skills-ai-api",
    SUBMODULE_PREFIX + "cc-skills-utils",
]


def _git(args: list[str], cwd: Path) -> tuple[int, str, str]:
    r = subprocess.run(
        ["git"] + args,
        capture_output=True, text=True, cwd=str(cwd),
    )
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _has_remote(cwd: Path) -> bool:
    code, out, _ = _git(["remote"], cwd)
    return bool(out.strip())


def _uncommitted(cwd: Path) -> list[str]:
    code, out, _ = _git(["status", "--short"], cwd)
    return [l for l in out.split("\n") if l.strip()] if out else []


def _ahead_of_origin(cwd: Path) -> list[str]:
    code, out, _ = _git(["log", "--oneline", "origin/main..HEAD"], cwd)
    return [l for l in out.split("\n") if l.strip()] if out else []


def _stale_submodule_pointers(parent: Path) -> list[str]:
    """Submodules where parent's gitlink != submodule HEAD."""
    results = []
    code, out, _ = _git(["submodule", "status"], parent)
    if not out:
        return results
    for line in out.split("\n"):
        if not line.strip():
            continue
        # Format: <status-char><commit-hash> <path> (<description>)
        status_char = line[0]
        parts = line[1:].strip().split()
        if len(parts) < 2:
            continue
        sha = parts[0]
        path = parts[1]
        # status_char: space = up to date, + = different, - = not initialized
        if status_char in ("+", "-"):
            results.append(f"{path} (parent gitlink: {sha[:8]})")
    return results


def main() -> int:
    problems = []

    for repo in REPOS:
        if not (repo / ".git").exists():
            continue
        uncommitted = _uncommitted(repo)
        ahead = _ahead_of_origin(repo) if _has_remote(repo) else []

        if uncommitted or ahead:
            problems.append((repo, uncommitted, ahead))

    # Check submodule pointers
    stale_pointers = _stale_submodule_pointers(Path("P:/"))
    if stale_pointers:
        problems.append((Path("P:/ (submodule pointers)"), stale_pointers, []))

    if not problems:
        print("All repos: clean and pushed.")
        return 0

    print("REPOS NEEDING ATTENTION:")
    print("=" * 60)
    for repo, uncommitted, ahead in problems:
        print(f"\n{repo}")
        if uncommitted:
            print(f"  Uncommitted ({len(uncommitted)} files):")
            for f in uncommitted[:5]:
                print(f"    {f}")
            if len(uncommitted) > 5:
                print(f"    ... and {len(uncommitted) - 5} more")
        if ahead:
            print(f"  Ahead of origin ({len(ahead)} commits):")
            for c in ahead[:5]:
                print(f"    {c}")
            if len(ahead) > 5:
                print(f"    ... and {len(ahead) - 5} more")
    print(f"\n{len(problems)} repo(s) need attention.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
