#!/usr/bin/env python3
"""
Dreaming Daemon - Async Background Service (T-008)

Background daemon that analyzes principle-events.jsonl to generate insights.
Uses async architecture for I/O-bound operations (file reads, JSON parsing).

Architecture:
- Windows mutex + PID file for singleton enforcement
- Offset-based JSONL tailing with rotation detection
- Sliding window aggregation for pattern detection
- Machine-readable insights (JSON) + optional markdown
- Heartbeat for health monitoring

Usage:
    python dreaming-daemon.py

Integration:
- Started by SessionStart_dreaming_daemon.py hook
- Reads from P:/.claude/logs/principle-events.jsonl
- Writes to P:/.claude/state/dreaming-insights.{json,md}
- State at P:/.claude/state/dreaming-daemon-state.json
"""

from __future__ import annotations

import asyncio
import atexit
import logging
import signal
import sys
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock

from dreaming_aggregator import InsightsGenerator

# Import core modules
from dreaming_config import load_config
from dreaming_insights import DreamingInsights, Pattern, PrincipleStats
from dreaming_mutex import acquire_singleton, release_singleton
from dreaming_state import DreamingState, load_state, save_state
from dreaming_tailer import JSONLTailer
from dreaming_writer import write_insights

# Import daemon configuration
from config.daemon_config import DAEMON_TYPES, get_daemon_config

# Constants
HOOKS_DIR = Path(__file__).resolve().parent
LOGS_DIR = HOOKS_DIR / "logs"
STATE_DIR = HOOKS_DIR / "state"

# Paths (will be configured based on daemon_type)
# Defaults for backward compatibility
LOG_PATH = Path("P:/.claude/logs/principle-events.jsonl")
STATE_FILE = STATE_DIR / "dreaming-daemon-state.json"  # type: ignore
PID_FILE = STATE_DIR / "dreaming-daemon.pid"  # type: ignore
DAEMON_LOG = LOGS_DIR / "dreaming-daemon.log"  # type: ignore

# Default configuration
DEFAULT_POLL_INTERVAL = 60  # seconds
DEFAULT_WINDOW_SECONDS = 3600  # 1 hour
DEFAULT_HEARTBEAT_INTERVAL = 60  # seconds (T-009)
DEFAULT_ZOMBIE_TIMEOUT = 180  # seconds (T-009)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(DAEMON_LOG), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Global shutdown flag and state lock (T-009)
_shutdown_requested = False
_state_lock = Lock()  # Protects state file writes for atomicity


def _check_for_zombie_daemon(config: dict) -> bool:
    """
    Check for stale mutex + heartbeat indicating zombie daemon (T-009).

    Enhanced with canonical PID preservation (T-002): Checks if stale PID is
    the legitimate daemon's canonical PID before attempting cleanup.

    Args:
        config: Configuration dict with zombie_timeout_seconds.

    Returns:
        True if zombie detected and cleaned up, False otherwise.
    """
    zombie_timeout = config.get("zombie_timeout_seconds", DEFAULT_ZOMBIE_TIMEOUT)

    try:
        # Check if state file exists with stale heartbeat
        state = load_state(STATE_FILE)

        if state.heartbeat:
            try:
                heartbeat_time = datetime.fromisoformat(state.heartbeat)
                age_seconds = (datetime.now(UTC) - heartbeat_time).total_seconds()

                if age_seconds > zombie_timeout:
                    # Zombie detected - stale mutex
                    logger.warning(
                        f"Zombie daemon detected: heartbeat is {age_seconds:.0f}s old "
                        f"(timeout: {zombie_timeout}s)"
                    )

                    # CRITICAL: Check if stale PID is the canonical PID (T-002)
                    # If the stale PID matches the canonical PID, DO NOT cleanup -
                    # it might be the legitimate daemon temporarily unresponsive
                    if state.canonical_pid != 0:
                        logger.info(
                            f"Checking stale PID against canonical PID: "
                            f"canonical_pid={state.canonical_pid}"
                        )

                        # Read PID file to get the stale PID
                        if PID_FILE.exists():
                            try:
                                stale_pid = int(PID_FILE.read_text().strip())

                                if stale_pid == state.canonical_pid:
                                    # Stale PID IS the canonical PID - DO NOT CLEANUP
                                    logger.error(
                                        f"CRITICAL: Stale PID {stale_pid} matches canonical PID. "
                                        f"REFUSING to cleanup - legitimate daemon may be temporarily "
                                        f"unresponsive. Age: {age_seconds:.0f}s"
                                    )
                                    return False
                                else:
                                    logger.info(
                                        f"Stale PID {stale_pid} != canonical PID {state.canonical_pid}. "
                                        f"Safe to cleanup zombie."
                                    )
                            except (OSError, ValueError) as e:
                                logger.warning(f"Could not read stale PID from PID file: {e}")
                                # If we can't read the stale PID, proceed with caution
                    else:
                        logger.info("No canonical PID set, proceeding with zombie cleanup")

                    # Force cleanup of stale mutex
                    logger.info("Cleaning up zombie daemon mutex...")
                    success, error = acquire_singleton(str(PID_FILE), force=True)

                    if success:
                        logger.info("Zombie daemon mutex cleaned up successfully")
                        # CRITICAL: Release mutex immediately after cleanup
                        # If we hold the mutex, the subsequent normal acquisition will
                        # detect this process as "already running"
                        release_singleton(str(PID_FILE))
                        logger.info("Released zombie cleanup mutex for normal acquisition")
                        return True
                    else:
                        logger.error(f"Failed to clean zombie mutex: {error}")
                        return False

            except (ValueError, OSError) as e:
                logger.error(f"Error parsing heartbeat timestamp: {e}")
                return False

    except Exception as e:
        logger.error(f"Error checking for zombie daemon: {e}")

    return False


