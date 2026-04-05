"""
Tests for --reverse flag in yt-fts search command.

These tests verify the --reverse flag that reverses the result order.
Following TDD RED phase - these tests are expected to FAIL initially.

Feature: --reverse flag
- Without --reverse: results show in default order (newest first)
- With --reverse: results show in reversed order (oldest first)
- Should work with both --format table and --format json
"""

import json
import os
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

# Ensure src is in path
_src_path = Path(__file__).parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from yt_fts.core.cli import cli
from yt_fts.utils.rich_console import reset_console_cache
from testing_utils import fetch_and_unzip_test_db

# On Windows, config is in APPDATA, on Linux/Mac it's in ~/.config
if sys.platform == "win32":
    CONFIG_DIR = os.path.join(os.getenv("APPDATA", ""), "yt-fts")
else:
    CONFIG_DIR = os.path.expanduser("~/.config/yt-fts")


@pytest.fixture(scope="function")
def test_db():
    """
    Set up test database for each test function.

    This fixture ensures a fresh test database is available.
    """
    # Fetch the test database
    fetch_and_unzip_test_db()

    db_path = os.path.join(CONFIG_DIR, "subtitles.db")
    return db_path


@pytest.fixture(scope="function")
def runner():
    """Provide a CliRunner instance."""
    return CliRunner()


class TestReverseFlagBasic:
    """
    Test suite for --reverse flag basic functionality.

    TDD RED Phase: These tests are written to FAIL initially.
    The --reverse flag does not exist yet.
    """

    def test_reverse_flag_changes_result_order(self, runner, test_db):
        """
        TSK-007-01: Test that --reverse changes the result order.

        Given: A database with subtitle data
        When: Running 'yt-fts search "guilt" --format json'
        And: Running 'yt-fts search "guilt" --format json --reverse'
        Then: The results should be in opposite order

        Expected: This test FAILS because --reverse flag doesn't exist yet.
        """
        # Reset console cache to ensure fresh output
        reset_console_cache()

        # Set environment so CliRunner can find the database
        env = {"YT_FTS_DB_PATH": test_db}

        # Run search WITHOUT --reverse (default order)
        result_default = runner.invoke(
            cli, ["search", "guilt", "--format", "json", "-l", "10"], env=env
        )

        # The command should succeed
        assert result_default.exit_code == 0, (
            f"Default command failed with: {result_default.output or result_default.stderr or result_default.exception}"
        )

        # Parse default order results
        default_results = json.loads(result_default.output)

        # Reset console cache again
        reset_console_cache()

        # Run search WITH --reverse (reversed order)
        result_reversed = runner.invoke(
            cli, ["search", "guilt", "--format", "json", "--reverse", "-l", "10"], env=env
        )

        # The command should succeed
        assert result_reversed.exit_code == 0, (
            f"Reverse command failed with: {result_reversed.output or result_reversed.stderr or result_reversed.exception}"
        )

        # Parse reversed order results
        reversed_results = json.loads(result_reversed.output)

        # Both should have the same number of results
        assert len(default_results) == len(reversed_results), (
            f"Result count mismatch: default={len(default_results)}, reversed={len(reversed_results)}"
        )

        # If we have results, verify they are in opposite order
        if len(default_results) > 1:
            # The first result in default should be the last result in reversed
            assert default_results[0]["video_id"] == reversed_results[-1]["video_id"], (
                f"First default result should match last reversed result. "
                f"Got: default[0]={default_results[0]['video_id']}, "
                f"reversed[-1]={reversed_results[-1]['video_id']}"
            )

            # The last result in default should be the first result in reversed
            assert default_results[-1]["video_id"] == reversed_results[0]["video_id"], (
                f"Last default result should match first reversed result. "
                f"Got: default[-1]={default_results[-1]['video_id']}, "
                f"reversed[0]={reversed_results[0]['video_id']}"
            )

    def test_default_behavior_unchanged_without_reverse_flag(self, runner, test_db):
        """
        TSK-007-02: Test that default behavior (no flag) is unchanged.

        Given: A database with subtitle data
        When: Running 'yt-fts search "guilt"' without --reverse
        Then: Results should be in default order (newest first)

        This ensures backward compatibility when adding --reverse flag.
        """
        # Reset console cache to ensure fresh output
        reset_console_cache()

        # Set environment so CliRunner can find the database
        env = {"YT_FTS_DB_PATH": test_db}

        # Run search command without --reverse flag
        result = runner.invoke(cli, ["search", "guilt", "--format", "json"], env=env)

        # The command should succeed
        assert result.exit_code == 0, (
            f"Command failed with: {result.output or result.stderr or result.exception}"
        )

        # Output should be valid JSON
        try:
            json_output = json.loads(result.output)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {e}\nOutput was:\n{result.output}")

        # Should be a list of results
        assert isinstance(json_output, list), "JSON output should be a list of search results"

        # Verify results are in default order (we can't verify "newest first" without
        # knowing the actual timestamps, but we can verify we get results)
        # The important thing is that the default behavior is preserved


