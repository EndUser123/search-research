#!/usr/bin/env python3
"""
Stop_positive_existence_guard.py - File/Ref Positive Existence Claim Guard
==========================================================================

Blocks responses asserting that a file/path exists at some location (repo,
remote, commit, branch, backup) when the claim rests only on *indirect*
evidence — typically a ``git log --stat`` / ``git diff --stat`` /
``git show --stat`` line mentioning the file in a past commit.

WHY THIS EXISTS
---------------
A stat summary describes what changed in a commit. It does NOT describe what
currently exists at a ref or on disk. The model saw a line like::

    PreToolUse_import_deletion_guard.py | 90 +

in ``git log --stat`` and asserted the file is present in the remote/backup.
A later ``git show <ref>:<path>`` proved the file does not exist. The root
cause: positive existence claim from indirect (stat) evidence.

FAILURE MODE CAUGHT
-------------------
    "The backup remote has PreToolUse_import_deletion_guard.py"
    "File X exists at origin/main"
    "Commit abc123 includes <path>"

-> Stat-only mention in tool history. No ``git show <ref>:<path>``,
   no Read, no Glob hit, no ``ls`` / ``cat`` / ``git ls-tree`` /
   ``git cat-file`` for that exact path THIS TURN.
-> Guard blocks and demands direct inspection.

WHAT COUNTS AS DIRECT INSPECTION
--------------------------------
- Read tool on the claimed path
- Glob pattern that matches the claimed path (result implies existence)
- Bash: ``ls``, ``cat``, ``head``, ``tail`` on the path
- Bash: ``git show <ref>:<path>``, ``git cat-file -e <ref>:<path>``,
  ``git ls-tree <ref> -- <path>``, ``git ls-files <path>``

WHAT DOES NOT COUNT (STAT INFERENCE)
------------------------------------
- ``git log --stat`` / ``git log --numstat``
- ``git diff --stat`` / ``git diff --numstat``
- ``git show --stat`` (without ``<ref>:<path>``)
- ``git show --name-only`` / ``--name-status``

These describe historical diff metadata, not current tree state.

TURN SCOPING
------------
Uses the shared turn-scoped evidence helper like the negative guard.

LIFECYCLE: Stop (blocking gate — exits with code 2 to block)
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
LOG_DIR = HOOKS_DIR / "state" / "logs"
sys.path.insert(0, str(HOOKS_DIR))

LOG_DIR.mkdir(parents=True, exist_ok=True)

_logger = logging.getLogger("positive_existence_guard")
try:
    _handler = logging.FileHandler(
        LOG_DIR / "positive_existence_guard.log", encoding="utf-8"
    )
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    _logger.addHandler(_handler)
except (OSError, PermissionError):
    pass
_logger.setLevel(logging.DEBUG)

try:
    from turn_scoped_evidence import load_turn_scoped_events
    EVIDENCE_AVAILABLE = True
except ImportError as exc:
    EVIDENCE_AVAILABLE = False
    _logger.warning("turn_scoped_evidence import failed: %s", exc)

    def load_turn_scoped_events(  # type: ignore[no-redef]
        *, session_id: str, terminal_id: str, limit: int
    ) -> list[dict] | None:
        del session_id, terminal_id, limit
        return None


# --- Patterns ---------------------------------------------------------------

# Path-bearing token: at least one slash or backslash, dot-extension allowed.
# Examples matched: PreToolUse_import_deletion_guard.py, .claude/hooks/X.py,
# packages/foo/bar.py, path\to\file.py
_PATH_TOKEN = r"([\w./\\-]*[\\/][\w./\\-]*\.[A-Za-z0-9]+|\b[\w.-]+\.[A-Za-z0-9]{1,6}\b)"

# Positive existence assertions that bind a path to a location/ref/backup.
# Deliberately narrow: we only block when the response names a specific target
# (remote, backup, commit, branch, origin, ref).
POSITIVE_EXISTENCE_PATTERNS = re.compile(
    r"(?:\b(?:remote|origin|backup|branch|commit|ref|main|master)\b"
    r"[\s\w/]{0,60}?(?:has|have|contains?|includes?|ships?|carries)\s+" + _PATH_TOKEN + r")"
    r"|(?:" + _PATH_TOKEN + r"\s+(?:exists?|is\s+present|is\s+there)\s+"
    r"(?:in|at|on|under)\s+(?:the\s+)?(?:remote|origin|backup|branch|commit|ref|main|master))"
    r"|(?:(?:commit|ref)\s+\w+\s+(?:includes?|adds?|contains?)\s+" + _PATH_TOKEN + r")"
    r"|(?:(?:the\s+)?(?:backup|remote|origin)\s+(?:repo\s+)?(?:has|contains?|includes?)\s+"
    + _PATH_TOKEN + r")",
    re.IGNORECASE,
)

# Heuristic: stat-like phrasing already visible in the response (helpful for messaging)
STAT_MENTION_PATTERNS = re.compile(
    r"\b(?:git\s+log|git\s+diff|git\s+show)\s+[^\n]*--(?:stat|numstat|name-only|name-status)\b"
    r"|\|\s*\d+\s*[+-]\s*$"  # "| 90 +" in a stat line
    r"|\b\d+\s+files?\s+changed\b",
    re.IGNORECASE | re.MULTILINE,
)


# Bash commands that DO count as direct inspection of a path at a ref/tree.
_DIRECT_INSPECTION_BASH = re.compile(
    r"\bgit\s+show\s+\S+:\S+"            # git show ref:path
    r"|\bgit\s+cat-file\b"               # git cat-file -e/-p ref:path
    r"|\bgit\s+ls-tree\b"                # git ls-tree ref -- path
    r"|\bgit\s+ls-files\b"               # git ls-files -- path
    r"|\bls\b"
    r"|\bcat\b"
    r"|\bhead\b"
    r"|\btail\b"
    r"|\bfind\b"
    r"|\bdir\b"
    r"|\bGet-ChildItem\b"
    r"|\btest\s+-f\b",
    re.IGNORECASE,
)

# Bash commands that are STAT-ONLY and MUST NOT count as inspection.
_STAT_ONLY_BASH = re.compile(
    r"\bgit\s+log\b[^\n|]*--(?:stat|numstat|name-only|name-status)\b"
    r"|\bgit\s+diff\b[^\n|]*--(?:stat|numstat|name-only|name-status)\b"
    r"|\bgit\s+show\b[^\n|]*--(?:stat|numstat|name-only|name-status)\b",
    re.IGNORECASE,
)


# --- Evidence loading -------------------------------------------------------


def _load_turn_events(session_id: str, terminal_id: str) -> list[dict] | None:
    if not EVIDENCE_AVAILABLE:
        return None
    if not session_id:
        return None
    return load_turn_scoped_events(
        session_id=session_id, terminal_id=terminal_id, limit=200
    )


def _extract_claim_paths(response: str) -> list[tuple[str, str]]:
    """Return list of (matched_text, path) for positive existence claims."""
    if not response:
        return []
    claims: list[tuple[str, str]] = []
    # Strip quoted strings — quoted material is data, not a claim.
    scrubbed = re.sub(r"'[^']*'|\"[^\"]*\"", "", response)
    for m in POSITIVE_EXISTENCE_PATTERNS.finditer(scrubbed):
        path = next((g for g in m.groups() if g), None)
        if path:
            claims.append((m.group(0), path))
    # Deduplicate on path
    seen: dict[str, tuple[str, str]] = {}
    for text, path in claims:
        seen.setdefault(path.lower(), (text, path))
    return list(seen.values())


def _path_inspected_directly(path: str, events: list[dict]) -> bool:
    """True if the specific path was inspected via a non-stat tool this turn."""
    path_lower = path.lower().replace("\\", "/")
    basename = path_lower.rsplit("/", 1)[-1]

    for event in events:
        tool = (event.get("name") or event.get("tool_name") or "").lower()

        if tool == "read":
            fp = (
                event.get("file_path")
                or (event.get("tool_input", {}) or {}).get("file_path", "")
                or ""
            ).lower().replace("\\", "/")
            if fp and (path_lower in fp or fp.endswith(basename)):
                return True

        if tool == "glob":
            pattern = (event.get("pattern") or event.get("command", "") or "").lower()
            if basename in pattern or path_lower in pattern:
                # Glob only counts if results were non-empty.
                output = (event.get("output_excerpt") or event.get("output") or "").strip()
                if output and output.lower() not in {"no files found", "[]", "none"}:
                    return True

        if tool == "bash":
            command = event.get("command", "") or ""
            # Must mention the path (or basename) AND use a direct-inspection verb
            # AND not be a stat-only invocation.
            cmd_lower = command.lower().replace("\\", "/")
            if basename not in cmd_lower and path_lower not in cmd_lower:
                continue
            if _STAT_ONLY_BASH.search(command):
                continue
            if _DIRECT_INSPECTION_BASH.search(command):
                # Require the tool output was non-empty / non-error, when available.
                output = (event.get("output_excerpt") or event.get("output") or "")
                if output and re.search(
                    r"fatal:|does not exist|no such|exit code [1-9]", output, re.IGNORECASE
                ):
                    continue
                return True
    return False


# --- Core check -------------------------------------------------------------


def check(data: dict) -> dict | None:
    response = data.get("assistant_response", "") or data.get("response", "")
    if not response:
        return None

    claims = _extract_claim_paths(response)
    if not claims:
        return None

    session_id = (
        data.get("session_id")
        or data.get("sessionId")
        or (data.get("session") or {}).get("id", "")
        or ""
    ).strip()
    terminal_id = (
        data.get("terminal_id")
        or data.get("terminalId")
        or os.environ.get("CLAUDE_TERMINAL_ID", "")
        or ""
    ).strip()

    supplied = data.get("tool_events")
    if isinstance(supplied, list) and supplied:
        events = supplied
    else:
        events = _load_turn_events(session_id, terminal_id)

    # Evidence system unavailable — warn, don't block.
    if events is None:
        lines = [
            "**⚠️ Unverified Positive Existence Claim (evidence system unavailable)**\n",
            "The response asserts a file exists at a specific location/ref, "
            "but the evidence store is unreachable and cannot verify direct inspection.\n",
        ]
        for text, path in claims:
            lines.append(f'- Claimed: "{text}"  (path: {path})')
        lines.append("")
        lines.append(
            "Stat output (`git log --stat`, `git diff --stat`) does NOT prove a file "
            "currently exists at a ref. Use `git show <ref>:<path>`, `git cat-file -e`, "
            "`git ls-tree`, `ls`, or Read on the exact path before asserting presence."
        )
        return {
            "decision": "warn",
            "reason": "\n".join(lines),
            "blocking_hook": "Stop_positive_existence_guard",
        }

    unverified: list[tuple[str, str]] = []
    for text, path in claims:
        if not _path_inspected_directly(path, events):
            unverified.append((text, path))

    if not unverified:
        return None

    stat_mentioned = bool(STAT_MENTION_PATTERNS.search(response))

    lines = ["**Unverified Positive Existence Claim Detected**\n"]
    lines.append(
        "The response asserts that the following path(s) exist at a specific "
        "location/ref, but no direct inspection of that exact path occurred "
        "this turn:\n"
    )
    for text, path in unverified:
        lines.append(f'- Claimed: "{text}"  (path: {path})')
    lines.append("")
    if stat_mentioned:
        lines.append(
            "⚠️ Stat-style output (`git log --stat` / `git diff --stat` / `| N +`) "
            "was seen this turn. Stat summaries describe a past diff, NOT current "
            "tree state. They cannot ground a presence claim."
        )
    lines.append(
        "Verify before asserting presence:\n"
        "  - `git show <ref>:<path>`      (confirm file at a commit/branch)\n"
        "  - `git cat-file -e <ref>:<path>`\n"
        "  - `git ls-tree <ref> -- <path>`\n"
        "  - `ls <path>` / `cat <path>` / Read tool on the exact path\n"
        "If the inspection returns empty/fatal, the file does NOT exist there."
    )

    return {
        "decision": "block",
        "reason": "\n".join(lines),
        "blocking_hook": "Stop_positive_existence_guard",
    }


def run(data: dict) -> dict | None:
    """In-process validator protocol for Stop_router."""
    result = check(data)
    if result and result.get("decision") == "block":
        return {
            "block": True,
            "reason": result.get("reason", ""),
            "blocking_hook": result.get("blocking_hook", "Stop_positive_existence_guard"),
        }
    return result


def main() -> None:
    try:
        raw = sys.stdin.read().strip()
        if not raw:
            sys.exit(0)
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    result = check(data)
    if result:
        print(json.dumps(result))
        if result.get("decision") == "block":
            sys.exit(2)


if __name__ == "__main__":
    main()
