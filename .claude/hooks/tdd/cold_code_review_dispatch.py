"""
Cold Code Review Dispatch for Clean-Room TDD Loop v2.

Dispatches blinded adversarial review after GREEN phase.
The reviewer is blinded from spec/plan to evaluate code strictly on merits.

ADR: P:/.claude/arch_decisions/ADR-20260324-clean-room-tdd-loop.md
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ColdReviewResult:
    """Result of cold code review dispatch."""

    passed: bool
    findings: list[dict[str, Any]]
    severity: str  # "none" | "low" | "medium" | "high"
    reviewer_notes: str = ""
    blindness_verified: bool = False


def should_dispatch_review(
    impl_path: str,
    phase: Any,
    state_dir: Path | None = None,
) -> bool:
    """Determine if review should be dispatched based on phase.

    Review is dispatched after GREEN phase to signal that a task is moving
    to REFACTOR.

    Args:
        impl_path: Path to implementation file
        phase: Current TDD phase
        state_dir: Optional state directory

    Returns:
        True if review should be dispatched, False otherwise
    """
    from tdd.tdd_phase_state import TDDPhaseState

    # Dispatch review after GREEN phase only
    return phase == TDDPhaseState.GREEN


def build_review_context(
    impl_path: str,
    test_paths: list[str],
    spec_path: str | None = None,
) -> dict[str, Any]:
    """Build review context for blinded adversarial review.

    The reviewer is intentionally blinded to the spec/plan to evaluate
    code strictly on merits.

    Args:
        impl_path: Path to implementation file
        test_paths: List of test file paths
        spec_path: Optional path to spec file (NOT included in context)

    Returns:
        Dict with impl_path, impl_content, test_paths, test_content
    """
    from pathlib import Path

    context: dict[str, Any] = {
        "impl_path": impl_path,
        "impl_content": "",
        "test_paths": test_paths,
        "test_content": "",
    }

    # Read impl file content
    impl = Path(impl_path)
    if impl.exists():
        context["impl_content"] = impl.read_text(encoding="utf-8")

    # Read test files content
    test_contents = []
    for test_path_str in test_paths:
        test_path = Path(test_path_str)
        if test_path.exists():
            test_contents.append(test_path.read_text(encoding="utf-8"))
    context["test_content"] = "\n\n".join(test_contents)

    # Note: spec_path is intentionally NOT included in context
    # This enforces the "blinded" aspect of cold code review

    return context


def build_blinded_prompt(
    impl_path: str,
    test_paths: list[str],
) -> str:
    """Build prompt for blinded adversarial review.

    The reviewer is intentionally blinded to the spec/plan to evaluate
    code strictly on merits.

    Args:
        impl_path: Path to implementation file
        test_paths: List of test file paths

    Returns:
        Prompt string for adversarial review
    """
    return f"""
Review this implementation for correctness, security, and quality.

IMPORTANT: You do NOT have access to the original spec or implementation plan.
Evaluate strictly on code merits.

Implementation: {impl_path}
Tests: {", ".join(test_paths)}

Focus on: logic errors, edge cases, security vulnerabilities, style issues, and potential bugs.

Do NOT reference any spec.md, plan.md, or requirements documents.
"""


def extract_findings_from_result(result: dict[str, Any]) -> ColdReviewResult:
    """Extract findings from review result.

    Args:
        result: Raw review result from adversarial agent

    Returns:
        ColdReviewResult with structured findings
    """
    findings = result.get("findings", [])
    severity = result.get("severity", "none")
    reviewer_notes = result.get("reviewer_notes", "")

    # Verify blindness (no spec/plan references)
    blindness_verified = True
    if result.get("spec_referenced") or result.get("plan_referenced"):
        blindness_verified = False
        logger.warning("Review may have violated blindness contract")

    return ColdReviewResult(
        passed=len(findings) == 0 or severity == "none",
        findings=findings,
        severity=severity,
        reviewer_notes=reviewer_notes,
        blindness_verified=blindness_verified,
    )


def dispatch_cold_code_review(
    impl_path: str,
    test_paths: list[str],
    phase: Any,
    state_dir: Path | None = None,
) -> ColdReviewResult:
    """Dispatch cold code review for an implementation.

    This is a placeholder for the actual Agent tool dispatch.
    In production, this would invoke the adversarial-review subagent.

    Args:
        impl_path: Path to implementation file
        test_paths: List of test file paths
        phase: Current TDD phase
        state_dir: Optional state directory

    Returns:
        ColdReviewResult with review findings
    """
    # Check if we should dispatch
    if not should_dispatch_review(impl_path, phase, state_dir):
        return ColdReviewResult(
            passed=True,
            findings=[],
            severity="none",
            reviewer_notes="Review not required for current phase",
            blindness_verified=True,
        )

    # Build blinded prompt
    prompt = build_blinded_prompt(impl_path, test_paths)

    # In production, this would dispatch to adversarial-review agent:
    # result = Agent(
    #     subagent_type="adversarial-review",
    #     prompt=prompt,
    #     description="Cold Code Review",
    # )
    #
    # For now, return a placeholder result
    logger.info(f"Cold code review would be dispatched for {impl_path}")

    return ColdReviewResult(
        passed=True,
        findings=[{"type": "placeholder", "message": "Review dispatch ready"}],
        severity="none",
        reviewer_notes="Production dispatch would use adversarial-review agent",
        blindness_verified=True,
    )
