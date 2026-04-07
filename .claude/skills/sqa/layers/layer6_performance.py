"""Layer 6 — PERFORMANCE: perf tracing, adversarial-performance bottleneck analysis."""

from __future__ import annotations

from pathlib import Path

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


def _is_command_available(cmd: str) -> bool:
    """Check if a command exists in PATH (shutil.which-style check)."""
    import shutil
    return shutil.which(cmd) is not None


def _run_adversarial_performance(target: Path) -> list[Finding]:
    """Run adversarial-performance agent analysis.

    adversarial-performance is an LLM subagent dispatched via the Agent tool from skill context.
    This Python module cannot invoke it — it returns empty findings with a clear message.

    To run adversarial performance analysis, use from skill context:
        Agent('adversarial-performance').analyze(target=target, findings=[...])

    Returns:
        Empty list — Agent dispatch is required at skill level.
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(
        "L6_PERFORMANCE: adversarial-performance requires Agent tool dispatch at skill level. "
        "Python layer returns empty findings. "
        "Use: Agent('adversarial-performance') from skill execution context."
    )
    return []