"""
Referent Anchor Extractor - UserPromptSubmit hook

Extracts entity anchor terms from user messages containing structured
lists/tables combined with referential language ("those", "them", etc.).
Writes anchor terms to a terminal-scoped state file consumed by
PreToolUse_referent_scope_gate.py.

Lifecycle: Single-turn. Anchors are created on UserPromptSubmit, used
during PreToolUse gating, and cleared by Stop.py at end of turn.
No cross-turn persistence — prevents stale-anchor lock after topic shifts.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

STATE_DIR = Path(__file__).resolve().parent.parent / "state"

_REFERENTIAL_PRONOUNS = re.compile(
    r"\b(?:those|them|any\s+of\s+(?:those|these)|these|which\s+of\s+those)\b",
    re.IGNORECASE,
)

# Investigative verbs that signal the user is asking to cover the listed items,
# not just showing data. Used to reduce false positives when a table/list appears
# without a clear investigation intent (e.g. "here's the output: | foo | bar |").
_INVESTIGATIVE_VERBS = re.compile(
    r"\b(?:investigate|check|analyze|look\s+into|debug|inspect|review|examine|audit|test|verify)\b",
    re.IGNORECASE,
)

_EXPANSION_LANGUAGE = re.compile(
    r"\b(?:and\s+anything\s+else|also\s+check|or\s+other|plus\s+any)\b",
    re.IGNORECASE,
)

_TABLE_ROW = re.compile(r"\|\s*([^|\n]+?)\s*\|")
_BULLET_ITEM = re.compile(r"^[ \t]*[-*]\s+(.+)$", re.MULTILINE)


def _extract_table_rows(text: str) -> list[str]:
    """Extract first-column text from markdown table rows, skipping headers."""
    lines = text.splitlines()
    header_indices: set[int] = set()
    for i, raw_line in enumerate(lines):
        if re.match(r"^\s*\|[\s\-:|]+\|\s*$", raw_line):
            if i > 0:
                header_indices.add(i - 1)

    rows: list[str] = []
    for i, raw_line in enumerate(lines):
        line = raw_line.strip()
        if i in header_indices:
            continue
        if not line.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:|]+\|$", line):
            continue
        match = re.match(r"^\|\s*([^|\n]+?)\s*\|", line)
        if match:
            cell = match.group(1).strip()
            if cell and not re.match(r"^[\s\-:]+$", cell):
                rows.append(cell)
    return rows


def _extract_bullet_items(text: str) -> list[str]:
    """Extract text from bullet list items."""
    return [m.group(1).strip() for m in _BULLET_ITEM.finditer(text)]


def _normalize_term(term: str) -> str:
    """Normalize an anchor term for matching: lowercase, strip punctuation."""
    term = term.lower().strip()
    term = re.sub(r"[^\w\s]", " ", term)
    term = re.sub(r"\s+", " ", term).strip()
    return term


def _has_referential_language(text: str) -> bool:
    return bool(_REFERENTIAL_PRONOUNS.search(text))


def _has_expansion_language(text: str) -> bool:
    return bool(_EXPANSION_LANGUAGE.search(text))


def _has_investigative_verb(text: str) -> bool:
    return bool(_INVESTIGATIVE_VERBS.search(text))


def _get_terminal_id(context: HookContext) -> str:
    if context.terminal_id:
        return context.terminal_id
    try:
        sys_path = str(Path(__file__).resolve().parent.parent / "__lib")
        import sys
        if sys_path not in sys.path:
            sys.path.insert(0, sys_path)
        from terminal_detection import detect_terminal_id
        return detect_terminal_id()
    except Exception:
        return "unknown"


def _read_state(terminal_id: str) -> dict | None:
    state_file = STATE_DIR / f"referent_anchors_{terminal_id}.json"
    if not state_file.exists():
        return None
    try:
        return json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _write_state(
    terminal_id: str,
    anchor_terms: list[str] | None,
    source_type: str,
    session_id: str | None,
    bypass_scope: bool = False,
) -> None:
    existing = _read_state(terminal_id)

    # Session boundary: if session_id changed (compaction, new session),
    # discard stale anchors from the previous session.
    if existing and existing.get("anchor_terms") and session_id:
        prev_session = existing.get("session_id", "")
        if prev_session and prev_session != session_id:
            existing = None

    # Single-turn lifecycle: always write current state.
    # Anchors are cleared at Stop, so no cross-turn preservation needed.
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file = STATE_DIR / f"referent_anchors_{terminal_id}.json"
    data = {
        "anchor_terms": anchor_terms or [],
        "source_type": source_type,
        "session_id": session_id or "",
        "terminal_id": terminal_id,
        "timestamp": time.time(),
        "bypass_scope": bypass_scope,
        "extraction_attempted": True,
        "exploration_used": False,
    }
    if anchor_terms is None:
        data["status"] = "no_anchors"
    state_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


@register_hook("referent_anchor", priority=6.0)
def referent_anchor_hook(context: HookContext) -> HookResult:
    prompt = context.prompt or ""
    terminal_id = _get_terminal_id(context)

    has_table = "|" in prompt
    has_bullets = bool(_BULLET_ITEM.search(prompt))
    has_referential = _has_referential_language(prompt)

    if not has_table and not has_bullets and not has_referential:
        _write_state(terminal_id, None, "none", context.session_id)
        return HookResult.empty()

    anchor_terms_raw: list[str] = []
    source_type = "none"

    if has_table:
        table_rows = _extract_table_rows(prompt)
        if len(table_rows) >= 3:
            anchor_terms_raw = table_rows
            source_type = "table"

    if not anchor_terms_raw and has_bullets:
        bullet_items = _extract_bullet_items(prompt)
        if len(bullet_items) >= 3:
            anchor_terms_raw = bullet_items
            source_type = "list"

    if not anchor_terms_raw or not has_referential or not _has_investigative_verb(prompt):
        _write_state(terminal_id, None, source_type, context.session_id)
        return HookResult.empty()

    anchor_terms = [_normalize_term(t) for t in anchor_terms_raw]
    anchor_terms = [t for t in anchor_terms if t]

    bypass_scope = _has_expansion_language(prompt)
    _write_state(terminal_id, anchor_terms, source_type, context.session_id, bypass_scope)

    return HookResult.empty()


# ---------------------------------------------------------------------------
# Lifecycle: Single-turn (created on UPS, cleared at Stop).
#
# Activation conditions (ALL must be true):
#   1. ≥3 table rows OR ≥3 bullet items in the user message
#   2. Referential pronoun present ("those", "them", "these", etc.)
#   3. Investigative verb nearby ("investigate", "check", "analyze", etc.)
#
# bypass_scope flag:
#   Set when user says "and anything else", "also check", "or other",
#   "plus any" — signals they want broader coverage beyond explicit items.
#
# State file: state/referent_anchors_{terminal_id}.json
#   Per-terminal isolation prevents cross-terminal anchor contamination.
# ---------------------------------------------------------------------------
