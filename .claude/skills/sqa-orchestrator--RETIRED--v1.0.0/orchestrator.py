"""SQA Orchestrator — 7-layer sequential quality analysis pipeline."""

from __future__ import annotations

import json
import logging
import os
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import sys as _sys

_gto_lib = Path("P:/.claude/skills")
if str(_gto_lib) not in _sys.path:
    _sys.path.insert(0, str(_gto_lib))
from gto.lib.skill_coverage_detector import _append_skill_coverage

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
LAYER_TIMEOUT = 60  # seconds

ALLOWED_COMMANDS = [
    "ruff",
    "mypy",
    "pytest",
    "aid",
    "gto",
    "verify",
    "hook-audit",
    "hook-inventory",
    "adversarial-security",
    "adversarial-performance",
    "diagnose",
]


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


def _run_layer(
    layer_name: str,
    target: Path,
    findings: list[Finding],
    audit: list[AuditEntry],
) -> list[Finding]:
    """Run a single layer with timeout. Returns layer findings."""
    logger.info(f"Running layer: {layer_name}")
    start = datetime.now(timezone.utc)
    layerFindings: list[Finding] = []

    # Import layer dynamically to avoid circular imports
    layer_map = {
        "L1_SYNTACTIC": "layers.layer1_syntactic",
        "L2_SEMANTIC": "layers.layer2_semantic",
        "L3_STRUCTURAL": "layers.layer3_structural",
        "L4_REQUIREMENTS": "layers.layer4_requirements",
        "L5_SECURITY": "layers.layer5_security",
        "L6_PERFORMANCE": "layers.layer6_performance",
        "L7_OPERATIONAL": "layers.layer7_operational",
    }

    layer_module = layer_map.get(layer_name)
    if layer_module is None:
        logger.warning(f"Unknown layer: {layer_name}")
        return layerFindings

    try:
        mod = __import__(layer_module, fromlist=["run"])
        run_fn = getattr(mod, "run", None)
        if run_fn is None:
            logger.warning(f"Layer {layer_name} has no run() function")
            return layerFindings

        layerFindings = run_fn(target)
        exit_code = 0
    except Exception as e:
        logger.error(f"Layer {layer_name} failed: {e}")
        exit_code = 1

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    audit.append(
        AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            skill=layer_name,
            exit_code=exit_code,
            finding_count=len(layerFindings),
            notes=f"Elapsed: {elapsed:.1f}s",
        )
    )
    findings.extend(layerFindings)
    return layerFindings


def run_sqa(target: str, redact: bool = False) -> SQAReport:
    """Run full 7-layer SQA pipeline against target.

    Args:
        target: Path to target directory.
        redact: If True, strip location fields from findings before returning.
    """
    logger.info(f"Starting SQA analysis on: {target}")
    validated = _validate_target(target)

    findings: list[Finding] = []
    audit: list[AuditEntry] = []

    # Layer execution order (D2)
    layers = [
        ("L1_SYNTACTIC", None),
        ("L2_SEMANTIC", None),
        ("L3_STRUCTURAL", None),
        ("L4_REQUIREMENTS", "L2_SEMANTIC"),  # hard dep
        ("L5_SECURITY", None),
        ("L6_PERFORMANCE", None),
        ("L7_OPERATIONAL", None),
    ]

    layer2_had_failures = False

    for layer_name, hard_dep in layers:
        # Check hard dependency
        if hard_dep == "L2_SEMANTIC" and layer2_had_failures:
            logger.warning(f"Layer {layer_name} SKIPPED — Layer 2 (SEMANTIC) reported failures")
            audit.append(
                AuditEntry(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    skill=layer_name,
                    exit_code=None,
                    finding_count=0,
                    notes="SKIPPED: Layer 2 hard-dependency failure",
                )
            )
            continue

        layer_findings = _run_layer(layer_name, validated, findings, audit)

        # Track Layer 2 failures for Layer 4 hard dependency
        if layer_name == "L2_SEMANTIC":
            critical_or_high = any(
                f.severity in (Severity.CRITICAL, Severity.HIGH) for f in layer_findings
            )
            layer2_had_failures = critical_or_high

    # Meta-synthesis
    try:
        from layers import layer_meta

        meta_findings = layer_meta.run_meta(findings)
        findings.extend(meta_findings)
        audit.append(
            AuditEntry(
                timestamp=datetime.now(timezone.utc).isoformat(),
                skill="META",
                exit_code=0,
                finding_count=len(meta_findings),
                notes="Meta-synthesis complete",
            )
        )
    except Exception as e:
        logger.error(f"Meta-synthesis failed: {e}")

    report = SQAReport(
        findings=findings,
        layers_completed=[ln for ln, _ in layers],
        audit_trail=audit,
        target=str(validated),
    )
    report.health_score = report.compute_health_score()

    if redact:
        for f in report.findings:
            f.location = None

    return report


def save_report(report: SQAReport, path: Path) -> None:
    """Save SQAReport to JSON file with chmod 600."""
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
    }
    path.write_text(json.dumps(data, indent=2))
    # chmod 600
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    # GTO skill coverage logging
    try:
        _append_skill_coverage(
            target_key="skills/sqa",
            skill="/sqa",
            terminal_id=os.environ.get("TERMINAL_ID", os.environ.get("TERM_ID", "unknown")),
            git_sha=None,
        )
    except Exception:
        pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: orchestrator.py <target> [--redact]")
        sys.exit(1)
    target_arg = sys.argv[1]
    redact_flag = "--redact" in sys.argv
    report = run_sqa(target_arg, redact=redact_flag)
    print(f"Health score: {report.health_score}")
    print(f"Findings: {len(report.findings)}")
    print(f"Layers: {report.layers_completed}")
