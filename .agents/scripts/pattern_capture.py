#!/usr/bin/env python3
"""Auto-capture improvement patterns from git commit messages.

Runs at session end. Scans this session's fix: commits, extracts the
abstract pattern, and appends to the findings index. This ensures every
fix produces a durable pattern entry without requiring the agent to
remember to capture it.

Usage (from close-py git-state phase or manually):
    python pattern_capture.py --session-id <UUID> --repo P:/ --repo ~/.grok
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path("P:/.agents/scripts")))
from findings_index import append  # noqa: E402

# Patterns that extract the abstract category from commit messages
_FIX_PATTERNS = {
    r"\bfix\b": "bug-fix",
    r"\bfield.?mismatch\b|\bschema.?drift\b": "FC-01-field-mismatch",
    r"\bsystem.?context\b|\b<rules>\b|\bcontamination\b": "FC-02-system-context",
    r"\bexecution.?receipt\b|\bnot.?verified\b|\binspection.?only\b": "FC-03-missing-receipt",
    r"\bpoll.?timeout\b|\btimeout.?config\b": "FC-04-timeout-config",
    r"\bstale.?ref\b|\bold.?path\b|\bconsolidat\b": "FC-05-stale-references",
    r"\bspecificat.?gaming\b|\bhand.?auth\b|\bfabricat\b": "FC-06-spec-gaming",
    r"\bdirty.?tree\b|\bscope.?contaminat\b|\bsibling.?session\b": "FC-07-dirty-tree",
    r"\bshell.?quot\b|\bclass.?c\b|\bpython.?-c\b": "FC-08-shell-quoting",
    r"\bpropagat\b|\bcross.?ref\b|\bstale.?slug\b": "FC-09-missing-propagation",
    r"\bnarrative.?clos\b|\bunverifi.?claim\b": "FC-10-narrative-closure",
}


def _get_session_commits(repo: str, session_id: str) -> list[str]:
    """Get commit messages from this session."""
    try:
        result = subprocess.run(
            ["git", "-C", repo, "log", "--oneline", "--since=12 hours ago", "--grep=fix:", "-i"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return []
        return [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def _classify_pattern(message: str) -> str:
    """Classify a commit message into a known failure-class pattern."""
    msg_lower = message.lower()
    for pattern, category in _FIX_PATTERNS.items():
        if re.search(pattern, msg_lower):
            return category
    return "general-fix"


def capture_patterns(session_id: str, repos: list[str]) -> list[dict]:
    """Capture patterns from fix: commits and append to findings index."""
    captured = []
    for repo in repos:
        commits = _get_session_commits(repo, session_id)
        for commit_line in commits:
            # Extract commit message (after the hash)
            parts = commit_line.split(" ", 1)
            if len(parts) < 2:
                continue
            message = parts[1]
            pattern_id = _classify_pattern(message)

            entry = append(
                source="commit",
                category="fix-pattern",
                severity="info",
                title=message[:200],
                session_id=session_id,
                detail=f"Auto-captured from {repo}: {commit_line}",
                path=repo,
                pattern_id=pattern_id,
                action_taken="fixed",
            )
            captured.append(entry)

    return captured


def main() -> None:
    parser = argparse.ArgumentParser(description="Auto-capture improvement patterns from commits")
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--repo", action="append", required=True)
    args = parser.parse_args()

    captured = capture_patterns(args.session_id, args.repo)
    print(json.dumps({"captured": len(captured), "entries": captured}, indent=2))


if __name__ == "__main__":
    main()
