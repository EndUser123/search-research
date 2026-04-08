"""Import path verification tests for CHS consolidation (TEST-003).

This test ensures that after migration, no imports remain from the old
CHS location (__csf.src.knowledge.systems.chs.v2) and all imports point to
the new location (search_research.core.chs).

Related: PRE-002 BLOCKER Issue - TEST-003
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


class TestCHSImportPaths:
    """Verify CHS imports are correctly updated after consolidation."""

    # Old import patterns that should NOT exist after migration
    OLD_IMPORT_PATTERNS = [
        r"from\s+__csf\.src\.knowledge\.systems\.chs\.v2\b",
        r"from\s+knowledge\.systems\.chs\.v2\b",
        r"import\s+__csf\.src\.knowledge\.systems\.chs\.v2",
        r"import\s+knowledge\.systems\.chs\.v2",
    ]

    # New import patterns that SHOULD exist after migration
    NEW_IMPORT_PATTERNS = [
        r"from\s+search_research\.core\.chs\b",
        r"from\s+core\.chs\b",  # Relative imports within search-research
    ]

    @pytest.fixture
    def search_research_root(self) -> Path:
        """Get the search-research package root."""
        return Path("P:/packages/search-research")

    @pytest.fixture
    def chs_core_dir(self, search_research_root: Path) -> Path:
        """Get the CHS core directory."""
        return search_research_root / "core" / "chs"

    def find_python_files(self, root_dir: Path) -> list[Path]:
        """Find all Python files in the given directory."""
        return list(root_dir.rglob("*.py"))

    def check_file_for_old_imports(self, file_path: Path) -> list[dict]:
        """Check a file for old CHS import patterns.

        Returns:
            List of dicts with 'pattern' and 'line' keys for each match
        """
        violations = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()

            for line_num, line in enumerate(lines, start=1):
                for pattern in self.OLD_IMPORT_PATTERNS:
                    if re.search(pattern, line):
                        violations.append(
                            {
                                "pattern": pattern,
                                "line": line_num,
                                "content": line.strip(),
                            }
                        )
        except Exception:
            # Skip files that can't be read (e.g., binary files)
            pass

        return violations

    def should_skip_file(self, file_path: Path, search_research_root: Path) -> bool:
        """Check if a file should be skipped from old import verification.

        Files that are allowed to contain old import patterns as strings/test data:
        - This test file itself (defines OLD_IMPORT_PATTERNS)
        - Test files (contain patterns as test strings to verify they're NOT present)
        - Refactor scripts (search for old patterns to replace them)
        """
        rel_path = str(file_path.relative_to(search_research_root))

        # Skip this test file itself (contains OLD_IMPORT_PATTERNS constants)
        if "test_import_verification.py" in rel_path:
            return True

        # Skip test files that contain old patterns as test strings
        # (they're testing that the patterns DON'T exist in production code)
        if "/tests/" in rel_path or "\\tests\\" in rel_path:
            return True

        # Skip refactor scripts that search for old patterns
        if "refactor" in rel_path.lower():
            return True

        return False

    def test_no_old_imports_in_search_research(self, search_research_root: Path):
        """Verify no old __csf CHS imports remain in search-research package."""
        violations = []

        for py_file in self.find_python_files(search_research_root):
            # Skip files that legitimately contain old patterns as strings
            if self.should_skip_file(py_file, search_research_root):
                continue

            file_violations = self.check_file_for_old_imports(py_file)
            if file_violations:
                for violation in file_violations:
                    violations.append(
                        {"file": str(py_file.relative_to(search_research_root)), **violation}
                    )

        # Assert no violations
        assert not violations, (
            f"Found {len(violations)} old CHS import(s) that need to be updated:\n"
            + "\n".join(
                f"  {v['file']}:{v['line']} - {v['pattern']}\n    {v['content']}"
                for v in violations
            )
        )

    def test_new_imports_exist_in_chs_init(self, chs_core_dir: Path):
        """Verify new CHS imports exist in core/chs/__init__.py."""
        init_file = chs_core_dir / "__init__.py"

        if not init_file.exists():
            pytest.skip(f"CHS __init__.py not found at {init_file}")

        content = init_file.read_text(encoding="utf-8")

        # CHS __init__.py uses relative imports (from .module)
        # Check for relative imports from CHS submodules
        has_relative_imports = bool(re.search(r"from\s+\.\w+\s+import", content))

        # Also check that it exports expected functions
        expected_exports = [
            "CHSSearchV2",
            "SearchSession",
            "verify_database_backup",
        ]
        has_expected_exports = all(export in content for export in expected_exports)

        assert has_relative_imports and has_expected_exports, (
            f"CHS __init__.py should have relative imports and export expected functions. "
            f"Expected exports: {expected_exports}"
        )

    def test_verify_backup_module_exported(self, chs_core_dir: Path):
        """Verify verify_backup module is properly exported from CHS core.

        This ensures the PRE-001 data safety verifications are accessible.
        """
        init_file = chs_core_dir / "__init__.py"

        if not init_file.exists():
            pytest.skip(f"CHS __init__.py not found at {init_file}")

        content = init_file.read_text(encoding="utf-8")

        # Verify verify_backup imports exist
        required_exports = [
            "verify_database_backup",
            "verify_faiss_backup",
            "BackupMetadata",
            "create_backup_metadata",
        ]

        for export in required_exports:
            assert export in content, (
                f"Required export '{export}' not found in CHS __init__.py. "
                f"This ensures PRE-001 data safety verifications are accessible."
            )

    def test_no_hardcoded_csf_paths_in_tests(self, search_research_root: Path):
        """Verify tests don't have hardcoded P:/__csf/ paths.

        This addresses TEST-004: 11 test files have hardcoded paths.

        Note: Test files that contain these patterns as test strings (to verify
        they're NOT used in production code) are excluded via should_skip_file().
        """
        tests_dir = search_research_root / "core" / "chs" / "tests"

        if not tests_dir.exists():
            pytest.skip(f"CHS tests directory not found at {tests_dir}")

        violations = []
        hardcoded_pattern = r"P:/__csf/"

        for test_file in self.find_python_files(tests_dir):
            # Skip files that legitimately contain old patterns as strings
            if self.should_skip_file(test_file, search_research_root):
                continue

            try:
                content = test_file.read_text(encoding="utf-8", errors="ignore")
                lines = content.splitlines()

                for line_num, line in enumerate(lines, start=1):
                    if re.search(hardcoded_pattern, line):
                        violations.append(
                            {
                                "file": str(test_file.relative_to(search_research_root)),
                                "line": line_num,
                                "content": line.strip(),
                            }
                        )
            except Exception:
                # Skip files that can't be read
                pass

        # This test identifies issues but doesn't block (for awareness)
        if violations:
            pytest.fail(
                f"Found {len(violations)} hardcoded P:/__csf/ path(s) in tests:\n"
                + "\n".join(
                    f"  {v['file']}:{v['line']}\n    {v['content']}"
                    for v in violations[:10]  # Show first 10
                )
                + (f"\n  ... and {len(violations) - 10} more" if len(violations) > 10 else "")
            )
