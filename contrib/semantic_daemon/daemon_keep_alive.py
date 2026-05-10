#!/usr/bin/env python3
"""
Daemon Keep-Alive Wrapper for Unified Semantic Daemon

This wrapper monitors the semantic daemon process and automatically restarts it
if it exits unexpectedly. It implements an idle timeout mechanism to shut down
the daemon when not in use, conserving system resources.

Features:
- Automatic daemon respawn on unexpected exit
- Idle timeout (default: 1 hour of no activity)
- Graceful shutdown on SIGTERM/SIGINT
- PID file management for process tracking
- Health monitoring with exponential backoff

Usage:
    python -m src.daemons.daemon_keep_alive [--idle-timeout SECONDS]
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Final

# ============================================================================
# Configuration
# ============================================================================

DEFAULT_IDLE_TIMEOUT: Final[int] = 3600  # 1 hour in seconds
MAX_RESPAWN_COUNT: Final[int] = 10  # Maximum respawn attempts
RESPAWN_DELAY_BASE: Final[float] = 5.0  # Base delay for exponential backoff
RESPAWN_DELAY_MAX: Final[float] = 60.0  # Maximum delay between respawns
HEALTH_CHECK_INTERVAL: Final[int] = 30  # Seconds between health checks

# State directory for PID files
STATE_DIR: Final[Path] = Path("P:\\\\\\__csf/data")

# ============================================================================
# Signal Handling
# ============================================================================

_shutdown_requested: bool = False


def signal_handler(signum: int, frame) -> None:
    """Handle shutdown signals gracefully."""
    global _shutdown_requested
    _shutdown_requested = True
    print(
        f"[Keep-Alive] Received signal {signum}, initiating graceful shutdown...", file=sys.stderr
    )


def setup_signal_handlers() -> None:
    """Register signal handlers for graceful shutdown."""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # Windows doesn't have SIGHUP, but we can try
    if hasattr(signal, "SIGHUP"):
        signal.signal(signal.SIGHUP, signal_handler)


# ============================================================================
# PID File Management
# ============================================================================


def get_pid_file_path() -> Path:
    """Get the path to the keep-alive PID file."""
    return STATE_DIR / "daemon_keep_alive.pid"


def write_pid_file() -> None:
    """Write current process PID to file."""
    pid_file = get_pid_file_path()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(os.getpid()))


def remove_pid_file() -> None:
    """Remove the keep-alive PID file."""
    pid_file = get_pid_file_path()
    pid_file.unlink(missing_ok=True)


def is_keep_alive_running() -> bool:
    """Check if another keep-alive process is already running."""
    pid_file = get_pid_file_path()
    if not pid_file.exists():
        return False

    try:
        pid = int(pid_file.read_text())
        # Check if process is running
        if sys.platform == "win32":
            import ctypes

            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_INFORMATION
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return False
        else:
            os.kill(pid, 0)  # Check if process exists
            return True
    except (OSError, ValueError, ProcessLookupError):
        # PID file is stale or invalid
        pid_file.unlink(missing_ok=True)
        return False


# ============================================================================
# Daemon Process Management
# ============================================================================


def start_daemon_process() -> subprocess.Popen | None:
    """Start the semantic daemon as a subprocess.

    Returns:
        The Popen object for the daemon process, or None if shutdown was requested.
    """
    if _shutdown_requested:
        return None

    # Use pythonw.exe on Windows to avoid console flash
    # pythonw.exe is specifically designed for GUI apps and never creates a console
    python_exe = sys.executable
    if sys.platform == "win32" and python_exe.endswith("python.exe"):
        python_exe = python_exe.replace("python.exe", "pythonw.exe")

    # Run as module to ensure proper import paths
    cmd = [python_exe, "-m", "src.daemons.unified_semantic_daemon"]

    print(f"[Keep-Alive] Starting daemon: {' '.join(cmd)}", file=sys.stderr)

    try:
        # Start daemon as subprocess
        # We capture stdout/stderr for monitoring but don't block on them
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            # Don't use DETACHED_PROCESS here - we want to monitor the child
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            close_fds=True,
        )
        print(f"[Keep-Alive] Daemon started with PID: {process.pid}", file=sys.stderr)
        return process
    except Exception as e:
        print(f"[Keep-Alive] Failed to start daemon: {e}", file=sys.stderr)
        return None


# ============================================================================
# Main Loop
# ============================================================================


def calculate_respawn_delay(attempt: int) -> float:
    """Calculate exponential backoff delay for respawn attempts.

    Args:
        attempt: The respawn attempt number (0-indexed)

    Returns:
        Delay in seconds
    """
    delay = RESPAWN_DELAY_BASE * (2**attempt)
    return min(delay, RESPAWN_DELAY_MAX)


def run_keep_alive_loop(idle_timeout: int) -> None:
    """Main keep-alive monitoring loop.

    Args:
        idle_timeout: Seconds of inactivity before shutdown
    """
    global _shutdown_requested
    discovery_file = STATE_DIR / "semantic_daemon_discovery.json"
    respawn_count = 0
    last_activity_time = time.time()

    print(f"[Keep-Alive] Starting keep-alive loop (idle_timeout={idle_timeout}s)", file=sys.stderr)

    while not _shutdown_requested:
        # Start daemon
        daemon_process = start_daemon_process()
        if not daemon_process:
            print("[Keep-Alive] Failed to start daemon, exiting keep-alive", file=sys.stderr)
            break

        # Reset respawn counter on successful start
        respawn_count = 0
        last_activity_time = time.time()

        # Monitor daemon
        while not _shutdown_requested:
            # Check if daemon is still running
            exit_code = daemon_process.poll()
            if exit_code is not None:
                # Daemon has exited
                print(f"[Keep-Alive] Daemon exited with code {exit_code}", file=sys.stderr)

                if respawn_count >= MAX_RESPAWN_COUNT:
                    print(
                        f"[Keep-Alive] Max respawn count ({MAX_RESPAWN_COUNT}) reached, giving up",
                        file=sys.stderr,
                    )
                    _shutdown_requested = True
                    break

                # Calculate respawn delay
                delay = calculate_respawn_delay(respawn_count)
                print(
                    f"[Keep-Alive] Waiting {delay:.1f}s before respawn (attempt {respawn_count + 1}/{MAX_RESPAWN_COUNT})",
                    file=sys.stderr,
                )

                time.sleep(delay)
                respawn_count += 1
                break  # Exit inner loop to respawn

            # Check idle timeout
            time_since_activity = time.time() - last_activity_time
            if time_since_activity > idle_timeout:
                print(
                    f"[Keep-Alive] Idle timeout ({idle_timeout}s) reached, shutting down",
                    file=sys.stderr,
                )
                _shutdown_requested = True
                break

            # Health check interval
            time.sleep(HEALTH_CHECK_INTERVAL)

            # Update activity time if discovery file was modified
            if discovery_file.exists():
                try:
                    mtime = discovery_file.stat().st_mtime
                    if mtime > last_activity_time:
                        last_activity_time = mtime
                        print(
                            "[Keep-Alive] Detected daemon activity, updated idle timer",
                            file=sys.stderr,
                        )
                except OSError:
                    pass

        # Cleanup if shutting down
        if _shutdown_requested:
            if daemon_process.poll() is None:
                print("[Keep-Alive] Sending SIGTERM to daemon", file=sys.stderr)
                daemon_process.terminate()
                try:
                    daemon_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    print(
                        "[Keep-Alive] Daemon did not exit gracefully, sending SIGKILL",
                        file=sys.stderr,
                    )
                    daemon_process.kill()
            break

    print("[Keep-Alive] Keep-alive loop terminated", file=sys.stderr)


# ============================================================================
# Entry Point
# ============================================================================


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Keep-alive wrapper for the unified semantic daemon"
    )
    parser.add_argument(
        "--idle-timeout",
        type=int,
        default=DEFAULT_IDLE_TIMEOUT,
        help=f"Idle timeout in seconds (default: {DEFAULT_IDLE_TIMEOUT})",
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Check if another keep-alive is already running
    if is_keep_alive_running():
        print("[Keep-Alive] Another keep-alive process is already running", file=sys.stderr)
        return 1

    # Write PID file
    write_pid_file()

    # Setup signal handlers
    setup_signal_handlers()

    try:
        # Run keep-alive loop
        run_keep_alive_loop(args.idle_timeout)
        return 0
    except KeyboardInterrupt:
        print("[Keep-Alive] Interrupted by user", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"[Keep-Alive] Fatal error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1
    finally:
        # Cleanup PID file
        remove_pid_file()


if __name__ == "__main__":
    sys.exit(main())
