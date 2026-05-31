#!/usr/bin/env python3
"""Stop gate: Skill directory correlation check (advisory).

Detects when tool events show reads from a different skill directory than the
skill mentioned in the user's conversation — catching the 'accurate reporting
of wrong artifact' entity confusion bug.

FAILURE MODE CAUGHT:
  User asks about /ai-pcli. AI does an unscoped Glob and hits ai-cli/ first.
  Reads ai-cli/SKILL.md, then reports findings as if they describe ai-pcli.
  All existing gates pass because the file WAS read and IS accurately described.
  The bug is not fabrication — it is accurate reporting of the wrong entity.

DETECTION:
  1. Extract skill name from conversation (last user message containing /skill-name)
  2. Load SCOPE_TURN_STRICT tool events from evidence_store
  3. Filter for Read/Glob/Grep events whose path is inside .claude/skills/
  4. Extract which skill directories were actually accessed
  5. Warn if accessed skill dirs do not include the expected skill

MODE: Advisory only — never blocks. Emits systemMessage for awareness.
ENABLED: SKILL_DIR_CORRELATION_ENABLED env var ("true"/"false", default "true")
"""
from __future__ import annotations


# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---




# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

def _normalize_stdout(data: dict) -> dict:
    """Normalize hook output to Claude Code Zod-valid schema."""
    if data.get('decision') == 'allow':
        return {'decision': 'approve'}
    if data.get('decision') == 'block':
        return {'decision': 'block', 'reason': data.get('reason', '')}
    if 'allow' in data:
        if data['allow'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'continue' in data:
        if data['continue'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'ok' in data:
        return {'decision': 'approve'}
    return data






import os
import re
import sys
from pathlib import Path
from typing import Any

HOOKS_DIR = _hooks_dir  # from bootstrap

# Matches .claude/skills/SKILLNAME/ in any path string (forward or back slash)
_SKILL_DIR_RE = re.compile(r"\.claude[/\\]skills[/\\]([^/\\.\s]+)", re.IGNORECASE)

# Matches /skill-name in user message text (slash prefix = explicit skill invocation)
_SLASH_SKILL_RE = re.compile(r"/([a-z][a-z0-9-]{1,40})\b", re.IGNORECASE)

# Non-skill entries that appear inside .claude/skills/ — skip these
_NON_SKILL_PREFIXES = ("_", ".")
_NON_SKILL_NAMES = frozenset({"__lib", "__pycache__", "README", "SKILL_TEMPLATE"})


def _is_enabled() -> bool:
    return os.environ.get("SKILL_DIR_CORRELATION_ENABLED", "true").lower() in ("1", "true", "yes")


def _extract_content_text(content: Any) -> str:
    """Extract plain text from a message content field (string or content block list)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                text = block.get("text") or block.get("content") or ""
                parts.append(str(text))
        return " ".join(parts)
    return ""


def _get_user_skill_from_conversation(data: dict) -> str | None:
    """Extract the skill name from the last user message containing a /skill-name pattern."""
    conversation = data.get("conversation")
    if not isinstance(conversation, list) or not conversation:
        return None

    for msg in reversed(conversation):
        if not isinstance(msg, dict):
            continue
        role = str(msg.get("role", "")).lower()
        if role not in ("user", "human"):
            continue
        content_text = _extract_content_text(msg.get("content", ""))
        if not content_text:
            continue
        m = _SLASH_SKILL_RE.search(content_text)
        if m:
            candidate = m.group(1).lower()
            # Skip common false positives (CLI flags, paths, etc.)
            if candidate not in ("v", "s", "n", "r", "f", "l", "h", "all", "help"):
                return candidate

    return None


def _extract_accessed_skills(events: list[dict]) -> set[str]:
    """Extract skill directory names from tool events that accessed .claude/skills/."""
    skills: set[str] = set()
    for evt in events:
        if str(evt.get("name", "")) not in ("Read", "Glob", "Grep"):
            continue
        path_str = str(evt.get("command") or evt.get("file_path") or "")
        if not path_str:
            continue
        for m in _SKILL_DIR_RE.finditer(path_str):
            name = m.group(1)
            if any(name.startswith(p) for p in _NON_SKILL_PREFIXES):
                continue
            if name in _NON_SKILL_NAMES:
                continue
            skills.add(name.lower())
    return skills


def run(data: dict) -> dict | None:
    """Run skill directory correlation advisory check.

    Returns a systemMessage advisory if the accessed skill directories do not
    include the skill the user was asking about. Never blocks.
    """
    if not _is_enabled():
        return None

    try:
        from evidence_scope import SCOPE_TURN_STRICT, load_scoped_tool_events
    except ImportError:
        return None

    try:
        # --- Resolve session/terminal scope (mirrors _resolve_scope_ids in Stop.py) ---
        session_obj = data.get("session")
        nested_session_id = ""
        nested_terminal_id = ""
        if isinstance(session_obj, dict):
            nested_session_id = str(
                session_obj.get("id")
                or session_obj.get("session_id")
                or session_obj.get("sessionId")
                or ""
            )
            nested_terminal_id = str(
                session_obj.get("terminal_id") or session_obj.get("terminalId") or ""
            )

        session_id = (
            nested_session_id
            or data.get("session_id")
            or data.get("sessionId")
            or os.environ.get("CLAUDE_SESSION_ID")
            or ""
        )
        terminal_id = (
            nested_terminal_id
            or data.get("terminal_id")
            or data.get("terminalId")
            or os.environ.get("CLAUDE_TERMINAL_ID")
            or ""
        )

        if not session_id:
            return None

        # --- 1. Determine the skill the user was asking about ---
        expected_skill = _get_user_skill_from_conversation(data)
        if not expected_skill:
            return None

        # --- 2. Load tool events for this turn ---
        events = load_scoped_tool_events(
            session_id=str(session_id),
            terminal_id=str(terminal_id),
            scope=SCOPE_TURN_STRICT,
        )

        # --- 3. Extract which skill directories were actually accessed ---
        accessed_skills = _extract_accessed_skills(events)
        if not accessed_skills:
            return None

        # --- 4. Check correlation ---
        if expected_skill in accessed_skills:
            return None  # Correct entity was accessed — no issue

        # --- 5. Emit advisory ---
        accessed_sorted = sorted(accessed_skills)
        return {
            "decision": "allow",
            "systemMessage": (
                f"⚠️ SKILL DIR CORRELATION\n"
                f"User asked about: /{expected_skill}\n"
                f"Skill dirs accessed this turn: {accessed_sorted}\n"
                f"Multiple skills share identical internal filenames "
                f"(SKILL.md, ai_cli.py, *-recipe.json). An unscoped Glob or Grep "
                f"may have matched the wrong entity.\n"
                f"Before reporting findings, verify your reads were inside "
                f".claude/skills/{expected_skill}/ specifically."
            ),
        }

    except Exception:
        # Gate must fail open — never break the Stop hook
        return None
