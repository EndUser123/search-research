"""
Tests for JSON output format in yt-fts search command.

These tests verify the --format json option for the search command.
Following TDD RED phase - these tests are expected to FAIL initially.
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


class TestJsonOutputFormat:
    """
    Test suite for --format json option in search command.

    TDD RED Phase: These tests are written to FAIL initially.
    The --format json option does not exist yet.
    """

    def test_search_with_format_json_produces_valid_json(self, runner, test_db):
        """
        TSK-001: Test that --format json produces valid JSON output.

        Given: A database with subtitle data
        When: Running 'yt-fts search "guilt" --format json'
        Then: Output should be valid JSON that can be parsed

        Expected: This test FAILS because --format json option doesn't exist yet.
        """
        # Reset console cache to ensure fresh output
        reset_console_cache()

        # Set environment so CliRunner can find the database
        env = {"YT_FTS_DB_PATH": test_db}

        # Run search command with --format json (option doesn't exist yet)
        result = runner.invoke(cli, ["search", "guilt", "--format", "json"], env=env)

        # The command should succeed
        assert result.exit_code == 0, f"Command failed with: {result.output or result.stderr or result.exception}"

        # Output should be valid JSON
        try:
            json_output = json.loads(result.output)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {e}\nOutput was:\n{result.output}")

        # Basic validation - should be a list
        assert isinstance(json_output, list), "JSON output should be a list of search results"

    def test_search_default_format_still_works(self, runner, test_db):
        """
        Test that default behavior (no --format) still produces table output.

        Given: A database with subtitle data
        When: Running 'yt-fts search "guilt"' without --format
        Then: Output should be the default table format (not JSON)

        This ensures backward compatibility when adding --format option.
        """
        # Reset console cache to ensure fresh output
        reset_console_cache()

        # Set environment so CliRunner can find the database
        env = {"YT_FTS_DB_PATH": test_db}

        # Run search command without --format option
        result = runner.invoke(cli, ["search", "guilt", "--fts-only"], env=env)

        # The command should succeed
        assert result.exit_code == 0, f"Command failed with: {result.output or result.stderr or result.exception}"

        # Output should NOT be valid JSON (it's a formatted table)
        try:
            json.loads(result.output)
            # If we got here, the output was parsable as JSON - which means default format is broken
            pytest.fail("Default output should not be JSON format")
        except json.JSONDecodeError:
            # This is expected - default output is a table, not JSON
            pass


class TestJsonSchemaValidation:
    """
    Test suite for JSON schema validation.

    TDD RED Phase: These tests verify the expected JSON schema.
    """

    def test_json_schema_has_required_fields(self, runner, test_db):
        """
        TSK-002: Test JSON output contains all required fields.

        Given: A database with subtitle data
        When: Running 'yt-fts search "guilt" --format json'
        Then: Each result should have: video_id, video_title, channel_name,
              timestamp, text, url

        Expected schema:
        [
            {
                "video_id": "abc123",
                "video_title": "Video Title",
                "channel_name": "Channel Name",
                "timestamp": 123.45,
                "text": "Subtitle text...",
                "url": "https://youtube.com/watch?v=abc123&t=123"
            }
        ]
        """
        # Reset console cache to ensure fresh output
        reset_console_cache()

        # Set environment so CliRunner can find the database
        env = {"YT_FTS_DB_PATH": test_db}

        # Run search command with --format json
        result = runner.invoke(cli, ["search", "guilt", "--format", "json"], env=env)

        # The command should succeed
        assert result.exit_code == 0, f"Command failed with: {result.output or result.stderr or result.exception}"

        # Parse JSON output
        try:
            json_output = json.loads(result.output)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {e}\nOutput was:\n{result.output}")

        # Verify it's a list
        assert isinstance(json_output, list), "JSON output should be a list"

        # If we have results, validate the schema
        if len(json_output) > 0:
            first_result = json_output[0]

            # Check all required fields exist
            required_fields = [
                "video_id",
                "video_title",
                "channel_name",
                "timestamp",
                "text",
                "url"
            ]

            for field in required_fields:
                assert field in first_result, f"Missing required field: {field}"

            # Validate field types
            assert isinstance(first_result["video_id"], str), "video_id should be a string"
            assert isinstance(first_result["video_title"], str), "video_title should be a string"
            assert isinstance(first_result["channel_name"], str), "channel_name should be a string"
            # timestamp can be int, float, or string representation
            assert isinstance(first_result["text"], str), "text should be a string"
            assert isinstance(first_result["url"], str), "url should be a string"

            # Validate URL format
            assert "youtube.com" in first_result["url"] or "youtu.be" in first_result["url"], \
                "url should be a YouTube URL"

    @pytest.mark.skip(reason="Channel resolution system requires valid channel IDs (UC prefix or @handle), not legacy numeric IDs")
    def test_json_schema_with_channel_search(self, runner, test_db):
        """
        Test JSON schema works correctly with channel-scoped search.

        Given: A database with subtitle data
        When: Running 'yt-fts search "criminal" -c "1" --format json'
        Then: JSON output should have correct schema for channel search
        """
        # Reset console cache to ensure fresh output
        reset_console_cache()

        # Set environment so CliRunner can find the database
        env = {"YT_FTS_DB_PATH": test_db}

        # Run search command with channel filter and JSON format
        result = runner.invoke(cli, ["search", "-c", "1", "criminal", "--format", "json"], env=env)

        # The command should succeed
        assert result.exit_code == 0, f"Command failed with: {result.output or result.stderr or result.exception}"

        # Parse and validate JSON
        try:
            json_output = json.loads(result.output)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {e}\nOutput was:\n{result.output}")

        # Should be a list
        assert isinstance(json_output, list), "JSON output should be a list"

        # If results exist, all should be from the searched channel
        if len(json_output) > 0:
            # Channel name could be "1" or the resolved name
            # Just verify schema is consistent
            first_result = json_output[0]
            assert "channel_name" in first_result, "Missing channel_name field"

    def test_json_empty_results(self, runner, test_db):
        """
        Test JSON output for empty search results.

        Given: A database with subtitle data
        When: Running 'yt-fts search "nonexistenttermxyz123" --format json'
        Then: JSON output should be an empty list or valid structure indicating no results
        """
        # Reset console cache to ensure fresh output
        reset_console_cache()

        # Set environment so CliRunner can find the database
        env = {"YT_FTS_DB_PATH": test_db}

        # Run search for a term that likely doesn't exist
        result = runner.invoke(cli, ["search", "nonexistenttermxyz123", "--format", "json"], env=env)

        # The command should succeed even with no results
        assert result.exit_code == 0, f"Command failed with: {result.output or result.stderr or result.exception}"

        # Parse JSON - should handle empty results gracefully
        try:
            json_output = json.loads(result.output)
            # Should be a list (possibly empty)
            assert isinstance(json_output, list), "JSON output should be a list even when empty"
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON for empty results: {e}\nOutput was:\n{result.output}")

    def test_json_with_limit_option(self, runner, test_db):
        """
        Test JSON output respects the --limit option.

        Given: A database with subtitle data
        When: Running 'yt-fts search "guilt" --format json -l 5'
        Then: JSON output should contain at most 5 results
        """
        # Reset console cache to ensure fresh output
        reset_console_cache()

        # Set environment so CliRunner can find the database
        env = {"YT_FTS_DB_PATH": test_db}

        # Run search with limit
        result = runner.invoke(cli, ["search", "guilt", "--format", "json", "-l", "5"], env=env)

        # The command should succeed
        assert result.exit_code == 0, f"Command failed with: {result.output or result.stderr or result.exception}"

        # Parse JSON
        try:
            json_output = json.loads(result.output)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {e}\nOutput was:\n{result.output}")

        # Should be a list with at most 5 results
        assert isinstance(json_output, list), "JSON output should be a list"
        assert len(json_output) <= 5, f"Expected at most 5 results, got {len(json_output)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
