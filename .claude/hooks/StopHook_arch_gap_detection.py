#!/usr/bin/env python3
"""StopHook_arch_gap_detection.py — Anti-Rationalization Gate for /arch Skill

Blocks responses that declare context gaps ("I don't have X") when the referenced
content actually exists in the transcript. Forces transcript verification before
allowing false gap declarations to pass.

DECISION-1: Stop hook blocking model
  - Exit Code 2 blocks the response and forces correction
  - Content injection via JSON: {"decision": "block", "reason": "...", "blocking_hook": "..."}

DECISION-3: Skill-scope gating via skill_state
  - skill_state.get("skill") from validator_input
  - Partial match: "arch" in skill_name.lower()
  - If not /arch session, exit immediately (allow)

INVARIANT-2: Sliding window transcript search (last 200 lines, then wrap)
INVARIANT-4: GAP_PATTERNS require article+noun after gap phrase

Environment:
  ARCH_GAP_DETECTION_ENABLED  (default: true)
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

# Session transcript lookup
_HOOK_NAME = Path(__file__).stem


# --------------------------------------------------------------------
# GAP PATTERNS — article+noun specificity (INVARIANT-4)
# Bare gap phrases ("i don't have") are too ambiguous — they match
# legitimate self-reflection like "I don't have enough context".
# Require article + noun after the gap phrase.
# --------------------------------------------------------------------
_GAP_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # Primary gap phrases with article+noun requirement
    # "i don't have the ideas" ✓  "i don't have enough context" ✗
    # Apostrophe variants (don't)
    (
        "i don't have the",
        re.compile(r"i\s+don't\s+have\s+(?:the\s+)?[a-zA-Z_][a-zA-Z0-9_-]*", re.IGNORECASE),
    ),
    (
        "i cannot find the",
        re.compile(r"i\s+cannot\s+find\s+(?:the\s+)?[a-zA-Z_][a-zA-Z0-9_-]*", re.IGNORECASE),
    ),
    # Space-separated variants (do not) — catches formal AI responses
    (
        "i do not have the",
        re.compile(r"i\s+do\s+not\s+have\s+(?:the\s+)?[a-zA-Z_][a-zA-Z0-9_-]*", re.IGNORECASE),
    ),
    (
        "i cannot locate the",
        re.compile(r"i\s+cannot\s+locate\s+(?:the\s+)?[a-zA-Z_][a-zA-Z0-9_-]*", re.IGNORECASE),
    ),
    (
        "context is missing",
        re.compile(r"context\s+is\s+missing", re.IGNORECASE),
    ),
    (
        "not provided in the conversation",
        re.compile(r"not\s+provided\s+in\s+the\s+conversation", re.IGNORECASE),
    ),
    (
        "was not discussed",
        re.compile(r"was\s+not\s+discussed", re.IGNORECASE),
    ),
    (
        "no prior context",
        re.compile(r"no\s+prior\s+context", re.IGNORECASE),
    ),
]


def _is_arch_session(data: dict[str, Any]) -> bool:
    """Check if this is an /arch skill session (INVARIANT: skill_scope check inside hook).

    DECISION-3: skill_state is passed via input_data.get("skill_state").
    Partial match: "arch" in skill_name.lower().
    """
    skill_state = data.get("skill_state")
    if not skill_state:
        return False
    skill_name = (skill_state.get("skill") or "").lower()
    return "arch" in skill_name


def _read_transcript_lines(transcript_path: str | None, session_id: str | None) -> tuple[list[str], int]:
    """Read transcript lines with sliding window hint.

    Returns (lines, skipped_count) where skipped_count is how many lines
    had parse errors (for warning message per INVARIANT-4 / FM-004).

    INVARIANT-2: Sliding window search — returns all lines in reading order.
    Caller decides which subset to search first based on position.
    """
    lines: list[str] = []
    skipped = 0

    # Primary path: explicit transcript_path
    if transcript_path:
        path = Path(transcript_path)
        if path.exists():
            try:
                content = path.read_text(encoding="utf-8")
                for line in content.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        json.loads(line)
                        lines.append(line)
                    except json.JSONDecodeError:
                        skipped += 1
            except OSError:
                pass  # fail-open on read error

    # Fallback: session JSONL in ~/.claude/sessions/
    if not lines and session_id:
        session_path = Path.home() / ".claude" / "sessions" / f"{session_id}.jsonl"
        if session_path.exists():
            try:
                content = session_path.read_text(encoding="utf-8")
                for line in content.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        json.loads(line)
                        lines.append(line)
                    except json.JSONDecodeError:
                        skipped += 1
            except OSError:
                pass

    return lines, skipped


def _extract_content_from_line(line: str) -> str:
    """Extract content field from a JSON transcript line."""
    try:
        obj = json.loads(line)
        content = obj.get("content", "") or obj.get("text", "")
        if isinstance(content, list):
            # Some transcript formats use content: [{type, text}, ...]
            content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
        return str(content)
    except (json.JSONDecodeError, TypeError):
        return ""


def _extract_noun_from_gap_response(response_text: str) -> str | None:
    """Extract the specific noun/content being claimed as missing from the response.

    For "i don't have the ideas" → returns "ideas"
    For "i cannot find the relevant code" → returns "relevant code"
    """
    # Direct content extraction after "don't have" or "cannot find"
    # Handles underscored content like THE_TARGET_CONTENT without requiring "the" before it
    gap_noun_patterns = [
        # Match content after "i don't have" - captures the content directly
        # Supports both spaced content ("the ideas") and underscored content ("THE_TARGET")
        re.compile(
            r"i\s+don't\s+have\s+(?:the\s+)?([a-zA-Z][a-zA-Z0-9_-]+)",
            re.IGNORECASE,
        ),
        re.compile(
            r"i\s+cannot\s+find\s+(?:the\s+)?([a-zA-Z][a-zA-Z0-9_-]+)",
            re.IGNORECASE,
        ),
    ]

    for pattern in gap_noun_patterns:
        match = pattern.search(response_text)
        if match:
            noun = match.group(1).strip()
            return noun if noun else None
    return None


def _search_transcript_for_content(
    lines: list[str],
    search_terms: list[str],
) -> list[tuple[int, str]]:
    """Search transcript for lines containing the specific content (not gap phrases).

    Uses sliding window: search last 200 lines first (most recent context),
    then wrap to beginning if not found.

    Returns list of (line_number, matched_content) tuples.
    """
    total = len(lines)
    if total == 0:
        return []

    window_size = min(200, total)
    # Search order: last window_size lines first, then wrap to beginning
    search_order = list(range(total - window_size, total)) + list(range(0, total - window_size))

    matches: list[tuple[int, str]] = []

    for idx in search_order:
        line = lines[idx]
        content = _extract_content_from_line(line)
        # Check if any search term is in the content
        for term in search_terms:
            if term.lower() in content.lower():
                snippet = content[:100].replace("\n", " ").strip()
                matches.append((idx + 1, snippet))
                break  # Only match once per line

    return matches


def _check_ordinal_plus_gap(text: str) -> bool:
    """Check if response contains ordinal reference (idea N / point N) + gap language.

    Returns True if gap language is combined with an ordinal reference.
    """
    gap_language = [
        r"don't\s+have",
        r"don't\s+posses",
        r"can't\s+find",
        r"cannot\s+find",
        r"lacks?\s",
        r"lacking\b",
        r"missing",
        r"unavailable",
        r"not\s+in\s+",
        r"not\s+provided",
        r"wasn't?\s+given",
        r"hasn't?\s+been\s+",
    ]

    ordinal_pattern = re.compile(
        r"\b(idea|point|item|option|choice|alternative| suggestion)\s+\d\b",
        re.IGNORECASE,
    )

    if not ordinal_pattern.search(text):
        return False

    # Check if any gap language appears near the ordinal reference
    for gap_re in gap_language:
        if re.search(gap_re, text, re.IGNORECASE):
            return True

    return False


def _evaluate_response(data: dict[str, Any]) -> dict[str, Any]:
    """Evaluate response for false gap declarations.

    Returns {"decision": "block", "reason": "...", "blocking_hook": "..."} or
    {"allow": True}.
    """
    # Skill-scope gating: only fire for /arch sessions
    if not _is_arch_session(data):
        return {"allow": True}

    response_text = data.get("response_text", "") or data.get("assistant_response", "")
    if not response_text:
        return {"allow": True}

    transcript_path = data.get("transcript_path")
    session_id = data.get("session_id")

    lines, skipped = _read_transcript_lines(transcript_path, session_id)

    if skipped > 0:
        sys.stderr.write(f"Warning: {skipped} transcript lines skipped due to parse errors\n")

    # Check GAP_PATTERNS
    for phrase, pattern in _GAP_PATTERNS:
        if pattern.search(response_text):
            # Found a gap phrase — extract what content is being claimed as missing
            noun = _extract_noun_from_gap_response(response_text)
            if noun:
                # Search transcript for the specific content (not the gap phrase itself)
                # Note: search for bare noun only, not "the {noun}" - transcript content
                # may not have "the" before the noun (e.g., "Here are my ideas" not "Here are the ideas")
                matches = _search_transcript_for_content(lines, [noun])
                if matches:
                    # Content found in transcript → block
                    line_nums = ", ".join(f"line {ln}" for ln, _ in matches[:3])
                    snippet = matches[0][1]
                    reason = (
                        f"False gap declaration detected: '{phrase}...' — "
                        f"content found in transcript ({line_nums}): \"{snippet}\""
                    )
                    return {
                        "decision": "block",
                        "reason": reason,
                        "blocking_hook": _HOOK_NAME,
                    }

    # Check ordinal + gap combination
    if _check_ordinal_plus_gap(response_text):
        # Extract ordinal reference (e.g., "idea 2" -> "idea 2")
        ordinal_match = re.search(r"\b(idea|point)\s+\d\b", response_text, re.IGNORECASE)
        if ordinal_match:
            ordinal_ref = ordinal_match.group(0)
            matches = _search_transcript_for_content(lines, [ordinal_ref])
            if matches:
                line_nums = ", ".join(f"line {ln}" for ln, _ in matches[:3])
                snippet = matches[0][1]
                reason = (
                    f"False ordinal gap detected — reference found in transcript "
                    f"({line_nums}): \"{snippet}\""
                )
                return {
                    "decision": "block",
                    "reason": reason,
                    "blocking_hook": _HOOK_NAME,
                }

    return {"allow": True}


def run(data: dict[str, Any]) -> dict[str, Any]:
    """Stop hook entry point for arch gap detection.

    Args:
        data: validator_input from Stop_router.py containing:
            - skill_state: {"skill": "...", ...}
            - response_text / assistant_response: AI response text
            - transcript_path: path to session transcript
            - session_id: current session ID

    Returns:
        {"decision": "block", "reason": "...", "blocking_hook": "..."} to block
        {"allow": True} to allow
    """
    if os.environ.get("ARCH_GAP_DETECTION_ENABLED", "true").lower() != "true":
        return {"allow": True}

    try:
        return _evaluate_response(data)
    except Exception:
        # Fail-open: any error should not block legitimate responses
        return {"allow": True}


if __name__ == "__main__":
    # Subprocess entry point: read JSON input from stdin
    input_data = json.load(sys.stdin)
    result = run(input_data)
    print(json.dumps(result))
    sys.exit(0)