def _setup_signal_handlers() -> None:
    """
    Setup signal handlers for graceful shutdown on Windows (T-009).

    Multi-layered cleanup approach:
    1. Primary: atexit handler (fires on normal exit, most reliable)
    2. Secondary: Periodic refresh check in main loop
    3. Tertiary: Best-effort signal handlers (set shutdown flag)
    """
    # Register cleanup on exit (PRIMARY - most reliable on Windows)
    atexit.register(_cleanup_on_exit)

    # Set signal handler for shutdown (TERTIARY - best-effort only)
    def _signal_handler(signum, frame):
        """Handle shutdown signals."""
        global _shutdown_requested
        _shutdown_requested = True
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")

    # Register for SIGINT (Ctrl+C) - works on Windows
    signal.signal(signal.SIGINT, _signal_handler)

    # On Windows, we can also use SIGBREAK (Ctrl+Break)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, _signal_handler)


def _cleanup_on_exit() -> None:
    """
    Cleanup function called on process exit (T-009).

    This is the PRIMARY cleanup mechanism on Windows, registered via atexit.
    More reliable than signal handlers which may not fire.
    """
    logger.info("Daemon exiting, releasing singleton lock...")
    try:
        # Mark shutdown in state before releasing mutex
        with _state_lock:
            try:
                state = load_state(STATE_FILE)
                state.shutdown = True
                save_state(state, STATE_FILE)
            except Exception as e:
                logger.error(f"Error marking shutdown in state: {e}")

        # Release the singleton mutex
        release_singleton(str(PID_FILE))
        logger.info("Cleanup completed successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


async def _load_config_async() -> dict:
    """Load configuration asynchronously."""
    # For now, config loading is synchronous (fast operation)
    # In the future, this could be extended to load from remote sources
    return load_config()


async def _update_heartbeat_and_state_async(
    state: DreamingState, offset: int | None = None, current_file: str | None = None
) -> None:
    """
    Update heartbeat and state in a single atomic write operation (T-009).

    Args:
        state: DreamingState instance to update.
        offset: Optional new offset value.
        current_file: Optional new current_file value.
    """
    with _state_lock:
        try:
            # Update heartbeat
            state.heartbeat = datetime.now(UTC).isoformat()

            # Update offset and current_file if provided
            if offset is not None:
                state.offset = offset
            if current_file is not None:
                state.current_file = current_file

            # Atomic write: heartbeat + state updated together
            # This prevents zombie detection from reading stale heartbeat
            # while daemon is alive
            save_state(state, STATE_FILE)

        except Exception as e:
            logger.error(f"Error updating heartbeat and state: {e}")
            # Don't crash on heartbeat update errors


async def _read_events_async(tailer: JSONLTailer) -> list[dict]:
    """Read new events from JSONL tailer asynchronously."""
    # The tailer's read_new_events() is synchronous (file I/O)
    # We wrap it in async to maintain consistent async architecture
    events = list(tailer.read_new_events())
    return events


async def _aggregate_events_async(generator: InsightsGenerator, events: list[dict]) -> dict:
    """Aggregate events and generate insights asynchronously."""
    # Event aggregation is CPU-bound (sync)
    # We wrap it in async to maintain consistent async architecture
    for event in events:
        generator.add_event(event)

    insights = generator.generate_insights()
    return insights


async def _write_insights_async(insights_data: dict, config: dict) -> None:
    """Write insights to files asynchronously."""
    # Create DreamingInsights object from aggregator output
    now = datetime.now(UTC).isoformat()

    # Convert aggregator insights to DreamingInsights format
    principle_stats = []
    for principle, count in insights_data.get("principle_counts", {}).items():
        # For now, use current timestamp for first_seen/last_seen
        # In production, track these properly from event timestamps
        principle_stats.append(
            PrincipleStats(principle=principle, count=count, first_seen=now, last_seen=now)
        )

    patterns = []
    if insights_data.get("top_principle"):
        patterns.append(
            Pattern(
                pattern_type="high_violation_principle",
                description=f"Principle '{insights_data['top_principle']}' has {insights_data['top_principle_count']} violations",
                examples=[insights_data["top_principle"]],
            )
        )

    recommendations = []
    if insights_data.get("high_violation_sessions"):
        recommendations.append(
            f"Review sessions with high violation counts: {list(insights_data['high_violation_sessions'].keys())}"
        )

    insights = DreamingInsights(
        generated_at=now,
        total_events=insights_data.get("total_events", 0),
        principle_stats=principle_stats,
        patterns=patterns,
        recommendations=recommendations,
    )

    # Write insights (sync I/O, wrapped in async)
    write_insights(insights, config)


async def _daemon_loop_async(
    config: dict, state: DreamingState, tailer: JSONLTailer, generator: InsightsGenerator
) -> None:
    """
    Main async daemon loop with Windows-specific reliability (T-009).

    Features:
    - Atomic heartbeat + state updates
    - Error wrapping with try/except
    - Exponential backoff on repeated errors
    - Periodic refresh check (SECONDARY cleanup mechanism)
    """
    global _shutdown_requested

    poll_interval = config.get("poll_interval_seconds", DEFAULT_POLL_INTERVAL)

    logger.info(f"Daemon loop started with {poll_interval}s poll interval")

    # Track consecutive errors for exponential backoff
    consecutive_errors = 0
    max_backoff = 300  # 5 minutes max backoff

    while not _shutdown_requested:
        try:
            # Step 1: Read new events (async file I/O wrapper)
            events = await _read_events_async(tailer)

            if events:
                logger.info(f"Processing {len(events)} new events")

                # Step 2: Aggregate events (CPU-bound, wrapped in async)
                insights_data = await _aggregate_events_async(generator, events)

                # Step 3: Write insights (async file I/O wrapper)
                await _write_insights_async(insights_data, config)

                logger.info(f"Generated insights: {insights_data['total_events']} total events")

            # Step 4: Update heartbeat with atomic state write (T-009)
            await _update_heartbeat_and_state_async(state)

            # Step 5: Periodic refresh check (SECONDARY cleanup mechanism)
            # This ensures cleanup even if atexit fails
            if _shutdown_requested:
                logger.info("Shutdown requested, breaking loop...")
                break

            # Step 6: Sleep for poll interval (async sleep)
            await asyncio.sleep(poll_interval)

            # Reset error counter on success
            consecutive_errors = 0

        except Exception as e:
            consecutive_errors += 1
            logger.error(f"Error in daemon loop (error #{consecutive_errors}): {e}", exc_info=True)

            # Exponential backoff on repeated errors
            backoff_time = min(2**consecutive_errors, max_backoff)
            logger.info(f"Backing off for {backoff_time}s before retry...")
            await asyncio.sleep(backoff_time)

    logger.info("Daemon loop terminated gracefully")


async def main_async(daemon_type: str = "dreaming", daemon_config: dict | None = None) -> int:
    """
    Main async entry point for dreaming daemon (T-009).

    Startup sequence:
    1. Use daemon config (passed from main)
    2. Check for zombie daemon (stale mutex + heartbeat)
    3. Acquire singleton lock with daemon-specific mutex name
    4. Load configuration
    5. Load or initialize state
    6. Initialize JSONL tailer
    7. Initialize insights generator
    8. Enter main async loop

    Args:
        daemon_type: Type of daemon to run ("dreaming" or "search"). Defaults to "dreaming".
        daemon_config: Daemon configuration dict (mutex_name, pid_file, etc.). If None, loads from get_daemon_config.

    Raises:
        ValueError: If daemon_type is not in DAEMON_TYPES.
    """
    global _shutdown_requested

    # Load daemon config if not provided
    if daemon_config is None:
        daemon_config = get_daemon_config(daemon_type)

    logger.info(f"Dreaming daemon starting as '{daemon_type}'...")

    # Step 1: Load configuration first (needed for zombie detection)
    config = await _load_config_async()
    logger.info(f"Configuration loaded: {config}")

    # Step 2: Check for zombie daemon (T-009)
    zombie_cleaned = _check_for_zombie_daemon(config)
    if zombie_cleaned:
        logger.info("Zombie daemon cleaned up, continuing startup...")

    # Step 3: Acquire singleton lock with daemon-specific mutex name (sync, must happen before async loop)
    mutex_name = daemon_config["mutex_name"]
    pid_file = STATE_DIR / daemon_config["pid_file"]
    success, error_msg = acquire_singleton(str(pid_file), mutex_name=mutex_name)
    if not success:
        logger.error(f"Failed to acquire singleton lock: {error_msg}")
        return 1

    logger.info("Singleton lock acquired successfully")

    # Step 4: Load or initialize state (sync, fast)
    state = load_state(STATE_FILE)

    # Reset shutdown flag on startup
    state.shutdown = False

    # Initial heartbeat update (atomic)
    await _update_heartbeat_and_state_async(state)

    logger.info(f"State loaded: offset={state.offset}, heartbeat={state.heartbeat}")

    # Step 5: Initialize JSONL tailer (sync, fast)
    try:
        tailer = JSONLTailer(
            log_path=LOG_PATH,
            max_size_mb=config.get("rotation_max_size_mb", 50),
            retention_days=config.get("rotation_retention_days", 30),
        )
        logger.info(f"JSONL tailer initialized for {LOG_PATH}")
    except Exception as e:
        logger.error(f"Failed to initialize JSONL tailer: {e}")
        release_singleton(str(PID_FILE))
        return 1

    # Step 6: Initialize insights generator (sync, fast)
    try:
        window_seconds = config.get("window_seconds", DEFAULT_WINDOW_SECONDS)
        generator = InsightsGenerator(window_seconds=window_seconds)
        logger.info(f"Insights generator initialized with {window_seconds}s window")
    except Exception as e:
        logger.error(f"Failed to initialize insights generator: {e}")
        release_singleton(str(PID_FILE))
        return 1

    # Step 7: Enter main async loop
    try:
        await _daemon_loop_async(config, state, tailer, generator)
    except Exception as e:
        logger.error(f"Fatal error in daemon loop: {e}", exc_info=True)
        return 1
    finally:
        # Ensure cleanup happens even if loop crashes
        logger.info("Dreaming daemon shutting down...")
        _cleanup_on_exit()

    return 0


def parse_args() -> str:
    """
    Parse command-line arguments for daemon type selection.

    Returns:
        Daemon type ('dreaming' or 'search').
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Claude Code Daemon - Background service for insights and search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m dreaming_daemon               # Start dreaming daemon (default)
  python -m dreaming_daemon --daemon-type dreaming
  python -m dreaming_daemon --daemon-type search
        """,
    )
    parser.add_argument(
        "--daemon-type",
        choices=list(DAEMON_TYPES.keys()),
        default="dreaming",
        help="Type of daemon to start (default: dreaming)",
    )

    args = parser.parse_args()
    return args.daemon_type


