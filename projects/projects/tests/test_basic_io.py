#!/usr/bin/env python3
"""
Basic I/O Tests - Tier 0 Smoke Test

Test Case ID: TC-TIER0-005
Priority: Critical
Test Type: Smoke Testing

Purpose:
Verify that basic input/output operations work correctly.
These tests ensure the system can read and write files safely.

Preconditions:
- System health tests pass
- File system permissions are adequate
- Test directories exist

Expected Results:
- File I/O operations work correctly
- Directory operations work correctly
- Error handling for I/O failures works

Test Duration: <0.3 seconds
"""

import json
import os
import sys
import time
from pathlib import Path


def test_file_creation_and_writing():
    """
    Test basic file creation and writing.

    Algorithm Approach: Create test files with different content types and verify writing works.

    Returns:
    bool: True if file creation and writing works correctly

    Raises:
    AssertionError: If file creation or writing fails
    """
    test_dir = Path("tests/test_outputs")
    test_dir.mkdir(parents=True, exist_ok=True)

    test_cases = [
        ("basic_text.txt", "Basic text content for testing file I/O operations."),
        ("unicode_text.txt", "Unicode test: 中文测试 🚀 ñáéíóú"),
        ("multiline_text.txt", "Line 1\nLine 2\nLine 3\n"),
        ("json_data.json", '{"test": "value", "number": 42, "array": [1, 2, 3]}'),
    ]

    created_files = []
    try:
        for filename, content in test_cases:
            file_path = test_dir / filename

            # Test file creation
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Verify file exists and has content
            assert file_path.exists(), f"File was not created: {file_path}"
            assert file_path.is_file(), f"Path is not a file: {file_path}"

            # Verify file size (allow for Windows line ending differences)
            file_size = file_path.stat().st_size
            assert file_size > 0, f"File appears empty: {file_path}"
            # Windows might use CRLF (\r\n) instead of LF (\n), so allow for size difference
            expected_size = len(content.encode("utf-8"))
            size_diff = abs(file_size - expected_size)
            assert (
                size_diff <= len(content.split("\n")) - 1
            ), f"File size mismatch: {file_size} vs {expected_size} (diff: {size_diff})"

            created_files.append(file_path)

        print(f"✓ File creation and writing works ({len(created_files)} files created)")

    except Exception as e:
        # Cleanup on error
        for file_path in created_files:
            if file_path.exists():
                file_path.unlink()
        raise AssertionError(f"File creation/writing test failed: {e}")


def test_file_reading():
    """
    Test basic file reading operations.

    Algorithm Approach: Read back the files created in the previous test and verify content.

    Returns:
    bool: True if file reading works correctly

    Raises:
    AssertionError: If file reading fails
    """
    test_dir = Path("tests/test_outputs")

    test_cases = [
        ("basic_text.txt", "Basic text content for testing file I/O operations."),
        ("unicode_text.txt", "Unicode test: 中文测试 🚀 ñáéíóú"),
        ("multiline_text.txt", "Line 1\nLine 2\nLine 3\n"),
        ("json_data.json", '{"test": "value", "number": 42, "array": [1, 2, 3]}'),
    ]

    try:
        for filename, expected_content in test_cases:
            file_path = test_dir / filename

            assert file_path.exists(), f"Test file missing: {file_path}"

            # Test file reading
            with open(file_path, encoding="utf-8") as f:
                read_content = f.read()

            assert read_content == expected_content, f"Content mismatch in {filename}"
            assert len(read_content) > 0, f"Read content appears empty for {filename}"

        print(f"✓ File reading works correctly ({len(test_cases)} files verified)")

    except Exception as e:
        raise AssertionError(f"File reading test failed: {e}")


def test_directory_operations():
    """
    Test basic directory operations.

    Algorithm Approach: Create, list, and manipulate directories.

    Returns:
    bool: True if directory operations work correctly

    Raises:
    AssertionError: If directory operations fail
    """
    base_test_dir = Path("tests/test_outputs/dir_operations_test")

    # Clean up any existing test directory
    if base_test_dir.exists():
        import shutil

        shutil.rmtree(base_test_dir)

    created_dirs = []
    try:
        # Test directory creation
        test_dirs = [
            base_test_dir,
            base_test_dir / "subdir1",
            base_test_dir / "subdir2",
            base_test_dir / "subdir1" / "nested",
        ]

        for dir_path in test_dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            assert dir_path.exists(), f"Directory not created: {dir_path}"
            assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"
            created_dirs.append(dir_path)

        # Test directory listing
        base_contents = list(base_test_dir.iterdir())
        subdir_names = [p.name for p in base_contents if p.is_dir()]
        assert "subdir1" in subdir_names, "subdir1 not found in listing"
        assert "subdir2" in subdir_names, "subdir2 not found in listing"

        # Test nested directory listing
        subdir1_contents = list((base_test_dir / "subdir1").iterdir())
        nested_names = [p.name for p in subdir1_contents if p.is_dir()]
        assert "nested" in nested_names, "nested directory not found"

        print(
            f"✓ Directory operations work correctly ({len(created_dirs)} directories created)"
        )

    except Exception as e:
        # Cleanup on error
        import shutil

        if base_test_dir.exists():
            shutil.rmtree(base_test_dir)
        raise AssertionError(f"Directory operations test failed: {e}")


