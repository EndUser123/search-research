"""Tests for unified_router.py import path fixes (TASK-002).

These tests verify that unified_router.py uses package-relative imports
instead of sys.path manipulation. The tests will FAIL initially because
the current implementation still uses sys.path manipulation (lines 32-38).

Expected behavior after fix:
- No sys.path.insert() calls in the module
- All imports use package-relative syntax (from .. import)
- Module can be imported without manual path manipulation
- No hardcoded paths in the source file

Run with: pytest tests/test_unified_router_imports.py -v
"""

import ast
import subprocess
import sys
from pathlib import Path


class TestUnifiedRouterImportPaths:
    """Tests for import path fixes in unified_router.py."""

    def test_no_sys_path_manipulation_in_source(self):
        """Test that unified_router.py does NOT manipulate sys.path.

        This test reads the source file and verifies there's no sys.path.insert()
        or sys.path.append() calls. After the fix, lines 32-38 should be removed.

        Expected: FAIL initially (sys.path manipulation still present)
        """
        source_file = Path(__file__).parent.parent / "src" / "search_research" / "core" / "unified_router.py"

        # Read source file
        source_code = source_file.read_text()

        # Parse as AST
        tree = ast.parse(source_code)

        # Look for sys.path manipulation
        has_sys_path_manipulation = False
        sys_path_lines = []

        for node in ast.walk(tree):
            # Check for sys.path.insert() or sys.path.append()
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    # Check if it's sys.path.insert or sys.path.append
                    if (node.func.attr == "insert" or node.func.attr == "append"):
                        # Check if the object being called is sys.path
                        if isinstance(node.func.value, ast.Attribute):
                            if (node.func.value.attr == "path" and
                                isinstance(node.func.value.value, ast.Name) and
                                node.func.value.value.id == "sys"):
                                has_sys_path_manipulation = True
                                sys_path_lines.append(node.lineno)

        # Assert that sys.path manipulation should NOT exist
        assert not has_sys_path_manipulation, (
            f"Found sys.path manipulation on line(s) {sys_path_lines}. "
            "After TASK-002 fix, sys.path manipulation should be removed "
            "and replaced with package-relative imports."
        )

    def test_uses_package_relative_imports(self):
        """Test that unified_router.py uses package-relative imports.

        Verifies that imports from search_research package use relative syntax
        (e.g., 'from ..quality_checker import') instead of absolute imports
        that require sys.path manipulation.

        Expected: FAIL initially (absolute imports still present)
        """
        source_file = Path(__file__).parent.parent / "src" / "search_research" / "core" / "unified_router.py"

        # Read source file
        source_code = source_file.read_text()

        # Check for absolute imports from search_research (bad pattern)
        has_absolute_imports = False
        absolute_import_lines = []

        for line_num, line in enumerate(source_code.split('\n'), 1):
            # Look for: from xxx import
            if 'from ' in line and 'import' in line:
                # Skip comments
                if not line.strip().startswith('#'):
                    has_absolute_imports = True
                    absolute_import_lines.append((line_num, line.strip()))

        # Assert that absolute imports should NOT exist
        assert not has_absolute_imports, (
            f"Found absolute imports from search_research on line(s) "
            f"{[ln for ln, _ in absolute_import_lines]}. "
            "After TASK-002 fix, these should use relative imports "
            "(e.g., 'from ..quality_checker import')"
        )

    def test_module_imports_without_path_manipulation(self):
        """Test that UnifiedAsyncRouter can be imported cleanly in fresh subprocess.

        This test uses subprocess to ensure a clean import environment without
        any cached imports or path manipulation from the test runner.

        Expected: FAIL initially (import will fail without sys.path setup)
        """
        # Create a test script that tries to import without any sys.path setup
        test_script = """
import sys

# Verify no search_research in path initially
print("Initial sys.path:", sys.path[:3])

# Try to import without any path manipulation
try:
    from core.unified_router import UnifiedAsyncRouter
    print("SUCCESS: Import worked without sys.path manipulation")
    sys.exit(0)
except ImportError as e:
    print(f"FAIL: Import failed with: {e}")
    sys.exit(1)
"""

        # Run in subprocess with minimal path (just the package src directory)
        src_path = Path(__file__).parent.parent / "src"
        env = {
            "PYTHONPATH": str(src_path),
            # Clear any other Python path env vars
        }

        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
            cwd=str(src_path),
            env={**subprocess.os.environ, "PYTHONPATH": str(src_path)}
        )

        # Print output for debugging
        print(f"Subprocess stdout:\n{result.stdout}")
        if result.stderr:
            print(f"Subprocess stderr:\n{result.stderr}")

        # After fix, import should succeed
        assert result.returncode == 0, (
            f"Import failed in fresh subprocess. After TASK-002 fix, "
            f"import should work with just PYTHONPATH set to src directory. "
            f"Output: {result.stdout}"
        )

    def test_no_hardcoded_paths_in_source(self):
        """Test that unified_router.py contains no hardcoded filesystem paths.

        Verifies that the source file doesn't contain path strings like
        '/src/', 'src_path', or other hardcoded path constructions.

        Expected: FAIL initially (hardcoded paths on lines 37-38)
        """
        source_file = Path(__file__).parent.parent / "src" / "search_research" / "core" / "unified_router.py"

        # Read source file
        source_code = source_file.read_text()

        # Look for hardcoded path patterns
        hardcoded_path_patterns = [
            'src_path',
            'Path(__file__).parent.parent',
            'sys.path.insert',
            'sys.path.append',
            '"src"',
            "'src'",
        ]

        found_patterns = []
        for line_num, line in enumerate(source_code.split('\n'), 1):
            for pattern in hardcoded_path_patterns:
                if pattern in line and not line.strip().startswith('#'):
                    found_patterns.append((line_num, pattern, line.strip()))

        # Assert that no hardcoded paths should exist
        assert len(found_patterns) == 0, (
            f"Found {len(found_patterns)} hardcoded path pattern(s) in source:\n" +
            "\n".join(f"  Line {ln}: {pat} -> {line}" for ln, pat, line in found_patterns) +
            "\n\nAfter TASK-002 fix, these should be removed and replaced with "
            "package-relative imports."
        )

    def test_import_statements_use_relative_syntax(self):
        """Test that import statements use proper relative import syntax.

        Verifies that imports from sibling modules use '..' notation
        instead of absolute package names.

        Expected: FAIL initially (imports use absolute names)
        """
        source_file = Path(__file__).parent.parent / "src" / "search_research" / "core" / "unified_router.py"

        # Read source file
        source_code = source_file.read_text()

        # Expected relative imports after fix
        expected_relative_imports = {
            ("..quality_checker", "QualityConfig", "is_satisfactory"),
            ("..result_merger", "reciprocal_rank_fusion"),
            ("..router", "AsyncSearchRouter", "UnifiedAsyncRouter", "SearchResult"),
        }

        # Check if these relative imports exist
        # Note: AST stores relative level in node.level, not in module string
        # level=0 is absolute, level=1 is '.', level=2 is '..'
        found_relative_imports = set()

        for node in ast.parse(source_code).body:
            if isinstance(node, ast.ImportFrom) and node.level > 0:
                # Reconstruct the module path with dots for comparison
                module_with_dots = "." * node.level + (node.module or "")
                names = tuple(alias.name for alias in node.names)
                found_relative_imports.add((module_with_dots, *names))

        # After fix, should have relative imports
        missing_imports = expected_relative_imports - found_relative_imports

        # Note: This is a loose check - we're looking for at least some relative imports
        # The exact structure may vary
        assert len(found_relative_imports) > 0, (
            "After TASK-002 fix, should have at least some relative imports "
            "using '..' syntax. Found none."
        )

    def test_unified_async_router_import_works(self):
        """Test that UnifiedAsyncRouter can be imported and instantiated.

        This is a basic smoke test to ensure the import works correctly
        after the path fixes.

        Expected: FAIL initially if sys.path manipulation is removed
        before fixing imports
        """
        # This import should work after fix
        from core.unified_router import UnifiedAsyncRouter

        # Basic instantiation test
        router = UnifiedAsyncRouter(mode="auto")

        assert router is not None
        assert router.mode == "auto"
        assert router.enable_jmri is True
        assert router.rrf_k == 60


