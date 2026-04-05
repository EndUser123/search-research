#!/usr/bin/env python3
"""
Tests for file_utils.py module.

Tests atomic file operations, checksum computation, and file snapshotting.
"""

import hashlib
import os
import tempfile
from pathlib import Path

import pytest

# Add lib directory to path
LIB_DIR = Path(__file__).parent.parent / "lib"
import sys

sys.path.insert(0, str(LIB_DIR))

from file_utils import (
    atomic_write,
    get_file_mtime_snapshot,
    sha256sum_file,
)


class TestAtomicWrite:
    """Test atomic file write operations."""

    def test_atomic_write_creates_file(self):
        """Atomic write should create the target file with correct content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")
            content = "Hello, World!"

            atomic_write(file_path, content)

            assert os.path.exists(file_path)
            with open(file_path, encoding='utf-8') as f:
                assert f.read() == content

    def test_atomic_write_overwrites_existing(self):
        """Atomic write should overwrite existing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")
            original = "Original content"

            # Write initial content
            atomic_write(file_path, original)
            assert os.path.exists(file_path)

            # Overwrite
            new_content = "New content"
            atomic_write(file_path, new_content)

            with open(file_path, encoding='utf-8') as f:
                assert f.read() == new_content

    def test_atomic_write_cleans_temp_file(self):
        """Atomic write should clean up temporary files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")
            content = "Test content"

            atomic_write(file_path, content)

            # Check for .tmp files
            tmp_files = list(Path(tmpdir).glob("*.tmp"))
            assert len(tmp_files) == 0

    def test_atomic_write_handles_unicode(self):
        """Atomic write should handle Unicode content correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "unicode.txt")
            content = "Hello 世界 🌍 Привет"

            atomic_write(file_path, content)

            with open(file_path, encoding='utf-8') as f:
                assert f.read() == content

    def test_atomic_write_empty_content(self):
        """Atomic write should handle empty content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "empty.txt")

            atomic_write(file_path, "")

            assert os.path.exists(file_path)
            with open(file_path, encoding='utf-8') as f:
                assert f.read() == ""

    def test_atomic_write_temp_cleanup_retry(self):
        """Atomic write should retry temp cleanup on failure."""
        import unittest.mock as mock

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")
            content = "Test content"

            # Track call counts
            unlink_calls = [0]
            original_unlink = Path.unlink
            original_replace = os.replace

            def mock_unlink(self, *args, **kwargs):
                """Mock unlink that fails once, then succeeds."""
                unlink_calls[0] += 1
                if unlink_calls[0] == 1:
                    # Simulate temporary file lock (common on Windows)
                    raise OSError("Simulated temporary lock")
                # Second attempt succeeds
                return original_unlink(self, *args, **kwargs)

            def mock_replace(src, dst, *args, **kwargs):
                """Mock replace that fails so temp file needs cleanup."""
                # Simulate write failure - temp file still exists
                raise OSError("Simulated write failure")

            # Patch both replace and unlink to simulate cleanup failure
            with mock.patch('os.replace', mock_replace):
                with mock.patch.object(Path, 'unlink', mock_unlink):
                    # atomic_write will raise OSError, but finally block should retry cleanup
                    try:
                        atomic_write(file_path, content)
                    except OSError:
                        # Expected - write failed
                        pass

            # Verify retry was attempted (called twice: first failed, second succeeded)
            assert unlink_calls[0] == 2, f"Expected 2 unlink calls, got {unlink_calls[0]}"


class TestSha256SumFile:
    """Test SHA256 checksum computation."""

    def test_sha256sum_file_returns_hash(self):
        """SHA256 sum should return correct hex digest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")
            content = b"Hello, World!"

            with open(file_path, 'wb') as f:
                f.write(content)

            # Compute expected hash
            expected = hashlib.sha256(content).hexdigest()
            result = sha256sum_file(file_path)

            assert result == expected

    def test_sha256sum_file_empty_file(self):
        """SHA256 sum of empty file should be known value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "empty.txt")

            with open(file_path, 'wb') as f:
                f.write(b"")

            # SHA256 of empty string
            expected = hashlib.sha256(b"").hexdigest()
            result = sha256sum_file(file_path)

            assert result == expected

    def test_sha256sum_file_not_found(self):
        """SHA256 sum should raise FileNotFoundError for missing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "nonexistent.txt")

            with pytest.raises(FileNotFoundError):
                sha256sum_file(file_path)

    def test_sha256sum_file_large_file(self):
        """SHA256 sum should handle large files efficiently."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "large.bin")
            # Create 1MB file
            content = b"x" * (1024 * 1024)

            with open(file_path, 'wb') as f:
                f.write(content)

            expected = hashlib.sha256(content).hexdigest()
            result = sha256sum_file(file_path)

            assert result == expected


class TestGetFileMtimeSnapshot:
    """Test file modification time snapshot functionality."""

    def test_snapshot_with_explicit_files(self):
        """Snapshot should return mtime for explicitly provided files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "file1.txt")
            file2 = os.path.join(tmpdir, "file2.txt")

            # Create files
            with open(file1, 'w') as f:
                f.write("content1")
            with open(file2, 'w') as f:
                f.write("content2")

            snapshot = get_file_mtime_snapshot(files=[file1, file2])

            assert len(snapshot) == 2
            assert file1 in snapshot
            assert file2 in snapshot
            assert snapshot[file1] > 0
            assert snapshot[file2] > 0

    def test_snapshot_with_glob_pattern(self):
        """Snapshot should use glob pattern when no files provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple Python files
            file1 = os.path.join(tmpdir, "test1.py")
            file2 = os.path.join(tmpdir, "test2.py")
            other = os.path.join(tmpdir, "test.txt")

            for f in [file1, file2, other]:
                with open(f, 'w') as fh:
                    fh.write("content")

            # Use default pattern (**/*.py)
            snapshot = get_file_mtime_snapshot(root_dir=tmpdir)

            # Should only find .py files
            assert len(snapshot) == 2
            assert file1 in snapshot or file1.replace("\\", "/") in snapshot
            assert file2 in snapshot or file2.replace("\\", "/") in snapshot

    def test_snapshot_empty_directory(self):
        """Snapshot should return empty dict for directory with no matches."""
        with tempfile.TemporaryDirectory() as tmpdir:
            snapshot = get_file_mtime_snapshot(root_dir=tmpdir)

            assert snapshot == {}

    def test_snapshot_with_custom_pattern(self):
        """Snapshot should use custom glob pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_file = os.path.join(tmpdir, "test.txt")
            py_file = os.path.join(tmpdir, "test.py")

            with open(txt_file, 'w') as f:
                f.write("text")
            with open(py_file, 'w') as f:
                f.write("python")

            snapshot = get_file_mtime_snapshot(
                pattern="*.txt",
                root_dir=tmpdir
            )

            assert len(snapshot) == 1
            assert txt_file in snapshot or txt_file.replace("\\", "/") in snapshot

    def test_snapshot_returns_floats(self):
        """Snapshot should return float values for mtimes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")

            with open(file_path, 'w') as f:
                f.write("content")

            snapshot = get_file_mtime_snapshot(files=[file_path])

            assert isinstance(list(snapshot.values())[0], float)


class TestAtomicWriteSymlinks:
    """Test atomic write behavior with symlinks."""

    def test_write_to_symlink_follows_link(self):
        """Writing to a symlink should write to the target file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create target file
            target_path = os.path.join(tmpdir, "target.txt")
            link_path = os.path.join(tmpdir, "link.txt")

            # Create symlink (skip on Windows if admin rights not available)
            try:
                os.symlink(target_path, link_path)
            except (OSError, NotImplementedError):
                # Symlink creation not supported (Windows without admin, etc.)
                pytest.skip("Symlink creation not supported on this system")

            content = "Hello via symlink"
            atomic_write(link_path, content)

            # Both link and target should have content
            assert os.path.exists(target_path)
            assert os.path.exists(link_path)
            with open(target_path, encoding='utf-8') as f:
                assert f.read() == content

    def test_write_to_symlink_preserves_link(self):
        """Writing via symlink should preserve the symlink itself."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = os.path.join(tmpdir, "target.txt")
            link_path = os.path.join(tmpdir, "link.txt")

            try:
                os.symlink(target_path, link_path)
            except (OSError, NotImplementedError):
                pytest.skip("Symlink creation not supported on this system")

            content = "Test content"
            atomic_write(link_path, content)

            # Verify link_path is still a symlink
            assert os.path.islink(link_path)

    def test_circular_symlink_raises_error(self):
        """Circular symlink should be handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a symlink that points to itself
            link_path = os.path.join(tmpdir, "circular.txt")

            try:
                # Create self-referential symlink
                os.symlink(link_path, link_path)
            except (OSError, NotImplementedError):
                pytest.skip("Symlink creation not supported on this system")

            content = "This should fail"
            # Should raise an error due to circular symlink
            with pytest.raises((OSError, ValueError)):
                atomic_write(link_path, content)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
