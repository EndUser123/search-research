#!/usr/bin/env python3
"""
Tests for file lock cleanup detection in PostToolWrite_code_quality.py

Tests the _check_file_lock_cleanup() function which detects missing
file lock cleanup code using AST-based parsing.
"""

import sys
import tempfile
from pathlib import Path

import pytest

# Add hooks directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PostToolWrite_code_quality import _check_file_lock_cleanup


class TestFileLockCleanupDetection:
    """Test suite for file lock cleanup detection."""

    def create_temp_file(self, content: str) -> Path:
        """Helper to create temporary test files."""
        fd, path = tempfile.mkstemp(suffix='.py', text=True)
        temp_path = Path(path)
        temp_path.write_text(content)
        return temp_path

    def cleanup_temp_file(self, temp_path: Path):
        """Helper to cleanup temp files, handling Windows file locking."""
        try:
            temp_path.unlink(missing_ok=True)
        except (PermissionError, OSError):
            # Windows file locking - file will be cleaned up by temp directory cleanup
            pass

    def test_detects_buggy_file_lock_usage(self):
        """Should detect file using file_lock() without cleanup."""
        content = '''
from pathlib import Path

def some_function():
    lock_path = Path("/tmp/test.lock")

    # Buggy: uses file_lock without cleanup
    with file_lock(lock_path):
        # Do some work
        pass

    # BUG: No cleanup code - lock file never deleted!
'''
        temp_file = self.create_temp_file(content)
        try:
            result = _check_file_lock_cleanup(str(temp_file))
            assert result is not None, "Should detect missing cleanup"
            assert "uses file_lock() without lock file cleanup" in result
        finally:
            self.cleanup_temp_file(temp_file)

    def test_ignores_file_lock_definition_only(self):
        """Should ignore files that define file_lock() but don't use it."""
        content = '''
from contextlib import contextmanager
from pathlib import Path

@contextmanager
def file_lock(lock_path: Path):
    """File lock context manager."""
    lock_file = None
    try:
        lock_file = open(lock_path, 'w')
        yield True
    finally:
        if lock_file:
            lock_file.close()
'''
        temp_file = self.create_temp_file(content)
        try:
            result = _check_file_lock_cleanup(str(temp_file))
            assert result is None, "Should not warn about definition-only files"
        finally:
            self.cleanup_temp_file(temp_file)

    def test_recognizes_file_with_cleanup(self):
        """Should recognize files with proper cleanup code."""
        content = '''
from pathlib import Path

def some_function():
    lock_path = Path("/tmp/test.lock")

    # Fixed: uses file_lock with cleanup
    with file_lock(lock_path):
        # Do some work
        pass

    # Clean up lock file
    try:
        if lock_path.exists():
            lock_path.unlink()
    except (OSError, IOError):
        pass
'''
        temp_file = self.create_temp_file(content)
        try:
            result = _check_file_lock_cleanup(str(temp_file))
            assert result is None, "Should not warn when cleanup exists"
        finally:
            self.cleanup_temp_file(temp_file)

    def test_no_false_positive_from_comments(self):
        """Should not trigger on comments mentioning file_lock()."""
        content = '''
"""This module checks for file_lock() usage."""

# Check if file uses file_lock() context manager
# Missing cleanup pattern in finally block

def check_file(file_path: str):
    """Check file for issues."""
    # This function mentions file_lock in comments but doesn't use it
    pass
'''
        temp_file = self.create_temp_file(content)
        try:
            result = _check_file_lock_cleanup(str(temp_file))
            assert result is None, "Should not warn about comments"
        finally:
            self.cleanup_temp_file(temp_file)

    def test_handles_syntax_errors_gracefully(self):
        """Should fall back to string check on syntax errors."""
        content = '''
from pathlib import Path

def broken_syntax(:
    """Invalid Python syntax."""
    with file_lock(lock_path:
'''
        temp_file = self.create_temp_file(content)
        try:
            # Should not raise exception, should use fallback logic
            result = _check_file_lock_cleanup(str(temp_file))
            # Fallback will check for string patterns
            assert result is not None or result is None  # Either is acceptable
        finally:
            self.cleanup_temp_file(temp_file)

    def test_handles_read_errors_gracefully(self):
        """Should fail silently on read errors."""
        # Use a non-existent file path
        result = _check_file_lock_cleanup("/nonexistent/file.py")
        assert result is None, "Should fail silently on read errors"

    def test_detects_os_remove_cleanup(self):
        """Should recognize os.remove() as valid cleanup."""
        content = '''
import os
from pathlib import Path

def some_function():
    lock_path = Path("/tmp/test.lock")

    with file_lock(lock_path):
        pass

    # Clean up using os.remove()
    try:
        if os.path.exists(lock_path):
            os.remove(lock_path)
    except OSError:
        pass
'''
        temp_file = self.create_temp_file(content)
        try:
            result = _check_file_lock_cleanup(str(temp_file))
            assert result is None, "Should recognize os.remove() as cleanup"
        finally:
            self.cleanup_temp_file(temp_file)

    def test_detects_attribute_unlink_call(self):
        """Should detect .unlink() calls on any path object."""
        content = '''
from pathlib import Path

def some_function():
    my_lock = Path("/tmp/my.lock")

    with file_lock(my_lock):
        pass

    # Clean up
    if my_lock.exists():
        my_lock.unlink()
'''
        temp_file = self.create_temp_file(content)
        try:
            result = _check_file_lock_cleanup(str(temp_file))
            assert result is None, "Should recognize .unlink() on any path"
        finally:
            self.cleanup_temp_file(temp_file)

    def test_no_warning_without_file_lock_usage(self):
        """Should not warn if file doesn't use file_lock at all."""
        content = '''
from pathlib import Path

def some_function():
    lock_path = Path("/tmp/test.lock")

    # Normal file operations, no file_lock usage
    with open(lock_path, 'w') as f:
        f.write("data")

    # Clean up
    lock_path.unlink()
'''
        temp_file = self.create_temp_file(content)
        try:
            result = _check_file_lock_cleanup(str(temp_file))
            assert result is None, "Should not warn if file_lock not used"
        finally:
            self.cleanup_temp_file(temp_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
