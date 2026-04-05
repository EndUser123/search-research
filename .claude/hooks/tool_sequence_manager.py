#!/usr/bin/env python3
from __future__ import annotations

"""
Tool Sequence Manager - Thread-safe access to current_tool_sequence.json
=========================================================================

Provides centralized, thread-safe access to the tool sequence file.
Uses file locking (fcntl on Unix, msvcrt on Windows) to prevent
race conditions when multiple hooks read/write concurrently.

Author: CSF
Version: 1.0.0
"""

import json
import sys
import threading
from datetime import UTC, datetime
from pathlib import Path

hooks_dir = Path(__file__).resolve().parent

# Platform-specific locking imports
if sys.platform == 'win32':
    import msvcrt
    fcntl = None
else:
    import fcntl
    msvcrt = None

# =============================================================================
# CONFIGURATION
# =============================================================================

STATE_DIR = hooks_dir / "session_data"
SEQUENCE_FILE = STATE_DIR / "current_tool_sequence.json"
MAX_TOOLS = 50
LOCK_TIMEOUT = 5  # seconds

# =============================================================================
# PLATFORM-SPECIFIC LOCKING
# =============================================================================

class FileLock:
    """Cross-platform file locking."""

    def __init__(self, file_obj):
        self.file_obj = file_obj
        self.is_locked = False
        self.platform = sys.platform

    def acquire(self):
        """Acquire exclusive lock on file (non-blocking)."""
        try:
            if self.platform == 'win32':
                # Windows: use msvcrt.locking with LK_NBLCK (Non-Blocking Lock)
                # Lock entire file (0 = from beginning, 1 = entire file)
                msvcrt.locking(self.file_obj.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                # Unix: use fcntl.flock with LOCK_NB (Non-Blocking)
                fcntl.flock(self.file_obj.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.is_locked = True
            return True
        except OSError:
            # Lock failed (file already locked)
            return False

    def release(self):
        """Release lock on file."""
        if not self.is_locked:
            return
        try:
            if self.platform == 'win32':
                msvcrt.locking(self.file_obj.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(self.file_obj.fileno(), fcntl.LOCK_UN)
            self.is_locked = False
        except OSError:
            pass  # Best effort release

    def __enter__(self):
        return self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


# =============================================================================
# TOOL SEQUENCE MANAGER
# =============================================================================

class ToolSequenceManager:
    """
    Thread-safe manager for tool sequence file.

    Usage:
        # Append a tool entry
        ToolSequenceManager.append({
            "name": "Read",
            "timestamp": datetime.now(UTC).isoformat(),
            "file_path": "path/to/file.py"
        })

        # Get recent tools
        tools = ToolSequenceManager.get_recent(count=10)

        # Get all tools
        all_tools = ToolSequenceManager.get_all()

        # Clear sequence (new session)
        ToolSequenceManager.clear()
    """

    # Class-level lock for thread safety within process
    _process_lock = threading.Lock()

    @classmethod
    def _ensure_directory(cls):
        """Ensure state directory exists."""
        STATE_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _load_raw(cls) -> dict:
        """
        Load raw sequence data with file locking.
        Returns empty dict if file doesn't exist or is invalid.
        """
        cls._ensure_directory()

        if not SEQUENCE_FILE.exists():
            return {"tools": [], "session_id": ""}

        try:
            with open(SEQUENCE_FILE, encoding='utf-8') as f:
                lock = FileLock(f)

                # Try to acquire lock with limited retries (fail fast for hook perf)
                for _ in range(3):  # 3 attempts, ~30ms total
                    if lock.acquire():
                        try:
                            content = f.read()
                            if content.strip():
                                return json.loads(content)
                        finally:
                            lock.release()
                    import time
                    time.sleep(0.01)

                # Lock contention - return empty (fail open)
                return {"tools": [], "session_id": ""}

        except (json.JSONDecodeError, OSError):
            return {"tools": [], "session_id": ""}

    @classmethod
    def _save_raw(cls, data: dict) -> bool:
        """
        Save sequence data with file locking.
        Returns True if successful, False otherwise.
        """
        cls._ensure_directory()

        try:
            with open(SEQUENCE_FILE, 'w', encoding='utf-8') as f:
                lock = FileLock(f)

                if not lock.acquire():
                    return False  # Could not acquire lock

                try:
                    json.dump(data, f, indent=2)
                    return True
                finally:
                    lock.release()

        except OSError:
            return False

    @classmethod
    def append(cls, tool_entry: dict, session_id: str = "") -> bool:
        """
        Append a tool entry to the sequence.

        Args:
            tool_entry: Dict with at least "name" and "timestamp" keys
            session_id: Current session ID (resets if different from stored)

        Returns:
            True if successful, False otherwise
        """
        with cls._process_lock:
            try:
                data = cls._load_raw()

                # Reset session if different
                if session_id and data.get("session_id") != session_id:
                    data["tools"] = []

                # Append new tool
                data["tools"].append(tool_entry)
                data["session_id"] = session_id

                # Trim to max size
                if len(data["tools"]) > MAX_TOOLS:
                    # Log truncation (optional: could write to a diagnostic log)
                    data["tools"] = data["tools"][-MAX_TOOLS:]

                data["updated"] = datetime.now(UTC).isoformat()

                return cls._save_raw(data)

            except Exception:
                return False

    @classmethod
    def get_recent(cls, count: int = 10) -> list[dict]:
        """
        Get the most recent tool entries.

        Args:
            count: Maximum number of entries to return

        Returns:
            List of tool entry dicts (empty if error)
        """
        with cls._process_lock:
            try:
                data = cls._load_raw()
                tools = data.get("tools", [])
                return tools[-count:] if count > 0 else tools
            except Exception:
                return []

    @classmethod
    def get_all(cls) -> dict:
        """
        Get all sequence data.

        Returns:
            Dict with "tools", "session_id", and "updated" keys
        """
        with cls._process_lock:
            try:
                return cls._load_raw()
            except Exception:
                return {"tools": [], "session_id": ""}

    @classmethod
    def clear(cls, session_id: str = "") -> bool:
        """
        Clear the sequence (start new session).

        Args:
            session_id: New session ID to set

        Returns:
            True if successful, False otherwise
        """
        with cls._process_lock:
            try:
                data = {
                    "tools": [],
                    "session_id": session_id,
                    "updated": datetime.now(UTC).isoformat()
                }
                return cls._save_raw(data)
            except Exception:
                return False


# =============================================================================
# CONVENIENCE FUNCTIONS FOR BACKWARD COMPATIBILITY
# =============================================================================

def load_tool_sequence() -> list[dict]:
    """
    Load current session's tool sequence.
    Backward compatibility wrapper for existing hooks.
    """
    return load_tool_sequence_filtered()


def load_tool_sequence_filtered(
    session_id: str = "",
    terminal_id: str = "",
    require_scoped_metadata: bool = False,
) -> list[dict]:
    """Load tool sequence with optional session/terminal filtering."""
    data = ToolSequenceManager.get_all()
    tools = data.get("tools", [])

    if not isinstance(tools, list):
        return []

    effective_session = (session_id or "").strip()
    effective_terminal = (terminal_id or "").strip()

    if not effective_session:
        effective_session = str(data.get("session_id", "")).strip()

    filtered: list[dict] = []
    for tool in tools:
        if not isinstance(tool, dict):
            continue

        tool_terminal = str(tool.get("terminal_id", "")).strip()
        tool_session = str(tool.get("session_id", "")).strip()

        if effective_terminal:
            if require_scoped_metadata and not tool_terminal:
                continue
            if tool_terminal and tool_terminal != effective_terminal:
                continue

        if effective_session:
            if require_scoped_metadata and not tool_session:
                continue
            if tool_session and tool_session != effective_session:
                continue

        filtered.append(tool)

    return filtered


def get_recent_tool_sequence(count: int = 10) -> list[dict]:
    """Get recent tool entries. Backward compatibility wrapper."""
    return ToolSequenceManager.get_recent(count)


# =============================================================================
# CLI / DIRECT EXECUTION
# =============================================================================

def main():
    """CLI interface for testing and manual operations."""
    import argparse

    parser = argparse.ArgumentParser(description="Tool Sequence Manager")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Status command
    subparsers.add_parser('status', help='Show current sequence status')

    # Get command
    get_parser = subparsers.add_parser('get', help='Get tools')
    get_parser.add_argument('-n', '--count', type=int, default=10,
                          help='Number of recent tools (default: 10)')

    # Clear command
    subparsers.add_parser('clear', help='Clear sequence')

    # Test lock command
    subparsers.add_parser('test-lock', help='Test file locking')

    args = parser.parse_args()

    if args.command == 'status':
        data = ToolSequenceManager.get_all()
        print(f"Session ID: {data.get('session_id', 'N/A')}")
        print(f"Tool count: {len(data.get('tools', []))}")
        print(f"Last updated: {data.get('updated', 'N/A')}")

    elif args.command == 'get':
        tools = ToolSequenceManager.get_recent(args.count)
        for i, tool in enumerate(tools, 1):
            print(f"{i}. {tool.get('name', 'Unknown')} @ {tool.get('timestamp', 'N/A')}")

    elif args.command == 'clear':
        if ToolSequenceManager.clear():
            print("Sequence cleared")
        else:
            print("Failed to clear sequence")

    elif args.command == 'test-lock':
        print("Testing file locking...")
        # Try concurrent access
        import concurrent.futures

        def write_worker(n):
            return ToolSequenceManager.append({
                "name": f"Test{n}",
                "timestamp": datetime.now(UTC).isoformat()
            }, session_id="test")

        def read_worker(n):
            return len(ToolSequenceManager.get_recent())

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Submit 5 writes and 5 reads concurrently
            futures = []
            for i in range(5):
                futures.append(executor.submit(write_worker, i))
                futures.append(executor.submit(read_worker, i))

            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # Verify result
        final_count = len(ToolSequenceManager.get_all().get("tools", []))
        print(f"Final tool count: {final_count} (expected: 5)")
        print(f"All operations returned: {results}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
