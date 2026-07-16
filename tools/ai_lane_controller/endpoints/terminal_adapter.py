"""Terminal adapter — the Claude side of the bridge (Path A interactive injection).

This daemon:
1. Watches a lane for messages routed from ChatGPT (phase == WAITING_FOR_CLAUDE)
2. Acquires the UI mutex (blocks user input in the Claude Code terminal)
3. Attaches to the Claude Code console and injects the message + Enter
4. Polls the screen buffer until completion is detected
5. Writes the response back to the lane (for ChromeEndpoint to relay to ChatGPT)
6. Releases the UI mutex (user can type again)

Interrupt: if the user deletes the lock file (or Ctrl+C the daemon), the
daemon aborts the current injection, releases all resources, and resets the
lane phase to IDLE.

This is the "true interactive injection" architecture (Path A).  It does NOT
use the Agent SDK — it talks to the user's actual Claude Code terminal session.
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Make parent package importable
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ai_lane_controller.endpoints.win_console_api import (
    ConsoleAPIError,
    console_attach,
    console_detach,
    find_console_windows,
    write_keystrokes,
    write_enter,
    get_screen_lines,
    get_console_handles,
)
from ai_lane_controller.endpoints.input_mutex import (
    UIMutexError,
    acquire_ui_mutex,
    release_ui_mutex,
    is_ui_mutex_held,
)
from ai_lane_controller.endpoints.completion_detector import (
    CompletionDetector,
    CompletionResult,
)
from ai_lane_controller import phase as phase_mod
from ai_lane_controller.storage import MessageStorage


# ── Configuration ─────────────────────────────────────────────────────────────


@dataclass
class AdapterConfig:
    """Runtime configuration for the terminal adapter."""

    lane_id: str = "default"
    storage_root: str = "P:/.ai-lanes"
    claude_window_regex: str = "claude"  # regex to find Claude Code window
    claude_pid: int | None = None        # explicit PID override
    poll_interval_s: float = 0.5
    idle_timeout_s: float = 1.5
    mutex_timeout_s: float = 30.0
    inject_delay_s: float = 0.3           # pause after injecting Enter
    max_response_wait_s: float = 600.0    # bail if Claude never responds


# ── Errors ────────────────────────────────────────────────────────────────────


class AdapterError(RuntimeError):
    """Terminal adapter operation failed."""


class AdapterInterrupted(AdapterError):
    """User interrupted the injection (deleted the lock file)."""


# ── Core adapter ──────────────────────────────────────────────────────────────


class TerminalAdapter:
    """Injects messages into a running Claude Code terminal session.

    The adapter does NOT own a Claude instance — it talks to whatever the
    user has running.  Find it by window title regex or explicit PID.
    """

    def __init__(self, config: AdapterConfig):
        self.config = config
        self.storage = MessageStorage(config.storage_root)
        self._stop_event = threading.Event()
        self._interrupted = False

    def stop(self) -> None:
        """Signal the daemon loop to stop after the current cycle."""
        self._stop_event.set()

    # ── Console discovery ──────────────────────────────────────────────────────

    def find_claude_console(self) -> tuple[int, str]:
        """Find the Claude Code console.

        Returns (pid, window_title).  Raises AdapterError if not found.
        """
        if self.config.claude_pid:
            return self.config.claude_pid, "(by PID)"

        windows = find_console_windows(self.config.claude_window_regex)
        if not windows:
            raise AdapterError(
                f"no console window matching '{self.config.claude_window_regex}'"
            )
        if len(windows) > 1:
            # Pick the most recently active (first match is fine for now)
            titles = [w.title for w in windows]
            sys.stderr.write(
                f"warning: {len(windows)} Claude windows found: {titles}\n"
            )
        win = windows[0]
        return win.pid, win.title

    # ── Injection ──────────────────────────────────────────────────────────────

    def inject_message(
        self,
        message: str,
        claude_pid: int,
    ) -> str:
        """Inject *message* into the Claude Code console and wait for completion.

        Acquires the UI mutex first.  Returns the response text.

        Raises AdapterInterrupted if the user deletes the lock file.
        Raises AdapterError on console API failures or timeout.
        """
        own_pid = _get_pid()

        # 1. Acquire UI mutex (blocks user input)
        try:
            lock_path = acquire_ui_mutex(
                own_pid, timeout_s=self.config.mutex_timeout_s
            )
        except UIMutexError as e:
            raise AdapterError(f"could not acquire UI mutex: {e}") from e

        try:
            # 2. Start interrupt monitor thread
            stop_monitor = threading.Event()

            def _watch_interrupt():
                while not stop_monitor.is_set():
                    if not is_ui_mutex_held():
                        self._interrupted = True
                        return
                    time.sleep(0.3)

            mon = threading.Thread(target=_watch_interrupt, daemon=True)
            mon.start()

            # 3. Attach to Claude's console
            try:
                console_attach(claude_pid)
                hin, hout = get_console_handles()
            except ConsoleAPIError as e:
                raise AdapterError(
                    f"could not attach to console (pid={claude_pid}): {e}"
                ) from e

            try:
                # 4. Snapshot pre-injection state
                detector = CompletionDetector(
                    lambda: get_screen_lines(hout),
                    idle_timeout=self.config.idle_timeout_s,
                    poll_interval=0.2,
                )
                detector.reset()

                # 5. Inject the message + Enter
                write_keystrokes(hin, message)
                write_enter(hin)
                time.sleep(self.config.inject_delay_s)

                # 6. Poll for completion
                deadline = time.monotonic() + self.config.max_response_wait_s
                result: CompletionResult | None = None
                while time.monotonic() < deadline:
                    if self._interrupted:
                        raise AdapterInterrupted(
                            "user deleted the UI mutex lock file"
                        )
                    if self._stop_event.is_set():
                        raise AdapterInterrupted("daemon stopping")

                    result = detector.poll()
                    if result.complete:
                        break
                    time.sleep(self.config.poll_interval_s)
                else:
                    raise AdapterError(
                        f"Claude did not respond within "
                        f"{self.config.max_response_wait_s}s"
                    )

                if result is None:
                    raise AdapterError("no completion result")

                response_text = detector.extract_response_text(result)
                return response_text

            finally:
                console_detach()

        finally:
            stop_monitor.set()
            # Always release the mutex, even on error
            try:
                release_ui_mutex(own_pid)
            except UIMutexError:
                # Lock may already be gone (interrupt) — best-effort
                pass

    # ── Daemon loop ───────────────────────────────────────────────────────────

    def run(self) -> None:
        """Main daemon loop: poll lane for messages, inject, respond."""
        # Discover the Claude console once at startup
        claude_pid, title = self.find_claude_console()
        sys.stderr.write(
            f"[terminal-adapter] attached to Claude Code console: "
            f"pid={claude_pid} title='{title}'\n"
        )

        # Install signal handlers for graceful shutdown
        def _sigint(sig, frame):
            sys.stderr.write("\n[terminal-adapter] interrupt received, stopping\n")
            self._stop_event.set()
        signal.signal(signal.SIGINT, _sigint)

        while not self._stop_event.is_set():
            try:
                self._poll_cycle(claude_pid)
            except AdapterInterrupted as e:
                sys.stderr.write(f"[terminal-adapter] interrupted: {e}\n")
                # Reset phase to IDLE
                try:
                    phase_mod.set_phase(
                        self.storage, self.config.lane_id,
                        phase_mod.PHASE_IDLE,
                    )
                except Exception:
                    pass
            except Exception as e:
                sys.stderr.write(f"[terminal-adapter] cycle error: {e}\n")
                time.sleep(2.0)  # Back off before retrying

            time.sleep(self.config.poll_interval_s)

    def _poll_cycle(self, claude_pid: int) -> None:
        """One poll cycle: check lane phase, inject if a message is waiting."""
        # Recover any stale phase first
        try:
            phase_mod.recover_stale_phase(self.storage, self.config.lane_id)
        except Exception:
            pass

        current_phase = phase_mod.get_phase(self.storage, self.config.lane_id)
        if current_phase is None:
            return
        if current_phase.phase != phase_mod.PHASE_WAITING_FOR_CLAUDE:
            return  # Nothing to do — wait for ChatGPT side to submit

        # Read the latest message from the lane (placeholder — wire to
        # the message store once that API is finalized).
        message = self._read_pending_message()
        if message is None:
            return

        sys.stderr.write(
            f"[terminal-adapter] injecting message ({len(message)} chars) "
            f"into Claude pid={claude_pid}\n"
        )

        response = self.inject_message(message, claude_pid)

        sys.stderr.write(
            f"[terminal-adapter] got response ({len(response)} chars)\n"
        )

        # Write response back to lane and transition phase to IDLE
        self._write_response(response)
        phase_mod.transition_phase(
            self.storage, self.config.lane_id,
            phase_mod.PHASE_WAITING_FOR_CLAUDE, phase_mod.PHASE_IDLE,
        )

    def _read_pending_message(self) -> str | None:
        """Read the latest unprocessed message from the lane.

        Placeholder implementation — wires to the message store once the
        message contract is finalized.  For now, reads from a known path.
        """
        msg_path = Path(self.config.storage_root) / self.config.lane_id / "pending.txt"
        if not msg_path.exists():
            return None
        try:
            text = msg_path.read_text(encoding="utf-8")
            # Consume the message
            msg_path.unlink()
            return text
        except OSError:
            return None

    def _write_response(self, response: str) -> None:
        """Write the response back to the lane for ChromeEndpoint to relay."""
        resp_path = Path(self.config.storage_root) / self.config.lane_id / "response.txt"
        resp_path.parent.mkdir(parents=True, exist_ok=True)
        resp_path.write_text(response, encoding="utf-8")


def _get_pid() -> int:
    import os
    return os.getpid()


# ── CLI entry point ───────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Claude terminal adapter — bridge Claude Code side (Path A)"
    )
    parser.add_argument("--lane", default="default", help="lane ID to serve")
    parser.add_argument("--storage", default="P:/.ai-lanes", help="lane storage root")
    parser.add_argument(
        "--claude-window", default="claude",
        help="regex to find the Claude Code window title",
    )
    parser.add_argument("--claude-pid", type=int, default=None, help="explicit PID")
    parser.add_argument("--idle-timeout", type=float, default=1.5)
    parser.add_argument("--poll-interval", type=float, default=0.5)
    args = parser.parse_args()

    config = AdapterConfig(
        lane_id=args.lane,
        storage_root=args.storage,
        claude_window_regex=args.claude_window,
        claude_pid=args.claude_pid,
        idle_timeout_s=args.idle_timeout,
        poll_interval_s=args.poll_interval,
    )

    adapter = TerminalAdapter(config)
    try:
        adapter.run()
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())