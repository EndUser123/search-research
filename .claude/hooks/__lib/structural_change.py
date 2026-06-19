"""Source-aware structural-change detection (shared).

WHY THIS EXISTS
  Detectors that regex-scan an undifferentiated text blob (serialized tool_input
  + tool output) conflate three unrelated things: a real shell deletion command,
  a code diff that removes a symbol, and a *string literal* that merely contains
  a deletion-command-shaped substring (test fixtures, quoted examples, docs).
  The third produces false positives (e.g. a test file whose body contains
  "rm old.py" gets flagged as deleting old.py).

  This module detects changes from the RIGHT field for the RIGHT tool:
    - shell COMMANDS for file deletions (boundary-anchored, mention-safe),
    - EDIT DIFFS (old_string vs new_string) for symbol/line removal.
  It never treats file content or tool output as operations.

  Single source of truth for "what is a real deletion" so multiple hooks do not
  each re-implement (and re-bug) it.
"""
from __future__ import annotations

import re

# A deletion verb only counts when it actually STARTS a command — at string
# start or after a shell separator (newline ; & | ` ( ) { } $( ) or xargs/-exec.
# This is why `grep "rm x.py"`, `echo rm x`, and heredoc bodies do NOT match.
_CMD_BOUNDARY = r"(?:^|[\n;&|`(){}]|\$\(|\bxargs\s+|-exec\s+)\s*"

# Each pattern captures the affected path in group "p" when determinable.
_PATH = r"(?P<p>[^\s;&|'\"]+)"
_DELETION_RES = [
    re.compile(_CMD_BOUNDARY + r"(?:sudo\s+)?rm\b(?:\s+-[a-zA-Z]+)*\s+['\"]?" + _PATH, re.IGNORECASE),
    re.compile(_CMD_BOUNDARY + r"git\s+rm\b(?:\s+-[a-zA-Z]+)*\s+['\"]?" + _PATH, re.IGNORECASE),
    re.compile(_CMD_BOUNDARY + r"unlink\s+['\"]?" + _PATH, re.IGNORECASE),
    re.compile(_CMD_BOUNDARY + r"rmdir\b(?:\s+-[a-zA-Z]+)*\s+['\"]?" + _PATH, re.IGNORECASE),
    # PowerShell / cmd — best-effort path; skip /switches and -Flags below.
    re.compile(_CMD_BOUNDARY + r"(?:Remove-Item|del)\b(?:\s+[-/][A-Za-z]+)*\s+['\"]?" + _PATH, re.IGNORECASE),
]

_DEF_RE = re.compile(r"^[ \t]*(?:async[ \t]+)?(def|class)[ \t]+(\w+)", re.MULTILINE)


def deletions_in_command(command: str) -> list[str]:
    """Return paths deleted by real shell deletion commands in `command`.

    Boundary-anchored and field-scoped: pass ONLY a shell command string, never
    file content. Returns [] for non-deletion commands. Pure / side-effect free.
    """
    if not command or not isinstance(command, str):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for rx in _DELETION_RES:
        for m in rx.finditer(command):
            p = (m.group("p") or "").strip("'\"")
            # skip option/switch tokens (Unix -flag, Windows /flag), bare
            # placeholders ({}), and anything without a word char — none name a
            # real, greppable target.
            if (not p or p.startswith("-") or p.startswith("/-")
                    or re.fullmatch(r"/[A-Za-z]", p) or not re.search(r"\w", p)):
                continue
            if p not in seen:
                seen.add(p)
                out.append(p)
    return out


def removed_symbols(old: str, new: str) -> list[tuple[str, str]]:
    """(kind, name) for def/class present in `old` but absent in `new`.

    Detects real removals from an edit diff — never from a content scan.
    """
    if not isinstance(old, str) or not isinstance(new, str):
        return []
    old_syms = set(_DEF_RE.findall(old))
    new_syms = set(_DEF_RE.findall(new))
    return sorted(old_syms - new_syms)


def lines_removed(old: str, new: str) -> int:
    """Net lines removed by an edit (old line count minus new line count)."""
    if not isinstance(old, str) or not isinstance(new, str):
        return 0
    return max(0, old.count("\n") - new.count("\n"))
