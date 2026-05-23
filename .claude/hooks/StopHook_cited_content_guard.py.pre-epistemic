#!/usr/bin/env python3
"""Stop hook: Cited content guard.

Detects when a response attributes specific code to a file at a specific
line number, then verifies that key identifiers from the cited code appear
in the evidence store's Read output excerpt for that file.

WHY THIS EXISTS:
  The existing gates verify that a file was Read before accepting claims
  about it. But reading a file does not verify that the QUOTED CONTENT
  actually exists in that file. An AI can read file X, then fabricate code
  attributed to "file X at line 97" — the existing gates pass it because
  the file WAS read.

FAILURE MODE CAUGHT (2026-04-04 session with MiniMax-M2.7):
  "The adversarial-agents.md reference file shows the problem at line 97:
     adversarial_findings = run_subagent_review(
         plan_content=pre_mortem_output,  # Use pre-mortem as 'plan'"
  -> adversarial-agents.md was read, but run_subagent_review doesn't appear
     in the output excerpt. The cited code was fabricated.

DETECTION:
  Response contains "[filename] shows [code/problem] at line N:" followed
  by an indented code block. Key identifiers from that block are extracted
  and checked against the Read event's output_excerpt.

TWO-TIER RESPONSE:
  - File NOT read at all → BLOCK (handled here too, for belt-and-suspenders)
  - File was read, identifiers absent from excerpt → WARN
    (excerpt may be truncated; can't hard-block on this alone)
  - File was read, identifiers found in excerpt → PASS

MODE: CITED_CONTENT_GUARD_MODE env var ("warn"/"block", default "warn")
ENABLED: CITED_CONTENT_GUARD_ENABLED env var ("true"/"false", default "true")
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

try:
    from evidence_scope import SCOPE_TURN_STRICT, load_scoped_tool_events
except ImportError:
    SCOPE_TURN_STRICT = ""
    load_scoped_tool_events = None  # type: ignore

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def _is_enabled() -> bool:
    return os.environ.get("CITED_CONTENT_GUARD_ENABLED", "true").lower() == "true"

def _get_mode() -> str:
    return os.environ.get("CITED_CONTENT_GUARD_MODE", "warn").lower()


# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------

# Matches: "something.md reference file shows the problem at line 97:"
# or "adversarial-agents.md ... at line 97:"
# Captures: (filename_with_ext, line_number)
_CITATION_RE = re.compile(
    r'([\w.\-]+\.(?:py|md|ts|js|json|yaml|txt|cfg|toml))'  # filename
    r'(?:[^\n]{0,120}?)'                                     # optional surrounding text
    r'\bat\s+line\s+(\d+)',                                  # "at line N"
    re.IGNORECASE,
)

# Identifiers: snake_case / camelCase tokens, 5+ chars to avoid noise
_IDENTIFIER_RE = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]{4,})\b')

# Common noise words to exclude from identifier extraction
_NOISE = frozenset({
    "false", "true", "none", "self", "return", "import", "class",
    "with", "pass", "raise", "yield", "async", "await", "lambda",
    "print", "isinstance", "hasattr", "getattr", "setattr",
    "items", "values", "keys", "append", "extend", "update",
    "format", "strip", "split", "lower", "upper", "join",
    "content", "output", "result", "value", "option", "config",
    "source", "target", "prefix", "suffix", "index", "count",
    "length", "error", "warning", "message", "reason", "status",
    "response", "request", "context", "session", "terminal",
    "default", "enabled", "disabled", "verbose", "debug",
    "analysis", "plan_content",  # too generic to be distinctive
})


def _extract_identifiers(text: str) -> list[str]:
    """Extract distinctive identifiers from a code block."""
    found = []
    for m in _IDENTIFIER_RE.finditer(text):
        name = m.group(1).lower()
        if name not in _NOISE:
            found.append(m.group(1))
    # Deduplicate, keep order
    seen: set[str] = set()
    result = []
    for ident in found:
        key = ident.lower()
        if key not in seen:
            seen.add(key)
            result.append(ident)
    return result[:10]  # cap to avoid runaway matching


def _extract_following_code(response: str, match_end: int) -> str:
    """Extract the code block that immediately follows a citation marker."""
    tail = response[match_end:]
    # Take up to 20 lines after the citation line
    lines = tail.split("\n")
    code_lines = []
    for line in lines[1:21]:  # skip the rest of the matched line
        if line.strip() == "" and code_lines:
            break  # blank line ends the block if we already have content
        if line.startswith(("  ", "\t")):  # indented = code
            code_lines.append(line)
        elif code_lines:  # non-indented after code = block ended
            break
    return "\n".join(code_lines)


# ---------------------------------------------------------------------------
# Evidence check
# ---------------------------------------------------------------------------

def _load_read_events(
    session_id: str, terminal_id: str
) -> list[dict[str, Any]]:
    """Load all Read tool events for this turn (fall-open on error)."""
    if load_scoped_tool_events is None:
        return []
    try:
        events = load_scoped_tool_events(
            session_id=session_id,
            terminal_id=terminal_id,
            scope=SCOPE_TURN_STRICT,
            limit=500,
        )
        return [e for e in events if e.get("name") == "Read"]
    except Exception:
        return []


def _find_read_events_for_basename(
    basename: str, read_events: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Match Read events by filename basename (case-insensitive)."""
    basename_lower = basename.lower()
    matches = []
    for ev in read_events:
        path = str(ev.get("command") or ev.get("file_path") or "")
        if Path(path).name.lower() == basename_lower:
            matches.append(ev)
    return matches