def main(daemon_type: str = "dreaming") -> int:
    """
    Synchronous entry point that runs async main.

    Args:
        daemon_type: Type of daemon to run ("dreaming" or "search"). Defaults to "dreaming".

    Returns:
        Exit code (0 for success, non-zero for failure).

    Raises:
        ValueError: If daemon_type is not in DAEMON_TYPES.
    """
    # Validate daemon_type early (before async context)
    if daemon_type not in DAEMON_TYPES:
        valid_types = ", ".join(f"'{dt}'" for dt in DAEMON_TYPES.keys())
        raise ValueError(f"Unknown daemon type: '{daemon_type}'. Valid types are: {valid_types}")

    # Load daemon-specific configuration (before async context for testability)
    daemon_config = get_daemon_config(daemon_type)
    logger.info(f"Daemon config loaded for type '{daemon_type}'")

    # Configure daemon-specific paths based on daemon_type
    global STATE_FILE, PID_FILE, DAEMON_LOG
    STATE_FILE = STATE_DIR / daemon_config["state_file"]
    PID_FILE = STATE_DIR / daemon_config["pid_file"]
    DAEMON_LOG = LOGS_DIR / daemon_config["daemon_log"]

    # Setup signal handlers before starting async loop
    _setup_signal_handlers()

    # Run async main
    try:
        exit_code = asyncio.run(main_async(daemon_type=daemon_type, daemon_config=daemon_config))
        return exit_code
    except KeyboardInterrupt:
        logger.info("Daemon interrupted by keyboard")
        return 0
    except Exception as e:
        logger.error(f"Unhandled exception in daemon: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    daemon_type = parse_args()
    sys.exit(main(daemon_type))
