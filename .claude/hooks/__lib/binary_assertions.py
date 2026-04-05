#!/usr/bin/env python3
"""Binary assertion framework for skill verification.

This module provides reusable assertion patterns for skill-based verification hooks.
Skills can define their own assertions and use the framework to execute them.

Exit codes:
    0: All assertions passed
    1: One or more assertions failed
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class AssertionResult:
    """Result of a single assertion check.

    Attributes:
        passed: Whether the assertion passed
        message: Human-readable description of the result
        assertion_id: Identifier for the assertion (e.g., "A1", "A2")
        description: What the assertion checks (e.g., "Artifacts exist")
    """

    passed: bool
    message: str
    assertion_id: str
    description: str

    def __str__(self) -> str:
        status = "✓" if self.passed else "✗"
        return f"{status} {self.assertion_id}: {self.message}"


class AssertionFramework:
    """Framework for running binary assertions on skill state.

    Skills can define their own assertions by extending this class or
    by providing a list of assertion functions.

    Example:
        framework = AssertionFramework("MySkill")

        @framework.assertion("A1", "Artifacts exist")
        def check_artifacts(state_dir: Path) -> tuple[bool, str]:
            return state_dir.exists(), f"State dir exists: {state_dir}"

        results = framework.run_all(state_dir=Path(".evidence/myskill"))
        if framework.all_passed(results):
            print("All assertions passed!")
    """

    def __init__(self, skill_name: str):
        """Initialize the assertion framework.

        Args:
            skill_name: Name of the skill (for logging)
        """
        self.skill_name = skill_name
        self.assertions: list[tuple[str, str, callable]] = []

    def assertion(self, assertion_id: str, description: str):
        """Decorator to register an assertion function.

        Args:
            assertion_id: Identifier for the assertion (e.g., "A1", "A2")
            description: What the assertion checks

        Returns:
            Decorator function

        Example:
            @framework.assertion("A1", "Artifacts exist")
            def check_artifacts(state_dir: Path) -> tuple[bool, str]:
                return state_dir.exists(), "State directory found"
        """

        def decorator(func: callable) -> callable:
            self.assertions.append((assertion_id, description, func))
            return func

        return decorator

    def run_all(
        self,
        state_dir: Path,
        session_start: datetime | None = None,
        **kwargs,
    ) -> list[AssertionResult]:
        """Run all registered assertions.

        Args:
            state_dir: Directory containing skill state/artifacts
            session_start: Session start time for recency checks
            **kwargs: Additional arguments passed to assertion functions

        Returns:
            List of AssertionResult objects
        """
        results = []

        for assertion_id, description, check_func in self.assertions:
            try:
                # Call assertion function with state_dir and other args
                passed, message = check_func(
                    state_dir,
                    session_start=session_start,
                    **kwargs,
                )
                results.append(
                    AssertionResult(
                        passed=passed,
                        message=message,
                        assertion_id=assertion_id,
                        description=description,
                    )
                )
            except Exception as e:
                # Assertion function failed - record as failed
                results.append(
                    AssertionResult(
                        passed=False,
                        message=f"Assertion error: {e}",
                        assertion_id=assertion_id,
                        description=description,
                    )
                )

        return results

    def all_passed(self, results: list[AssertionResult]) -> bool:
        """Check if all assertions passed.

        Args:
            results: List of AssertionResult objects

        Returns:
            True if all assertions passed, False otherwise
        """
        return all(result.passed for result in results)

    def get_score(self, results: list[AssertionResult]) -> tuple[int, int]:
        """Get assertion score.

        Args:
            results: List of AssertionResult objects

        Returns:
            Tuple of (passed_count, total_count)
        """
        passed = sum(1 for r in results if r.passed)
        total = len(results)
        return passed, total

    def format_results(self, results: list[AssertionResult]) -> str:
        """Format assertion results for display.

        Args:
            results: List of AssertionResult objects

        Returns:
            Formatted string output
        """
        passed, total = self.get_score(results)
        score_percent = int(passed * 100 / total) if total > 0 else 0

        output = [f"{self.skill_name} ASSERTIONS: {passed}/{total}"]
        output.append("")

        for result in results:
            output.append(str(result))

        output.append("")
        if self.all_passed(results):
            output.append("ALL_ASSERTIONS_PASSED: true")
            output.append(f"SCORE: {score_percent}/100")
        else:
            output.append(f"SCORE: {score_percent}/100")

        return "\n".join(output)


# Common assertion functions that can be reused across skills


def check_artifacts_exist(
    state_dir: Path,
    session_start: datetime | None = None,
    patterns: list[str] | None = None,
) -> tuple[bool, str]:
    """Check that artifacts exist in state directory.

    Args:
        state_dir: Directory containing skill artifacts
        session_start: Session start time for recency check
        patterns: Glob patterns to match (default: ["*.md", "*.json"])

    Returns:
        Tuple of (passed, message)
    """
    if not state_dir.exists():
        return False, f"State directory does not exist: {state_dir}"

    now = datetime.now()
    time_threshold = (
        session_start if session_start else now - __import__("datetime").timedelta(hours=1)
    )

    patterns = patterns or ["*.md", "*.json"]
    recent_files = []

    for pattern in patterns:
        for match in state_dir.glob(pattern):
            mtime = datetime.fromtimestamp(match.stat().st_mtime)
            if mtime >= time_threshold:
                recent_files.append(match.name)

    if len(recent_files) >= 1:
        return True, f"Found {len(recent_files)} recent artifact(s): {', '.join(recent_files[:3])}"

    if session_start:
        return False, f"No artifacts found since session start ({session_start.isoformat()})"
    return False, "No recent artifacts found (need at least 1 in last hour)"


def check_directory_accessible(state_dir: Path, **kwargs) -> tuple[bool, str]:
    """Check that state directory is accessible.

    Args:
        state_dir: Directory to check
        **kwargs: Ignored (for interface compatibility)

    Returns:
        Tuple of (passed, message)
    """
    if not state_dir.exists():
        return False, f"State directory does not exist: {state_dir}"

    if not state_dir.is_dir():
        return False, f"State path exists but is not a directory: {state_dir}"

    try:
        files = list(state_dir.glob("*"))
        return True, f"State directory accessible: {len(files)} files found"
    except Exception as e:
        return False, f"Cannot access state directory: {e}"


def check_git_valid(project_root: Path, **kwargs) -> tuple[bool, str]:
    """Check that git repository is valid.

    Args:
        project_root: Project root directory
        **kwargs: Ignored (for interface compatibility)

    Returns:
        Tuple of (passed, message)
    """
    git_dir = project_root / ".git"

    if not git_dir.exists():
        return False, f"No .git directory found in {project_root}"

    if not git_dir.is_dir():
        return False, f".git exists but is not a directory in {project_root}"

    head_file = git_dir / "HEAD"
    if not head_file.exists():
        return False, "No HEAD file in .git directory"

    return True, f"Valid git repository: {project_root}"
