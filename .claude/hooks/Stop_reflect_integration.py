#!/usr/bin/env python3
"""
Reflect Integration Hook - Global Suggestion Logger
===================================================

Fast analysis phase: extracts signals and logs to global suggestion file.
Manual review phase: user runs /reflect to approve and apply changes.

Benefits:
- Global accumulation across all terminals and sessions
- Learning from all contexts in one place
- User controls when to review and apply
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent


def _get_suggestion_path() -> Path:
    """Get path to global suggestion file (accumulates across all terminals/sessions)."""
    return Path.home() / ".claude" / "state" / "reflect" / "suggestions.json"


def _get_lock_path() -> Path:
    """Get path to lock file for concurrent write protection."""
    return Path.home() / ".claude" / "state" / "reflect" / "suggestions.lock"


def _acquire_lock(timeout: float = 5.0) -> bool:
    """
    Acquire exclusive lock for writing suggestion file.

    Uses simple lock file with timeout for cross-platform compatibility.
    Returns True if lock acquired, False if timeout.
    """
    lock_path = _get_lock_path()
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            # Try to create lock file exclusively (fails if exists)
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return True
        except FileExistsError:
            # Lock exists, wait a bit and retry
            time.sleep(0.05)
        except OSError:
            break

    return False


def _release_lock() -> None:
    """Release the lock file."""
    lock_path = _get_lock_path()
    try:
        lock_path.unlink()
    except OSError:
        pass  # Lock already released or doesn't exist


def _log(message: str) -> None:
    """Append message to reflect log file."""
    try:
        log_file = Path.home() / ".claude" / "reflect-hook.log"
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except OSError:
        pass  # Logging failures should not break hook


def _merge_signals(existing: dict, new_signals: dict) -> dict:
    """
    Merge new signals with existing suggestions.

    Aggregates signals by skill name to accumulate findings across sessions.
    """
    merged = dict(existing)  # Start with existing

    for skill_name, signal_list in new_signals.items():
        if skill_name not in merged:
            merged[skill_name] = []
        merged[skill_name].extend(signal_list)

    return merged


def _extract_signals_fast(transcript_path: str, suggestion_path: Path) -> None:
    """
    Fast signal extraction and logging.

    Runs extract_signals and merges results with existing suggestions.
    This is the fast automated phase (~65ms).
    """
    # Try P: drive first (CSF package structure), fallback to home directory
    skill_dir = Path("P:/") / ".claude" / "skills" / "reflect"
    if not skill_dir.exists():
        skill_dir = Path.home() / ".claude" / "skills" / "reflect"

    extract_script = skill_dir / "scripts" / "extract_signals.py"

    if not extract_script.exists():
        _log(f"Extract script not found: {extract_script}")
        return

    _log("Extracting signals (global accumulation)")

    # Create output directory
    suggestion_path.parent.mkdir(parents=True, exist_ok=True)

    # Run extract_signals and capture output
    try:
        env = os.environ.copy()
        env["TRANSCRIPT_PATH"] = transcript_path
        env["SKIP_NOVELTY_CHECK"] = "1"  # Disable novelty filtering during accumulation

        result = subprocess.run(
            [sys.executable, str(extract_script)],
            env=env,
            capture_output=True,
            text=True,
            timeout=5,  # 5 second timeout (~65ms expected, 5s = 76x safety margin)
            cwd=skill_dir,
        )

        # Parse output as JSON
        try:
            new_signals = json.loads(result.stdout) if result.stdout else {}
        except json.JSONDecodeError:
            new_signals = {}

        if not new_signals:
            _log("No signals found in transcript")
            return

        # Acquire lock for read-modify-write
        if not _acquire_lock(timeout=5.0):
            _log("Failed to acquire lock, skipping signal extraction")
            return

        try:
            # Load existing suggestions and merge
            existing_signals = {}
            if suggestion_path.exists():
                try:
                    existing_signals = json.loads(suggestion_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    _log("Failed to load existing suggestions, starting fresh")

            # Merge new signals with existing
            merged_signals = _merge_signals(existing_signals, new_signals)

            # Write merged signals to suggestion file
            suggestion_path.write_text(
                json.dumps(merged_signals, indent=2),
                encoding="utf-8",
            )

            new_count = sum(len(new_signals.get(skill, [])) for skill in new_signals.keys())
            total_count = sum(len(merged_signals.get(skill, [])) for skill in merged_signals.keys())
            _log(f"Extracted {new_count} new signals, {total_count} total accumulated (global)")

        finally:
            _release_lock()

    except subprocess.TimeoutExpired:
        _log("Signal extraction timed out after 5 seconds")
    except Exception as e:
        _log(f"Signal extraction failed: {e}")


def run_reflect_hook(data: dict) -> dict | None:
    """
    Main entry point for Stop hook integration.

    Fast phase: Extract signals and log to global suggestion file.
    Manual phase: User runs /reflect to review and apply suggestions.

    Args:
        data: Stop hook payload (may contain transcript_path)

    Returns:
        None (always passes through, never blocks)
    """
    # Get global suggestion file path
    suggestion_path = _get_suggestion_path()

    # Get transcript path
    transcript_path = data.get("transcript_path", "")

    if not transcript_path:
        # No transcript available, skip
        return None

    _log(f"Extracting signals from {transcript_path}")

    # Fast signal extraction (non-blocking, ~65ms)
    _extract_signals_fast(transcript_path, suggestion_path)

    # Return immediately (no blocking)
    return None
