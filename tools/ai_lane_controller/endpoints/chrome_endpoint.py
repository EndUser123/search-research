"""ChromeEndpoint — the ChatGPT/Chrome side of the bridge.

This daemon:
1. Finds or launches a Chrome instance attached to chatgpt.com
2. Watches the lane for phase transitions (WAITING_FOR_CHATGPT)
3. Reads the lane message, injects it into ChatGPT's textarea via CDP
4. Clicks send, polls for response completion
5. Writes the response back to the lane

Phase flow:
  IDLE -> inject message -> WAITING_FOR_CHATGPT
  ChatGPT responds -> polls for completion -> writes to lane
  Phase -> WAITING_FOR_CLAUDE (so terminal adapter picks it up)
  Terminal adapter injects into Claude -> writes back -> IDLE
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ai_lane_controller.endpoints.chrome_endpoint_cdp import (
    CDPError,
    CDPConnection,
    CircuitBreaker,
    find_chatgpt_tab_via_http,
    find_chrome_exe,
    safe_evaluate,
    read_cdp_artifact,
    write_cdp_artifact,
    delete_cdp_artifact,
    cdp_command,
)
from ai_lane_controller.endpoints.chrome_endpoint_dom import (
    load_selectors,
    inject_text,
    click_send,
    wait_for_response,
    preflight_check,
)
from ai_lane_controller.endpoints.input_mutex import is_ui_mutex_held
from ai_lane_controller import phase as phase_mod
from ai_lane_controller.storage import MessageStorage
from ai_lane_controller.messages import create_message, validate_message


@dataclass
class ChromeConfig:
    lane_id: str = "default"
    storage_root: str = "P:/.ai-lanes"
    selectors_version: str = "v1"
    poll_interval_s: float = 0.5
    max_response_wait_s: float = 120.0
    preflight_every_n: int = 10  # Run health check every N cycles


class ChromeEndpoint:
    """Injects messages from the lane into ChatGPT and reads responses."""

    def __init__(self, config: ChromeConfig):
        self.config = config
        self.storage = MessageStorage(config.storage_root)
        self.selectors = load_selectors(config.selectors_version)
        self._stop_event = False
        self._conn: CDPConnection | None = None
        self._breaker = CircuitBreaker()
        self._cycle_count = 0

    def stop(self):
        self._stop_event = True

    # -- Connection management -------------------------------------------------

    def _ensure_connection(self) -> CDPConnection:
        """Get or re-establish a CDP connection to a ChatGPT tab."""
        if self._conn is not None and not self._breaker.is_open:
            return self._conn

        if self._breaker.is_open:
            raise CDPError("circuit breaker open")

        # Try to find an existing ChatGPT tab on an already-debugging Chrome
        conn = find_chatgpt_tab_via_http()
        if conn is not None:
            write_cdp_artifact(self.storage, self.config.lane_id, conn)
            self._breaker.succeed()
            self._conn = conn
            return conn

        # No Chrome with remote debugging found — try to launch one
        chrome_path = find_chrome_exe()
        if chrome_path is None:
            raise CDPError("no Chrome/Edge executable found on system")

        import subprocess
        port = 9222
        try:
            subprocess.Popen(
                [
                    chrome_path,
                    f"--remote-debugging-port={port}",
                    "--remote-allow-origins=http://127.0.0.1:9222",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "https://chatgpt.com",
                ],
                shell=False,
            )
        except OSError as e:
            raise CDPError(f"failed to launch Chrome: {e}") from e

        # Wait for Chrome to start and find the ChatGPT tab
        deadline = time.monotonic() + 30.0
        while time.monotonic() < deadline:
            conn = find_chatgpt_tab_via_http()
            if conn is not None:
                write_cdp_artifact(self.storage, self.config.lane_id, conn)
                self._breaker.succeed()
                self._conn = conn
                return conn
            time.sleep(0.5)

        raise CDPError("Chrome started but ChatGPT tab not found within 30s")

    def _disconnect(self) -> None:
        self._conn = None
        delete_cdp_artifact(self.storage, self.config.lane_id)

    # -- Pre-flight health check -----------------------------------------------

    def _preflight(self) -> bool:
        """Run health checks. Returns True if healthy."""
        if self._conn is None:
            return False
        result = preflight_check(self._conn.websocket_url, self.selectors)
        if not result.get("ok", False):
            sys.stderr.write(
                f"[chrome-endpoint] preflight failed: "
                f"auth={result.get('authenticated')}, "
                f"error={result.get('error_detected')}, "
                f"textarea={result.get('textarea_found')}\n"
            )
            return False
        return True

    # -- Inject and read -------------------------------------------------------

    def _inject_and_send(self, message: str) -> str | None:
        """Inject *message* into ChatGPT textarea and send it.

        Returns the ChatGPT response text, or None on failure.
        """
        if self._conn is None:
            return None

        ws = self._conn.websocket_url
        sel = self.selectors

        # 1. Inject text
        result = inject_text(ws, message, sel["textarea"])
        if result.get("result", {}).get("value", {}).get("error"):
            raise CDPError(f"textarea injection failed: {result}")

        # 2. Click send
        click_send(ws, sel["send_button"])

        # 3. Wait for response
        response = wait_for_response(
            ws,
            sel["response_container"],
            sel.get("streaming_indicator", "[class*='streaming']"),
            max_wait_s=self.config.max_response_wait_s,
        )
        return response

    # -- Main loop -------------------------------------------------------------

    def run(self) -> None:
        """Main daemon loop."""
        signal.signal(signal.SIGINT, lambda s, f: self.stop())

        while not self._stop_event:
            try:
                self._cycle()
            except CDPError as e:
                delay = self._breaker.fail()
                sys.stderr.write(
                    f"[chrome-endpoint] CDP error: {e}. "
                    f"retry in {delay:.1f}s (failures={self._breaker._failures})\n"
                )
                self._disconnect()
                time.sleep(delay)
            except Exception as e:
                sys.stderr.write(f"[chrome-endpoint] cycle error: {e}\n")
                time.sleep(2.0)

            time.sleep(self.config.poll_interval_s)

    def _cycle(self) -> None:
        """One poll cycle: check phase, connect, inject, respond."""
        self._cycle_count += 1

        # 1. Ensure CDP connection
        try:
            self._ensure_connection()
        except CDPError:
            return

        # 2. Periodic preflight
        if self._cycle_count % self.config.preflight_every_n == 0:
            if not self._preflight():
                self._disconnect()
                return

        # 3. Phase recovery
        try:
            phase_mod.recover_stale_phase(self.storage, self.config.lane_id)
        except Exception:
            pass

        current = phase_mod.get_phase(self.storage, self.config.lane_id)
        if current is None or current.phase != phase_mod.PHASE_IDLE:
            return  # Not our turn

        # 4. Read pending message from the terminal adapter's response
        #    (source="chatgpt" means we sent it; source="claude" is their reply)
        msgs = self.storage.list_messages(self.config.lane_id)
        if not msgs:
            return

        # Look for a message destined for chatgpt (Claude's response to relay)
        # or an unprocessed message from chatgpt that needs sending
        pending_msg = None
        for msg in msgs:
            if msg.get("status") == "pending" and msg.get("destination") == "chatgpt":
                pending_msg = msg
                break

        if pending_msg is None:
            # No pending message to relay — check if we should start a new exchange
            return

        # 5. Read the payload
        payload = self.storage.read_payload(self.config.lane_id, pending_msg["id"])
        if payload is None:
            return

        sys.stderr.write(
            f"[chrome-endpoint] relaying message ({len(payload)} chars) "
            f"to ChatGPT\n"
        )

        # 6. Preflight before injection
        if not self._preflight():
            raise CDPError("preflight failed before injection")

        # 7. Transition phase
        phase_mod.transition_phase(
            self.storage, self.config.lane_id,
            phase_mod.PHASE_IDLE, phase_mod.PHASE_WAITING_FOR_CHATGPT,
        )

        try:
            # 8. Inject
            response = self._inject_and_send(payload)
            if response is None:
                raise CDPError("no response from ChatGPT")

            sys.stderr.write(
                f"[chrome-endpoint] got response ({len(response)} chars)\n"
            )

            # 9. Write response to lane
            out_msg = create_message(
                lane_id=self.config.lane_id,
                source="chatgpt",
                destination="claude",
                payload=response,
            )
            self.storage.store_message(out_msg, response)
        finally:
            # 10. Transition to WAITING_FOR_CLAUDE so terminal adapter picks it up
            phase_mod.transition_phase(
                self.storage, self.config.lane_id,
                phase_mod.PHASE_WAITING_FOR_CHATGPT, phase_mod.PHASE_WAITING_FOR_CLAUDE,
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="ChromeEndpoint — ChatGPT bridge side")
    parser.add_argument("--lane", default="default")
    parser.add_argument("--storage", default="P:/.ai-lanes")
    parser.add_argument("--selectors-version", default="v1")
    parser.add_argument("--poll-interval", type=float, default=0.5)
    parser.add_argument("--max-response-wait", type=float, default=120.0)
    args = parser.parse_args()

    config = ChromeConfig(
        lane_id=args.lane,
        storage_root=args.storage,
        selectors_version=args.selectors_version,
        poll_interval_s=args.poll_interval,
        max_response_wait_s=args.max_response_wait,
    )

    endpoint = ChromeEndpoint(config)
    try:
        endpoint.run()
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())