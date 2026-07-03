#!/usr/bin/env python3
"""Play a 'done' audio cue when Claude Code finishes a response (Stop event).

Mirrors the non-blocking design of Notification_voice_hook.py: read stdin,
print `{}`, and spawn a detached worker via pythonw.exe with CREATE_NO_WINDOW
so the launcher returns in milliseconds and never stalls the hook loop.

Cue style is argv-controlled so it can be flipped without code edits:
  - (default, no arg)  short non-verbal system chime via winsound.MessageBeep
  - `--voice`          reuse voice_notifications_worker.py to speak "Done."
  - `--beep`           custom two-tone chirp via winsound.Beep (no system sound)

Workers are launched detached and this script exits immediately; sound output
failures never propagate back to Claude Code.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _pythonw_executable() -> str:
    """Prefer pythonw.exe on Windows so no console window flashes."""
    if sys.platform != "win32":
        return sys.executable
    exe = Path(sys.executable)
    pythonw = exe.with_name("pythonw.exe")
    return str(pythonw) if pythonw.exists() else sys.executable


def _detached_kwargs() -> dict:
    kwargs = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "close_fds": True,
    }
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    return kwargs


def _spawn_chime() -> None:
    """Play the Windows 'asterisk' system sound in a detached pythonw process."""
    # Inline worker source so no extra file is required. MessageBeep type
    # 0x40 (MB_ICONASTERISK) = the informational chime. Falls back to a plain
    # beep if MessageBeep returns False (no configured sound scheme).
    worker_code = (
        "import sys, winsound; "
        "ok = winsound.MessageBeep(0x40); "
        "sys.exit(0 if ok else 0);"
    )
    subprocess.Popen([_pythonw_executable(), "-c", worker_code], **_detached_kwargs())


def _spawn_beep() -> None:
    """Play a custom two-tone chirp via winsound.Beep (no system sound needed)."""
    worker_code = (
        "import winsound; "
        "winsound.Beep(880, 120); winsound.Beep(1175, 160);"
    )
    subprocess.Popen([_pythonw_executable(), "-c", worker_code], **_detached_kwargs())


def _spawn_voice() -> None:
    """Reuse the existing SAPI worker to speak a short 'Done' message."""
    worker = Path(__file__).with_name("voice_notifications_worker.py")
    subprocess.Popen(
        [_pythonw_executable(), str(worker), "Done."], **_detached_kwargs()
    )


def main() -> int:
    # Drain stdin regardless of content; the Stop payload is informational only.
    try:
        sys.stdin.read()
    except Exception:
        pass

    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "--voice":
        _spawn_voice()
    elif arg == "--beep":
        _spawn_beep()
    else:
        _spawn_chime()

    print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
