"""Tests for datetime suffix in output filenames.

These tests verify that when --output-file is specified, the output filename
includes a datetime suffix (e.g., output_YYYYMMDD_HHMMSS.json).

Run with: pytest P:/.claude/skills/ai-cli/tests/test_datetime_filename.py -v
"""

import json
import re

# Add parent directory to path for imports
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_cli import main


class TestDatetimeFilename:
    """Tests for datetime suffix in output filenames when --output-file is specified."""

    def test_output_file_includes_datetime_suffix(self, temp_dir):
        """
        Test that --output-file appends datetime to filename (e.g., output_YYYYMMDD_HHMMSS.json).

        Given: ask_cli.py is run with --output-file flag
        When: The CLI executes with a simple query
        Then: The output filename should have datetime pattern (output_YYYYMMDD_HHMMSS.json)
              And: The file should be created with valid JSON content

        This test FAILS (RED phase) because the datetime suffix feature is not yet implemented.
        """
        # Arrange
        base_filename = "output.json"
        output_file_arg = str(temp_dir / base_filename)
        query = "test query"

        # Mock run_parallel_llm to avoid actual LLM calls
        mock_results = {
            "qwen": {"output": "Qwen response", "error": None},
            "gemini": {"output": "Gemini response", "error": None},
        }

        # Act - Run ask_cli with --output-file flag
        with patch("ai_cli.run_parallel_llm", return_value=mock_results):
            with patch.object(
                sys,
                "argv",
                [
                    "ask_cli.py",
                    query,
                    "--output-file",
                    output_file_arg,
                    "--output-format",
                    "json",
                    "--qwen-only",  # Use single LLM for faster test
                ],
            ):
                try:
                    main()
                except SystemExit:
                    # argparse calls sys.exit() in some scenarios
                    pass

        # Assert - Verify the output filename has datetime pattern
        # Expected pattern: output_YYYYMMDD_HHMMSS_XXXXXX.json (with microseconds)
        datetime_pattern = re.compile(r"^output_\d{8}_\d{6}_\d{6}\.json$")

        # Check all files in temp_dir for matching pattern
        output_files = list(temp_dir.glob("output_*.json"))
        assert len(output_files) > 0, "Should create at least one output file with datetime suffix"

        # Verify at least one file matches the expected datetime pattern
        matching_files = [f for f in output_files if datetime_pattern.match(f.name)]
        assert len(matching_files) > 0, (
            f"Expected output file with datetime suffix (e.g., output_YYYYMMDD_HHMMSS.json). "
            f"Found files: {[f.name for f in output_files]}"
        )

        # Verify the file was created with valid JSON content
        output_file = matching_files[0]
        assert output_file.exists(), f"Output file should exist: {output_file}"

        content = output_file.read_text(encoding="utf-8")
        parsed_json = json.loads(content)
        assert "qwen" in parsed_json, "Output JSON should contain qwen result"
        assert parsed_json["qwen"]["output"] == "Qwen response"

    def test_output_file_without_extension_gets_json_extension(self, temp_dir):
        """
        Test that --output-file without .json extension gets .json added with datetime suffix.

        Given: ask_cli.py is run with --output-file flag (no .json extension)
        When: The CLI executes
        Then: The output filename should be <basename>_YYYYMMDD_HHMMSS.json

        This test FAILS (RED phase) because the datetime suffix feature is not yet implemented.
        """
        # Arrange
        base_filename = "output"  # No .json extension
        output_file_arg = str(temp_dir / base_filename)
        query = "test query"

        # Mock run_parallel_llm to avoid actual LLM calls
        mock_results = {
            "qwen": {"output": "Response", "error": None},
        }

        # Act
        with patch("ai_cli.run_parallel_llm", return_value=mock_results):
            with patch.object(
                sys,
                "argv",
                [
                    "ask_cli.py",
                    query,
                    "--output-file",
                    output_file_arg,
                    "--output-format",
                    "json",
                    "--qwen-only",
                ],
            ):
                try:
                    main()
                except SystemExit:
                    pass

        # Assert - Verify .json extension is added with datetime suffix (with microseconds)
        datetime_pattern = re.compile(r"^output_\d{8}_\d{6}_\d{6}\.json$")
        output_files = list(temp_dir.glob("output_*.json"))

        assert (
            len(output_files) > 0
        ), "Should create output file with .json extension and datetime suffix"
        matching_files = [f for f in output_files if datetime_pattern.match(f.name)]
        assert len(matching_files) > 0, (
            f"Expected file with pattern: output_YYYYMMDD_HHMMSS.json. "
            f"Found: {[f.name for f in output_files]}"
        )

    def test_datetime_suffix_is_unique_for_concurrent_runs(self, temp_dir):
        """
        Test that multiple runs with same --output-file create unique datetime-suffixed files.

        Given: ask_cli.py is run multiple times with same --output-file argument
        When: The CLI executes multiple times
        Then: Each run should create a file with unique datetime suffix

        This test FAILS (RED phase) because the datetime suffix feature is not yet implemented.
        """
        # Arrange
        base_filename = "output.json"
        output_file_arg = str(temp_dir / base_filename)
        query = "test query"

        mock_results = {
            "qwen": {"output": "Response", "error": None},
        }

        # Act - Run the CLI multiple times
        created_files = []
        for i in range(3):
            # Get files before this run
            files_before = {f.name for f in temp_dir.glob("output_*.json")}

            with patch("ai_cli.run_parallel_llm", return_value=mock_results):
                with patch.object(
                    sys,
                    "argv",
                    [
                        "ask_cli.py",
                        f"{query} {i}",
                        "--output-file",
                        output_file_arg,
                        "--output-format",
                        "json",
                        "--qwen-only",
                    ],
                ):
                    try:
                        main()
                    except SystemExit:
                        pass

            # Collect only NEW files created in this iteration
            files_after = {f.name for f in temp_dir.glob("output_*.json")}
            new_files = files_after - files_before
            created_files.extend(new_files)

        # Assert - Should have 3 unique files with different datetime suffixes (with microseconds)
        datetime_pattern = re.compile(r"^output_\d{8}_\d{6}_\d{6}\.json$")
        matching_files = [name for name in created_files if datetime_pattern.match(name)]

        assert len(matching_files) >= 3, (
            f"Expected at least 3 unique output files with datetime suffixes. "
            f"Found {len(matching_files)}: {matching_files}"
        )

        # Verify all filenames are unique
        unique_files = set(matching_files)
        assert len(unique_files) == len(
            matching_files
        ), f"All output filenames should be unique. Duplicates found: {matching_files}"


