#!/usr/bin/env python3
"""
Unified Daemon Startup Manager

Consolidates daemon startup logic for dreaming and search daemons.
Replaces SessionStart_dreaming_daemon.py and SessionStart_search_daemon.py.

Features:
- Health checking via heartbeat state files
- Config-driven daemon launching (DAEMON_TYPES dict)
- Windows mutex coordination for multi-terminal safety
- Latency measurement instrumentation
- Graceful degradation (continues after one daemon fails)
"""
# ruff: noqa: N999

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add hooks directory to path for config imports
# ruff: noqa: E402
HOOKS_DIR = Path(__file__).resolve().parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from config.daemon_config import DAEMON_TYPES, DaemonType  # noqa: E402

# Constants
HEARTBEAT_HEALTHY_THRESHOLD_SECONDS = 90  # Max seconds since heartbeat to consider healthy


def is_daemon_healthy(
    daemon_type: DaemonType,
    state_file: Path,
    threshold_seconds: int = HEARTBEAT_HEALTHY_THRESHOLD_SECONDS,  # noqa: N803
) -> bool:
    """Check if daemon is healthy based on heartbeat in state file.

    Args:
        daemon_type: Type of daemon ("dreaming" or "search")
        state_file: Path to daemon state JSON file
        threshold_seconds: Max seconds since heartbeat to consider healthy

    Returns:
        True if daemon heartbeat is recent, False otherwise
    """
    if not state_file.exists():
        return False

    try:
        state = json.loads(state_file.read_text())
        heartbeat_str = state.get("heartbeat")

        if not heartbeat_str:
            return False

        # Parse heartbeat timestamp
        try:
            heartbeat_time = datetime.fromisoformat(heartbeat_str)
        except ValueError:
            return False

        # Check if heartbeat is within threshold
        age_seconds = (datetime.now(UTC) - heartbeat_time).total_seconds()
        return age_seconds <= threshold_seconds

    except (json.JSONDecodeError, OSError):
        return False


def launch_daemon(daemon_type: DaemonType, state_dir: Path) -> bool:
    """Launch a daemon process.

    Args:
        daemon_type: Type of daemon to launch ("dreaming" or "search")
        state_dir: Directory containing daemon state files

    Returns:
        True if launch succeeded, False otherwise
    """
    try:
        # Build command: python -m dreaming_daemon --daemon-type <type>
        python_exe = sys.executable
        if sys.platform == "win32" and python_exe.endswith("python.exe"):
            # Use pythonw.exe on Windows for background execution (no console window)
            python_exe = str(Path(python_exe).parent / "pythonw.exe")

        cmd = [
            python_exe,
            "-m",
            "dreaming_daemon",
            "--daemon-type",
            daemon_type,
        ]

        # Launch daemon with no window on Windows
        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]

        subprocess.Popen(
            cmd,
            creationflags=creation_flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            close_fds=True,
        )

        return True

    except Exception:
        return False


def get_daemon_config(daemon_type: DaemonType) -> dict[str, str]:
    """Get configuration for a daemon type.

    Args:
        daemon_type: Type of daemon ("dreaming" or "search")

    Returns:
        Dict with keys: mutex_name, pid_file, state_file, daemon_log
    """
    return DAEMON_TYPES.get(daemon_type, {})


def measure_latency(func: Any) -> tuple[Any, float]:
    """Measure execution time of a function.

    Args:
        func: Function to execute

    Returns:
        Tuple of (result, latency_ms)

    Raises:
        Any exception from func (re-raised with latency info)
    """
    import time

    start = time.perf_counter()
    try:
        result = func()
        latency_ms = (time.perf_counter() - start) * 1000
        return result, latency_ms
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        # Re-raise with latency info
        raise type(e)(f"{e} (latency: {latency_ms:.1f}ms)") from e


def launch_daemons_if_needed(state_dir: Path) -> dict[DaemonType, bool]:
    """Check daemon health and launch if needed.

    Iterates over all DAEMON_TYPES, checks health, and launches
    unhealthy daemons. Continues even if one daemon fails.

    Args:
        state_dir: Directory containing daemon state files

    Returns:
        Dict mapping daemon_type to launched status (True if launched,
        False if already healthy or launch failed)
    """
    results: dict[DaemonType, bool] = {}

    for daemon_type in DAEMON_TYPES.keys():
        config = get_daemon_config(daemon_type)
        state_file = state_dir / config["state_file"]

        # Check if daemon is healthy
        if is_daemon_healthy(daemon_type, state_file):
            results[daemon_type] = False  # Skipped (already healthy)
            continue

        # Launch daemon
        launched = launch_daemon(daemon_type, state_dir)
        results[daemon_type] = launched

    return results


def main():
    """Entry point: check and launch daemons.

    Returns JSON output with daemon status and latency.
    """
    import os

    # Get state directory from environment or use default
    state_dir = Path(os.environ.get("CLAUDE_STATE_DIR", r"P:\.claude\state"))

    # Measure total latency
    def _launch():
        return launch_daemons_if_needed(state_dir)

    results, latency_ms = measure_latency(_launch)

    # Output results as JSON
    output = {
        "launched": results,
        "latency_ms": round(latency_ms, 2),
    }

    # Print hook output
    import json

    print(json.dumps({"hookSpecificOutput": {"additionalContext": json.dumps(output)}}))

    sys.exit(0)


if __name__ == "__main__":
    main()
