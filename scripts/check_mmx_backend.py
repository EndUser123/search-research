#!/usr/bin/env python3
"""check_mmx_backend.py - deterministic viability check for the mmx CLI
(MiniMax Token-Plan), which core/cli.py:_minimax_search shells out to for
`--mode minimax`.

LOCAL + deterministic (no network): safe to run anytime. Catches the three
real failure modes — mmx uninstalled, shadowed by a broken third-party
mmx.exe shim, or redesigned so `search query` is gone. It does NOT verify
live groundedness; run that on demand:

    mmx search query "test" --region global --output json --non-interactive
    # assert: exit 0 AND response JSON has organic[] with >= 1 link

Exit codes:
  0  = healthy (mmx resolves, --version exits 0, `search query` subcommand exists)
  2  = critical (mmx missing / broken shim / search-query removed)
  1  = invocation error
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

TIMEOUT_S = 15


def _mmx_argv(extra: list[str]) -> list[str]:
    """Resolve the official npm mmx exactly as core/cli.py does.

    Windows: npm ships only mmx.cmd (CreateProcess can't exec .cmd directly, and
    a stale third-party mmx.exe shim can shadow it via PATHEXT), so use
    `cmd /c <npm mmx.cmd>`. Bare `mmx` is the non-Windows fallback.
    """
    if os.name == "nt":
        npm_mmx = Path(os.environ.get("APPDATA", "")) / "npm" / "mmx.cmd"
        if npm_mmx.is_file():
            return ["cmd", "/c", str(npm_mmx)] + extra
    return ["mmx"] + extra


def _run(argv: list[str]) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_S,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except (FileNotFoundError, subprocess.SubprocessError) as exc:
        return -1, str(exc)


def run() -> dict:
    argv = _mmx_argv(["--version"])
    rc, out = _run(argv)
    if rc != 0:
        return _exit(2, {
            "name": "mmx_backend",
            "status": "critical",
            "message": "mmx CLI not runnable (uninstalled, shadowed by a broken shim, or not on PATH)",
            "details": [f"argv: {' '.join(argv)}", f"rc={rc}", f"output: {out.strip()[:200]}",
                        "Fix: npm install -g mmx-cli  (on Windows also remove any broken Python mmx.exe shim)"],
        })

    version = out.strip().splitlines()[-1] if out.strip() else "unknown"

    src, sout = _run(_mmx_argv(["search", "--help"]))
    if src != 0 or "query" not in sout.lower():
        return _exit(2, {
            "name": "mmx_backend",
            "status": "critical",
            "message": "mmx installed but `search query` subcommand missing (CLI redesign?)",
            "details": [f"version: {version}", f"search --help rc={src}",
                        "Fix: check mmx-cli changelog; update core/cli.py _minimax_search"],
        })

    return _exit(0, {
        "name": "mmx_backend",
        "status": "healthy",
        "message": f"mmx viable ({version}); `search query` present",
        "details": [f"version: {version}",
                    "Live groundedness (on demand): mmx search query \"test\" --region global --output json"],
    })


def _exit(code: int, payload: dict) -> dict:
    print(json.dumps(payload))
    sys.exit(code)


if __name__ == "__main__":
    run()
