# Test Patterns for yt-fts

This document codifies the testing patterns and conventions used in this codebase.

## Characterization Tests

Characterization tests CAPTURE CURRENT BEHAVIOR before refactoring. They are not about what code *should* do, but what it *currently* does.

### Purpose

- **Before refactoring**: Document existing behavior so changes don't break it
- **After refactoring**: Verify behavior is preserved
- **For complex functions**: Create a safety net for changes

### File Naming Convention

Tests use the pattern: tests/yt_fts/module/test_feature_characterization.py

Examples:
- tests/yt_fts/download/test_channel_stats_characterization.py
- tests/yt_fts/download/test_batch_download_characterization.py

### Test Structure

"""Characterization tests for component_name.

These tests CAPTURE CURRENT BEHAVIOR before refactoring.
Run with: pytest tests/path/to/test_name_characterization.py -v
"""

from unittest.mock import MagicMock, patch
import pytest

from yt_fts.module import ClassUnderTest


class TestComponentNameBasicFormatting:
    """Tests for basic feature behavior."""

    @pytest.fixture
    def setup(self):
        """Create test fixture."""
        return ClassUnderTest(config="test")

    def test_specific_behavior(self, setup):
        """Characterization: what this test captures."""
        result = setup.method_under_test(params)
        
        # Assert current behavior - adjust if behavior changes
        assert result["key"] == expected_value



## Test Class Organization

Group related tests in classes by responsibility:

class TestFormatDbStatsBasicFormatting:
    """Tests for basic stats formatting."""

    def test_basic_stats_formatting(self, downloader):
        # ...

    def test_stats_with_unavailable(self, downloader):
        # ...

class TestFormatDbStatsImpossibleCounts:
    """Tests for impossible count detection."""

    def test_with_subs_exceeds_total(self, downloader):
        # ...

class TestFormatDbStatsVideoGaps:
    """Tests for unexplained video gap detection."""

    def test_significant_gap_high_severity(self, downloader):
        # ...

## Fixtures for Common Setup

@pytest.fixture
def downloader():
    """Create BatchDownloader with test config."""
    return BatchDownloader(
        channels=["@testchannel"],
        suppress_quota_print=True,
        suppress_verbose=True,
    )

@pytest.fixture
def runner():
    """Create Click CliRunner for CLI testing."""
    return CliRunner()

@pytest.fixture
def temp_channels_file(self):
    """Create temporary channels file for testing."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix="_channels.txt", delete=False, encoding="utf-8"
    ) as f:
        for line in ["@testchannel1", "https://youtube.com/@testchannel2"]:
            f.write(line + "
")
        temp_path = f.name
    yield temp_path
    try:
        os.unlink(temp_path)
    except OSError:
        pass

## Test Naming Conventions

| Test Type | Pattern | Example |
|-----------|---------|---------|
| Unit test | test_function_scenario | test_format_subscriber_count_millions |
| Characterization | test_feature_characterization | test_batch_download_characterization |
| Edge case | test_edge_case_description | test_zero_total_count |
| Integration | test_workflow_end_to_end | test_download_workflow_end_to_end |

## Assertion Patterns

Dictionary Return Values:
    def test_return_dict_contains_all_keys(self, downloader):
        result = downloader._format_db_stats(...)
        expected_keys = {
            "stats", "inconsistent", "reason", "severity",
            "type", "details", "inconsistency_id",
        }
        assert set(result.keys()) == expected_keys

String Formatting:
    def test_basic_stats_formatting(self, downloader):
        result = downloader._format_db_stats(...)
        assert result["stats"] == "100 total | 80 cc, 20 no cc"

Exception Behavior:
    def test_invalid_input_raises_error(self):
        with pytest.raises(ValueError, match="Invalid channel ID"):
            process_channel("invalid-id")

## Running Tests

Run All Tests:
    pytest -v

Run Specific Test File:
    pytest tests/yt_fts/download/test_channel_stats_characterization.py -v

Run Specific Test Class:
    pytest tests/yt_fts/download/test_channel_stats_characterization.py::TestFormatDbStatsBasicFormatting -v

Run Specific Test:
    pytest tests/yt_fts/download/test_channel_stats_characterization.py::TestFormatDbStatsBasicFormatting::test_basic_stats_formatting -v

Run with Coverage:
    pytest --cov=src/yt_fts/download --cov-report=html

## Best Practices

1. One assertion per test - Tests should verify one thing
2. Descriptive names - Test names should describe what they test
3. Arrange-Act-Assert - Structure tests clearly
4. Use fixtures - Don't repeat setup code
5. Mock external deps - Don't depend on external services
6. Test edge cases - Empty, zero, null, negative values
7. Characterize before refactor - Never refactor without tests

## Examples from This Codebase

ChannelStatisticsManager Characterization:
- File: tests/yt_fts/download/test_channel_stats_characterization.py
- Tests: 29 tests covering formatting, inconsistency detection, gaps, over-counting
- Run: pytest tests/yt_fts/download/test_channel_stats_characterization.py -v
