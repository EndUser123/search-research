#!/usr/bin/env python3
"""
Stop_comparative_claim_guard.py - Comparative Claim Detector
===========================================================

Blocks responses that compare files, skills, or systems WITHOUT
evidence that all compared items were Read/Grep'd/Glob'd in the
current turn.

FAILURE MODE CAUGHT:
  "Pre-mortem reads my analysis; critique reads actual source code"
  -> No Read tool events for pre-mortem SKILL.md in this turn.
  -> Gate blocks and demands verification.

LIFECYCLE: Stop (blocking gate -- exits with code 2 to block)
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
STATE_DIR = HOOKS_DIR / "state" / "turn_markers"
LOG_DIR = HOOKS_DIR / "state" / "logs"
sys.path.insert(0, str(HOOKS_DIR))

LOG_DIR.mkdir(parents=True, exist_ok=True)

_logger = logging.getLogger("comparative_claim_guard")
_handler = logging.FileHandler(LOG_DIR / "comparative_claim_guard.log", encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(logging.DEBUG)

try:
    from evidence_store import load_tool_events

    EVIDENCE_AVAILABLE = True
except ImportError as exc:
    EVIDENCE_AVAILABLE = False
    _logger.warning("evidence_store import failed: %s", exc)


# --- Patterns: Comparison constructs ----------------------------------------

# Table-style comparisons: ┌─┬─┐ row separators, | col dividers
TABLE_ROW_RE = re.compile(r"^\s*[││|].*[││|].*[││|].*$", re.MULTILINE)

# Bullet-vs patterns: "item A vs item B", "A vs. B", "A versus B"
# Items on either side of vs/versus are captured
# No lookbehind needed - pattern is specific enough
# File/skill path: must have extension (.py, .md, .SKILL, etc.) OR start with /
# Bare English words (X, Y, what, implemented) are NOT file references
VS_PHRASE_RE = re.compile(
    r"(/[\w\-./]+|[\w\-./]+\.(?:py|md|json|yml|yaml|txt|SKILL))\s+(?:vs\.?|versus)\s+(/[\w\-./]+|[\w\-./]+\.(?:py|md|json|yml|yaml|txt|SKILL))",
    re.IGNORECASE,
)

# Prose comparison keywords
PROSE_COMPARE_RE = re.compile(
    r"(?i)(unlike|compared to|comparison with|in contrast to|whereas|while\s+\w+\s+is)\s+([/\w\-.]+(?:\.(?:py|md|SKILL))?)",
)


def _extract_file(cmd: str) -> str | None:
    """Extract first path-like token from a tool command string.

    Handles all three tool formats:
    - Read:   'Read /path/to/file.py'
    - Grep:   'Grep pattern /path/to/file.py'   (path is 2nd or 3rd token)
    - Glob:   'Glob *.py /path/to'              (path is 2nd or 3rd token)
    - Any:    '/path/to/file.py'                (bare path as entire command)
    """
    if not cmd:
        return None
    # Find any token that looks like a path (contains / and not a URL)
    tokens = cmd.strip().split()
    for token in tokens[1:]:  # Skip tool name
        token = token.rstrip(",")
        # Skip common non-path tokens
        if token in ("-r", "-i", "-n", "-E", "-F", "-l", "-h", "--", "-w", "skill"):
            continue
        # Accept if it looks like a file path (contains /)
        if "/" in token or token.startswith(("P:", "p:", "C:", "c:", "~")):
            return token
        # Also accept if it has a known file extension (file.py, file.md, etc.)
        if re.match(r"[\w\-./]+\.(?:py|md|json|yml|yaml|txt|SKILL)$", token, re.IGNORECASE):
            return token
    return None


def _build_verified_set(tool_events: list[dict]) -> set[str]:
    """Build set of files/aliases verified by tool calls this turn."""
    verified = set()
    for evt in tool_events:
        name = evt.get("name", "")
        if name not in ("Read", "Grep", "Glob"):
            continue
        cmd = evt.get("command", "") or ""
        path = _extract_file(cmd)
        if not path:
            continue

        verified.add(path)

        # For skill SKILL.md paths like /skills/critique/SKILL.md
        # extract bare skill name "critique"
        if "SKILL.md" in path:
            parts = path.split("/SKILL.md")[0].split("/")
            if parts:
                skill = parts[-1]
                verified.add(skill)
                verified.add(f"/{skill}")
        # For other paths with / in them, add the last path component as bare name
        elif "/" in path:
            verified.add(path.split("/")[-1])

    # Normalize skill references: for each /skill-name in verified, also add bare skill-name
    # This handles comparisons where "critique" (bare) is found but "/critique" was verified
    verified_normalized: set[str] = set(verified)
    for item in verified:
        if item.startswith("/") and "/" not in item[1:] and "." not in item:
            # It's a /skill-name style reference - add bare version
            verified_normalized.add(item[1:])
    return verified_normalized


def _find_comparisons(response: str) -> list[str]:
    """Find all file/skill references in comparative constructs."""
    found: list[str] = []

    # Skip standalone "skill" as it's a common word in phrases like "X skill vs Y skill"
    skip_words = {"skill", "file", "path", "code"}

    def _is_file_reference(text: str) -> bool:
        """Check if cell looks like a file/skill path, not markdown text."""
        # Must contain path indicators: /, file extension, or be /-prefixed
        if text.startswith("/"):
            return True
        if re.search(r"\.(?:py|md|json|yml|yaml|txt|SKILL)$", text, re.IGNORECASE):
            return True
        if "/" in text:
            return True
        return False

    def _is_plausible_path(text: str) -> bool:
        """Reject unrealistically long strings that are content, not paths."""
        # Real file paths are rarely > 150 chars
        if len(text) > 150:
            return False
        return True

    def _is_markdown_artifact(text: str) -> bool:
        """Check if cell is a markdown artifact (backtick-wrapped, separator, etc.)."""
        if text.startswith("`") and text.endswith("`"):
            return True
        # Table separator rows: mostly hyphens and dashes (|-------|-----|)
        if re.match(r"^[-:\s|]+$", text):
            return True
        return False

    # 1. Table rows (┌─┬─┐ format) - must be Claude box-drawing format
    # Require at least one box-drawing char AND minimum 3 chars per cell
    for line in response.splitlines():
        line = line.strip()
        if not line:
            continue
        # Must be Claude box format: contains │ or | pipe chars
        pipe_count = line.count("│") + line.count("|")
        if pipe_count < 2:
            continue
        # Require at least one box-drawing char for table format
        if "│" not in line and "┌" not in line and "└" not in line:
            continue
        # Extract cells - split on pipe and whitespace
        cells = re.split(r"[││|\s]{2,}", line)
        for cell in cells:
            cell = cell.strip("││| \t")
            if not cell:
                continue
            if _is_markdown_artifact(cell):
                continue
            # Skip single-char cells unless they start with / (skill references)
            if len(cell) < 2 and not cell.startswith("/"):
                continue
            if cell.lower() in skip_words:
                continue
            if not _is_file_reference(cell):
                continue
            if not _is_plausible_path(cell):
                continue
            found.append(cell)

    # 2. vs/versus phrases
    for m in VS_PHRASE_RE.finditer(response):
        g1, g2 = m.group(1), m.group(2)
        if g1.lower() not in skip_words and _is_file_reference(g1) and not _is_markdown_artifact(g1) and _is_plausible_path(g1):
            found.append(g1)
        if g2.lower() not in skip_words and _is_file_reference(g2) and not _is_markdown_artifact(g2) and _is_plausible_path(g2):
            found.append(g2)

    # 3. Prose comparison keywords
    for m in PROSE_COMPARE_RE.finditer(response):
        item = m.group(2)
        if item.lower() not in skip_words and _is_file_reference(item) and _is_plausible_path(item):
            found.append(item)

    return found


def check(data: dict) -> dict | None:
    """Core gate logic. Returns block dict or None (allow)."""
    response = data.get("assistant_response", "")
    if not response:
        return None

    comparisons = _find_comparisons(response)
    if not comparisons:
        return None

    _logger.debug("Found %d comparison references: %s", len(comparisons), comparisons)

    # Build verified set from tool_events in input data
    tool_events = data.get("tool_events", [])
    if not tool_events:
        # Fallback: try via evidence_store
        if EVIDENCE_AVAILABLE:
            session_id = _resolve_session_id(data)
            terminal_id = _get_terminal_id(data)
            if session_id:
                try:
                    tool_events = load_tool_events(session_id=session_id, limit=200)
                except Exception as exc:
                    _logger.warning("load_tool_events failed: %s", exc)

    verified = _build_verified_set(tool_events)

    # Also add transcript path if present — comparing transcript content
    # (e.g., "Based on the transcript") doesn't require reading the transcript
    # as a file, it's referencing the session's own accumulated history
    for key in ("transcript_path", "transcript"):
        tp = data.get(key, "")
        if tp:
            tp = tp.strip()
            if tp:
                verified.add(tp)
                # Normalize Windows backslashes and drive letter variations
                normalized = tp.replace("\\", "/")
                verified.add(normalized)
                # Also add bare filename
                verified.add(tp.split("/")[-1])

    _logger.debug("Verified files this turn: %s", verified)

    unverified = [c for c in comparisons if c not in verified]
    if not unverified:
        _logger.info("All %d comparisons verified", len(comparisons))
        return None

    _logger.warning("BLOCK: %d unverified comparisons: %s", len(unverified), unverified)

    lines = ["**Comparative Claim Without Verification Detected**\n"]
    lines.append(
        f"The response compares {len(unverified)} item(s) without evidence "
        "that all were read this turn:\n"
    )
    for item in sorted(unverified):
        lines.append(f"  - `{item}`")
    lines.append("")
    lines.append(
        "Before comparing files or skills, read each one first using "
        "Read, Grep, or Glob tools."
    )
    return {
        "allow": False,
        "reason": "\n".join(lines),
        "blocking_hook": "Stop_comparative_claim_guard.py",
    }


def _resolve_session_id(data: dict) -> str:
    for key in ("session_id", "sessionId"):
        val = data.get(key)
        if val:
            return str(val).strip()
    for key in ("session", "Session"):
        val = data.get(key)
        if isinstance(val, dict):
            return str(val.get("id", "")).strip()
    return os.environ.get("CLAUDE_SESSION_ID", "")


def _get_terminal_id(data: dict) -> str:
    for key in ("terminal_id", "terminalId"):
        val = data.get(key)
        if val:
            return str(val).strip()
    return os.environ.get("CLAUDE_TERMINAL_ID", "")


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
        if not result.get("allow", True):
            sys.exit(2)


if __name__ == "__main__":
    main()
