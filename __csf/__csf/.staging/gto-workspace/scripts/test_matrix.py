"""Test Verification Matrix for /gto skill.

Cross-references code changes with test status.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TestMatrixGenerator:
    """Generate test verification matrix for code changes."""

    def __init__(self, working_dir: str | Path = ".") -> None:
        """Initialize test matrix generator."""
        self.working_dir = Path(working_dir)
        logger.info(f"TestMatrixGenerator initialized for {self.working_dir}")

    def find_test_files(self) -> list[Path]:
        """Find all test files in working directory."""
        return list(self.working_dir.rglob("test_*.py")) + list(self.working_dir.rglob("tests/test_*.py"))

    def find_source_files(self) -> list[Path]:
        """Find all source Python files."""
        return [f for f in self.working_dir.rglob("*.py") if "test" not in f.name]

    def check_test_coverage(self, source_file: Path, test_files: list[Path]) -> dict[str, Any]:
        """Check if source file has corresponding test."""
        module_name = source_file.stem
        test_candidates = [
            t for t in test_files
            if module_name in t.stem or module_name.replace("_", "") in t.stem
        ]
        return {
            "source": str(source_file),
            "has_tests": len(test_candidates) > 0,
            "test_files": [str(t) for t in test_candidates],
            "coverage": "covered" if test_candidates else "uncovered"
        }

    def generate_matrix(self) -> dict[str, Any]:
        """Generate full test verification matrix."""
        test_files = self.find_test_files()
        source_files = self.find_source_files()
        
        matrix = []
        covered = 0
        for source in source_files:
            entry = self.check_test_coverage(source, test_files)
            matrix.append(entry)
            if entry["has_tests"]:
                covered += 1
        
        coverage_rate = covered / len(source_files) if source_files else 0
        return {
            "matrix": matrix,
            "total_sources": len(source_files),
            "total_tests": len(test_files),
            "covered_count": covered,
            "coverage_rate": coverage_rate
        }
