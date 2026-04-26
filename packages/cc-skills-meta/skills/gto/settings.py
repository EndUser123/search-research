from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import os
from datetime import datetime, timezone


@dataclass(frozen=True)
class GTOPaths:
    root: Path
    artifacts_dir: Path
    state_dir: Path
    inputs_dir: Path
    outputs_dir: Path
    logs_dir: Path


@dataclass(frozen=True)
class GTOSettings:
    terminal_id: str
    session_id: str
    git_sha: str | None
    root: Path
    mode: str = "full"

    @property
    def paths(self) -> GTOPaths:
        base = self.root / ".claude" / ".artifacts" / self.terminal_id / "gto"
        return GTOPaths(
            root=self.root,
            artifacts_dir=base,
            state_dir=base / "state",
            inputs_dir=base / "inputs",
            outputs_dir=base / "outputs",
            logs_dir=base / "logs",
        )


def detect_terminal_id() -> str:
    """Canonical terminal ID detection matching /id and hook patterns.

    Priority:
    1. CLAUDE_TERMINAL_ID (set by SessionStart hook)
    2. WT_SESSION (Windows Terminal UUID, normalized to console_ prefix)
    3. PID+timestamp hash fallback
    """
    # Priority 1: explicit env override
    value = os.environ.get("CLAUDE_TERMINAL_ID", "").strip()
    if value:
        return value

    # Priority 2: Windows Terminal session UUID
    wt_session = os.environ.get("WT_SESSION", "").strip()
    if wt_session:
        return f"console_{wt_session}"

    # Priority 3: PID+timestamp hash (stable within session)
    pid = os.getpid()
    ts = int(datetime.now(timezone.utc).timestamp())
    unique = f"{pid}_{ts}".encode()
    return hashlib.sha1(unique).hexdigest()[:12]
