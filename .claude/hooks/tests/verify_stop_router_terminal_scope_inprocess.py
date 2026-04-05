#!/usr/bin/env python3
"""In-process verification for Stop_router terminal/session observation recovery.

This script validates the regression fix without pytest tmp fixtures:
- Stop_router must not synthesize CLAUDE_TERMINAL_ID from session_id.
- Observation fallback must recover terminal-scoped evidence even when session mismatches.
"""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path


def fail(msg: str) -> int:
    print(f"[FAIL] {msg}")
    return 1


def main() -> int:
    hooks_dir = Path(__file__).resolve().parents[1]
    if str(hooks_dir) not in sys.path:
        sys.path.insert(0, str(hooks_dir))

    try:
        import Stop_router  # type: ignore
        import terminal_detection  # type: ignore
    except Exception as exc:
        return fail(f"Import error: {exc}")

    # Isolate env for this check.
    old_session = os.environ.pop("CLAUDE_SESSION_ID", None)
    old_terminal = os.environ.pop("CLAUDE_TERMINAL_ID", None)

    # Inject a fake tool sequence manager where evidence exists only under terminal scope.
    fake = types.ModuleType("tool_sequence_manager")

    def _fake_load_tool_sequence_filtered(**kwargs):
        terminal_id = kwargs.get("terminal_id")
        if terminal_id == "env_real_terminal":
            return [
                {
                    "name": "Read",
                    "path": "P:/repo/evidence.md",
                    "terminal_id": "env_real_terminal",
                    "session_id": "different-session",
                }
            ]
        return []

    fake.load_tool_sequence_filtered = _fake_load_tool_sequence_filtered
    fake.get_recent_tool_sequence = lambda count=20: []

    original_module = sys.modules.get("tool_sequence_manager")
    sys.modules["tool_sequence_manager"] = fake

    original_detect = terminal_detection.detect_terminal_id
    terminal_detection.detect_terminal_id = lambda: "env_real_terminal"

    try:
        data = {
            "session_id": "194b664d-0fc4-4032-a05b-ad4b56d9c955",
            "tools_used": [],
        }

        Stop_router._set_session_terminal_context(data)
        observed = Stop_router._extract_observation_entries(data)

        if os.environ.get("CLAUDE_SESSION_ID") != data["session_id"]:
            return fail("CLAUDE_SESSION_ID was not set to input session_id")

        if "CLAUDE_TERMINAL_ID" in os.environ:
            return fail("CLAUDE_TERMINAL_ID should not be synthesized from session_id")

        if not observed:
            return fail("No observations recovered from terminal-scoped fallback")

        if observed[0].get("name") != "Read":
            return fail(f"Unexpected first observation: {observed[0]}")

        print("[PASS] Stop_router terminal/session scope regression check passed.")
        print("       recovered_observations:", len(observed))
        return 0
    finally:
        # Restore monkeypatches/modules/env.
        terminal_detection.detect_terminal_id = original_detect
        if original_module is not None:
            sys.modules["tool_sequence_manager"] = original_module
        else:
            sys.modules.pop("tool_sequence_manager", None)

        os.environ.pop("CLAUDE_SESSION_ID", None)
        os.environ.pop("CLAUDE_TERMINAL_ID", None)
        if old_session is not None:
            os.environ["CLAUDE_SESSION_ID"] = old_session
        if old_terminal is not None:
            os.environ["CLAUDE_TERMINAL_ID"] = old_terminal


if __name__ == "__main__":
    raise SystemExit(main())