def test_file_append_operations():
    """
    Test file append operations.

    Algorithm Approach: Test appending to existing files.

    Returns:
    bool: True if file append operations work correctly

    Raises:
    AssertionError: If file append operations fail
    """
    test_dir = Path("tests/test_outputs")
    test_file = test_dir / "append_test.txt"

    try:
        # Create initial file
        initial_content = "Initial content\n"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(initial_content)

        # Test append operation
        append_content = "Appended content\n"
        with open(test_file, "a", encoding="utf-8") as f:
            f.write(append_content)

        # Verify content
        with open(test_file, encoding="utf-8") as f:
            final_content = f.read()

        expected_content = initial_content + append_content
        assert (
            final_content == expected_content
        ), f"Append operation failed: {final_content}"

        # Test multiple appends
        with open(test_file, "a", encoding="utf-8") as f:
            f.write("Second append\n")

        with open(test_file, encoding="utf-8") as f:
            final_content = f.read()

        assert "Second append" in final_content, "Second append not found"
        assert (
            final_content.count("\n") == 3
        ), f"Expected 3 newlines, got {final_content.count('\n')}"

        print("✓ File append operations work correctly")

    except Exception as e:
        # Cleanup
        if test_file.exists():
            test_file.unlink()
        raise AssertionError(f"File append test failed: {e}")


