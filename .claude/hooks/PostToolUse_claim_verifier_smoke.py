#!/usr/bin/env python3
"""Automatic smoke test for claim verifier wiring.

Runs a tiny pytest suite whenever the claim verifier surface changes.
This catches wiring regressions immediately after the relevant files are edited.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


HOOKS_DIR = Path(__file__).resolve().parent
TEST_FILE = HOOKS_DIR / "tests" / "test_claim_verifier_runtime_assertions.py"

_RELEVANT_SUFFIXES = (
    "/.claude/hooks/unified_claim_verifier.py",
    "/.claude/hooks/stop_router.py",
    "/.claude/hooks/posttooluse/__init__.py",
    "/.claude/hooks/tests/test_claim_verifier_runtime_assertions.py",
    "/.claude/settings.json",
)

_DEFAULT_TIMEOUT_SECONDS = 20.0


def _enabled() -> bool:
    return os.environ.get("CLAIM_VERIFIER_SMOKE_ENABLED", "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _normalize_path(value: str | None) -> str:
    if not value:
        return ""
    return str(Path(value)).replace("\\", "/").lower()


def _extract_paths(tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]) -> list[str]:
    paths: list[str] = []

    if tool_name == "MultiEdit":
        edits = tool_input.get("edits", [])
        if isinstance(edits, list):
            for edit in edits:
                if not isinstance(edit, dict):
                    continue
                for key in ("file_path", "path", "target"):
                    value = edit.get(key)
                    if isinstance(value, str) and value.strip():
                        paths.append(value.strip())
    else:
        for key in ("file_path", "path", "target"):
            value = tool_input.get(key)
            if isinstance(value, str) and value.strip():
                paths.append(value.strip())

    if not paths and isinstance(tool_response, dict):
        for key in ("file_path", "path"):
            value = tool_response.get(key)
            if isinstance(value, str) and value.strip():
                paths.append(value.strip())

    return paths


def _is_relevant_path(path: str) -> bool:
    normalized = _normalize_path(path)
    return any(normalized.endswith(suffix) for suffix in _RELEVANT_SUFFIXES)


def _tail(text: str, max_lines: int = 40) -> str:
    if not text.strip():
        return ""
    lines = text.splitlines()
    return "\n".join(lines[-max_lines:])


def _run_pytest() -> dict[str, Any]:
    command = [sys.executable, "-m", "pytest", str(TEST_FILE), "-q"]
    try:
        result = subprocess.run(
            command,
            cwd=str(HOOKS_DIR),
            capture_output=True,
            text=True,
            timeout=_DEFAULT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "reason": "TIMEOUT",
            "returncode": None,
            "stdout": _tail(exc.stdout or ""),
            "stderr": _tail(exc.stderr or ""),
            "command": command,
        }
    except Exception as exc:
        return {
            "ok": False,
            "reason": f"{type(exc).__name__}: {exc}",
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "command": command,
        }

    stdout = result.stdout or ""
    stderr = result.stderr or ""
    ok = result.returncode == 0
    return {
        "ok": ok,
        "reason": "PASS" if ok else "FAIL",
        "returncode": result.returncode,
        "stdout": _tail(stdout),
        "stderr": _tail(stderr),
        "command": command,
    }


def run(data: dict[str, Any]) -> dict[str, Any]:
    if not _enabled():
        return {"passed": True, "skipped": True, "reason": "disabled"}

    tool_name = str(data.get("tool_name", ""))
    if tool_name not in {"Write", "Edit", "MultiEdit"}:
        return {"passed": True, "skipped": True, "reason": "tool_mismatch"}

    tool_input = data.get("tool_input", {})
    tool_response = data.get("tool_response") or data.get("tool_result") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}
    if not isinstance(tool_response, dict):
        tool_response = {}

    paths = _extract_paths(tool_name, tool_input, tool_response)
    relevant_paths = [path for path in paths if _is_relevant_path(path)]
    if not relevant_paths:
        return {"passed": True, "skipped": True, "reason": "no_relevant_paths"}

    smoke = _run_pytest()
    if smoke["ok"]:
        return {
            "passed": True,
            "smoke_checked": True,
            "paths": relevant_paths,
            "reason": "CLAIM_VERIFIER_SMOKE_PASSED",
        }

    stdout = str(smoke.get("stdout", "")).strip()
    stderr = str(smoke.get("stderr", "")).strip()
    detail_parts = [
        "Claim verifier smoke failed.",
        f"Files: {', '.join(relevant_paths)}",
        f"Command: {' '.join(smoke['command'])}",
    ]
    if stdout:
        detail_parts.append(f"stdout:\n{stdout}")
    if stderr:
        detail_parts.append(f"stderr:\n{stderr}")

    detail = "\n\n".join(detail_parts)
    return {
        "decision": "block",
        "reason": "CLAIM_VERIFIER_SMOKE_FAILED",
        "systemMessage": "Claim verifier smoke suite failed. Fix the wiring before continuing.",
        "injection": detail,
        "diagnostic": smoke,
        "smoke_checked": True,
        "paths": relevant_paths,
    }


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        print("{}")
        return 0

    try:
        data = json.loads(raw.lstrip("\ufeff"))
    except json.JSONDecodeError:
        print("{}")
        return 0

    if not isinstance(data, dict):
        print("{}")
        return 0

    result = run(data)
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
