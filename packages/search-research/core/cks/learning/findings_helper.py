"""Convenience functions for creating diagnostic findings.

Provides skill-specific helpers for /rca, /debug, /tdd, /arch, /vdate-security
to create structured findings with minimal boilerplate.

Example:
    from src.cks.learning.findings_helper import rca_finding, store_finding

    finding = rca_finding(
        summary="Null pointer dereference",
        details="Missing null check before accessing user_data",
        file_path="contract_api.py",
        line_number=142,
    )
    store_finding(finding)

"""

from __future__ import annotations

from src.knowledge.systems.cks.learning.diagnostic_writer import DiagnosticFinding, store_finding


def rca_finding(
    summary: str,
    details: str,
    category: str = "BUG",
    file_path: str | None = None,
    line_number: int | None = None,
    confidence: str = "medium",
) -> DiagnosticFinding:
    """Create a diagnostic finding from RCA (Root Cause Analysis).

    Args:
        summary: Brief summary of the root cause
        details: Detailed explanation of the issue
        category: Finding category (default: "BUG")
        file_path: Optional file path reference
        line_number: Optional line number reference
        confidence: Confidence level (default: "medium")

    Returns:
        DiagnosticFinding instance with skill_source="rca"

    """
    return DiagnosticFinding(
        category=category,
        file_path=file_path,
        line_number=line_number,
        summary=summary,
        details=details,
        skill_source="rca",
        confidence=confidence,
    )


def debug_finding(
    summary: str,
    details: str,
    category: str = "BUG",
    file_path: str | None = None,
    line_number: int | None = None,
) -> DiagnosticFinding:
    """Create a diagnostic finding from debug session.

    Args:
        summary: Brief summary of the bug found
        details: Detailed explanation of the issue
        category: Finding category (default: "BUG")
        file_path: Optional file path reference
        line_number: Optional line number reference

    Returns:
        DiagnosticFinding instance with skill_source="debug"

    """
    return DiagnosticFinding(
        category=category,
        file_path=file_path,
        line_number=line_number,
        summary=summary,
        details=details,
        skill_source="debug",
    )


def tdd_finding(
    summary: str,
    details: str,
    category: str = "PATTERN",
    file_path: str | None = None,
    line_number: int | None = None,
) -> DiagnosticFinding:
    """Create a diagnostic finding from TDD session.

    Args:
        summary: Brief summary of the test/finding
        details: Detailed explanation
        category: Finding category (default: "PATTERN")
        file_path: Optional file path reference
        line_number: Optional line number reference

    Returns:
        DiagnosticFinding instance with skill_source="tdd"

    """
    return DiagnosticFinding(
        category=category,
        file_path=file_path,
        line_number=line_number,
        summary=summary,
        details=details,
        skill_source="tdd",
    )


def arch_finding(
    summary: str,
    details: str,
    category: str = "PATTERN",
    file_path: str | None = None,
    line_number: int | None = None,
) -> DiagnosticFinding:
    """Create a diagnostic finding from architecture analysis.

    Args:
        summary: Brief summary of the architectural finding
        details: Detailed explanation
        category: Finding category (default: "PATTERN")
        file_path: Optional file path reference
        line_number: Optional line number reference

    Returns:
        DiagnosticFinding instance with skill_source="arch"

    """
    return DiagnosticFinding(
        category=category,
        file_path=file_path,
        line_number=line_number,
        summary=summary,
        details=details,
        skill_source="arch",
    )


def security_finding(
    summary: str,
    details: str,
    category: str = "VULNERABILITY",
    file_path: str | None = None,
    line_number: int | None = None,
) -> DiagnosticFinding:
    """Create a diagnostic finding from security analysis.

    Args:
        summary: Brief summary of the security issue
        details: Detailed explanation
        category: Finding category (default: "VULNERABILITY")
        file_path: Optional file path reference
        line_number: Optional line number reference

    Returns:
        DiagnosticFinding instance with skill_source="security"

    """
    return DiagnosticFinding(
        category=category,
        file_path=file_path,
        line_number=line_number,
        summary=summary,
        details=details,
        skill_source="security",
    )


