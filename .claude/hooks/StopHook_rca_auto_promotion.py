#!/usr/bin/env python3
"""StopHook_rca_auto_promotion — TASK-002.

Automatically promotes recurring RCA patterns to bugfixes.md after threshold.

Fires only when rca_turn=True and RCA contract passed.
Queries CKS entries table for prior occurrences.
Appends to bugfixes.md on threshold match.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

CKS_DB = Path(r"P:\__csf\data\cks.db")
BUGFIXES_PATH = Path(r"P:\.claude\bugfixes.md")
STATE_DIR = Path(r"P:\.claude\state")
DEFAULT_THRESHOLD = 2


def _get_threshold() -> int:
    """Read RCA_AUTO_PROMO_THRESHOLD from environment."""
    val = os.environ.get("RCA_AUTO_PROMO_THRESHOLD", str(DEFAULT_THRESHOLD))
    try:
        return max(1, int(val))
    except ValueError:
        return DEFAULT_THRESHOLD


def _extract_rca_fields(response: str) -> dict[str, str]:
    """Extract Root Cause and Fix sections from RCA response text."""
    root_cause_match = re.search(
        r"(?i)^##\s*Root\s+Cause\s*\n(.+?)(?=^##|\Z)",
        response,
        re.MULTILINE | re.DOTALL,
    )
    fix_match = re.search(
        r"(?i)^##\s*Fix\s*\n(.+?)(?=^##|\Z)",
        response,
        re.MULTILINE | re.DOTALL,
    )
    return {
        "root_cause": (root_cause_match.group(1).strip()) if root_cause_match else "",
        "fix": (fix_match.group(1).strip()) if fix_match else "",
    }


def _escape_like(value: str) -> str:
    """Escape LIKE wildcards to prevent SQL injection."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _query_cks(root_cause: str) -> int:
    """Query CKS for prior occurrences of root cause pattern.

    Uses entries table (NOT knowledge table).
    """
    if not CKS_DB.exists():
        return 0

    escaped = _escape_like(root_cause)
    pattern = f"%{escaped}%"

    try:
        conn = sqlite3.connect(f"file:{CKS_DB}?mode=ro", uri=True, timeout=2.0)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) FROM entries
            WHERE type IN ('pattern', 'memory')
            AND LOWER(content) LIKE ?
            LIMIT 100
            """,
            (pattern,),
        )
        count = cur.fetchone()[0]
        conn.close()
        return count
    except (sqlite3.Error, OSError) as e:
        logger.warning("CKS query failed: %s", e)
        return 0


def _parse_bugfixes(bugfixes_path: Path) -> list[dict[str, str]]:
    """Parse existing bugfixes.md entries."""
    if not bugfixes_path.exists():
        return []

    entries: list[dict[str, str]] = []
    content = bugfixes_path.read_text(encoding="utf-8")

    # Parse entries separated by ## headers
    entry_blocks = re.split(r"(?=^##\s+)", content, flags=re.MULTILINE)
    for block in entry_blocks:
        if not block.strip():
            continue
        rc_match = re.search(r"Root Cause:\s*(.+?)(?:\n|$)", block)
        fix_match = re.search(r"Fix:\s*(.+?)(?:\n|$)", block)
        if rc_match and fix_match:
            entries.append(
                {
                    "root_cause": rc_match.group(1).strip(),
                    "fix": fix_match.group(1).strip(),
                }
            )
    return entries


def _is_duplicate(entry: dict[str, str], existing: list[dict[str, str]]) -> bool:
    """Check if entry already exists in bugfixes."""
    for ex in existing:
        if ex["root_cause"] == entry["root_cause"] and ex["fix"] == entry["fix"]:
            return True
    return False


def _build_entry(root_cause: str, fix: str, session_id: str) -> list[str]:
    """Build a bugfix entry lines list."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return [
        f"## {ts} [{session_id}]",
        f"Root Cause: {root_cause}",
        f"Fix: {fix}",
        "",
    ]


def _promote_to_bugfixes(
    root_cause: str,
    fix: str,
    session_id: str,
) -> bool:
    """Append entry to bugfixes.md if not duplicate. Returns True if promoted."""
    if not root_cause or not fix:
        return False

    entry = {"root_cause": root_cause, "fix": fix}
    existing = _parse_bugfixes(BUGFIXES_PATH)

    if _is_duplicate(entry, existing):
        logger.info("Duplicate entry, skipping: %s", root_cause)
        return False

    lines = _build_entry(root_cause, fix, session_id)

    BUGFIXES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(BUGFIXES_PATH, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
        if not lines[-1].endswith("\n"):
            fh.write("\n")

    logger.info("Promoted to bugfixes.md: %s", root_cause)
    return True


def _get_state(session_id: str, terminal_id: str) -> dict:
    """Load state for session."""
    state_file = STATE_DIR / f"rca_auto_promo_{terminal_id}_{session_id}.json"
    if state_file.exists():
        try:
            with open(state_file, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}
    return {}


def _save_state(session_id: str, terminal_id: str, state: dict) -> None:
    """Save state for session."""
    state_file = STATE_DIR / f"rca_auto_promo_{terminal_id}_{session_id}.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, default=str)
    except OSError:
        pass


def check(data: dict) -> dict | None:
    """Main guard — advisory only, never blocks RCA completion."""
    rca_turn = data.get("rca_turn", False)
    if not rca_turn:
        return None

    # Check if RCA contract passed (allow means no block reasons)
    rca_result = data.get("rca_contract_result")
    if rca_result is not None:
        is_valid = rca_result.get("is_valid", True)
        if not is_valid:
            return None  # Contract failed, don't promote

    session_id = data.get("session_id", "unknown")
    terminal_id = data.get("terminal_id", "unknown")

    response = data.get("response", "")
    fields = _extract_rca_fields(response)
    root_cause = fields["root_cause"]
    fix = fields["fix"]

    if not root_cause:
        return None

    # Query CKS for prior occurrences
    cks_count = _query_cks(root_cause)

    # Load local session state
    state = _get_state(session_id, terminal_id)
    local_count = state.get("local_count", 0)

    total_count = max(cks_count, local_count)

    threshold = _get_threshold()

    if total_count >= threshold:
        promoted = _promote_to_bugfixes(root_cause, fix, session_id)
        if promoted:
            # Reset local count after promotion
            state["local_count"] = 0
            _save_state(session_id, terminal_id, state)
            return {
                "allow": True,
                "systemMessage": (
                    "Recurring RCA pattern detected — promoted to bugfixes.md "
                    f"(occurrence #{total_count + 1})"
                ),
            }
    else:
        # Increment local count
        state["local_count"] = local_count + 1
        _save_state(session_id, terminal_id, state)

    return None
