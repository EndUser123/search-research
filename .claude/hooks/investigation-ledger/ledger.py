"""Investigation Ledger - Hardened Implementation.

Tracks what CC actually investigates (files read, searches, executions).
Used by Stop hook to validate claims reference investigated topics.

Addresses critique concerns:
- File locking for parallel tool safety
- JSON error handling with recovery
- Platform-agnostic paths
- Graceful degradation on errors
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from collections.abc import Set
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

# Type aliases for clarity
type LedgerDict = dict[str, Any]
type FileEntry = dict[str, Any]
type SearchEntry = dict[str, Any]
type ExecutionEntry = dict[str, Any]
type TopicSet = set[str]

# Platform-specific imports
if sys.platform != "win32":
    import fcntl
else:
    fcntl = None  # Windows uses msvcrt instead

# Platform-agnostic ledger location with terminal isolation.
# Default to the workspace root inferred from this file, not the current
# working directory, so subprocesses and tests resolve the same ledger path.
_DEFAULT_PROJECT_DIR = Path(__file__).resolve().parents[3]
LEDGER_DIR = (
    Path(os.environ.get("CLAUDE_PROJECT_DIR", str(_DEFAULT_PROJECT_DIR))) / ".claude" / "data"
)


def _sanitize_terminal_key(value: str) -> str:
    """Sanitize terminal/session identifiers for filesystem-safe keys."""
    safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", value.strip())
    safe = re.sub(r"_+", "_", safe).strip("_")
    return safe


def _resolve_terminal_id() -> str:
    """Resolve terminal id with stable env/session-first precedence."""
    explicit_terminal_id = os.environ.get("CLAUDE_TERMINAL_ID", "").strip()
    if explicit_terminal_id:
        return _sanitize_terminal_key(explicit_terminal_id)

    explicit_session_id = os.environ.get("CLAUDE_SESSION_ID", "").strip().lower()
    if explicit_session_id and re.fullmatch(r"[a-f0-9\-]{36}", explicit_session_id):
        return _sanitize_terminal_key(f"session_{explicit_session_id}")

    return ""


# Terminal isolation: use terminal_detection.py for proper isolation
def _get_terminal_id() -> str:
    """Get unique terminal identifier for ledger isolation.

    Uses terminal_detection.py for consistent terminal ID across all hooks.
    This prevents lock file proliferation (PID-based fallback created 100+ leaked files).
    """
    stable_id = _resolve_terminal_id()
    if stable_id:
        return stable_id

    # Add hooks directory to path for terminal_detection import
    hooks_dir = Path(__file__).resolve().parent.parent
    if str(hooks_dir) not in sys.path:
        sys.path.insert(0, str(hooks_dir))

    try:
        from __lib.terminal_detection import detect_terminal_id

        return _sanitize_terminal_key(detect_terminal_id())
    except ImportError:
        # Fallback to CLAUDE_SESSION_ID if terminal_detection not available
        session_id = os.environ.get("CLAUDE_SESSION_ID", "")
        if session_id:
            return _sanitize_terminal_key(f"session_{session_id}")

        # Last resort: TTY/console handle (better than PID)
        try:
            if hasattr(sys.stdin, "fileno"):
                return _sanitize_terminal_key(f"tty{sys.stdin.fileno()}")
        except:
            pass

        # No generic fallback: empty string preserves degraded semantics
        # without pretending we have a stable terminal identity.
        return ""


_TERMINAL_ID = _get_terminal_id()
LEDGER_PATH = LEDGER_DIR / f"session_ledger_{_TERMINAL_ID}.json"
LOCK_PATH = LEDGER_DIR / f"session_ledger_{_TERMINAL_ID}.lock"

# Session timeout: reset ledger if older than 4 hours
SESSION_TIMEOUT_HOURS = 4


@contextmanager
def file_lock(lock_path: Path, timeout: float = 5.0) -> Any:
    """
    Cross-platform file locking with timeout.
    Prevents race conditions on parallel tool calls.
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_file = None
    start = time.time()

    try:
        lock_file = open(lock_path, "w")
        while True:
            try:
                if sys.platform == "win32":
                    import msvcrt

                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except (OSError, BlockingIOError):
                if time.time() - start > timeout:
                    # Timeout - raise instead of silent degradation
                    raise TimeoutError(f"Could not acquire lock on {lock_path} after {timeout}s")
                time.sleep(0.05)
        yield True
    finally:
        if lock_file:
            try:
                if sys.platform == "win32":
                    import msvcrt

                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            except:
                pass
            lock_file.close()

        # Clean up lock file to prevent accumulation
        try:
            if lock_path.exists():
                lock_path.unlink()
        except OSError:
            pass  # Lock cleanup failed, but lock is already released


