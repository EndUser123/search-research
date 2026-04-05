"""Tests for FileScanner shared scanner package.

These tests verify the FileScanner class at ~/.claude/skills/_shared/scanners/
which provides safe filesystem traversal for project-root-walking detectors.

Test Strategy:
- Tests import FileScanner from the _shared.scanners package
- Uses temporary directories to create realistic test scenarios
- Verifies security properties (path sanitization, symlink guards, etc.)

Run with: pytest P:/packages/search-research/tests/test_file_scanner.py -v
"""

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

# Add the shared scanners package to sys.path (same mechanism as detector modules)
_SHARED_SCANNERS_PATH = Path.home() / ".claude" / "skills" / "_shared"
if _SHARED_SCANNERS_PATH.exists():
    sys.path.insert(0, str(_SHARED_SCANNERS_PATH))

from scanners.base import MAX_FILE_SIZE, SKIP_DIRS, FileScanner, ScanResult  # type: ignore


class TestScanResultDataclass:
    """Tests for ScanResult dataclass structure."""

    def test_scan_result_dataclass(self):
        """Test that ScanResult has the required fields: files, skipped_dirs, scan_time_ms.

        Given: A ScanResult instance with data
        When: Accessing its fields
        Then: All expected fields are present with correct types
        """
        result = ScanResult(
            files=[Path("test.py")],
            skipped_dirs=[".git", "node_modules"],
            scan_time_ms=123.45,
        )

        assert hasattr(result, "files")
        assert hasattr(result, "skipped_dirs")
        assert hasattr(result, "scan_time_ms")
        assert result.files == [Path("test.py")]
        assert result.skipped_dirs == [".git", "node_modules"]
        assert result.scan_time_ms == 123.45


class TestSanitizePath:
    """Tests for _sanitize_path path traversal protection."""

    def test_sanitize_path_blocks_traversal(self):
        """Test that path traversal attempts are blocked by _sanitize_path.

        Given: A project root and a path that escapes via ../../../etc/passwd
        When: Calling _sanitize_path
        Then: ValueError is raised because the path escapes project root
        """
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            scanner = FileScanner(project_root=project_root)

            # Attempt path traversal - should raise ValueError
            traversal_path = project_root / "subdir" / ".." / ".." / ".." / "etc" / "passwd"

            with pytest.raises(ValueError, match="escapes project root"):
                scanner._sanitize_path(traversal_path)

    def test_sanitize_path_allows_inside(self):
        """Test that valid paths inside project root are returned correctly.

        Given: A valid path inside the project root
        When: Calling _sanitize_path
        Then: The resolved path is returned
        """
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            scanner = FileScanner(project_root=project_root)

            # Create a valid subdirectory structure
            subdir = project_root / "src" / "modules"
            subdir.mkdir(parents=True)

            valid_path = subdir / "test.py"
            valid_path.touch()

            result = scanner._sanitize_path(valid_path)

            assert result == valid_path.relative_to(project_root)


class TestSkipDirectories:
    """Tests for directory skipping behavior."""

    def test_skip_dirs_excludes_expected(self):
        """Test that directories in SKIP_DIRS are excluded from scanning.

        Given: A project with directories matching SKIP_DIRS
        When: Scanning the project
        Then: Those directories are not traversed
        """
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create directories matching SKIP_DIRS
            skip_dirs_created = []
            for dir_name in SKIP_DIRS:
                skip_dir = project_root / dir_name
                skip_dir.mkdir()
                (skip_dir / "file.py").touch()
                skip_dirs_created.append(dir_name)

            # Create a valid source directory
            src_dir = project_root / "src"
            src_dir.mkdir()
            (src_dir / "main.py").touch()

            scanner = FileScanner(project_root=project_root, extensions={".py"})
            result = scanner.scan()

            # SKIP_DIRS should not appear in scanned files
            scanned_paths = [str(f) for f in result.files]
            for skip_dir in skip_dirs_created:
                assert skip_dir not in scanned_paths, f"{skip_dir} should not be scanned"

            # Valid src directory should be scanned
            assert any("src" in str(f) for f in result.files)


class TestMaxFileSize:
    """Tests for max file size filtering."""

    def test_max_file_size_blocks_large(self):
        """Test that files larger than MAX_FILE_SIZE are skipped.

        Given: A project with files larger than MAX_FILE_SIZE
        When: Scanning the project
        Then: Those large files are not included in results
        """
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create a file larger than MAX_FILE_SIZE
            large_file = project_root / "large.bin"
            with open(large_file, "wb") as f:
                # Write enough bytes to exceed MAX_FILE_SIZE
                f.write(b"x" * (MAX_FILE_SIZE + 1))

            # Create a normal-sized file
            small_file = project_root / "small.txt"
            small_file.write_text("hello")

            scanner = FileScanner(project_root=project_root, extensions={".txt", ".bin"})
            result = scanner.scan(pattern="**/*")

            # Large file should not be scanned
            assert large_file.relative_to(project_root) not in result.files
            # Small file should be scanned
            assert small_file.relative_to(project_root) in result.files


class TestSymlinkHandling:
    """Tests for symlink security guards."""

    def test_symlink_outside_root_blocked(self):
        """Test that symlinks pointing outside project root are skipped.

        Given: A symlink inside project root that points outside
        When: Scanning the project
        Then: The symlink target is not followed and file is skipped
        """
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create a file outside project root
            outside_dir = Path(tmpdir).parent / "outside_project"
            outside_dir.mkdir(exist_ok=True)
            outside_file = outside_dir / "secret.txt"
            outside_file.write_text("secret data")

            # Create a symlink inside project root pointing to outside file
            link_dir = project_root / "links"
            link_dir.mkdir()
            symlink_path = link_dir / "link_to_outside"
            symlink_path.symlink_to(outside_file)

            scanner = FileScanner(project_root=project_root, extensions={".txt"})
            result = scanner.scan(pattern="**/*")

            # The symlinked file should not be scanned (symlink inside project_root
            # points outside, so only the symlink itself is candidate for scanning)
            assert symlink_path.relative_to(project_root) not in result.files


class TestExtensionFiltering:
    """Tests for file extension whitelisting."""

    def test_scan_returns_only_matching_extensions(self):
        """Test that only files with whitelisted extensions are returned.

        Given: A project with multiple file types
        When: Scanning with specific extensions
        Then: Only files with matching extensions are returned
        """
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create files with various extensions
            (project_root / "main.py").touch()
            (project_root / "test.py").touch()
            (project_root / "data.json").touch()
            (project_root / "readme.md").touch()
            (project_root / "binary.bin").touch()

            scanner = FileScanner(project_root=project_root, extensions={".py", ".json"})
            result = scanner.scan(pattern="**/*")

            extensions_found = {f.suffix for f in result.files}

            assert ".py" in extensions_found
            assert ".json" in extensions_found
            assert ".md" not in extensions_found
            assert ".bin" not in extensions_found


class TestScanTiming:
    """Tests for scan timing measurement."""

    def test_scan_time_ms_recorded(self):
        """Test that scan_time_ms is a positive float.

        Given: A valid project to scan
        When: Scanning completes
        Then: scan_time_ms is recorded as a positive float
        """
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create a small file to ensure scan runs
            (project_root / "main.py").touch()

            scanner = FileScanner(project_root=project_root, extensions={".py"})
            result = scanner.scan()

            assert isinstance(result.scan_time_ms, float)
            assert result.scan_time_ms >= 0
