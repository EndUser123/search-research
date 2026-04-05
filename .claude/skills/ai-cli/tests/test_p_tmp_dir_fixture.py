"""Test p_tmp_dir fixture functionality."""

from pathlib import Path

import pytest


@pytest.fixture
def p_tmp_dir():
    """
    Create and cleanup P:/tmp/ directory.

    Creates P:/tmp/ directory if it doesn't exist.
    Returns Path object pointing to P:/tmp/.
    Cleans up test files created during test (optional).
    Scope: function level (default).
    """
    p_tmp = Path("P:/tmp/")
    p_tmp.mkdir(parents=True, exist_ok=True)
    yield p_tmp
    # Cleanup after test
    if p_tmp.exists():
        for f in p_tmp.glob("test_*"):
            try:
                f.unlink()
            except OSError:
                pass


class TestPTmpDirFixture:
    """Tests for p_tmp_dir fixture."""

    def test_p_tmp_dir_creates_directory(self, p_tmp_dir):
        """
        Test that p_tmp_dir fixture creates P:/tmp/ directory.

        Given: p_tmp_dir fixture is available
        When: Test uses p_tmp_dir fixture
        Then: P:/tmp/ directory should exist
        """
        # Assert directory exists
        assert p_tmp_dir.exists(), "P:/tmp/ directory should exist"
        assert p_tmp_dir.is_dir(), "P:/tmp/ should be a directory"

    def test_p_tmp_dir_returns_path_object(self, p_tmp_dir):
        """
        Test that p_tmp_dir returns a Path object.

        Given: p_tmp_dir fixture is available
        When: Test uses p_tmp_dir fixture
        Then: Should return Path object pointing to P:/tmp/
        """
        # Assert it's a Path object
        assert isinstance(p_tmp_dir, Path), "p_tmp_dir should return Path object"
        assert str(p_tmp_dir) == r"P:\tmp", "Should point to P:/tmp/"

    def test_p_tmp_dir_can_write_files(self, p_tmp_dir):
        """
        Test that p_tmp_dir allows writing test files.

        Given: p_tmp_dir fixture is available
        When: Test writes a file to p_tmp_dir
        Then: File should be writable and readable
        """
        # Create a test file
        test_file = p_tmp_dir / "test_fixture_write.txt"
        test_content = "Fixture test content"

        # Write and read
        test_file.write_text(test_content, encoding="utf-8")
        assert test_file.exists(), "Test file should exist"

        # Verify content
        content = test_file.read_text(encoding="utf-8")
        assert content == test_content, "Content should match"

    def test_p_tmp_dir_cleanup_after_test(self, p_tmp_dir):
        """
        Test that p_tmp_dir fixture cleans up test files (optional).

        Given: p_tmp_dir fixture is available
        When: Test creates files with test_ prefix
        Then: Files should be cleaned up after test (if cleanup is implemented)
        """
        # Create a test file with test_ prefix
        test_file = p_tmp_dir / "test_cleanup_example.txt"
        test_file.write_text("Cleanup test", encoding="utf-8")

        # File should exist during test
        assert test_file.exists(), "Test file should exist during test"

        # Note: Cleanup happens in fixture teardown after test completes
        # This test verifies the file can be created during test execution
