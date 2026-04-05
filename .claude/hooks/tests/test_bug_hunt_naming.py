#!/usr/bin/env python3
"""
Tests for Bug-Hunt Naming Check Integration.

TDD RED phase: These tests FAIL initially, then drive implementation.

This module tests the integration of variable naming checks into the bug-hunt workflow.
"""

import tempfile
from pathlib import Path

import pytest
from variable_naming import check_variable_naming, detect_confusable_names, suggest_better_names


def test_bug_hunt_detects_confusable_variables_in_batch_downloader():
    """
    Test that bug-hunt workflow detects confusable variables in real code.

    Given: A Python file with confusable variable names like completed_count vs successful_downloads
    When: The bug-hunt naming check runs
    Then: Should detect and report the confusable pair with suggestions

    This is the real-world scenario that caused the [0/10] display bug.
    """
    code = """
class BatchDownloader:
    def __init__(self):
        self.completed_count = 0  # All channels processed
        self.successful_downloads = 0  # Only channels with content
        self.failed_count = 0

    def update_progress(self):
        # Bug: using successful_downloads here causes [0/3] display
        self.progress_bar.update(self.successful_downloads)
"""

    result = detect_confusable_names(code)

    assert result is not None, "Should detect confusable names in batch downloader code"
    assert len(result) >= 1, "Should find at least one confusable pair"
    # Should find completed_count vs successful_downloads
    pair_names = [f"{a}/{b}" for a, b in result]
    assert any("completed" in p and "successful" in p for p in pair_names), \
        "Should detect completed_count vs successful_downloads"


def test_bug_hunt_provides_suggestions_for_confusable_pairs():
    """
    Test that bug-hunt workflow provides better name suggestions.

    Given: Confusable variables detected in code
    When: Better name suggestions are requested
    Then: Should return clearer, more semantic names

    The suggestions help users rename variables to prevent confusion.
    """
    confusable_pair = ("completed_count", "successful_downloads")

    suggestions = suggest_better_names(confusable_pair)

    assert len(suggestions) == 2, "Should suggest exactly two names"
    # Suggestions should make the semantics more explicit
    assert any("attempted" in s.lower() or "processed" in s.lower()
               for s in suggestions), \
        "Should suggest more explicit names like 'attempted' or 'processed'"


def test_bug_hunt_naming_check_on_directory():
    """
    Test that bug-hunt can scan a directory for confusable variables.

    Given: A directory with Python files containing confusable variables
    When: Bug-hunt naming check runs on the directory
    Then: Should find all confusable pairs across all files

    This enables bulk scanning of entire modules.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create a Python file with confusable variables
        test_file = tmpdir / "module.py"
        test_file.write_text("""
def process_batch():
    total_count = 0
    completed_count = 0
    success_count = 0
    return total_count, completed_count, success_count
""")

        # Read and check the file
        code = test_file.read_text()
        result = detect_confusable_names(code)

        assert result is not None, "Should detect confusable names in directory scan"
        # Should detect multiple *_count variables
        var_names = [v for pair in result for v in pair]
        assert "total_count" in var_names
        assert "completed_count" in var_names
        assert "success_count" in var_names


def test_bug_hunt_naming_check_full_workflow():
    """
    Test the full bug-hunt naming check workflow.

    Given: An edit with confusable variable names (simulating bug-hunt finding code)
    When: check_variable_naming is called with file context
    Then: Should return a properly formatted warning with suggestions

    This tests the integration point that bug-hunt would use.
    """
    old_code = "def process():\n    pass"
    new_code = """
def process():
    completed_count = 0
    successful_downloads = 0
    progress_bar.update(completed_count)
"""

    result = check_variable_naming(
        file_path="test_module.py",
        old_string=old_code,
        new_string=new_code
    )

    assert result is not None, "Should return a warning result"
    assert result.get("allowed") == True, "Should be a warning (allowed), not a block"
    assert result.get("severity") == "warning", "Should have warning severity"
    assert result.get("category") == "confusable_variable_names", "Should have correct category"
    assert "suggestions" in result, "Should include better name suggestions"
    assert len(result["suggestions"]) == 2, "Should have exactly 2 suggestions"


def test_bug_hunt_naming_check_filters_false_positives():
    """
    Test that bug-hunt naming check doesn't flag clearly different variables.

    Given: Code with clearly different variable names
    When: The naming check runs
    Then: Should NOT flag them as confusable (false positive prevention)

    This prevents excessive warnings on legitimate code.
    """
    code = """
def process():
    user_id = 123
    video_count = 10
    transcript_length = 5000
    channel_name = "example"
    return user_id, video_count, transcript_length, channel_name
"""

    result = detect_confusable_names(code)

    # Should return empty list or None for clearly different names
    assert result is None or len(result) == 0, \
        "Should not flag clearly different variable names"


def test_bug_hunt_naming_check_handles_single_variables():
    """
    Test that bug-hunt naming check handles code with single variable gracefully.

    Given: Code with only one variable assignment
    When: The naming check runs
    Then: Should return None (no pairs to compare)

    Edge case handling for minimal code.
    """
    code = """
def process():
    count = 0
    return count
"""

    result = detect_confusable_names(code)

    assert result is None or len(result) == 0, \
        "Should handle single variable gracefully"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
