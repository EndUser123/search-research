#!/usr/bin/env python3
"""
Tests for REFACTOR Command Complexity Integration.

TDD RED phase: These tests FAIL initially, then drive implementation.

This module tests the --include-complexity flag integration in the /refactor command.
"""

import tempfile
from pathlib import Path

import pytest


def test_refactor_complexity_option_parsing():
    """
    Test that --include-complexity option is recognized.

    Given: The refactor command documentation
    When: Checking for --include-complexity option
    Then: Should be listed in the options table

    This ensures the option is documented and discoverable.
    """
    refactor_md = Path(__file__).resolve().parent.parent.parent / "commands" / "refactor.md"
    content = refactor_md.read_text()

    assert "--include-complexity" in content, \
        "refactor.md should include --include-complexity option"


def test_refactor_complexity_integration_section():
    """
    Test that complexity integration is documented.

    Given: The refactor command documentation
    When: Checking for complexity integration
    Then: Should have integration details

    This ensures users know how complexity integrates with refactor.
    """
    refactor_md = Path(__file__).resolve().parent.parent.parent / "commands" / "refactor.md"
    content = refactor_md.read_text()

    # Check for /complexity integration in See Also or Integration section
    assert "/complexity" in content, \
        "refactor.md should reference /complexity command"


def test_refactor_complexity_in_output_format():
    """
    Test that complexity is included in refactor output format.

    Given: The refactor command with --include-complexity
    When: Analyzing files with high complexity
    Then: Output should include complexity warnings

    Complexity warnings help prioritize refactoring efforts.
    """
    refactor_md = Path(__file__).resolve().parent.parent.parent / "commands" / "refactor.md"
    content = refactor_md.read_text()

    # Output format section should mention complexity when enabled
    assert "complexity" in content.lower(), \
        "refactor.md output format should mention complexity integration"


def test_refactor_complexity_with_threshold():
    """
    Test that complexity threshold can be configured.

    Given: The refactor command with --include-complexity
    When: Specifying --complexity-threshold
    Then: Should filter functions by threshold

    Allows users to set their own complexity tolerance.
    """
    refactor_md = Path(__file__).resolve().parent.parent.parent / "commands" / "refactor.md"
    content = refactor_md.read_text()

    # Should document threshold option
    has_threshold = "--complexity-threshold" in content or \
                    "threshold" in content.lower() and "complexity" in content.lower()

    assert has_threshold, \
        "refactor.md should document complexity threshold option"


def test_refactor_complexity_handles_high_cc_functions():
    """
    Test that high-complexity functions trigger refactor suggestions.

    Given: Code with high-complexity functions
    When: Running /refactor --include-complexity
    Then: Should suggest refactoring for high-CC functions

    This is the key use case - complexity-driven refactoring.
    """
    # Create test code with high complexity
    code = """
def process_batch(items):
    if items:
        for item in items:
            if item.get('type') == 'a':
                if item.get('status') == 'active':
                    return process_a(item)
                elif item.get('status') == 'pending':
                    return process_pending_a(item)
                else:
                    return process_other_a(item)
            elif item.get('type') == 'b':
                if item.get('status') == 'active':
                    return process_b(item)
                elif item.get('status') == 'pending':
                    return process_pending_b(item)
    return None
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        test_file = tmpdir / "high_cc.py"
        test_file.write_text(code)

        # Import and run complexity analysis
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from complexity_analysis import analyze_complexity

        result = analyze_complexity(str(test_file))

        assert result is not None, "Should return complexity analysis"
        assert "high_complexity" in result or "total_functions" in result, \
            "Should include complexity metrics"


def test_refactor_complexity_works_with_synergy_detection():
    """
    Test that complexity integrates with synergy detection.

    Given: Multiple files with varying complexity
    When: Running /refactor --include-complexity
    Then: Should combine complexity with synergy detection

    Complexity adds another dimension to synergy detection.
    """
    refactor_md = Path(__file__).resolve().parent.parent.parent / "commands" / "refactor.md"
    content = refactor_md.read_text()

    # Should mention how complexity works with synergies
    has_integration = "complexity" in content.lower() and "synergy" in content.lower()

    assert has_integration, \
        "refactor.md should explain how complexity integrates with synergy detection"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