def _get_empty_ledger() -> LedgerDict:
    """Return fresh ledger structure."""
    return {
        "session_start": datetime.now().isoformat(),
        "files_read": [],
        "searches": [],
        "executions": [],
        "topics": [],
    }


def _load_ledger() -> LedgerDict:
    """
    Load ledger with error recovery.
    Returns empty ledger on corruption/missing.
    """
    if not LEDGER_PATH.exists():
        return _get_empty_ledger()

    try:
        content = LEDGER_PATH.read_text(encoding="utf-8")
        if not content.strip():
            return _get_empty_ledger()

        ledger = json.loads(content)

        # Check session timeout
        session_start = ledger.get("session_start", "")
        if session_start:
            try:
                start_time = datetime.fromisoformat(session_start)
                age_hours = (datetime.now() - start_time).total_seconds() / 3600
                if age_hours > SESSION_TIMEOUT_HOURS:
                    return _get_empty_ledger()
            except:
                pass

        return ledger

    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as e:
        # Corrupted - start fresh, log error
        _log_error(f"Ledger corrupted, resetting: {e}")
        return _get_empty_ledger()


def _save_ledger(ledger: LedgerDict) -> bool:
    """
    Save ledger with atomic write.
    Returns False on error (graceful degradation).
    """
    try:
        LEDGER_DIR.mkdir(parents=True, exist_ok=True)

        # Atomic write: write to temp, then rename
        temp_path = LEDGER_PATH.with_suffix(".tmp")
        temp_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
        temp_path.replace(LEDGER_PATH)
        return True

    except OSError as e:
        _log_error(f"Failed to save ledger: {e}")
        return False


def _log_error(message: str):
    """Log errors to stderr (visible in hook debug output)."""
    print(f"[investigation-ledger] {message}", file=sys.stderr)


def _extract_topics(text: str) -> TopicSet:
    """
    Extract semantic topics from paths and queries.
    e.g., "src/auth/login.py" → {"src", "auth", "login"}
    """
    topics = set()

    # Split on path separators and common delimiters
    parts = re.split(r"[/\\._\-\s]+", text.lower())

    # Filter: keep meaningful parts (3+ chars, not common noise)
    noise = {
        "src",
        "lib",
        "test",
        "tests",
        "spec",
        "specs",
        "tmp",
        "temp",
        "the",
        "and",
        "for",
        "with",
        "from",
        "this",
        "that",
        "py",
        "js",
        "ts",
        "md",
        "json",
        "yaml",
        "yml",
        "txt",
        "log",
        "cfg",
        "ini",
    }

    for part in parts:
        if len(part) >= 3 and part not in noise and part.isalnum():
            topics.add(part)

    return topics


# === Public API ===


def record_file_read(path: str, content_hash: str | None = None) -> bool:
    """Record that a file was read. Returns success status."""
    with file_lock(LOCK_PATH) as locked:
        ledger = _load_ledger()

        # Avoid duplicates
        existing_paths = {f["path"] for f in ledger["files_read"]}
        if path in existing_paths:
            return True

        ledger["files_read"].append(
            {
                "path": path,
                "timestamp": datetime.now().isoformat(),
                "content_hash": content_hash or "",
            }
        )

        # Extract and add topics
        new_topics = _extract_topics(path)
        existing_topics = set(ledger["topics"])
        ledger["topics"] = list(existing_topics | new_topics)

        result = _save_ledger(ledger)

        # Log via existing infrastructure
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
            from cc_diagnostic_logger import log_tool_call

            log_tool_call(
                "investigation_ledger",
                {"action": "file_read", "path": path, "topics": list(new_topics)},
            )
        except Exception:
            pass

        return result


