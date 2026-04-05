"""SQA Orchestrator — Pure utilities only. No orchestration logic.

This module provides utility functions for SQA. The actual orchestration
(the CONDUCTOR) is the LLM executing the SKILL.md workflow.

What stays here (utilities):
- _validate_target: path validation with resource bounds
- _atomic_write: safe atomic file writes
- _get_terminal_state_dir: terminal-isolated state
- L2State: checkpoint dataclass
- SQAReport: report dataclass
- save_report: atomic report persistence

What does NOT belong here (orchestration — done by LLM in SKILL.md):
- Layer execution order
- Agent tool dispatch for adversarial layers
- Parallel vs sequential layer grouping
- Hard dependency logic (L2 → L4)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from findings.models import (
    AuditEntry,
    Finding,
    Severity,
    SQAReport,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

MAX_FILES = 10_000
MAX_TOTAL_SIZE = 100 * 1024 * 1024  # 100MB

ALLOWED_COMMANDS = [
    "ruff",
    "mypy",
    "pytest",
    "aid",
    "gto",
    "verify",
    "hook-audit",
    "hook-inventory",
    "diagnose",
]


@dataclass
class L2State:
    """Checkpoint state persisted after Layer 2 completes."""

    layer2_had_failures: bool
    target: str


def _atomic_write(path: Path, data: str) -> None:
    """Write data atomically using os.replace() with a temp file.

    os.replace() is atomic on all POSIX and Windows Vista+.
    No chmod() call — any post-write operation would break atomicity.
    """
    tmp = path.with_suffix(".tmp")
    tmp.write_text(data)
    os.replace(str(tmp), str(path))


def _get_terminal_state_dir() -> Path:
    """Return terminal-scoped state directory with sanitized terminal_id.

    Fallback chain: CLAUDE_TERMINAL_ID -> TERMINAL_ID -> "default"
    Sanitization strips any char not in [a-zA-Z0-9_-] to prevent path traversal.
    """
    raw_id = os.environ.get("CLAUDE_TERMINAL_ID", os.environ.get("TERMINAL_ID", "default"))
    terminal_id = re.sub(r"[^a-zA-Z0-9_-]", "", raw_id) or "default"
    state_root = Path.home() / ".claude" / "sqa_state" / f"terminal_{terminal_id}"
    state_root.mkdir(parents=True, exist_ok=True)
    return state_root


def _validate_target(target: str) -> Path:
    """Validate and resolve target path. Raises AssertionError on failure."""
    resolved = Path(os.path.realpath(target))
    assert resolved.exists(), f"Target {target} does not exist"
    assert resolved.is_dir(), f"Target {target} is not a directory"
    assert not resolved.is_symlink(), f"Target {target} is a symlink"
    allowed_roots = [Path.cwd()]
    assert any(
        resolved.is_relative_to(r) for r in allowed_roots
    ), f"Target {target} outside allowed roots"
    # Resource bounds
    files = list(resolved.rglob("*"))
    file_count = sum(1 for f in files if f.is_file())
    total_size = sum(f.stat().st_size for f in files if f.is_file())
    assert file_count <= MAX_FILES, f"Target exceeds {MAX_FILES} file limit ({file_count})"
    assert (
        total_size <= MAX_TOTAL_SIZE
    ), f"Target exceeds {MAX_TOTAL_SIZE // (1024 * 1024)}MB limit ({total_size // (1024 * 1024)}MB)"
    return resolved


def _check_command(cmd: str) -> None:
    """Validate command against ALLOWED_COMMANDS."""
    cmd_name = cmd.split()[0] if isinstance(cmd, str) else cmd[0]
    assert cmd_name in ALLOWED_COMMANDS, f"Command {cmd_name} not in ALLOWED_COMMANDS"


def save_report(report: SQAReport, _path: Path | None) -> None:
    """Save SQAReport to terminal-isolated, atomic-written JSON file.

    Report lands in ~/.claude/sqa_reports/terminal_{tid}/{target_hash}.json.
    Uses os.replace() for true atomicity — no chmod() post-write.
    """
    raw_id = os.environ.get("CLAUDE_TERMINAL_ID", os.environ.get("TERMINAL_ID", "default"))
    terminal_id = re.sub(r"[^a-zA-Z0-9_-]", "", raw_id) or "default"
    report_dir = Path.home() / ".claude" / "sqa_reports" / f"terminal_{terminal_id}"
    report_dir.mkdir(parents=True, exist_ok=True)
    target_hash = hashlib.sha256(report.target.encode()).hexdigest()[:16]
    terminal_path = report_dir / f"{target_hash}.json"
    data = {
        "findings": [
            {
                "finding_id": f.finding_id,
                "severity": f.severity.value,
                "layer": f.layer.value,
                "title": f.title,
                "description": f.description,
                "location": f.location,
                "evidence_tier": f.evidence_tier.value,
                "consensus": f.consensus,
                "category": f.category,
                "evidence": [
                    {
                        "tier": e.tier.value,
                        "description": e.description,
                        "location": e.location,
                    }
                    for e in f.evidence
                ],
            }
            for f in report.findings
        ],
        "health_score": report.health_score,
        "layers_completed": report.layers_completed,
        "audit_trail": [
            {
                "timestamp": a.timestamp,
                "skill": a.skill,
                "exit_code": a.exit_code,
                "finding_count": a.finding_count,
                "notes": a.notes,
            }
            for a in report.audit_trail
        ],
        "target": report.target,
        "timestamp": report.timestamp,
    }
    _atomic_write(terminal_path, json.dumps(data, indent=2))


if __name__ == "__main__":
    print("SQA utilities module. Run via /sqa skill, not directly.")
    print("This module provides: _validate_target, _atomic_write, _get_terminal_state_dir,")
    print("L2State, SQAReport, save_report")
    print("No orchestration logic — orchestration is done by the LLM via SKILL.md")