class TestDatetimeFilenameFormat:
    """Tests for verifying the exact format of the datetime suffix."""

    def test_datetime_suffix_format_is_yyyymmdd_hhmmss(self, temp_dir):
        """
        Test that datetime suffix follows exact format: YYYYMMDD_HHMMSS

        Given: ask_cli.py is run with --output-file flag
        When: The CLI executes
        Then: The datetime suffix should match pattern: <name>_YYYYMMDD_HHMMSS.json
              Where:
                - YYYY is 4-digit year
                - MM is 2-digit month (01-12)
                - DD is 2-digit day (01-31)
                - HH is 2-digit hour (00-23)
                - MM is 2-digit minute (00-59)
                - SS is 2-digit second (00-59)

        This test FAILS (RED phase) because the datetime suffix feature is not yet implemented.
        """
        # Arrange
        base_filename = "test_output.json"
        output_file_arg = str(temp_dir / base_filename)
        query = "test query"

        mock_results = {
            "qwen": {"output": "Response", "error": None},
        }

        # Act
        with patch("ai_cli.run_parallel_llm", return_value=mock_results):
            with patch.object(
                sys,
                "argv",
                [
                    "ask_cli.py",
                    query,
                    "--output-file",
                    output_file_arg,
                    "--output-format",
                    "json",
                    "--qwen-only",
                ],
            ):
                try:
                    main()
                except SystemExit:
                    pass

        # Assert - Verify exact datetime format
        # Pattern: test_output_YYYYMMDD_HHMMSS_XXXXXX.json (with microseconds)
        exact_datetime_pattern = re.compile(r"^test_output_\d{8}_\d{6}_\d{6}\.json$")
        output_files = list(temp_dir.glob("test_output_*.json"))

        assert len(output_files) > 0, "Should create output file with datetime suffix"
        matching_files = [f for f in output_files if exact_datetime_pattern.match(f.name)]
        assert len(matching_files) > 0, (
            f"Expected file with pattern: test_output_YYYYMMDD_HHMMSS.json. "
            f"Found: {[f.name for f in output_files]}"
        )

        # Verify the datetime represents a valid date/time
        output_file = matching_files[0]
        # Extract datetime from filename: test_output_YYYYMMDD_HHMMSS.json
        match = exact_datetime_pattern.match(output_file.name)
        assert match, f"Filename should match datetime pattern: {output_file.name}"

        # Further validation could parse the datetime to ensure it's valid
        # For now, the regex pattern ensures basic format compliance