def test_json_file_operations():
    """
    Test JSON file operations.

    Algorithm Approach: Test reading and writing JSON files.

    Returns:
    bool: True if JSON file operations work correctly

    Raises:
    AssertionError: If JSON file operations fail
    """
    test_dir = Path("tests/test_outputs")
    json_file = test_dir / "io_test.json"

    test_data = {
        "test_name": "basic_io_operations",
        "timestamp": time.time(),
        "data_types": {
            "string": "test string",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "array": [1, "two", 3.0, {"nested": "object"}],
            "object": {"key1": "value1", "key2": 2},
        },
        "unicode": "Unicode test: 中文测试 🚀",
    }

    try:
        # Test JSON writing
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)

        assert json_file.exists(), f"JSON file not created: {json_file}"
        assert (
            json_file.stat().st_size > 50
        ), f"JSON file too small: {json_file.stat().st_size}"

        # Test JSON reading
        with open(json_file, encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data == test_data, "JSON round-trip failed"
        assert loaded_data["unicode"] == test_data["unicode"], "Unicode data lost"

        # Test pretty format reading
        with open(json_file, encoding="utf-8") as f:
            raw_content = f.read()

        assert "    " in raw_content, "JSON not properly formatted"
        assert (
            test_data["data_types"]["string"] in raw_content
        ), "Expected content not in file"

        print("✓ JSON file operations work correctly")

    except Exception as e:
        # Cleanup
        if json_file.exists():
            json_file.unlink()
        raise AssertionError(f"JSON file operations test failed: {e}")


def test_error_handling():
    """
    Test I/O error handling.

    Algorithm Approach: Test that I/O operations handle errors gracefully.

    Returns:
    bool: True if error handling works correctly

    Raises:
    AssertionError: If error handling is insufficient
    """
    test_dir = Path("tests/test_outputs")
    non_existent_file = test_dir / "non_existent_file.txt"

    # Test reading non-existent file
    try:
        with open(non_existent_file) as f:
            content = f.read()
        raise AssertionError("Should have failed to read non-existent file")
    except FileNotFoundError:
        pass  # Expected
    except Exception as e:
        raise AssertionError(f"Unexpected error type for non-existent file: {e}")

    # Test writing to invalid location (if possible)
    invalid_path = (
        Path("/invalid/path/test.txt")
        if os.name != "nt"
        else Path("Z:\\invalid\\path\\test.txt")
    )

    try:
        with open(invalid_path, "w") as f:
            f.write("test")
        # If we get here, the path was somehow valid (rare case)
        invalid_path.unlink()  # Cleanup
        print("⚠ Invalid path test skipped (path was somehow valid)")
    except (FileNotFoundError, PermissionError, OSError):
        pass  # Expected
    except Exception as e:
        raise AssertionError(f"Unexpected error type for invalid path: {e}")

    # Test permission error simulation (create read-only file and try to write)
    readonly_file = test_dir / "readonly_test.txt"
    try:
        # Create a file
        with open(readonly_file, "w") as f:
            f.write("initial content")

        # Make it read-only (Unix systems)
        try:
            readonly_file.chmod(0o444)
            # Try to append to read-only file
            with open(readonly_file, "a") as f:
                f.write("should fail")
            raise AssertionError("Should have failed to write to read-only file")
        except PermissionError:
            pass  # Expected
        except OSError:
            pass  # Expected on some systems
        finally:
            # Restore write permission for cleanup
            readonly_file.chmod(0o644)
            readonly_file.unlink()

        print("✓ I/O error handling working correctly")

    except Exception as e:
        # Cleanup on error
        if readonly_file.exists():
            try:
                readonly_file.unlink()
            except:
                pass
        raise AssertionError(f"I/O error handling test failed: {e}")


def test_file_metadata_operations():
    """
    Test file metadata operations.

    Algorithm Approach: Test getting and basic file metadata operations.

    Returns:
    bool: True if file metadata operations work correctly

    Raises:
    AssertionError: If file metadata operations fail
    """
    test_dir = Path("tests/test_outputs")
    test_file = test_dir / "metadata_test.txt"

    try:
        # Create a test file
        test_content = "File metadata test content"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        # Get file stats
        stat = test_file.stat()

        # Verify basic metadata
        assert stat.st_size > 0, "File size should be greater than 0"
        assert stat.st_size == len(test_content.encode("utf-8")), "File size mismatch"
        assert stat.st_mtime > 0, "Modification time should be positive"

        # Test file existence checks
        assert test_file.exists(), "File should exist"
        assert test_file.is_file(), "Path should be a file"
        assert not test_file.is_dir(), "File path should not be a directory"

        # Test path operations
        assert test_file.name == "metadata_test.txt", "Filename mismatch"
        assert test_file.suffix == ".txt", "File extension mismatch"
        assert test_file.stem == "metadata_test", "File stem mismatch"

        # Test parent directory
        parent = test_file.parent
        assert parent == test_dir, "Parent directory mismatch"
        assert parent.name == "test_outputs", "Parent name mismatch"

        print("✓ File metadata operations work correctly")

    except Exception as e:
        # Cleanup
        if test_file.exists():
            test_file.unlink()
        raise AssertionError(f"File metadata operations test failed: {e}")


def cleanup_test_files():
    """
    Clean up test files created during I/O tests.

    Algorithm Approach: Remove all test files and directories created during testing.

    Returns:
    bool: True if cleanup completed successfully
    """
    test_dir = Path("tests/test_outputs")

    # Files to clean up
    files_to_clean = [
        "basic_text.txt",
        "unicode_text.txt",
        "multiline_text.txt",
        "json_data.json",
        "append_test.txt",
        "io_test.json",
        "metadata_test.txt",
    ]

    # Directories to clean up
    dirs_to_clean = ["dir_operations_test"]

    cleaned_count = 0

    try:
        # Clean up files
        for filename in files_to_clean:
            file_path = test_dir / filename
            if file_path.exists():
                file_path.unlink()
                cleaned_count += 1

        # Clean up directories
        import shutil

        for dirname in dirs_to_clean:
            dir_path = test_dir / dirname
            if dir_path.exists():
                shutil.rmtree(dir_path)
                cleaned_count += 1

        print(f"✓ Cleaned up {cleaned_count} test files/directories")

    except Exception as e:
        print(f"⚠ Cleanup completed with warnings: {e}")


def run_all_basic_io_tests():
    """
    Run all basic I/O smoke tests.

    Algorithm Approach: Execute all I/O tests in sequence and report results.

    Returns:
    tuple: (total_tests, passed_tests, failed_tests)
    """
    test_functions = [
        test_file_creation_and_writing,
        test_file_reading,
        test_directory_operations,
        test_file_append_operations,
        test_json_file_operations,
        test_error_handling,
        test_file_metadata_operations,
    ]

    total_tests = len(test_functions)
    passed_tests = 0
    failed_tests = []

    print("Running Basic I/O Smoke Tests...")
    print("=" * 50)

    try:
        for test_func in test_functions:
            try:
                test_func()
                passed_tests += 1
            except Exception as e:
                failed_tests.append(f"{test_func.__name__}: {e}")
                print(f"✗ {test_func.__name__} failed: {e}")

    finally:
        # Always attempt cleanup
        try:
            cleanup_test_files()
        except Exception as cleanup_error:
            print(f"⚠ Cleanup error: {cleanup_error}")

    print("=" * 50)
    print(f"Basic I/O Tests: {passed_tests}/{total_tests} passed")

    if failed_tests:
        print("Failed tests:")
        for failure in failed_tests:
            print(f"  - {failure}")

    return total_tests, passed_tests, failed_tests


if __name__ == "__main__":
    """
    Main execution for standalone testing.
    """
    total, passed, failed = run_all_basic_io_tests()

    if len(failed) == 0:
        print("✅ All Basic I/O smoke tests passed!")
        sys.exit(0)
    else:
        print("❌ Some Basic I/O smoke tests failed!")
        sys.exit(1)
