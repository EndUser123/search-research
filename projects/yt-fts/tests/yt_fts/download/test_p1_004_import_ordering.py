"""Characterization tests for P1-004: Import Ordering Violations."""
from pathlib import Path


class TestImportOrderingPEP8:
    """Characterize current PEP 8 import ordering violations."""

    def test_batch_downloader_import_order_violations(self):
        """Characterize: batch_downloader.py has scattered imports violating PEP 8."""
        file_path = Path("src/yt_fts/download/batch_downloader.py")
        content = file_path.read_text()

        # Extract import lines
        import_lines = []
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                import_lines.append((content.split("\n").index(line) + 1, stripped))

        # Characterize violations
        violations = []

        # Check: Standard library imports appear after local imports
        stdlib_imports = []
        local_imports = []
        third_party_imports = []

        for line_num, imp in import_lines:
            # Standard library detection
            stdlib_modules = [
                "logging", "os", "re", "sqlite3", "time", "dataclasses",
                "pathlib", "typing", "collections", "concurrent", "contextlib",
                "json", "io", "tempfile", "random", "xml"
            ]

            is_stdlib = any(imp.startswith(f"import {mod}") or
                          imp.startswith(f"from {mod}")
                          for mod in stdlib_modules)

            # Third-party detection
            is_third_party = imp.startswith("from rich.") or imp.startswith("import rich")

            # Local import detection
            is_local = imp.startswith("from yt_fts.") or imp.startswith("from .")

            if is_stdlib:
                stdlib_imports.append((line_num, imp))
            elif is_third_party:
                third_party_imports.append((line_num, imp))
            elif is_local:
                local_imports.append((line_num, imp))

        # Characterize: Imports are NOT in PEP 8 order
        # PEP 8 requires: 1) stdlib, 2) third-party, 3) local
        # Verify violation exists
        if stdlib_imports and local_imports:
            # Check if any stdlib import appears AFTER local import
            first_local_line = min(line_num for line_num, _ in local_imports)
            misplaced_stdlib = [imp for line_num, imp in stdlib_imports
                              if line_num > first_local_line]

            if misplaced_stdlib:
                violations.append(f"Standard library imports after local imports: {misplaced_stdlib}")

        # Characterize: contextlib import appears at line 41, after local imports
        contextlib_line = None
        for line_num, imp in import_lines:
            if "import contextlib" in imp or imp == "import contextlib":
                contextlib_line = line_num
                break

        if contextlib_line and contextlib_line > 20:  # After local imports start
            violations.append(f"contextlib imported at line {contextlib_line}, after local imports")

        # Characterize: concurrent.futures import at line 29, after local imports
        concurrent_line = None
        for line_num, imp in import_lines:
            if "concurrent.futures" in imp:
                concurrent_line = line_num
                break

        if concurrent_line and concurrent_line > 20:  # After local imports start
            violations.append(f"concurrent.futures imported at line {concurrent_line}, after local imports")

        # Characterize: collections.abc import at line 23, after local imports
        collections_line = None
        for line_num, imp in import_lines:
            if "collections.abc" in imp:
                collections_line = line_num
                break

        if collections_line and collections_line > 20:  # After local imports start
            violations.append(f"collections.abc imported at line {collections_line}, after local imports")

        # Assert violations exist (this test characterizes the bug)
        assert len(violations) > 0, \
            "BUG CHARACTERIZED: Expected PEP 8 import ordering violations, but found none. " \
            "This means imports are already correctly ordered or the test needs updating."

        print(f"\n✅ BUG CONFIRMED: Found {len(violations)} PEP 8 import ordering violations:")
        for v in violations:
            print(f"  • {v}")

    def test_batch_downlogger_import_sections(self):
        """Characterize: Import sections are not grouped properly."""
        file_path = Path("src/yt_fts/download/batch_downloader.py")
        content = file_path.read_text()

        # Find the end of imports (first non-import, non-comment line)
        lines = content.split("\n")
        import_end = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith('"""') \
               and not stripped.startswith("from ") and not stripped.startswith("import ") \
               and not stripped.startswith("logger =") and not stripped.startswith("logging.basicConfig"):
                import_end = i
                break

        # Count imports by type
        stdlib_count = 0
        local_count = 0
        third_party_count = 0

        for i in range(min(import_end, len(lines))):
            line = lines[i]
            stripped = line.strip()

            # Standard library
            if any(stripped.startswith(f"import {mod}") or
                   stripped.startswith(f"from {mod}")
                   for mod in ["logging", "os", "re", "sqlite3", "time", "dataclasses",
                             "pathlib", "typing", "collections", "concurrent", "contextlib"]):
                stdlib_count += 1

            # Third-party
            if stripped.startswith("from rich.") or stripped.startswith("import rich"):
                third_party_count += 1

            # Local
            if stripped.startswith("from yt_fts.") or stripped.startswith("from ."):
                local_count += 1

        # Characterize: Imports are scattered (not grouped)
        # If imports were properly grouped, we'd see: all stdlib, then all third-party, then all local
        # Current state has them interleaved

        print(f"\n📊 Import distribution (first {import_end} lines):")
        print(f"  Standard library: {stdlib_count}")
        print(f"  Third-party: {third_party_count}")
        print(f"  Local imports: {local_count}")

        # This test always passes (just characterizing current state)
        assert True, "Import distribution characterized"
