#!/usr/bin/env python3
"""
SessionEnd Hook: Write Session Summary

Fires on session end. Reads session_start.txt for duration,
aggregates activity, and writes summary to terminal-scoped state file.

Terminal-scoped paths prevent cross-terminal collision.
Atomic write (temp file + rename) prevents torn writes.
File locking prevents concurrent write races.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import tempfile
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

HOOKS_DIR = Path(__file__).resolve().parent
STATE_DIR = HOOKS_DIR.parent / "state" / "session_tldr"

# Import terminal_id resolver from hook_base (centralized source of truth)
_get_terminal_id: Callable[[dict | None], str] | None = None
try:
    sys.path.insert(0, str(HOOKS_DIR / "__lib"))
    from hook_base import get_terminal_id as _get_terminal_id_func
    _get_terminal_id = _get_terminal_id_func
except ImportError as exc:
    # Fallback if hook_base unavailable - log for diagnostics
    _logger = logging.getLogger(__name__)
    _logger.warning(
        "SessionEnd_tldr: hook_base.get_terminal_id unavailable, "
        "using terminal_unknown fallback. ImportError: %s",
        exc,
    )
    _get_terminal_id = None

# Secret patterns for credential redaction (matches PreToolUse/secret_scanner.py)
_SECRET_PATTERNS = [
    r"sk-[a-zA-Z0-9]{32,}",  # OpenAI key
    r"AKIA[0-9A-Z]{16}",  # AWS access key
    r"ghp_[a-zA-Z0-9]{36}",  # GitHub token
    r"xoxb-[0-9]{10,}-[0-9]{10,}-[a-zA-Z0-9]{24}",  # Slack token
    r"AAAA[a-zA-Z0-9_-]{28,}",  # Firebase key
    r"(?i)(api[_-]?key|apikey)\s*[=:]\s*[\"']?[a-zA-Z0-9_\-]{20,}[\"']?",  # API key
    r"(?i)(secret[_-]?key|password|pass|secret)\s*[=:]\s*[\"']?[a-zA-Z0-9_\-]{12,}[\"']?",  # Secret/password
    r"(?i)(token|auth[_-]?token)\s*[=:]\s*[\"']?[a-zA-Z0-9_\-]{20,}[\"']?",  # Token
    r"Bearer\s+[a-zA-Z0-9_\-]{20,}",  # Bearer token
]


def _redact_secrets(text: str) -> str:
    """Redact embedded secrets from text (file paths, etc.)."""
    if not text:
        return text
    for pattern in _SECRET_PATTERNS:
        text = re.sub(pattern, "[REDACTED]", text, flags=re.IGNORECASE)
    return text


# Import file lock — fail open if unavailable (best-effort)
try:
    sys.path.insert(0, str(HOOKS_DIR / "__lib"))
    from file_lock import FileLock
except ImportError:

    class FileLock:
        def __init__(self, *_a: object, **_k: object) -> None:
            pass

        def __enter__(self) -> FileLock:
            return self

        def __exit__(self, *_a: object) -> None:
            pass


def _resolve_terminal_id(data: dict | None = None) -> str:
    """Resolve terminal_id using centralized hook_base implementation.

    Uses get_terminal_id() from hook_base which provides:
    - Priority: hook input > env vars > console detection > PID+timestamp
    - Returns empty string if all detection fails (caller handles fallback)
    """
    if _get_terminal_id is not None:
        result = _get_terminal_id(data)
        if result:
            return result
    # Fallback only if all detection methods fail
    return "terminal_unknown"


def _safe_id(value: str) -> str:
    """Sanitize terminal_id for use in file paths."""
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


def _get_state_path(terminal_id: str) -> Path:
    """Return terminal-scoped path to last session summary."""
    safe_tid = _safe_id(terminal_id)
    return STATE_DIR / f"{safe_tid}_last_session.md"


def _get_session_start_path(terminal_id: str) -> Path:
    """Return terminal-scoped path to session start timestamp."""
    safe_tid = _safe_id(terminal_id)
    return STATE_DIR / f"{safe_tid}_session_start.txt"


def _calculate_duration(start_iso: str | None) -> str | None:
    """Calculate human-readable duration from ISO start timestamp."""
    if not start_iso:
        return None
    try:
        start = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    try:
        end = datetime.now(UTC)
        delta = end - start
        total_seconds = delta.total_seconds()
        if total_seconds < 0:
            return "unknown (clock skew)"
        hours, remainder = divmod(int(total_seconds), 3600)
        minutes, _ = divmod(remainder, 60)
        if hours > 0:
            return f"~{hours}h {minutes}m"
        return f"~{minutes}m"
    except Exception:
        return None


def _get_ended_at() -> str:
    """Return current timestamp in ISO format."""
    return datetime.now(UTC).isoformat()


def _collect_session_activity() -> dict:
    """Collect session activity from available sources.

    Returns dict with keys: files_changed, accomplishments, open_items.
    Falls back to breadcrumbs/ledger if available.
    """
    result = {"files_changed": [], "accomplishments": [], "open_items": []}

    # Try to read from breadcrumb/state files
    state_base = HOOKS_DIR.parent / "state"
    terminal_id = _resolve_terminal_id(None)
    safe_tid = _safe_id(terminal_id)

    # Look for recent file modifications in breadcrumb logs
    try:
        breadcrumbs_dir = state_base / "breadcrumb"
        if breadcrumbs_dir.exists():
            recent_files: set[str] = set()
            # Scan recent breadcrumb files for file operations
            for f in sorted(
                breadcrumbs_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True
            )[:20]:
                if f.is_file() and safe_tid in f.name:
                    try:
                        content = f.read_text(encoding="utf-8", errors="ignore")
                        # Extract file paths mentioned
                        for line in content.splitlines():
                            if any(op in line for op in ["Edit:", "Write:", "Bash:", "Read:"]):
                                # Try to extract file paths
                                parts = line.split(":", 2)
                                if len(parts) >= 2:
                                    path_part = parts[1].strip()
                                    if path_part and path_part not in ("", "None"):
                                        recent_files.add(_redact_secrets(path_part))
                    except Exception:
                        continue
            result["files_changed"] = sorted(recent_files)[:10]
    except Exception as e:
        logger.warning("SessionEnd_tldr: failed to collect breadcrumb activity: %s", e)

    # Try investigation-ledger for accomplishments
    try:
        ledger_path = state_base / "investigation-ledger" / "ledger.db"
        if ledger_path.exists():
            import sqlite3

            conn = sqlite3.connect(str(ledger_path))
            cursor = conn.execute(
                "SELECT action FROM events WHERE terminal_id = ? ORDER BY timestamp DESC LIMIT 50",
                (terminal_id,),
            )
            actions = [row[0] for row in cursor.fetchall() if row[0]]
            conn.close()

            # Deduplicate and limit
            unique_actions = list(dict.fromkeys(actions))[:10]
            result["accomplishments"] = [f"- {_redact_secrets(a)}" for a in unique_actions if a]
    except Exception as e:
        logger.warning("SessionEnd_tldr: failed to read investigation ledger: %s", e)

    return result


def _atomic_write(path: Path, content: str) -> None:
    """Write content to path atomically: temp file + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path_str = tempfile.mkstemp(dir=path.parent, suffix=".tmp", prefix=".tldr_")
    try:
        tmp_path = Path(tmp_path_str)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(str(tmp_path), str(path))
    except Exception:
        # Clean up temp file on failure
        try:
            os.unlink(tmp_path_str)
        except Exception:
            pass
        raise