def _identifiers_in_excerpt(
    identifiers: list[str], excerpt: str
) -> list[str]:
    """Return identifiers found in the excerpt (case-insensitive)."""
    excerpt_lower = excerpt.lower()
    return [i for i in identifiers if i.lower() in excerpt_lower]


# ---------------------------------------------------------------------------
# Core check
# ---------------------------------------------------------------------------

def check(data: dict[str, Any]) -> dict[str, Any] | None:
    if not _is_enabled():
        return None

    response = str(
        data.get("assistant_response") or data.get("response") or ""
    )
    if not response or len(response) < 50:
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

    # Find all "filename at line N" citations
    citations = list(_CITATION_RE.finditer(response))
    if not citations:
        return None

    # Without a session_id we cannot look up evidence — fail open
    if not session_id:
        return None

    # Load Read events once (fail-open if unavailable)
    read_events = _load_read_events(session_id, terminal_id)

    violations: list[str] = []
    not_read: list[str] = []

    for m in citations:
        filename = m.group(1)
        line_num = m.group(2)
        code_block = _extract_following_code(response, m.end())

        if not code_block.strip():
            # No code block follows — not a cited-code pattern
            continue

        identifiers = _extract_identifiers(code_block)
        if not identifiers:
            # No distinctive identifiers — can't verify, skip
            continue

        # Was this file Read at all?
        file_read_events = _find_read_events_for_basename(filename, read_events)

        if not file_read_events:
            # File was never Read — strong signal; block regardless of mode
            not_read.append(
                f"  - `{filename}` at line {line_num}: "
                f"cited identifiers [{', '.join(identifiers[:3])}] "
                f"but file was never Read this turn"
            )
            continue

        # File was Read — check if identifiers appear in excerpt
        all_excerpts = " ".join(ev.get("output", "") for ev in file_read_events)
        found = _identifiers_in_excerpt(identifiers, all_excerpts)
        missing = [i for i in identifiers if i not in found]

        if missing and len(all_excerpts) > 200:
            # Excerpt is substantial but identifiers absent — suspicious
            violations.append(
                f"  - `{filename}` at line {line_num}: "
                f"identifiers [{', '.join(missing[:3])}] not found in Read output excerpt "
                f"({len(all_excerpts)} chars)"
            )

    if not violations and not not_read:
        return None

    lines = []

    if not_read:
        lines.append("CITED CODE FROM UNREAD FILES\n")
        lines.append(
            "The response quotes code from files that were never Read this turn:"
        )
        lines.extend(not_read)
        lines.append("")
        lines.append(
            "Before citing specific code from a file, Read the file first "
            "and verify the code exists there."
        )
        return {"block": True, "reason": "\n".join(lines), "blocking_hook": "StopHook_cited_content_guard"}

    # Soft violations (file was read, identifiers absent from excerpt)
    lines.append("CITED CODE NOT VERIFIABLE IN READ OUTPUT\n")
    lines.append(
        "The response attributes specific code to files at specific line numbers, "
        "but the cited identifiers do not appear in the Read tool output for those files:"
    )
    lines.extend(violations)
    lines.append("")
    lines.append(
        "This may indicate fabricated code citations. Verify the quoted code "
        "actually exists in the file before presenting it as evidence."
    )

    mode = _get_mode()
    if mode == "block":
        return {"block": True, "reason": "\n".join(lines), "blocking_hook": "StopHook_cited_content_guard"}
    else:
        # warn — inject advisory but allow
        return {"allow": True, "warning": "\n".join(lines)}


# ---------------------------------------------------------------------------
# Router protocol
# ---------------------------------------------------------------------------

def run(data: dict[str, Any]) -> dict[str, Any] | None:
    """In-process validator protocol for Stop_router."""
    try:
        return check(data)
    except Exception:
        return None  # fail-open
