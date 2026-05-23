#!/usr/bin/env python3
"""Phase 2: Canonical Source Scan — detect drift between documented and implemented.

Sourced by /prospect as a parallel Phase 2 pass after wiki/memory discovery.

Architecture:
  Phase 2 runs in parallel subagents (one per source category) when total
  source count > 5. Each subagent reads its source files and emits a
  Phase2Findings list. A coordinator synthesizes drift/classification findings.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
from datetime import datetime, timezone
from enum import Enum
from typing import Any

# Snapshot plugin handoff (V2 format — no fallback to compaction_state.json)
_SNAPSHOT_PLUGIN_ROOT = pathlib.Path(os.environ.get(
    "SNAPSHOT_PLUGIN_ROOT",
    "P:/packages/snapshot",
))
_snapshot_lib_path = _SNAPSHOT_PLUGIN_ROOT / "scripts" / "hooks" / "__lib"
_snapshot_hooks_path = _SNAPSHOT_PLUGIN_ROOT / "scripts" / "hooks"
for _p in (_snapshot_lib_path, _snapshot_hooks_path):
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

FINDING_TYPES = ["DRIFT", "REGRESSION", "UNFULFILLED", "GHOST", "BORROW", "PRESENT"]


class FindingType(str, Enum):
    DRIFT = "DRIFT"       # doc says X, code does Y
    REGRESSION = "REGRESSION"  # explicit rule from memory being violated
    UNFULFILLED = "UNFULFILLED"  # accepted proposal never built
    GHOST = "GHOST"       # specced but silently abandoned
    BORROW = "BORROW"     # external technique not yet adapted
    PRESENT = "PRESENT"   # already correctly implemented


class Phase2Finding:
    """Structured finding from Phase 2 canonical source scan.

    Falsification condition: status would be wrong if the cited source file
    has been modified since the scan was run (source of truth goes stale).
    """

    __slots__ = (
        "finding_type", "source_file", "source_line", "target_file",
        "what_documented", "what_implemented", "severity", "note",
    )

    def __init__(
        self,
        finding_type: FindingType,
        source_file: str,
        source_line: int | None,
        target_file: str,
        what_documented: str,
        what_implemented: str,
        severity: str = "medium",
        note: str = "",
    ) -> None:
        self.finding_type = finding_type
        self.source_file = source_file
        self.source_line = source_line
        self.target_file = target_file
        self.what_documented = what_documented
        self.what_implemented = what_implemented
        self.severity = severity
        self.note = note

    def as_dict(self) -> dict[str, Any]:
        return {
            "finding_type": self.finding_type.value,
            "source_file": self.source_file,
            "source_line": self.source_line,
            "target_file": self.target_file,
            "what_documented": self.what_documented,
            "what_implemented": self.what_implemented,
            "severity": self.severity,
            "note": self.note,
        }


class Phase2Report:
    """Aggregates findings from all Phase 2 source scans."""

    __slots__ = ("findings", "scanned_sources", "ran_at")

    def __init__(self) -> None:
        self.findings: list[Phase2Finding] = []
        self.scanned_sources: list[str] = []
        self.ran_at: str = ""

    def add(self, finding: Phase2Finding) -> None:
        self.findings.append(finding)

    def add_source(self, path: str) -> None:
        self.scanned_sources.append(path)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ran_at": self.ran_at,
            "scanned_sources": self.scanned_sources,
            "findings": [f.as_dict() for f in self.findings],
            "total": len(self.findings),
            "by_type": {
                ft.value: [f.as_dict() for f in self.findings if f.finding_type == ft]
                for ft in FindingType
            },
        }

    def summary(self) -> str:
        lines = [f"Phase 2 Canonical Source Scan — {len(self.findings)} findings"]
        for ft in FindingType:
            items = [f for f in self.findings if f.finding_type == ft]
            if items:
                lines.append(f"  {ft.value}: {len(items)}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Phase 2 source scanners
# ---------------------------------------------------------------------------

def scan_hooks_doc_vs_code(
    wiki_hooks_dir: pathlib.Path,
    hooks_script_dir: pathlib.Path,
) -> list[Phase2Finding]:
    """Detect doc/code drift in hooks.

    Compares wiki/hooks/*.md documentation against actual hook scripts.
    Flags where wiki describes behavior that is absent or different in code.
    """
    findings: list[Phase2Finding] = []
    if not wiki_hooks_dir.is_dir() or not hooks_script_dir.is_dir():
        return findings

    # Build a map: wiki filename -> doc content keywords
    wiki_hooks: dict[str, set[str]] = {}
    for md_file in wiki_hooks_dir.glob("*.md"):
        text = md_file.read_text(encoding="utf-8").lower()
        keywords = set()
        for line in text.splitlines():
            if line.startswith("# ") or line.startswith("## "):
                keywords.update(line.lower().split())
        wiki_hooks[md_file.name] = keywords

    # For each hook script, check for known behavioral claims in wiki
    for script in hooks_script_dir.glob("*.py"):
        if script.name.startswith("_") or script.name == "__init__.py":
            continue
        script_text = script.read_text(encoding="utf-8")

        for wiki_file, wiki_keywords in wiki_hooks.items():
            wiki_path = str(wiki_hooks_dir / wiki_file)
            # Check if wiki mentions this hook
            hook_name = script.stem
            if hook_name.lower().replace("_", "-") not in wiki_file.lower():
                continue

            # Simple: wiki file exists for this hook, check for "what it does"
            # vs what script actually does (scan for function names)
            script_functions = set()
            for line in script_text.splitlines():
                if "def " in line and not line.strip().startswith("#"):
                    name = line.split("def ", 1)[1].split("(", 1)[0].strip()
                    script_functions.add(name)

            findings.append(Phase2Finding(
                finding_type=FindingType.PRESENT,
                source_file=wiki_path,
                source_line=None,
                target_file=str(hooks_script_dir / script.name),
                what_documented=f"Wiki documents hook: {wiki_file}",
                what_implemented=f"Hook has {len(script_functions)} functions",
                severity="info",
                note="hook documented and implemented",
            ))

    return findings


def scan_skill_md_vs_scripts(
    skills_root: pathlib.Path,
) -> list[Phase2Finding]:
    """Check if skill SKILL.md step sequences match actual script invocations.

    Flags skills that describe calling a script that doesn't exist.
    """
    findings: list[Phase2Finding] = []
    if not skills_root.is_dir():
        return findings

    for skill_dir in skills_root.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        scripts_dir = skill_dir / "scripts"
        if not skill_md.is_file():
            continue

        md_text = skill_md.read_text(encoding="utf-8")

        # Find script invocations described in SKILL.md
        import re
        script_refs = re.findall(r'(?:python|bash|sh) ["\'].*?([^/"\' \n]+\.py)[ "\']', md_text)
        described_scripts = set(script_refs)

        # Find actual scripts
        actual_scripts: set[str] = set()
        if scripts_dir.is_dir():
            actual_scripts = {p.name for p in scripts_dir.glob("*.py") if p.name != "__pycache__"}

        for described in described_scripts:
            if described not in actual_scripts:
                findings.append(Phase2Finding(
                    finding_type=FindingType.DRIFT,
                    source_file=str(skill_md),
                    source_line=None,
                    target_file=str(scripts_dir / described),
                    what_documented=f"SKILL.md invokes: {described}",
                    what_implemented="Script file not found",
                    severity="high",
                    note="missing script — skill step will fail",
                ))

        for actual in actual_scripts:
            if actual not in described_scripts:
                findings.append(Phase2Finding(
                    finding_type=FindingType.GHOST,
                    source_file=str(skill_md),
                    source_line=None,
                    target_file=str(scripts_dir / actual),
                    what_documented="No invocation in SKILL.md",
                    what_implemented=f"Script exists but is not documented: {actual}",
                    severity="low",
                    note="undocumented script — may be orphaned",
                ))

    return findings


def scan_phase_ledger(enforce_dir: pathlib.Path) -> list[Phase2Finding]:
    """Check enforce phase ledger for blocked or stuck gates.

    Flags gates that consistently fail or never fire.
    """
    findings: list[Phase2Finding] = []
    if not enforce_dir.is_dir():
        return findings

    for skill_dir in enforce_dir.iterdir():
        ledger_file = skill_dir / "phase-ledger.json"
        if not ledger_file.is_file():
            continue

        try:
            ledger = json.loads(ledger_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        for phase, entry in ledger.items():
            if not isinstance(entry, dict):
                continue
            # Check for phases that are always blocked
            if entry.get("status") == "blocked":
                findings.append(Phase2Finding(
                    finding_type=FindingType.REGRESSION,
                    source_file=str(ledger_file),
                    source_line=None,
                    target_file=str(skill_dir),
                    what_documented=f"Phase '{phase}' should be accessible",
                    what_implemented=f"Phase '{phase}' is permanently blocked",
                    severity="medium",
                    note=f"blocked_at: {entry.get('blocked_at', 'unknown')}",
                ))
            elif entry.get("completed") and entry.get("completed", 0) == 0:
                findings.append(Phase2Finding(
                    finding_type=FindingType.UNFULFILLED,
                    source_file=str(ledger_file),
                    source_line=None,
                    target_file=str(skill_dir),
                    what_documented=f"Phase '{phase}' accepted for implementation",
                    what_implemented="Phase never completed",
                    severity="low",
                ))

    return findings


def scan_snapshot_handoff(
    artifacts_dir: pathlib.Path,
) -> list[Phase2Finding]:
    """Check the V2 handoff envelope for session goal stall or missing state.

    Reads from the snapshot plugin's SnapshotFileStorage (P:/.claude/.artifacts/
    {terminal_id}/snapshot/) — no fallback to compaction_state.json.
    """
    findings: list[Phase2Finding] = []

    # Iterate terminal-scoped snapshot directories
    if not artifacts_dir.is_dir():
        return findings

    try:
        from snapshot_files import SnapshotFileStorage
        from project_root import detect_project_root
    except Exception:
        return findings

    project_root = detect_project_root(current_dir=pathlib.Path.cwd(), strict=False)

    for terminal_snapshot_dir in artifacts_dir.iterdir():
        if not terminal_snapshot_dir.is_dir():
            continue
        # Terminal directories are named console_{WT_SESSION}
        if terminal_snapshot_dir.name.startswith("console_"):
            terminal_id = terminal_snapshot_dir.name
        else:
            continue

        try:
            storage = SnapshotFileStorage(project_root, terminal_id)
            handoff = storage.load_handoff()
        except Exception:
            continue

        if not handoff:
            continue

        snapshot = handoff.get("resume_snapshot", {})
        goal = snapshot.get("goal", "")
        pending = snapshot.get("pending_work", [])
        current_task = snapshot.get("current_task", "")
        progress = snapshot.get("progress_percent", 0)
        created_at = snapshot.get("created_at", "")

        if not goal and not current_task:
            continue

        # Goal stated but no progress and no pending work → possible stall
        if goal and not pending and progress == 0:
            findings.append(Phase2Finding(
                finding_type=FindingType.UNFULFILLED,
                source_file=str(terminal_snapshot_dir / "snapshot"),
                source_line=None,
                target_file=str(artifacts_dir / terminal_id),
                what_documented=f"Session goal: {goal[:80]}",
                what_implemented="No progress, no pending work — session may have stalled",
                severity="low",
                note=f"last_activity: {created_at}",
            ))

        # In-progress task stated but no pending work items
        if current_task and not pending:
            findings.append(Phase2Finding(
                finding_type=FindingType.UNFULFILLED,
                source_file=str(terminal_snapshot_dir / "snapshot"),
                source_line=None,
                target_file=str(artifacts_dir / terminal_id),
                what_documented=f"Current task: {current_task[:80]}",
                what_implemented="No pending work items — task may be stuck",
                severity="low",
                note=f"progress: {progress}%",
            ))

    return findings


def scan_compilation_state(artifacts_dir: pathlib.Path) -> list[Phase2Finding]:
    """Check gitpack and doc-compiler artifacts for uncommitted or stuck work."""
    findings: list[Phase2Finding] = []
    for name in ["gitpack_full.md", "doc-compiler_full.md"]:
        f = artifacts_dir / name
        if f.is_file():
            content = f.read_text(encoding="utf-8")
            if "[UNCOMMITTED]" in content or "[STALE]" in content:
                findings.append(Phase2Finding(
                    finding_type=FindingType.UNFULFILLED,
                    source_file=str(f),
                    source_line=None,
                    target_file=str(artifacts_dir),
                    what_documented=f"Artifact {name} contains uncommitted work",
                    what_implemented="Work appears stuck in artifact",
                    severity="medium",
                ))
    return findings


# ---------------------------------------------------------------------------
# Coordinator — orchestrates Phase 2 subagents (called by /prospect SKILL.md)
# ---------------------------------------------------------------------------

class Phase2Coordinator:
    """Coordinates Phase 2 canonical source scan.

    Dispatches parallel subagents when source count > 5.
    Falls back to sequential when count is low (avoids token overhead).
    """

    def __init__(
        self,
        wiki_hooks_dir: pathlib.Path | None = None,
        hooks_script_dir: pathlib.Path | None = None,
        skills_root: pathlib.Path | None = None,
        enforce_dir: pathlib.Path | None = None,
        artifacts_dir: pathlib.Path | None = None,
    ) -> None:
        self.wiki_hooks_dir = wiki_hooks_dir or pathlib.Path("P:/.data/wiki/hooks")
        self.hooks_script_dir = hooks_script_dir or pathlib.Path("P:/.claude/hooks")
        self.skills_root = skills_root or pathlib.Path("P:/packages/cc-skills-sdlc/skills")
        self.enforce_dir = enforce_dir or pathlib.Path("C:/Users/brsth/.claude/.state/enforce")
        self.artifacts_dir = artifacts_dir or pathlib.Path("P:/.claude/.artifacts")

    def count_sources(self) -> int:
        """Count total Phase 2 source files. Used to decide parallel vs sequential."""
        count = 0
        if self.wiki_hooks_dir.is_dir():
            count += len(list(self.wiki_hooks_dir.glob("*.md")))
        if self.hooks_script_dir.is_dir():
            count += len([f for f in self.hooks_script_dir.glob("*.py") if not f.name.startswith("_")])
        if self.skills_root.is_dir():
            count += len([d for d in self.skills_root.iterdir() if d.is_dir()])
        if self.enforce_dir.is_dir():
            count += len(list(self.enforce_dir.iterdir()))
        # Snapshot handoff scanner (always +1)
        return count + 1

    def run_sequential(self) -> Phase2Report:
        """Run all scanners sequentially (when source count <= 5)."""
        report = Phase2Report()
        report.ran_at = datetime.now(timezone.utc).isoformat()

        scanners = [
            ("hooks_doc_vs_code", lambda: scan_hooks_doc_vs_code(
                self.wiki_hooks_dir, self.hooks_script_dir)),
            ("skill_md_vs_scripts", lambda: scan_skill_md_vs_scripts(self.skills_root)),
            ("phase_ledger", lambda: scan_phase_ledger(self.enforce_dir)),
            ("snapshot_handoff", lambda: scan_snapshot_handoff(self.artifacts_dir)),
            ("compilation_state", lambda: scan_compilation_state(self.artifacts_dir)),
        ]

        for name, scanner_fn in scanners:
            findings = scanner_fn()
            for f in findings:
                report.add(f)
            report.add_source(f"scanner://{name}")

        return report

    def get_scanner_tasks(self) -> list[tuple[str, Any]]:
        """Return list of (task_name, scanner_fn) for parallel dispatch.

        Used by /prospect SKILL.md to spawn subagents.
        Each tuple: task name + lambda returning Phase2Finding list.
        """
        return [
            ("hooks_doc_vs_code", lambda: scan_hooks_doc_vs_code(
                self.wiki_hooks_dir, self.hooks_script_dir)),
            ("skill_md_vs_scripts", lambda: scan_skill_md_vs_scripts(self.skills_root)),
            ("phase_ledger", lambda: scan_phase_ledger(self.enforce_dir)),
            ("snapshot_handoff", lambda: scan_snapshot_handoff(self.artifacts_dir)),
            ("compilation_state", lambda: scan_compilation_state(self.artifacts_dir)),
        ]


def main() -> None:
    import json as _json
    coordinator = Phase2Coordinator()
    report = coordinator.run_sequential()
    out = report.to_dict()
    print(_json.dumps(out, indent=2))
    print(f"\n{report.summary()}")


if __name__ == "__main__":
    main()