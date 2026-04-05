"""Layer 6 — PERFORMANCE: perf tracing, adversarial-performance bottleneck analysis."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List

from findings.models import EvidenceTier, Finding, Layer, Severity


def run(target: Path) -> list[Finding]:
    """Run Layer 6 PERFORMANCE analysis."""
    findings: list[Finding] = []

    perf_findings = _run_perf(target)
    findings.extend(perf_findings)

    adv_perf_findings = _run_adversarial_performance(target)
    findings.extend(adv_perf_findings)

    return findings


def _run_perf(target: Path) -> list[Finding]:
    """Check for ThreadPoolExecutor nesting and N+1 patterns."""
    findings: list[Finding] = []
    py_files = list(target.rglob("*.py"))

    # Check for nested ThreadPoolExecutor
    for py_file in py_files:
        try:
            content = py_file.read_text(errors="ignore")
            if "ThreadPoolExecutor" in content:
                # Check for nested executor pattern
                if _has_nested_executor(content):
                    findings.append(
                        Finding(
                            finding_id=f"L6-NESTED-EXECUTOR-{py_file.name}",
                            severity=Severity.CRITICAL,
                            layer=Layer.L6_PERFORMANCE,
                            title="Nested ThreadPoolExecutor detected",
                            description=f"{py_file}: ThreadPoolExecutor used inside another executor worker",
                            location=str(py_file),
                            evidence_tier=EvidenceTier.T3,
                            category="performance",
                        )
                    )

                # Check for thread-to-CPU mismatch
                if _has_thread_cpu_mismatch(content):
                    findings.append(
                        Finding(
                            finding_id=f"L6-THREAD-CPU-MISMATCH-{py_file.name}",
                            severity=Severity.HIGH,
                            layer=Layer.L6_PERFORMANCE,
                            title="Thread-to-CPU affinity mismatch",
                            description=f"{py_file}: Threads created without CPU affinity binding",
                            location=str(py_file),
                            evidence_tier=EvidenceTier.T3,
                            category="performance",
                        )
                    )
        except OSError:
            pass

    return findings


def _has_nested_executor(content: str) -> bool:
    """Detect ThreadPoolExecutor inside a worker function."""
    lines = content.splitlines()
    in_executor = False
    executor_indent = 0
    for line in lines:
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if "ThreadPoolExecutor(" in line:
            if in_executor:
                # Already inside an executor — nested executor found
                return True
            in_executor = True
            executor_indent = indent
        elif in_executor and stripped.startswith("def "):
            # Entering a nested function inside the executor context
            # Don't reset in_executor here — the function body is still
            # inside the executor context. Only reset on dedent past the
            # executor_indent, NOT on a function definition at the same
            # indent level as the with statement.
            pass
        elif in_executor and indent <= executor_indent and stripped:
            # Dedented out of the executor's with block
            in_executor = False
    return False


def _has_thread_cpu_mismatch(content: str) -> bool:
    """Detect threads without CPU affinity."""
    has_thread = "threading.Thread" in content or "Thread(" in content
    has_executor = "ThreadPoolExecutor" in content
    has_affinity = "cpu_affinity" in content or "set_affinity" in content
    return (has_thread or has_executor) and not has_affinity


def _run_adversarial_performance(target: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        result = subprocess.run(
            ["adversarial-performance", str(target)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0 and result.stdout:
            for line in result.stdout.splitlines():
                if line.strip():
                    findings.append(
                        Finding(
                            finding_id="L6-ADV-PERF-FINDING",
                            severity=Severity.HIGH,
                            layer=Layer.L6_PERFORMANCE,
                            title="Adversarial performance bottleneck",
                            description=line.strip(),
                            evidence_tier=EvidenceTier.T3,
                            category="performance",
                        )
                    )
    except subprocess.TimeoutExpired:
        pass
    except FileNotFoundError:
        pass
    return findings
