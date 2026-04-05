"""
GTOAssertions - Self-verifying assertion runner for GTO contracts.

Implements TASK-004 from ADR-20260324-clean-room-tdd-loop.md:
- file_exists assertion type
- test_passes assertion type
- no_import_errors assertion type
- Result aggregation produces pass/fail summary
- Atomic write pattern for JSON state (FM-2408)

ADR: P:/.claude/arch_decisions/ADR-20260324-clean-room-tdd-loop.md
"""

from __future__ import annotations

import importlib.util
import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class AssertionResult:
    """Result of a single assertion execution."""

    assertion: str
    passed: bool
    reason: str = ""
    details: dict = field(default_factory=dict)


class GTOAssertionRunner:
    """Runner for GTO-style assertions from evals.json.

    Supports assertion types:
    - file_exists: Check if file exists
    - test_passes: Run pytest on test file
    - no_import_errors: Verify Python file has no import errors

    Usage:
        runner = GTOAssertionRunner(base_path=Path.cwd())
        result = runner.run_assertion({"type": "file_exists", "path": "impl.py"})
        summary = runner.run_all(Path("evals.json"))
    """

    def __init__(self, base_path: Path | None = None):
        """Initialize assertion runner.

        Args:
            base_path: Base directory for relative paths (defaults to cwd)
        """
        self.base_path = base_path or Path.cwd()

    def run_assertion(self, assertion: dict) -> AssertionResult:
        """Run a single assertion.

        Args:
            assertion: Assertion configuration dict with 'type' key

        Returns:
            AssertionResult with pass/fail status
        """
        assertion_type = assertion.get("type", "")

        if assertion_type == "file_exists":
            return self._check_file_exists(assertion)
        elif assertion_type == "test_passes":
            return self._check_test_passes(assertion)
        elif assertion_type == "no_import_errors":
            return self._check_no_import_errors(assertion)
        else:
            return AssertionResult(
                assertion=assertion_type,
                passed=False,
                reason=f"Unknown assertion type: {assertion_type}",
            )

    def _check_file_exists(self, assertion: dict) -> AssertionResult:
        """Check if file exists.

        Args:
            assertion: {"type": "file_exists", "path": "relative/path.txt"}

        Returns:
            AssertionResult
        """
        path = assertion.get("path", "")
        full_path = self.base_path / path

        if full_path.exists():
            return AssertionResult(
                assertion="file_exists",
                passed=True,
                details={"path": str(full_path)},
            )
        else:
            return AssertionResult(
                assertion="file_exists",
                passed=False,
                reason=f"File not found: {path}",
                details={"path": str(full_path)},
            )

    def _check_test_passes(self, assertion: dict) -> AssertionResult:
        """Run pytest on test file.

        Args:
            assertion: {"type": "test_passes", "test_file": "test_x.py"}

        Returns:
            AssertionResult
        """
        test_file = assertion.get("test_file", "")
        full_path = self.base_path / test_file

        if not full_path.exists():
            return AssertionResult(
                assertion="test_passes",
                passed=False,
                reason=f"Test file not found: {test_file}",
            )

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(full_path), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.base_path),
            )

            if result.returncode == 0:
                return AssertionResult(
                    assertion="test_passes",
                    passed=True,
                    details={"output": result.stdout[-500:] if result.stdout else ""},
                )
            else:
                return AssertionResult(
                    assertion="test_passes",
                    passed=False,
                    reason="Tests failed",
                    details={"output": result.stdout[-500:] if result.stdout else ""},
                )
        except subprocess.TimeoutExpired:
            return AssertionResult(
                assertion="test_passes",
                passed=False,
                reason="Test execution timed out (30s)",
            )
        except Exception as e:
            return AssertionResult(
                assertion="test_passes",
                passed=False,
                reason=f"Error running tests: {e}",
            )

    def _check_no_import_errors(self, assertion: dict) -> AssertionResult:
        """Check if Python file has no import errors.

        Args:
            assertion: {"type": "no_import_errors", "file": "module.py"}

        Returns:
            AssertionResult
        """
        file_path = assertion.get("file", "")
        full_path = self.base_path / file_path

        if not full_path.exists():
            return AssertionResult(
                assertion="no_import_errors",
                passed=False,
                reason=f"File not found: {file_path}",
            )

        try:
            spec = importlib.util.spec_from_file_location("test_module", full_path)
            if spec is None or spec.loader is None:
                return AssertionResult(
                    assertion="no_import_errors",
                    passed=False,
                    reason="Could not load module spec",
                )

            module = importlib.util.module_from_spec(spec)
            sys.modules["test_module"] = module
            spec.loader.exec_module(module)

            return AssertionResult(
                assertion="no_import_errors",
                passed=True,
                details={"file": str(full_path)},
            )
        except ImportError as e:
            return AssertionResult(
                assertion="no_import_errors",
                passed=False,
                reason=f"Import error: {e}",
            )
        except Exception as e:
            return AssertionResult(
                assertion="no_import_errors",
                passed=False,
                reason=f"Error loading module: {e}",
            )

    def run_all(self, evals_path: Path) -> dict:
        """Run all assertions from evals.json file.

        Args:
            evals_path: Path to evals.json file

        Returns:
            Summary dict with total/passed/failed counts and status
        """
        if not evals_path.exists():
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "status": "fail",
                "reason": f"evals.json not found: {evals_path}",
            }

        try:
            with open(evals_path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "status": "fail",
                "reason": f"Invalid JSON: {e}",
            }

        assertions = data.get("assertions", [])
        results = []

        for assertion in assertions:
            result = self.run_assertion(assertion)
            results.append(result)

        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)

        return {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "status": "pass" if failed == 0 else "fail",
            "results": [
                {
                    "assertion": r.assertion,
                    "passed": r.passed,
                    "reason": r.reason,
                }
                for r in results
            ],
        }

    def save_state(self, state_path: Path, state: dict) -> None:
        """Save state to JSON file with atomic write pattern (FM-2408).

        Args:
            state_path: Path to state file
            state: State dictionary to save
        """
        state_path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write pattern: write to temp file, then rename
        temp_path = state_path.with_suffix(".tmp")

        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)

            # Atomic rename
            temp_path.replace(state_path)

        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

    def load_state(self, state_path: Path) -> dict:
        """Load state from JSON file.

        Args:
            state_path: Path to state file

        Returns:
            State dictionary (empty if file doesn't exist)
        """
        if not state_path.exists():
            return {}

        try:
            with open(state_path, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Corrupted state file: {state_path}")
            return {}
