"""Simple test to verify temp_dir fixture works correctly.

Run with: pytest P:/.claude/skills/ai-cli/tests/test_temp_dir_fixture.py -v
"""

from pathlib import Path


def test_temp_dir_fixture_exists(temp_dir):
    """
    Test that temp_dir fixture provides a Path object to a temporary directory.

    Given: temp_dir fixture is available
    When: test uses temp_dir parameter
    Then: temp_dir should be a Path object pointing to an existing directory
    """
    # Assert - temp_dir should be a Path object
    assert isinstance(temp_dir, Path), f"temp_dir should be Path object, got {type(temp_dir)}"

    # Assert - temp_dir should point to an existing directory
    assert temp_dir.exists(), f"temp_dir path should exist: {temp_dir}"
    assert temp_dir.is_dir(), f"temp_dir should be a directory: {temp_dir}"


def test_temp_dir_can_create_files(temp_dir):
    """
    Test that temp_dir fixture allows creating test files.

    Given: temp_dir fixture provides a temporary directory
    When: test creates a file in temp_dir
    Then: file should be created successfully and be readable
    """
    # Arrange - Create a test file
    test_file = temp_dir / "test_example.txt"
    test_content = "Hello from temp_dir fixture!"

    # Act - Write content to file
    test_file.write_text(test_content, encoding="utf-8")

    # Assert - File should exist and contain expected content
    assert test_file.exists(), "Test file should exist in temp_dir"
    assert test_file.read_text(encoding="utf-8") == test_content, "File content should match"


def test_temp_dir_isolated_between_tests(temp_dir):
    """
    Test that each test gets a clean temp_dir (no contamination from previous tests).

    Given: Multiple tests use temp_dir fixture
    When: This test runs after other tests
    Then: temp_dir should be empty (fresh directory for this test)
    """
    # Assert - temp_dir should be empty at test start
    # (pytest's tmp_path provides a fresh directory for each test)
    contents = list(temp_dir.iterdir())
    assert len(contents) == 0, f"temp_dir should be empty at test start, found: {contents}"
