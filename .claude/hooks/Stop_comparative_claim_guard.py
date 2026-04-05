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
VS_PHRASE_RE = re.compile(
    r"(?<![^\s])([\w\-./]+(?:\.(?:py|md|json|yml|yaml|txt|skILL))?)\s+(?:vs\.?|versus)\s+([\w\-./]+(?:\.(?:py|md|json|yml|yaml|txt|skILL))?)",
    re.IGNORECASE,
)

# Prose comparison keywords
PROSE_COMPARE_RE = re.compile(
    r"(?i)(unlike|compared to|comparison with|in contrast to|whereas|while\s+\w+\s+is)\s+([/\w\-.]+(?:\.(?:py|md|skILL))?)",
)


def _extract_file(cmd: str) -> str | None:
    """Extract first path-like argument from a tool command string."""
    if not cmd:
        return None
    # Skip tool name prefix (Read /path, Grep pattern /path, Glob pattern)
    parts = cmd.strip().split(None, 1)
    if len(parts) < 2:
        return None
    rest = parts[1].strip()
    # Take first whitespace-delimited token that looks like a path
    first = rest.split()[0] if rest else ""
    if not first:
        return None
    # Accept paths starting with /, ./, P:/, C:/, or containing /
    if first.startswith(("P:/", "/", "./", "C:/", "c:/", "D:/", "~")) or "/" in first:
        return first.rstrip(",")
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
        if path:
            verified.add(path)
            # Normalize: bare filename
            if "/" in path:
                verified.add(path.split("/")[-1])
            # Normalize: skill alias from /skill/SKILL.md
            if "SKILL.md" in path:
                skill = path.split("/SKILL.md")[0].lstrip("/")
                if skill:
                    verified.add(f"/{skill}")
                    verified.add(skill)

        # Grep/Glob with pattern may reference files in output -- skip output scanning
        # as it would be fragile. The command string itself is sufficient.

    return verified


def _find_comparisons(response: str) -> list[str]:
    """Find all file/skill references in comparative constructs."""
    found: list[str] = []

    # 1. Table rows (┌─┬─┐ format)
    for line in response.splitlines():
        line = line.strip()
        if not line:
            continue
        # Must look like a table cell (contains | and some content)
        pipe_count = line.count("│") + line.count("|")
        if pipe_count >= 2:
            # Extract token-like fragments
            cells = re.split(r"[││|\s]{2,}", line)
            for cell in cells:
                cell = cell.strip("││| \t")
                if not cell:
                    continue
                # Accept path-like or /skill references
                if "/" in cell or cell.startswith("/") or cell.endswith(".py") or cell.endswith(".md") or cell == "skILL.md":
                    found.append(cell)

    # 2. vs/versus phrases
    for m in VS_PHRASE_RE.finditer(response):
        found.append(m.group(1))
        found.append(m.group(2))

    # 3. Prose comparison keywords
    for m in PROSE_COMPARE_RE.finditer(response):
        found.append(m.group(2))

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
