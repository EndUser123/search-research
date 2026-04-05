#!/usr/bin/env python3
"""Portable hook launcher and diagnostics for rca skill hooks."""

from __future__ import annotations

import argparse
import json
import os
import runpy
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPECTED_HOOKS = (
    "PostToolUse_rca_init.py",
    "PostToolUse_rca_phase_tracker.py",
    "PostToolUse_rca_action_tracker.py",  # Flow-of-Action tracking
    "SessionEnd_rca_cleanup.py",
    "StopHook_rca_enforcement.py",
)


def _candidate_hook_roots() -> list[Path]:
    here = Path(__file__).resolve()
    candidates = [
        here.parent / "skill" / "hooks",
        here.parents[2] / "skill" / "hooks",
        Path.cwd() / "skill" / "hooks",
    ]
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in candidates:
        resolved = path.resolve()
        if resolved not in seen:
            unique.append(resolved)
            seen.add(resolved)
    return unique


def resolve_hooks_root() -> Path:
    env_root = os.environ.get("DEBUG_RCA_HOOK_ROOT")
    if env_root:
        root = Path(env_root).expanduser().resolve()
        if not root.exists():
            raise FileNotFoundError(f"DEBUG_RCA_HOOK_ROOT does not exist: {root}")
        return root

    for candidate in _candidate_hook_roots():
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "Unable to locate hooks directory. Set DEBUG_RCA_HOOK_ROOT explicitly."
    )


def resolve_hook_file(hook_name: str) -> Path:
    hook_path = resolve_hooks_root() / hook_name
    if not hook_path.exists():
        raise FileNotFoundError(
            f"Hook not found: {hook_path} (cwd={Path.cwd()})"
        )
    return hook_path


def run_hook(hook_name: str, hook_args: list[str]) -> int:
    hook_path = resolve_hook_file(hook_name)
    sys.argv = [str(hook_path)] + hook_args
    try:
        runpy.run_path(str(hook_path), run_name="__main__")
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 0
    except Exception as exc:
        print(f"Error running hook: {exc}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 4
    return 0


def _doctor_probe(hook_name: str, cwd: Path) -> dict[str, Any]:
    cmd = [sys.executable, "-m", "rca.hook_launcher", hook_name]
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    stderr = (proc.stderr or "").strip()
    stdout = (proc.stdout or "").strip()
    return {
        "hook_name": hook_name,
        "cwd": str(cwd),
        "exit_code": proc.returncode,
        "stdout": stdout[:240],
        "stderr": stderr[:240],
    }


def run_doctor() -> int:
    now = datetime.now(timezone.utc).isoformat()
    hooks_root = resolve_hooks_root()
    skill_root = hooks_root.parent
    candidate_cwds = [Path.cwd().resolve(), skill_root.resolve()]
    unique_cwds: list[Path] = []
    for path in candidate_cwds:
        if path not in unique_cwds:
            unique_cwds.append(path)

    checks: list[dict[str, Any]] = []
    for cwd in unique_cwds:
        for hook_name in EXPECTED_HOOKS:
            checks.append(_doctor_probe(hook_name, cwd))

    failed = [c for c in checks if c["exit_code"] != 0]
    summary = {
        "timestamp": now,
        "status": "PASS" if not failed else "FAIL",
        "hooks_root": str(hooks_root),
        "skill_root": str(skill_root),
        "checks_total": len(checks),
        "failed_checks": len(failed),
        "checks": checks,
    }
    print(json.dumps(summary))
    return 0 if not failed else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m rca.hook_launcher",
        description="Run rca hooks with portable path resolution.",
    )
    parser.add_argument("hook_name", nargs="?")
    parser.add_argument("hook_args", nargs=argparse.REMAINDER)
    parser.add_argument("--doctor", action="store_true")
    args = parser.parse_args(argv)

    if args.doctor:
        return run_doctor()

    if not args.hook_name:
        parser.error("hook_name is required unless --doctor is used")

    return run_hook(args.hook_name, args.hook_args)


if __name__ == "__main__":
    raise SystemExit(main())

