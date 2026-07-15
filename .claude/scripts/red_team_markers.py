#!/usr/bin/env python3
"""Marker/deadline tracking for OpenCode red-team process lifecycle.

Provides atomic marker creation, removal, and scanning for processes launched
by red_team_blind_review.py. Markers survive parent-process termination so the
reaper (reap_red_team_processes.py) can kill orphaned process trees.

Marker directory: P:\\.claude\\state\\red-team-processes\\
Marker schema version: 1
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

MARKER_DIR = Path(
    os.environ.get(
        "RED_TEAM_MARKER_DIR",
        "P:/.claude/state/red-team-processes",
    )
)

MARKER_SCHEMA_VERSION = "1"


def _get_process_creation_time(pid: int) -> float | None:
    """Return the creation time (Unix epoch seconds) for a PID, or None.

    Uses psutil if available, falls back to ctypes GetProcessTimes on Windows.
    """
    try:
        import psutil

        return psutil.Process(pid).create_time()
    except Exception:
        pass

    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            class FILETIME(ctypes.Structure):
                _fields_ = [
                    ("dwLowDateTime", wintypes.DWORD),
                    ("dwHighDateTime", wintypes.DWORD),
                ]

            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not handle:
                return None
            try:
                creation = FILETIME()
                exited = FILETIME()
                kernel = FILETIME()
                user = FILETIME()
                ok = kernel32.GetProcessTimes(
                    handle,
                    ctypes.byref(creation),
                    ctypes.byref(exited),
                    ctypes.byref(kernel),
                    ctypes.byref(user),
                )
                if not ok:
                    return None
                val = (creation.dwHighDateTime << 32) | creation.dwLowDateTime
                return (val - 116444736000000000) / 1e7
            finally:
                kernel32.CloseHandle(handle)
        except Exception:
            return None

    return None


def _get_process_cmdline(pid: int) -> list[str] | None:
    """Return the command line for a PID, or None if unavailable."""
    try:
        import psutil

        return psutil.Process(pid).cmdline()
    except Exception:
        return None


def _command_fingerprint(command: list[str]) -> str:
    """Return a SHA-256 fingerprint of the command line."""
    joined = "\0".join(str(arg) for arg in command)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def marker_path(task_id: str) -> Path:
    """Return the file path for a marker with the given task_id."""
    safe_name = task_id.replace("/", "_").replace("\\", "_").replace(":", "_")
    return MARKER_DIR / f"{safe_name}.json"


def create_marker(
    task_id: str,
    reviewer: str,
    model_id: str,
    root_pid: int,
    command: list[str],
    cwd: str,
    deadline_seconds: int,
) -> dict:
    """Build a marker dict with all required fields."""
    now = time.time()
    creation_time = _get_process_creation_time(root_pid)
    return {
        "schema_version": MARKER_SCHEMA_VERSION,
        "task_id": task_id,
        "reviewer": reviewer,
        "model_id": model_id,
        "root_pid": root_pid,
        "process_creation_time": creation_time,
        "start_time": now,
        "start_time_iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now)),
        "deadline": now + deadline_seconds,
        "deadline_iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now + deadline_seconds)),
        "cwd": cwd,
        "command": [str(a) for a in command],
        "command_fingerprint": _command_fingerprint(command),
    }


def write_marker(marker: dict) -> Path:
    """Atomically write a marker to the marker directory.

    Writes to a temp file first, then os.replace() to the final path.
    Creates the marker directory if it doesn't exist.
    """
    MARKER_DIR.mkdir(parents=True, exist_ok=True)
    path = marker_path(marker["task_id"])
    tmp_path = path.with_suffix(".json.tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(marker, f, indent=2, sort_keys=True)
    os.replace(str(tmp_path), str(path))
    return path


def remove_marker(task_id: str) -> bool:
    """Remove a marker file. Returns True if removed, False if not found."""
    path = marker_path(task_id)
    try:
        path.unlink()
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


def read_marker(path: Path) -> dict | None:
    """Read and parse a marker file. Returns None on malformed JSON."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None
        return data
    except Exception:
        return None


def is_marker_expired(marker: dict, now: float | None = None) -> bool:
    """Return True if the marker's deadline has passed."""
    if now is None:
        now = time.time()
    deadline = marker.get("deadline")
    if deadline is None:
        return False
    return now >= deadline


def is_process_alive(pid: int) -> bool:
    """Return True if a process with the given PID is running."""
    try:
        import psutil

        return psutil.pid_exists(pid)
    except Exception:
        pass

    if os.name == "nt":
        try:
            import subprocess

            result = subprocess.run(
                ["tasklist.exe", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return str(pid) in (result.stdout or "")
        except Exception:
            return False

    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, OSError):
        return False


def verify_pid_creation_time(pid: int, expected_creation_time: float | None) -> bool:
    """Verify that the process at pid has the expected creation time.

    Returns False if:
    - expected_creation_time is None (can't verify)
    - the PID doesn't exist
    - the current creation time differs (PID was reused)
    """
    if expected_creation_time is None:
        return False
    actual = _get_process_creation_time(pid)
    if actual is None:
        return False
    return abs(actual - expected_creation_time) < 1.0


def verify_command_fingerprint(pid: int, expected_fingerprint: str) -> bool:
    """Verify that the current command line matches the recorded fingerprint."""
    cmdline = _get_process_cmdline(pid)
    if cmdline is None:
        return False
    return _command_fingerprint(cmdline) == expected_fingerprint


def is_interactive_opencode(marker: dict) -> bool:
    """Return True if the marker's command looks like an interactive OpenCode session.

    Interactive sessions use 'opencode' without 'run', or have no '--format' flag.
    We never want to kill interactive sessions.
    """
    command = marker.get("command", [])
    if not command:
        return True  # Can't verify — treat as interactive (safe default)

    has_run = any(arg == "run" for arg in command)
    if not has_run:
        return True

    has_format_json = "--format" in command and "json" in command
    if not has_format_json:
        return True

    return False


def kill_process_tree(pid: int) -> dict:
    """Kill the entire process tree rooted at pid. Returns status dict."""
    if os.name == "nt":
        try:
            import subprocess

            result = subprocess.run(
                ["taskkill.exe", "/PID", str(pid), "/T", "/F"],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except FileNotFoundError:
            return {"ok": False, "error": "taskkill.exe not found"}
        except Exception as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}"}
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()[:200]
            return {"ok": False, "error": f"taskkill exit {result.returncode}: {stderr}"}
        return {"ok": True, "error": None}
    else:
        try:
            import signal

            sig = getattr(signal, "SIGKILL", signal.SIGTERM)
            os.kill(pid, sig)
        except ProcessLookupError:
            return {"ok": True, "error": None}
        except OSError as e:
            return {"ok": False, "error": f"OSError: {e}"}
        return {"ok": True, "error": None}
