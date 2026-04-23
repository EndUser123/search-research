#!/usr/bin/env python3
"""SessionStart hook: capture authoritative identity to cache file.

Reads session_id, transcript_path, cwd from hook stdin JSON.
Reads terminal_id from WT_SESSION env var.
Writes combined identity to P:/.claude/.artifacts/{terminal_id}/identity.json.

This is the single source of truth for the /id skill.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR / "__lib"))
from terminal_detection import detect_terminal_id

ARTIFACTS_ROOT = Path("P:/.claude/.artifacts")

_REGISTRY_PATH = ARTIFACTS_ROOT / "session_registry.jsonl"
_REGISTRY_MAX_LINES = 10_000
_REGISTRY_KEEP_LINES = 5_000


def _prune_session_registry() -> None:
    if not _REGISTRY_PATH.exists():
        return
    try:
        lines = _REGISTRY_PATH.read_text(encoding="utf-8").splitlines()
        if len(lines) < _REGISTRY_MAX_LINES:
            return
        kept = lines[-_REGISTRY_KEEP_LINES:]
        tmp = _REGISTRY_PATH.with_suffix(".tmp")
        tmp.write_text("\n".join(kept) + "\n", encoding="utf-8")
        _REGISTRY_PATH.unlink()
        tmp.rename(_REGISTRY_PATH)
    except Exception:
        pass  # Non-fatal: prune failure must not block SessionStart


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        return 0

    try:
        data = json.loads(raw.lstrip("﻿"))
    except json.JSONDecodeError:
        return 0

    if not isinstance(data, dict):
        return 0

    terminal_id = detect_terminal_id()
    if not terminal_id:
        return 0

    identity = {
        "terminal": {
            "id": terminal_id,
            "source": "WT_SESSION",
        },
        "claude": {
            "session_id": data.get("session_id", ""),
            "transcript_path": data.get("transcript_path", ""),
            "cwd": data.get("cwd", ""),
        },
        "captured_at": datetime.now(UTC).isoformat(),
    }

    safe_tid = terminal_id.replace("/", "-").replace("\\", "-").replace(":", "-")
    artifact_dir = ARTIFACTS_ROOT / safe_tid
    artifact_dir.mkdir(parents=True, exist_ok=True)
    dest = artifact_dir / "identity.json"
    tmp = dest.with_suffix(".tmp")

    tmp.write_text(json.dumps(identity, indent=2) + "\n", encoding="utf-8")
    if dest.exists():
        dest.unlink()
    tmp.rename(dest)

    # Prune session registry if it exceeds 10K lines (keep last 5K)
    _prune_session_registry()

    return 0


if __name__ == "__main__":
    sys.exit(main())
