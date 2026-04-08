"""CHS v2 Indexer Daemon.

Run the indexer daemon with file locking and idle timeout handling.

Usage:
    python -m knowledge.systems.chs.v2.scripts.run_indexer
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path


def acquire_lock(lock_path: Path) -> bool:
    """Acquire exclusive file lock to prevent multiple indexer instances.

    Uses cross-platform file locking (msvcrt on Windows, fcntl on Unix).

    Args:
        lock_path: Path to lock file

    Returns:
        True if lock acquired, False if another instance is running
    """
    try:
        import msvcrt

        lock_fd = open(lock_path, "w")
        try:
            msvcrt.locking(lock_fd.fileno(), msvcrt.LK_NBLCK, 1)
            return (True, lock_fd)
        except OSError:
            lock_fd.close()
            return (False, None)
    except ImportError:
        import fcntl

        try:
            lock_fd = open(lock_path, "w")
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return (True, lock_fd)
        except OSError:
            return (False, None)


def main() -> int:
    """Run indexer daemon with file locking and idle timeout.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(description="Run CHS v2 indexer daemon")
    parser.add_argument(
        "--idle-timeout", type=int, default=300, help="Idle timeout in seconds (default: 300)"
    )
    parser.add_argument(
        "--loop-interval", type=int, default=60, help="Loop interval in seconds (default: 60)"
    )
    parser.add_argument(
        "--lock-path",
        type=str,
        default=None,
        help="Path to lock file (default: /tmp/chs_indexer.lock)",
    )
    args = parser.parse_args()
    if args.lock_path:
        lock_path = Path(args.lock_path)
    else:
        lock_path = Path(os.path.join(os.getenv("TMP", "/tmp"), "chs_indexer.lock"))
    lock_fd = None
    lock_acquired, lock_fd = acquire_lock(lock_path)
    if not lock_acquired:
        print("ERROR: Another indexer instance is already running", file=sys.stderr)
        return 1
    try:
        print(f"CHS v2 Indexer started (PID: {os.getpid()})")
        print(f"Idle timeout: {args.idle_timeout}s, Loop interval: {args.loop_interval}s")
        idle_count = 0
        max_idle_cycles = args.idle_timeout // args.loop_interval
        while True:
            try:
                from search_research.core.chs.config import Config

                config = Config()
            except (ValueError, ImportError) as e:
                print(f"ERROR: Configuration validation failed: {e}", file=sys.stderr)
                return 1
            jsonl_dir = config.jsonl_dir
            jsonl_files = list(jsonl_dir.glob("*.jsonl"))
            if jsonl_files:
                print(f"Found {len(jsonl_files)} JSONL file(s) to index")
                idle_count = 0
                try:
                    from search_research.core.chs.indexer import ChatIndexer  # noqa: F401

                    for jsonl_file in jsonl_files:
                        print(f"  - {jsonl_file.name}")
                except ImportError:
                    print("WARNING: Indexer module not yet implemented", file=sys.stderr)
                    print("Indexer daemon running in monitoring mode...")
            else:
                idle_count += 1
                if idle_count >= max_idle_cycles:
                    print(f"Idle timeout reached ({args.idle_timeout}s)")
                    print("Exiting indexer daemon")
                    break
            time.sleep(args.loop_interval)
        return 0
    except KeyboardInterrupt:
        print("\nIndexer daemon stopped by user")
        return 0
    except Exception as e:
        print(f"ERROR: Indexer daemon failed: {e}", file=sys.stderr)
        return 1
    finally:
        if lock_fd:
            try:
                lock_fd.close()
            except Exception:
                pass
            try:
                if lock_path.exists():
                    lock_path.unlink()
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(main())
