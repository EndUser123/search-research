#!/usr/bin/env python3
"""Launch voice notifications without spawning a visible console on Windows."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _extract_message(raw_input: str) -> str:
    if not raw_input.strip():
        return "Notification received"
    try:
        payload = json.loads(raw_input)
    except json.JSONDecodeError:
        return "Notification received"

    message = payload.get("message")
    if isinstance(message, str) and message.strip():
        return message.strip()
    return "Notification received"


def _pythonw_executable() -> str:
    if sys.platform != "win32":
        return sys.executable
    exe = Path(sys.executable)
    pythonw = exe.with_name("pythonw.exe")
    if pythonw.exists():
        return str(pythonw)
    return sys.executable


def main() -> int:
    message = _extract_message(sys.stdin.read())
    worker = Path(__file__).with_name("voice_notifications_worker.py")
    cmd = [_pythonw_executable(), str(worker), message]

    kwargs = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "close_fds": True,
    }
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    subprocess.Popen(cmd, **kwargs)
    print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
