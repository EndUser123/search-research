#!/usr/bin/env python3
"""
PID management system for dnld_telegram processes
Handles cleanup of orphaned processes and tracking current processes
"""

import atexit
import logging
import os
import signal
import sys
from pathlib import Path

import psutil

logger = logging.getLogger(__name__)

APP_IDENTIFIER = (
    "dnld_telegram_app_instance"  # A unique identifier for this application
)


class PIDManager:
    """Manages process IDs for dnld_telegram to prevent orphaned processes"""

    def __init__(self, config_dir: str = None):
        if config_dir is None:
            # Default to config directory relative to this file
            self.config_dir = Path(__file__).parent
        else:
            self.config_dir = Path(config_dir)

        self.pid_file = self.config_dir / "dnld_telegram.pid"
        self.current_pid = os.getpid()

        # Register cleanup on exit
        atexit.register(self.cleanup_on_exit)

        # Register signal handlers for graceful shutdown
        if hasattr(signal, "SIGINT"):
            signal.signal(signal.SIGINT, self._signal_handler)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.cleanup_on_exit()
        sys.exit(0)

    def kill_orphaned_processes(self) -> list[int]:
        """Kill any orphaned dnld_telegram processes from previous runs"""
        killed_pids = []

        if not self.pid_file.exists():
            logger.debug("No PID file found, no orphaned processes to clean")
            return killed_pids

        try:
            with open(self.pid_file) as f:
                stored_entries = [line.strip().split(",") for line in f if line.strip()]

            for entry in stored_entries:
                if len(entry) == 2:
                    pid, identifier = entry
                    try:
                        pid = int(pid)
                        if self._kill_process_if_exists(pid, identifier):
                            killed_pids.append(pid)
                    except ValueError:
                        logger.warning(f"Invalid PID entry in file: {entry}")
                else:
                    logger.warning(f"Invalid PID file entry format: {entry}")

            logger.info(f"Killed {len(killed_pids)} orphaned processes: {killed_pids}")

        except (OSError, ValueError) as e:
            logger.warning(f"Error reading PID file: {e}")

        return killed_pids

    def _kill_process_if_exists(self, pid: int, identifier: str) -> bool:
        """Kill a process if it exists and is a Python process with the correct identifier"""
        try:
            if not psutil.pid_exists(pid):
                return False

            process = psutil.Process(pid)

            # Only kill if it's a Python process and matches our APP_IDENTIFIER
            if "python" not in process.name().lower():
                logger.debug(
                    f"PID {pid} is not a Python process ({process.name()}), skipping"
                )
                return False

            # Verify APP_IDENTIFIER from process environment or command line
            try:
                # Check command line for app-specific markers
                cmdline = process.cmdline()
                is_dnld_telegram_cmd = any(
                    "dnld_telegram" in arg or "src.download" in arg for arg in cmdline
                )

                # Check environment variables for the APP_IDENTIFIER
                process_env = process.environ()
                is_correct_app_id = (
                    process_env.get("DNLD_TELEGRAM_APP_IDENTIFIER") == identifier
                )

                if not (is_dnld_telegram_cmd and is_correct_app_id):
                    logger.debug(
                        f"PID {pid} doesn't appear to be a verified dnld_telegram process (cmdline/env mismatch), skipping"
                    )
                    return False

            except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
                logger.debug(f"Cannot access process details for PID {pid}, skipping")
                return False

            # Kill the process
            logger.info(
                f"Killing orphaned dnld_telegram process {pid} ({process.name()})"
            )
            process.terminate()

            # Wait up to 5 seconds for graceful termination
            try:
                process.wait(timeout=5)
            except psutil.TimeoutExpired:
                logger.warning(
                    f"Process {pid} didn't terminate gracefully, force killing"
                )
                process.kill()
                process.wait(timeout=2)

            return True

        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError) as e:
            logger.debug(f"Could not kill process {pid}: {e}")
            return False

    def register_current_process(self):
        """Register the current process PID and APP_IDENTIFIER"""
        try:
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # Write current PID and APP_IDENTIFIER to file
            with open(self.pid_file, "w") as f:
                f.write(f"{self.current_pid},{APP_IDENTIFIER}\n")

            logger.info(
                f"Registered current process PID: {self.current_pid} with identifier {APP_IDENTIFIER}"
            )

        except OSError as e:
            logger.error(f"Could not write PID file: {e}")

    def cleanup_on_exit(self):
        """Clean up PID file on exit"""
        try:
            if self.pid_file.exists():
                # Read existing entries
                remaining_entries = []
                with open(self.pid_file) as f:
                    for line in f:
                        parts = line.strip().split(",")
                        if len(parts) == 2:
                            pid, identifier = parts
                            try:
                                if int(pid) != self.current_pid:
                                    remaining_entries.append(line.strip())
                            except ValueError:
                                logger.warning(
                                    f"Invalid PID entry during cleanup: {line.strip()}"
                                )

                if remaining_entries:
                    # Write remaining entries back
                    with open(self.pid_file, "w") as f:
                        for entry in remaining_entries:
                            f.write(f"{entry}\n")
                else:
                    # Remove file if no PIDs remain
                    self.pid_file.unlink()

                logger.info(f"Cleaned up PID {self.current_pid} from PID file")

        except (OSError, ValueError) as e:
            logger.debug(f"Error during PID cleanup: {e}")

    def start_process_management(self):
        """Start complete process management: kill orphans and register current"""
        logger.info("Starting PID management...")
        killed = self.kill_orphaned_processes()
        self.register_current_process()
        return killed


# Global instance
_pid_manager = None


def get_pid_manager(config_dir: str = None) -> PIDManager:
    """Get global PID manager instance"""
    global _pid_manager
    if _pid_manager is None:
        _pid_manager = PIDManager(config_dir)
    return _pid_manager


def start_process_management(config_dir: str = None) -> list[int]:
    """Convenience function to start process management"""
    manager = get_pid_manager(config_dir)
    return manager.start_process_management()


if __name__ == "__main__":
    # Test the PID manager
    logging.basicConfig(level=logging.INFO)
    manager = PIDManager()
    killed = manager.start_process_management()
    print(f"Killed orphaned processes: {killed}")
    print(f"Current PID: {manager.current_pid}")
