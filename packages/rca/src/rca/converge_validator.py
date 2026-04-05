"""Converge Criteria Validator for rca Tier 1.

Validates that solutions meet convergence criteria before marking done:
- Hypothesis score > 0.7
- 100% test pass in impacted modules
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def _load_settings():
    """Lazy load settings to avoid import issues."""
    from .config import _load_settings as _load
    return _load()


class ConvergeValidator:
    """Validates convergence criteria for root cause analysis solutions.

    Per the 5-phase RCA protocol, a solution converges when:
    1. Hypothesis score > 0.7 (high confidence)
    2. 100% test pass in impacted modules (no regressions)

    Attributes:
        score_threshold: Minimum hypothesis score (default 0.7).
        test_threshold: Minimum test pass rate (default 1.0 for 100%).
        impacted_modules: List of module paths to validate.

    Examples:
        >>> validator = ConvergeValidator(
        ...     score_threshold=0.7,
        ...     impacted_modules=["src/rca/tier1"]
        ... )
        >>> validator.validate(hypothesis_score=0.85)
        ValidationResult(is_valid=True, score_met=True, tests_met=True)
    """

    # Default score threshold per specification
    DEFAULT_SCORE_THRESHOLD = 0.7
    # Default test threshold (100% pass required)
    DEFAULT_TEST_THRESHOLD = 1.0

    def __init__(
        self,
        score_threshold: float = DEFAULT_SCORE_THRESHOLD,
        test_threshold: float = DEFAULT_TEST_THRESHOLD,
        impacted_modules: Optional[List[str]] = None,
    ):
        """Initialize the converge validator.

        Args:
            score_threshold: Minimum hypothesis score (default 0.7).
            test_threshold: Minimum test pass rate (0.0 to 1.0, default 1.0).
            impacted_modules: List of module paths to validate tests for.
        """
        self.score_threshold = score_threshold
        self.test_threshold = test_threshold
        self.impacted_modules = impacted_modules or []

    def validate(
        self,
        hypothesis_score: float,
        test_output: Optional[str] = None,
    ) -> "ValidationResult":
        """Validate convergence criteria.

        Args:
            hypothesis_score: The hypothesis confidence score.
            test_output: Optional pytest output to parse for pass rate.

        Returns:
            ValidationResult with validation status.

        Examples:
            >>> validator = ConvergeValidator()
            >>> result = validator.validate(hypothesis_score=0.85)
            >>> result.is_valid
            True
        """
        score_met = hypothesis_score >= self.score_threshold

        tests_met = True
        test_pass_rate = 1.0

        if self.impacted_modules:
            test_result = self._run_impacted_tests()
            tests_met = test_result["pass_rate"] >= self.test_threshold
            test_pass_rate = test_result["pass_rate"]
        elif test_output:
            # Parse provided test output
            test_result = self._parse_test_output(test_output)
            tests_met = test_result["pass_rate"] >= self.test_threshold
            test_pass_rate = test_result["pass_rate"]

        is_valid = score_met and tests_met

        return ValidationResult(
            is_valid=is_valid,
            score_met=score_met,
            tests_met=tests_met,
            hypothesis_score=hypothesis_score,
            score_threshold=self.score_threshold,
            test_pass_rate=test_pass_rate,
            test_threshold=self.test_threshold,
        )

    def _run_impacted_tests(self) -> Dict[str, Any]:
        """Run pytest on impacted modules.

        Returns:
            Dictionary with test results including pass rate.
        """
        if not self.impacted_modules:
            return {"passed": 0, "failed": 0, "total": 0, "pass_rate": 1.0}

        # Build pytest command for impacted modules
        pytest_args = [sys.executable, "-m", "pytest"]
        for module in self.impacted_modules:
            pytest_args.append(str(module))
        pytest_args.extend(["-v", "--tb=no"])

        try:
            result = subprocess.run(
                pytest_args,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            return self._parse_test_output(result.stdout + result.stderr)
        except subprocess.TimeoutExpired:
            return {"passed": 0, "failed": -1, "total": 0, "pass_rate": 0.0, "error": "timeout"}
        except Exception as e:
            return {"passed": 0, "failed": -1, "total": 0, "pass_rate": 0.0, "error": str(e)}

    def _parse_test_output(self, output: str) -> Dict[str, Any]:
        """Parse pytest output to extract pass/fail counts.

        Args:
            output: The combined stdout/stderr from pytest.

        Returns:
            Dictionary with passed, failed, total, and pass_rate.
        """
        # Default values
        result = {"passed": 0, "failed": 0, "total": 0, "pass_rate": 0.0}

        # Look for summary line: "X passed, Y failed"
        import re

        # Pattern 1: "X passed, Y failed"
        pattern1 = r"(\d+) passed(?:, (\d+) failed)?"
        # Pattern 2: "X passed"
        pattern2 = r"(\d+) passed"
        # Pattern 3: "==X PASSED=="
        pattern3 = r"==(\d+) PASSED"

        for line in output.split("\n"):
            match = re.search(pattern1, line)
            if match:
                result["passed"] = int(match.group(1))
                failed = match.group(2)
                result["failed"] = int(failed) if failed else 0
                result["total"] = result["passed"] + result["failed"]
                break
            elif "passed" in line:
                match = re.search(pattern2, line)
                if match:
                    result["passed"] = int(match.group(1))
                    result["total"] = result["passed"]
                    break

        # Also check for PASSED summary
        for line in output.split("\n"):
            match = re.search(pattern3, line)
            if match:
                result["passed"] = int(match.group(1))
                result["total"] = result["passed"]
                break

        # Calculate pass rate
        if result["total"] > 0:
            result["pass_rate"] = result["passed"] / result["total"]
        elif result["passed"] > 0:
            # No failures detected
            result["pass_rate"] = 1.0

        return result

    def set_impacted_modules(self, modules: List[str]) -> None:
        """Set the list of impacted modules for validation.

        Args:
            modules: List of module or file paths to test.

        Examples:
            >>> validator = ConvergeValidator()
            >>> validator.set_impacted_modules(["src/rca/tier1"])
        """
        self.impacted_modules = list(modules)

    def add_impacted_module(self, module: str) -> None:
        """Add an impacted module for validation.

        Args:
            module: Module or file path to test.

        Examples:
            >>> validator = ConvergeValidator()
            >>> validator.add_impacted_module("tests/test_hypothesis_scorer.py")
        """
        if module not in self.impacted_modules:
            self.impacted_modules.append(module)


class ValidationResult:
    """Result of convergence validation.

    Attributes:
        is_valid: Overall validation result (all criteria met).
        score_met: Whether hypothesis score meets threshold.
        tests_met: Whether test pass rate meets threshold.
        hypothesis_score: The actual hypothesis score.
        score_threshold: The required score threshold.
        test_pass_rate: The actual test pass rate.
        test_threshold: The required test threshold.
    """

    def __init__(
        self,
        is_valid: bool,
        score_met: bool,
        tests_met: bool,
        hypothesis_score: float,
        score_threshold: float,
        test_pass_rate: float,
        test_threshold: float,
    ):
        """Initialize validation result.

        Args:
            is_valid: Overall validation result.
            score_met: Whether score criterion met.
            tests_met: Whether test criterion met.
            hypothesis_score: Actual hypothesis score.
            score_threshold: Required score threshold.
            test_pass_rate: Actual test pass rate.
            test_threshold: Required test threshold.
        """
        self.is_valid = is_valid
        self.score_met = score_met
        self.tests_met = tests_met
        self.hypothesis_score = hypothesis_score
        self.score_threshold = score_threshold
        self.test_pass_rate = test_pass_rate
        self.test_threshold = test_threshold

    def __repr__(self) -> str:
        """Return string representation of validation result."""
        return (
            f"ValidationResult(is_valid={self.is_valid}, "
            f"score_met={self.score_met} ({self.hypothesis_score:.2f}/{self.score_threshold:.2f}), "
            f"tests_met={self.tests_met} ({self.test_pass_rate:.2%}/{self.test_threshold:.2%}))"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary.

        Returns:
            Dictionary representation of the validation result.
        """
        return {
            "is_valid": self.is_valid,
            "score_met": self.score_met,
            "tests_met": self.tests_met,
            "hypothesis_score": self.hypothesis_score,
            "score_threshold": self.score_threshold,
            "test_pass_rate": self.test_pass_rate,
            "test_threshold": self.test_threshold,
        }

    @property
    def blocked_on(self) -> Optional[str]:
        """Return what criterion is blocking convergence, if any.

        Returns:
            'score', 'tests', 'both', or None if valid.
        """
        if self.is_valid:
            return None
        if not self.score_met and not self.tests_met:
            return "both"
        if not self.score_met:
            return "score"
        return "tests"