class TestReverseFlagWithFormats:
    """
    Test suite for --reverse flag with different output formats.

    TDD RED Phase: These tests verify --reverse works with all formats.
    """

    def test_reverse_flag_with_json_format(self, runner, test_db):
        """
        TSK-007-03: Test that --reverse works with JSON format.

        Given: A database with subtitle data
        When: Running 'yt-fts search "guilt" --format json --reverse'
        Then: JSON output should have results in reversed order

        Expected: This test FAILS because --reverse flag doesn't exist yet.
        """
        # Reset console cache to ensure fresh output
        reset_console_cache()

        # Set environment so CliRunner can find the database
        env = {"YT_FTS_DB_PATH": test_db}

        # Run search with --reverse and JSON format
        result = runner.invoke(
            cli, ["search", "guilt", "--format", "json", "--reverse", "-l", "10"], env=env
        )

        # The command should succeed
        assert result.exit_code == 0, (
            f"Command failed with: {result.output or result.stderr or result.exception}"
        )

        # Output should be valid JSON
        try:
            json_output = json.loads(result.output)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {e}\nOutput was:\n{result.output}")

        # Should be a list
        assert isinstance(json_output, list), "JSON output should be a list"

        # Get default order for comparison
        reset_console_cache()
        result_default = runner.invoke(
            cli, ["search", "guilt", "--format", "json", "-l", "10"], env=env
        )

        default_results = json.loads(result_default.output)

        # Verify reversed order
        if len(default_results) > 1 and len(json_output) > 1:
            assert default_results[0]["video_id"] == json_output[-1]["video_id"], (
                "Results should be in opposite order with --reverse"
            )

    def test_reverse_flag_with_table_format(self, runner, test_db):
        """
        TSK-007-04: Test that --reverse works with table format.

        Given: A database with subtitle data
        When: Running 'yt-fts search "guilt" --format table --reverse'
        Then: Table output should have results in reversed order

        Note: This test verifies the command succeeds. Testing actual table
        output order is difficult since table rendering is done by Rich.
        We rely on JSON tests for order verification.

        Expected: This test FAILS because --reverse flag doesn't exist yet.
        """
        # Reset console cache to ensure fresh output
        reset_console_cache()

        # Set environment so CliRunner can find the database
        env = {"YT_FTS_DB_PATH": test_db}

        # Run search with --reverse and table format (explicit)
        result = runner.invoke(
            cli, ["search", "guilt", "--format", "table", "--reverse", "-l", "10"], env=env
        )

        # The command should succeed
        assert result.exit_code == 0, (
            f"Command failed with: {result.output or result.stderr or result.exception}"
        )

        # Note: We can't easily verify table output order since Rich console
        # output goes to actual stdout, not result.output


class TestReverseFlagCombinations:
    """
    Test suite for --reverse flag combined with other options.

    TDD RED Phase: These tests verify --reverse works in various combinations.
    """

    def test_reverse_flag_with_limit(self, runner, test_db):
        """
        TSK-007-05: Test that --reverse works correctly with --limit.

        Given: A database with subtitle data
        When: Running 'yt-fts search "guilt" --format json --reverse -l 5'
        Then: Should get 5 results in reversed order

        Expected: This test FAILS because --reverse flag doesn't exist yet.
        """
        # Reset console cache to ensure fresh output
        reset_console_cache()

        # Set environment so CliRunner can find the database
        env = {"YT_FTS_DB_PATH": test_db}

        # Run search with --reverse and limit
        result = runner.invoke(
            cli, ["search", "guilt", "--format", "json", "--reverse", "-l", "5"], env=env
        )

        # The command should succeed
        assert result.exit_code == 0, (
            f"Command failed with: {result.output or result.stderr or result.exception}"
        )

        # Parse JSON output
        json_output = json.loads(result.output)

        # Should have at most 5 results
        assert len(json_output) <= 5, f"Expected at most 5 results, got {len(json_output)}"

        # Get results with same limit but without reverse for comparison
        reset_console_cache()
        result_default = runner.invoke(
            cli, ["search", "guilt", "--format", "json", "-l", "5"], env=env
        )

        default_results = json.loads(result_default.output)

        # Same number of results
        assert len(json_output) == len(default_results), (
            f"Result count should match with/without reverse. "
            f"Got: {len(json_output)} with reverse, {len(default_results)} without"
        )

        # If we have results, verify reversed order
        if len(default_results) > 1 and len(json_output) > 1:
            assert default_results[0]["video_id"] == json_output[-1]["video_id"], (
                "Results should be in opposite order with --reverse, even with limit"
            )

    def test_reverse_flag_with_channel_search(self, runner, test_db):
        """
        TSK-007-06: Test that --reverse works with channel-scoped search.

        Given: A database with subtitle data
        When: Running 'yt-fts search "criminal" -c "1" --format json --reverse'
        Then: JSON output should have channel results in reversed order

        Expected: This test FAILS because --reverse flag doesn't exist yet.
        """
        # Reset console cache to ensure fresh output
        reset_console_cache()

        # Set environment so CliRunner can find the database
        env = {"YT_FTS_DB_PATH": test_db}

        # Run channel search with --reverse
        result = runner.invoke(
            cli, ["search", "-c", "1", "criminal", "--format", "json", "--reverse", "-l", "10"], env=env
        )

        # The command should succeed
        assert result.exit_code == 0, (
            f"Command failed with: {result.output or result.stderr or result.exception}"
        )

        # Parse JSON output
        try:
            json_output = json.loads(result.output)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {e}\nOutput was:\n{result.output}")

        # Should be a list
        assert isinstance(json_output, list), "JSON output should be a list"

        # Get default order for comparison
        reset_console_cache()
        result_default = runner.invoke(
            cli, ["search", "-c", "1", "criminal", "--format", "json", "-l", "10"], env=env
        )

        default_results = json.loads(result_default.output)

        # Same number of results
        assert len(json_output) == len(default_results), (
            f"Result count should match with/without reverse. "
            f"Got: {len(json_output)} with reverse, {len(default_results)} without"
        )

        # If we have results, verify reversed order
        if len(default_results) > 1 and len(json_output) > 1:
            assert default_results[0]["video_id"] == json_output[-1]["video_id"], (
                "Channel search results should be in opposite order with --reverse"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