def _write_summary(terminal_id: str, start_iso: str | None, ended_at: str, activity: dict) -> None:
    """Write session summary atomically with file locking."""
    summary_path = _get_state_path(terminal_id)
    lock_path = summary_path.with_suffix(".lock")

    duration = _calculate_duration(start_iso)

    # Build markdown summary
    lines = [
        "## Session Summary",
        f"**When:** {start_iso or 'unknown'}",
        f"**Ended:** {ended_at}",
    ]
    if duration:
        lines.append(f"**Duration:** {duration}")

    if activity["accomplishments"]:
        lines.append("**Accomplished:**")
        lines.extend(activity["accomplishments"])
    else:
        lines.append("**Accomplished:** - (no activity recorded)")

    if activity["files_changed"]:
        lines.append("**Files changed:**")
        lines.extend(activity["files_changed"])
    else:
        lines.append("**Files changed:** - (none)")

    if activity["open_items"]:
        lines.append("**Open items:**")
        lines.extend(activity["open_items"])

    summary = "\n".join(lines) + "\n"

    try:
        with FileLock(lock_path, timeout=30.0):
            _atomic_write(summary_path, summary)
    except (TimeoutError, OSError) as e:
        # Lock timeout or write failure — best effort, don't block session end
        # but at least surface the failure for observability
        logger.warning("SessionEnd_tldr: failed to write summary to %s: %s", summary_path, e)


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        data: dict = {}
    else:
        try:
            data = json.loads(raw.lstrip("\ufeff"))
        except json.JSONDecodeError:
            data = {}

    terminal_id = _resolve_terminal_id(data)
    session_start_path = _get_session_start_path(terminal_id)

    # Read session start time
    start_iso: str | None = None
    if session_start_path.exists():
        try:
            start_iso = session_start_path.read_text(encoding="utf-8").strip()
        except Exception:
            pass

    ended_at = _get_ended_at()
    activity = _collect_session_activity()

    _write_summary(terminal_id, start_iso, ended_at, activity)

    # Always exit 0 — best-effort summary, never block session end
    print("{}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