def quality_finding(
    summary: str,
    details: str,
    category: str = "PATTERN",
    file_path: str | None = None,
    line_number: int | None = None,
    confidence: str = "medium",
) -> DiagnosticFinding:
    """Create a diagnostic finding from quality analysis.

    Args:
        summary: Brief summary of the quality issue
        details: Detailed explanation
        category: Finding category (default: "PATTERN")
        file_path: Optional file path reference
        line_number: Optional line number reference
        confidence: Confidence level (default: "medium")

    Returns:
        DiagnosticFinding instance with skill_source="quality"

    """
    return DiagnosticFinding(
        category=category,
        file_path=file_path,
        line_number=line_number,
        summary=summary,
        details=details,
        skill_source="quality",
        confidence=confidence,
    )


def q_finding(
    summary: str,
    details: str,
    category: str = "PATTERN",
    file_path: str | None = None,
    line_number: int | None = None,
    confidence: str = "medium",
) -> DiagnosticFinding:
    """Create a diagnostic finding from strategic quality assessment (/q).

    Args:
        summary: Brief summary of the strategic finding
        details: Detailed explanation
        category: Finding category (default: "PATTERN")
        file_path: Optional file path reference
        line_number: Optional line number reference
        confidence: Confidence level (default: "medium")

    Returns:
        DiagnosticFinding instance with skill_source="q"

    Example:
        finding = q_finding(
            summary="Over-engineered architecture",
            details="Three-layer abstraction for simple CRUD operation",
            category="PATTERN",
            confidence="high",
        )

    """
    return DiagnosticFinding(
        category=category,
        file_path=file_path,
        line_number=line_number,
        summary=summary,
        details=details,
        skill_source="q",
        confidence=confidence,
    )


def p_finding(
    summary: str,
    details: str,
    category: str = "BUG",
    file_path: str | None = None,
    line_number: int | None = None,
    confidence: str = "medium",
) -> DiagnosticFinding:
    """Create a diagnostic finding from tactical quality assessment (/p).

    Args:
        summary: Brief summary of the tactical finding
        details: Detailed explanation
        category: Finding category (default: "BUG")
        file_path: Optional file path reference
        line_number: Optional line number reference
        confidence: Confidence level (default: "medium")

    Returns:
        DiagnosticFinding instance with skill_source="p"

    Example:
        finding = p_finding(
            summary="Missing test coverage",
            details="Function authenticate_user() has no unit tests",
            category="BUG",
            confidence="high",
        )

    """
    return DiagnosticFinding(
        category=category,
        file_path=file_path,
        line_number=line_number,
        summary=summary,
        details=details,
        skill_source="p",
        confidence=confidence,
    )


def store_quick_finding(
    skill: str,
    summary: str,
    details: str,
    category: str = "DISCOVERY",
    file_path: str | None = None,
    line_number: int | None = None,
) -> bool:
    """Quickly create and store a finding in one call.

    Convenience function for one-off findings without creating
    a DiagnosticFinding object explicitly.

    Args:
        skill: Skill source (e.g., "rca", "debug", "arch", "security")
        summary: Brief summary of the finding
        details: Detailed explanation
        category: Finding category (default: "DISCOVERY")
        file_path: Optional file path reference
        line_number: Optional line number reference

    Returns:
        True if successfully stored, False on error

    Example:
        store_quick_finding(
            skill="rca",
            summary="Missing null check",
            details="Function doesn't validate user_data before access",
            file_path="contract_api.py",
            line_number=142,
        )

    """
    finding = DiagnosticFinding(
        category=category,
        file_path=file_path,
        line_number=line_number,
        summary=summary,
        details=details,
        skill_source=skill,
    )
    return store_finding(finding)


def batch_findings(findings: list[DiagnosticFinding]) -> dict[str, bool]:
    """Store multiple findings and return success status for each.

    Args:
        findings: List of DiagnosticFinding instances to store

    Returns:
        Dict mapping summary → success status (True/False)

    Example:
        results = batch_findings([
            rca_finding("Issue 1", "Details 1"),
            debug_finding("Issue 2", "Details 2"),
        ])
        # {"Issue 1": True, "Issue 2": False}

    """
    results = {}
    for finding in findings:
        results[finding.summary] = store_finding(finding)
    return results


__all__ = [
    "DiagnosticFinding",
    "arch_finding",
    "batch_findings",
    "debug_finding",
    "p_finding",
    "q_finding",
    "quality_finding",
    "rca_finding",
    "security_finding",
    "store_finding",
    "store_quick_finding",
    "tdd_finding",
]