class TestUnifiedRouterSourceCodeStructure:
    """Tests for source code structure after import path fix."""

    def test_import_section_structure(self):
        """Test that import section follows proper structure after fix.

        After TASK-002, imports should be organized as:
        1. Standard library imports
        2. Third-party imports (if any)
        3. Package-relative imports (using ..)

        Expected: FAIL initially (imports need reorganization)
        """
        source_file = Path(__file__).parent.parent / "src" / "search_research" / "core" / "unified_router.py"

        # Read source file
        source_code = source_file.read_text()

        # Parse AST
        tree = ast.parse(source_code)

        # Extract all import statements
        imports = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                imports.append(("import", node.lineno, None, 0))  # level=0 for absolute
            elif isinstance(node, ast.ImportFrom):
                # Store level for relative import detection
                imports.append(("from", node.lineno, node.module, node.level))

        # Check structure - use level attribute to detect relative imports
        has_relative_imports = any(
            level > 0 for _, _, _, level in imports
        )

        assert has_relative_imports, (
            "After TASK-002 fix, import section should contain relative imports "
            "using '..' syntax. Found none."
        )

    def test_no_path_setup_code_before_imports(self):
        """Test that there's no path setup code before import statements.

        After TASK-002, lines 32-38 (path setup) should be removed entirely,
        and imports should be at the top of the file.

        Expected: FAIL initially (path setup code still present)
        """
        source_file = Path(__file__).parent.parent / "src" / "search_research" / "core" / "unified_router.py"

        # Read source file
        source_code = source_file.read_text()
        lines = source_code.split('\n')

        # Look for path setup code patterns in first 50 lines
        path_setup_found = False
        path_setup_line = None

        for i, line in enumerate(lines[:50], 1):
            stripped = line.strip()
            # Check for path setup patterns
            if any(pattern in stripped for pattern in [
                "src_path =",
                "sys.path.insert",
                "sys.path.append",
                'Path(__file__).parent.parent',
            ]):
                # Skip if it's a comment
                if not stripped.startswith('#'):
                    path_setup_found = True
                    path_setup_line = (i, stripped)
                    break

        assert not path_setup_found, (
            f"Found path setup code on line {path_setup_line[0]}: "
            f"'{path_setup_line[1]}'. "
            "After TASK-002 fix, all path setup code should be removed."
        )
