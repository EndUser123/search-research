"""Layer 5 — SECURITY: path traversal, adversarial-security, anti-bleed gates."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from findings.models import EvidenceTier, Finding, Layer, Severity

# io-validation patterns from UCI agent_triggers — replaces crude _is_validated_open heuristic
_IO_VALIDATION_PATTERNS: list[str] = [
    r"open\s*\(",  # file open
    r"Path\s*\(",  # Path(...)
    r"path\.join",  # path.join
    r"pathlib",  # pathlib usage
    r"\.exists\(",  # exists()
    r"\.mkdir\(",  # mkdir
    r"\.rmdir\(",  # rmdir
    r"\.remove\(",  # remove
    r"\.unlink\(",  # unlink
    r"\.write_text\(",  # write_text
    r"\.read_text\(",  # read_text
    r"\.read_bytes\(",  # read_bytes
    r"shutil\.",  # shutil operations
    r"os\.remove",  # os.remove
    r"os\.path",  # os.path operations
    r"file_exists",  # file_exists check
    r"ensure_dir",  # ensure directory exists
    r"validate_path",  # path validation
    r"sanitize_path",  # path sanitization
]

# invariant patterns for integrity checks
_INVARIANT_PATTERNS: list[str] = [
    r"\bunique\b",
    r"\buuid\b",
    r"constraint",
    r"foreign.?key",
    r"referential.?integrity",
    r"\batomic\b",
    r"transaction",
    r"rollback",
    r"commit",
    r"dedupe",
    r"deduplicate",
    r"duplicate.*check",
    r"id\s*=",  # ID assignment
    r"generate_id",
    r"new_id",
    r"cursor\.lastrowid",
    r"RETURNING.*id",
    r"ON CONFLICT",
    r"UNIQUE\s+CONSTRAINT",
]

# Validation keywords that indicate a path operation is guarded
_VALIDATION_KEYWORDS: list[str] = [
    "assert",
    "validate",
    "realpath",
    "is_relative_to",
    "safepath",
    "normalize",
    "resolve",
    "absolute",
]

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


def _is_command_available(cmd: str) -> bool:
    """Check if a command exists in PATH (shutil.which-style check)."""
    import shutil
    return shutil.which(cmd) is not None


def _check_command(cmd: str) -> None:
    """Validate command against ALLOWED_COMMANDS (allowlist, not availability)."""
    cmd_name = cmd.split()[0] if isinstance(cmd, str) else cmd[0]
    assert cmd_name in ALLOWED_COMMANDS, f"Command {cmd_name} not in ALLOWED_COMMANDS"


def _check_path_traversal(target: Path) -> list[Finding]:
    """Check for path traversal and I/O vulnerabilities using UCI trigger patterns."""
    findings: list[Finding] = []
    py_files = list(target.rglob("*.py"))

    for py_file in py_files:
        try:
            content = py_file.read_text(errors="ignore")
            content_by_line = content.splitlines()

            # Check each line for dangerous I/O patterns
            for i, line in enumerate(content_by_line, 1):
                if _has_dangerous_io_pattern(line) and not _is_validated_line(
                    line, content_by_line, i
                ):
                    findings.append(
                        Finding(
                            finding_id=f"L5-PATH-TRAV-{py_file.name}-{i}",
                            severity=Severity.CRITICAL,
                            layer=Layer.L5_SECURITY,
                            title="Potentially unsafe path operation — unvalidated input",
                            description=f"{py_file}:{i}: {line.strip()}",
                            location=f"{py_file}:{i}",
                            evidence_tier=EvidenceTier.T3,
                            category="security",
                        )
                    )

            # Check for invariant/integrity violations (file-level, not per-line)
            invariant_matches = _count_invariant_violations(content)
            if invariant_matches >= 2:
                findings.append(
                    Finding(
                        finding_id=f"L5-INTEGRITY-{py_file.name}",
                        severity=Severity.HIGH,
                        layer=Layer.L5_SECURITY,
                        title=f"Potential integrity constraint issue — {invariant_matches} risk signals",
                        description=f"{py_file}: Multiple invariant violation patterns detected: transaction/atomic/unique without proper constraint handling",
                        location=str(py_file),
                        evidence_tier=EvidenceTier.T3,
                        category="integrity",
                    )
                )
        except OSError:
            pass

    return findings


def _has_dangerous_io_pattern(line: str) -> bool:
    """Check if a line contains a dangerous I/O operation pattern."""
    for pattern in _IO_VALIDATION_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    return False


def _is_validated_line(
    line: str, lines: list[str] | None = None, line_num: int = 0
) -> bool:
    """Check if a dangerous line has explicit validation nearby (±3 lines)."""
    # If the line itself has validation, it's guarded
    for kw in _VALIDATION_KEYWORDS:
        if kw.lower() in line.lower():
            return True

    # Check surrounding lines for validation context
    _lines = lines if lines is not None else [line]
    start = max(0, line_num - 4)
    end = min(len(_lines), line_num + 2)
    context = "\n".join(_lines[start:end])
    for kw in _VALIDATION_KEYWORDS:
        if kw.lower() in context.lower():
            return True
    return False


def _count_invariant_violations(content: str) -> int:
    """Count invariant/integrity violation patterns in content."""
    count = 0
    for pattern in _INVARIANT_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            count += 1
    return count


def _run_adversarial_security(target: Path) -> list[Finding]:
    """Run adversarial-security agent. Requires Agent tool dispatch from skill context.

    adversarial-security is an LLM subagent — not a CLI tool.
    This module cannot invoke it via subprocess.
    """
    import logging
    logger = logging.getLogger(__name__)

    findings: list[Finding] = []

    if not _is_command_available("adversarial-security"):
        logger.warning(
            "adversarial-security is an LLM subagent (Agent tool), not a CLI tool. "
            "It cannot be invoked via subprocess. "
            "From skill context, use: Agent('adversarial-security').analyze(target, findings=[...])"
        )
        return findings

    _check_command("adversarial-security")
    try:
        result = subprocess.run(
            ["adversarial-security", str(target)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0 and result.stdout:
            for line in result.stdout.splitlines():
                if line.strip():
                    findings.append(
                        Finding(
                            finding_id="L5-ADV-SEC-FINDING",
                            severity=Severity.HIGH,
                            layer=Layer.L5_SECURITY,
                            title="Adversarial security finding",
                            description=line.strip(),
                            evidence_tier=EvidenceTier.T3,
                            category="security",
                        )
                    )
    except subprocess.TimeoutExpired:
        logger.warning("adversarial-security timed out after 60s")
    except FileNotFoundError:
        logger.warning("adversarial-security command not found in PATH")
    return findings


def _check_anti_bleed(target: Path) -> list[Finding]:
    """Check for data-safety guards on VCS operations."""
    import logging
    logger = logging.getLogger(__name__)

    findings: list[Finding] = []

    if not _is_command_available("data-safety-vcs"):
        logger.warning(
            "data-safety-vcs not found in PATH — skipping anti-bleed check. "
            "Install data-safety-vcs or ensure it is on PATH to enable VCS safety verification."
        )
        return findings

    try:
        result = subprocess.run(
            ["data-safety-vcs", "--verify", str(target)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0 and result.stdout:
            for line in result.stdout.splitlines():
                if line.strip():
                    findings.append(
                        Finding(
                            finding_id="L5-ANTI-BLEED-MISSING",
                            severity=Severity.MEDIUM,
                            layer=Layer.L5_SECURITY,
                            title="Missing data-safety guard on VCS operation",
                            description=line.strip(),
                            evidence_tier=EvidenceTier.T3,
                            category="safety",
                        )
                    )
    except subprocess.TimeoutExpired:
        logger.warning("data-safety-vcs timed out after 60s")
    except FileNotFoundError:
        logger.warning("data-safety-vcs command not found in PATH")
    return findings


def run(target: Path) -> list[Finding]:
    """Run Layer 5 SECURITY analysis."""
    findings: list[Finding] = []

    pt_findings = _check_path_traversal(target)
    findings.extend(pt_findings)

    sec_findings = _run_adversarial_security(target)
    findings.extend(sec_findings)

    bleed_findings = _check_anti_bleed(target)
    findings.extend(bleed_findings)

    return findings