def record_search(query: str, results_count: int = 0) -> bool:
    """Record that a search was performed. Returns success status."""
    with file_lock(LOCK_PATH) as locked:
        ledger = _load_ledger()

        ledger["searches"].append(
            {
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "results_count": results_count,
            }
        )

        # Extract and add topics from query
        new_topics = _extract_topics(query)
        existing_topics = set(ledger["topics"])
        ledger["topics"] = list(existing_topics | new_topics)

        result = _save_ledger(ledger)

        # Log via existing infrastructure
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
            from cc_diagnostic_logger import log_tool_call

            log_tool_call(
                "investigation_ledger",
                {
                    "action": "search",
                    "query": query,
                    "results": results_count,
                    "topics": list(new_topics),
                },
            )
        except Exception:
            pass

        return result


def record_execution(command: str, exit_code: int) -> bool:
    """Record that a command was executed. Returns success status."""
    with file_lock(LOCK_PATH) as locked:
        ledger = _load_ledger()

        ledger["executions"].append(
            {
                "command": command[:500],  # Truncate long commands
                "timestamp": datetime.now().isoformat(),
                "exit_code": exit_code,
            }
        )

        result = _save_ledger(ledger)

        # Log via existing infrastructure
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
            from cc_diagnostic_logger import log_tool_call

            log_tool_call(
                "investigation_ledger",
                {"action": "execution", "command": command[:200], "exit_code": exit_code},
            )
        except Exception:
            pass

        return result


def get_investigated_topics() -> Set[str]:
    """Get all topics that have been investigated this session."""
    with file_lock(LOCK_PATH) as locked:
        ledger = _load_ledger()
        return set(ledger.get("topics", []))


def get_investigation_stats() -> dict:
    """Get summary statistics for current session."""
    with file_lock(LOCK_PATH) as locked:
        ledger = _load_ledger()

        successful_execs = sum(1 for e in ledger.get("executions", []) if e.get("exit_code") == 0)

        return {
            "files_read": len(ledger.get("files_read", [])),
            "searches": len(ledger.get("searches", [])),
            "executions": len(ledger.get("executions", [])),
            "successful_executions": successful_execs,
            "topics": ledger.get("topics", []),
        }


def calculate_confidence_ceiling() -> dict:
    """
    Calculate confidence ceiling based on investigation depth.

    Returns:
        {"ceiling": int, "tier": int|None, "reason": str}
    """
    stats = get_investigation_stats()

    files = stats["files_read"]
    searches = stats["searches"]
    successful_execs = stats["successful_executions"]
    total_execs = stats["executions"]

    # No investigation at all
    if files == 0 and searches == 0:
        return {"ceiling": 0, "tier": None, "reason": "No investigation performed"}

    # Tier 1: Comprehensive investigation with execution verification
    if files >= 3 and successful_execs >= 1:
        return {"ceiling": 95, "tier": 1, "reason": f"Tier 1: {files} files + verified execution"}

    # Tier 2: Good investigation depth
    if files >= 3 or (files >= 2 and searches >= 3):
        return {"ceiling": 85, "tier": 2, "reason": f"Tier 2: {files} files, {searches} searches"}

    # Tier 3: Moderate investigation
    if files >= 2 or (files >= 1 and searches >= 2):
        return {"ceiling": 75, "tier": 3, "reason": f"Tier 3: {files} files, {searches} searches"}

    # Tier 4: Basic investigation
    if files >= 1 or searches >= 1:
        return {"ceiling": 50, "tier": 4, "reason": f"Tier 4: {files} files, {searches} searches"}

    return {"ceiling": 0, "tier": None, "reason": "No investigation"}


def reset_ledger() -> bool:
    """Reset the ledger for a new session."""
    with file_lock(LOCK_PATH) as locked:
        return _save_ledger(_get_empty_ledger())


def get_files_read() -> list[str]:
    """Get list of file paths that have been read."""
    with file_lock(LOCK_PATH) as locked:
        ledger = _load_ledger()
        return [f["path"] for f in ledger.get("files_read", [])]
