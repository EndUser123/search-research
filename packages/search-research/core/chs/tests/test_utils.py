"""TDD Tests for CHS v2 Utility Functions.

RED phase: Write failing tests first.
These tests define the expected behavior - implementation follows.

Implementation file: P:\\\\__csf/src/knowledge/systems/chs/v2/utils.py
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def temp_chat_dir(tmp_path: Path) -> Path:
    """Create temporary directory with sample JSONL chat files."""
    chat_dir = tmp_path / "chat_logs"
    chat_dir.mkdir()
    (chat_dir / "chat_1.jsonl").write_text(
        '{"role": "user", "content": "Hello"}\n{"role": "assistant", "content": "Hi there"}\n'
    )
    (chat_dir / "chat_2.jsonl").write_text(
        '{"role": "user", "content": "How are you?"}\n{"role": "assistant", "content": "I am doing well"}\n'
    )
    (chat_dir / "readme.txt").write_text("This is not a JSONL file")
    subdir = chat_dir / "subdir"
    subdir.mkdir()
    (subdir / "chat_3.jsonl").write_text('{"role": "user", "content": "Nested chat"}\n')
    return chat_dir


class TestFileIdentity:
    """Tests for file_identity() function."""

    def test_returns_consistent_hash_for_same_content(self, tmp_path: Path) -> None:
        """file_identity() should return the same hash for identical file content."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        content = "identical content"
        file1.write_text(content)
        file2.write_text(content)
        from core.chs.utils import file_identity

        hash1 = file_identity(file1)
        hash2 = file_identity(file2)
        assert hash1 == hash2, "Identical files should have identical hashes"
        assert isinstance(hash1, str), "Hash should be a string"
        assert len(hash1) > 0, "Hash should not be empty"

    def test_hash_changes_when_content_changes(self, tmp_path: Path) -> None:
        """file_identity() should return different hash when content changes."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("original content")
        from core.chs.utils import file_identity

        original_hash = file_identity(test_file)
        test_file.write_text("modified content")
        modified_hash = file_identity(test_file)
        assert original_hash != modified_hash, "Hash should change when content changes"

    def test_hash_is_deterministic(self, tmp_path: Path) -> None:
        """file_identity() should return the same hash across multiple calls."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        from core.chs.utils import file_identity

        hash1 = file_identity(test_file)
        hash2 = file_identity(test_file)
        hash3 = file_identity(test_file)
        assert hash1 == hash2 == hash3, "Hash should be deterministic"

    def test_hash_format(self, tmp_path: Path) -> None:
        """file_identity() should return a hash in expected format (hex string)."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        from core.chs.utils import file_identity

        hash_value = file_identity(test_file)
        assert all(c in "0123456789abcdef" for c in hash_value), "Hash should be hexadecimal string"


class TestParseJsonlLine:
    """Tests for parse_jsonl_line() function."""

    def test_parses_valid_jsonl_line(self) -> None:
        """parse_jsonl_line() should parse valid JSONL line correctly."""
        from core.chs.utils import parse_jsonl_line

        line = '{"role": "user", "content": "Hello world"}'
        result = parse_jsonl_line(line)
        assert result == {"role": "user", "content": "Hello world"}
        assert isinstance(result, dict)

    def test_parses_jsonl_with_newline(self) -> None:
        """parse_jsonl_line() should handle JSONL line with trailing newline."""
        from core.chs.utils import parse_jsonl_line

        line = '{"role": "user", "content": "Test"}\n'
        result = parse_jsonl_line(line)
        assert result == {"role": "user", "content": "Test"}

    def test_handles_invalid_jsonl_line_returns_none(self) -> None:
        """parse_jsonl_line() should return None for invalid JSONL line."""
        from core.chs.utils import parse_jsonl_line

        line = "not valid json"
        result = parse_jsonl_line(line)
        assert result is None, "Invalid JSON should return None"

    def test_handles_malformed_json(self) -> None:
        """parse_jsonl_line() should return None for malformed JSON."""
        from core.chs.utils import parse_jsonl_line

        line = '{"unclosed": true'
        result = parse_jsonl_line(line)
        assert result is None, "Malformed JSON should return None"

    def test_handles_empty_line(self) -> None:
        """parse_jsonl_line() should handle empty line gracefully."""
        from core.chs.utils import parse_jsonl_line

        result = parse_jsonl_line("")
        assert result is None, "Empty line should return None"

    def test_handles_whitespace_only(self) -> None:
        """parse_jsonl_line() should handle whitespace-only line."""
        from core.chs.utils import parse_jsonl_line

        result = parse_jsonl_line("   \n\t  ")
        assert result is None, "Whitespace-only line should return None"


class TestDiscoverChatLogs:
    """Tests for discover_chat_logs() function."""

    def test_finds_jsonl_files_in_directory(self, temp_chat_dir: Path) -> None:
        """discover_chat_logs() should find all JSONL files in directory."""
        from core.chs.utils import discover_chat_logs

        jsonl_files = list(discover_chat_logs(temp_chat_dir))
        assert len(jsonl_files) == 3, f"Expected 3 JSONL files, found {len(jsonl_files)}"
        for f in jsonl_files:
            assert isinstance(f, Path), "Should return Path objects"
            assert f.suffix == ".jsonl", "Should only return .jsonl files"

    def test_excludes_non_jsonl_files(self, temp_chat_dir: Path) -> None:
        """discover_chat_logs() should exclude non-JSONL files."""
        from core.chs.utils import discover_chat_logs

        jsonl_files = list(discover_chat_logs(temp_chat_dir))
        file_names = [f.name for f in jsonl_files]
        assert "readme.txt" not in file_names, "Should exclude non-JSONL files"
        assert "chat_1.jsonl" in file_names, "Should include JSONL files"

    def test_searches_recursively(self, temp_chat_dir: Path) -> None:
        """discover_chat_logs() should search subdirectories recursively."""
        from core.chs.utils import discover_chat_logs

        jsonl_files = list(discover_chat_logs(temp_chat_dir))
        file_names = [f.name for f in jsonl_files]
        assert "chat_3.jsonl" in file_names, "Should search subdirectories"

    def test_returns_empty_list_for_empty_directory(self, tmp_path: Path) -> None:
        """discover_chat_logs() should return empty generator for empty directory."""
        from core.chs.utils import discover_chat_logs

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        jsonl_files = list(discover_chat_logs(empty_dir))
        assert jsonl_files == [], "Empty directory should return empty list"

    def test_returns_absolute_paths(self, temp_chat_dir: Path) -> None:
        """discover_chat_logs() should return absolute paths."""
        from core.chs.utils import discover_chat_logs

        jsonl_files = list(discover_chat_logs(temp_chat_dir))
        for f in jsonl_files:
            assert f.is_absolute(), "Should return absolute paths"


class TestAdaptiveLambda:
    """Tests for adaptive_lambda() function."""

    def test_increases_lambda_for_long_queries(self) -> None:
        """adaptive_lambda() should increase lambda for longer queries."""
        from core.chs.utils import adaptive_lambda

        lambda_short = adaptive_lambda("test query")
        lambda_long = adaptive_lambda("this is a very long and detailed query with many words")
        assert lambda_long > lambda_short, "Longer queries should have higher lambda"

    def test_decreases_lambda_for_short_queries(self) -> None:
        """adaptive_lambda() should decrease lambda for shorter queries."""
        from core.chs.utils import adaptive_lambda

        lambda_short = adaptive_lambda("test")
        lambda_medium = adaptive_lambda("test query medium")
        assert lambda_short < lambda_medium, "Shorter queries should have lower lambda"

    def test_returns_float_between_0_and_1(self) -> None:
        """adaptive_lambda() should return value between 0 and 1."""
        from core.chs.utils import adaptive_lambda

        for query in ["", "test", "a " * 100]:
            result = adaptive_lambda(query)
            assert isinstance(result, (float, int)), "Should return numeric value"
            assert 0 <= result <= 1, "Lambda should be between 0 and 1"

    def test_handles_empty_query(self) -> None:
        """adaptive_lambda() should handle empty query string."""
        from core.chs.utils import adaptive_lambda

        result = adaptive_lambda("")
        assert isinstance(result, (float, int)), "Should handle empty query"
        assert 0 <= result <= 1, "Result should be valid range"

    def test_has_minimum_lambda_value(self) -> None:
        """adaptive_lambda() should have a minimum lambda floor."""
        from core.chs.utils import adaptive_lambda

        result = adaptive_lambda("x")
        assert result >= 0.1, "Should have minimum lambda value"

    def test_has_maximum_lambda_value(self) -> None:
        """adaptive_lambda() should have a maximum lambda ceiling."""
        from core.chs.utils import adaptive_lambda

        result = adaptive_lambda("word " * 1000)
        assert result <= 1.0, "Should not exceed maximum lambda"


class TestEscapeFts5Query:
    """Tests for escape_fts5_query() function."""

    def test_escapes_double_quotes(self) -> None:
        """escape_fts5_query() should escape double quote characters."""
        from core.chs.utils import escape_fts5_query

        query = 'test "quoted" text'
        result = escape_fts5_query(query)
        assert '\\"' in result or '""' in result, "Should escape double quotes"

    def test_escapes_single_quotes(self) -> None:
        """escape_fts5_query() should escape single quote characters."""
        from core.chs.utils import escape_fts5_query

        query = "test 'single' quoted text"
        result = escape_fts5_query(query)
        assert "''" in result or "\\'" in result, "Should escape single quotes"

    def test_escapes_brackets(self) -> None:
        """escape_fts5_query() should escape square brackets."""
        from core.chs.utils import escape_fts5_query

        query = "test [bracketed] text"
        result = escape_fts5_query(query)
        assert "[" not in result or result.count("[") == 2, "Should handle brackets"
        assert "]" not in result or result.count("]") == 2, "Should handle brackets"

    def test_escapes_ampersand(self) -> None:
        """escape_fts5_query() should escape ampersand character."""
        from core.chs.utils import escape_fts5_query

        query = "test & ampersand"
        result = escape_fts5_query(query)
        assert "&" not in result or "\\&" in result, "Should escape ampersand"

    def test_escapes_pipe(self) -> None:
        """escape_fts5_query() should escape pipe character."""
        from core.chs.utils import escape_fts5_query

        query = "test | pipe"
        result = escape_fts5_query(query)
        assert "|" not in result or "\\|" in result, "Should escape pipe"

    def test_escapes_asterisk(self) -> None:
        """escape_fts5_query() should escape asterisk wildcard."""
        from core.chs.utils import escape_fts5_query

        query = "test * wildcard"
        result = escape_fts5_query(query)
        assert "*" not in result or "\\*" in result, "Should escape asterisk"

    def test_escapes_tilde(self) -> None:
        """escape_fts5_query() should escape tilde character."""
        from core.chs.utils import escape_fts5_query

        query = "test ~ tilde"
        result = escape_fts5_query(query)
        assert "~" not in result or "\\~" in result, "Should escape tilde"

    def test_handles_empty_string(self) -> None:
        """escape_fts5_query() should handle empty string gracefully."""
        from core.chs.utils import escape_fts5_query

        result = escape_fts5_query("")
        assert result == "", "Empty string should remain empty"

    def test_preserves_alphanumeric(self) -> None:
        """escape_fts5_query() should preserve alphanumeric characters."""
        from core.chs.utils import escape_fts5_query

        query = "test123 ABC xyz"
        result = escape_fts5_query(query)
        assert "test123" in result or "test" in result
        assert "ABC" in result or "abc" in result

    def test_handles_multiple_special_chars(self) -> None:
        """escape_fts5_query() should handle multiple special characters."""
        from core.chs.utils import escape_fts5_query

        query = 'test "quotes" & [brackets] | pipe * wildcard'
        result = escape_fts5_query(query)
        assert isinstance(result, str)

    def test_returns_safe_query_string(self) -> None:
        """escape_fts5_query() should return safe-to-use query string."""
        from core.chs.utils import escape_fts5_query

        query = 'test "dangerous" & [chars]'
        result = escape_fts5_query(query)
        assert isinstance(result, str)

    def test_normalizes_slash_commands(self) -> None:
        """escape_fts5_query() should normalize slash commands to text equivalents."""
        from core.chs.utils import escape_fts5_query

        query = "/s usage examples"
        result = escape_fts5_query(query)
        assert "slash s" in result.lower(), f"Should convert /s to 'slash s', got: {result}"
        assert "/" not in result, f"Should remove all forward slashes, got: {result}"
        query = "/search --help"
        result = escape_fts5_query(query)
        assert (
            "search command" in result.lower()
        ), f"Should convert /search to 'search command', got: {result}"
        assert "/" not in result, f"Should remove all forward slashes, got: {result}"

    def test_removes_periods(self) -> None:
        """escape_fts5_query() should remove all periods regardless of position."""
        from core.chs.utils import escape_fts5_query

        query = "test.example"
        result = escape_fts5_query(query)
        assert "." not in result, f"Should remove all periods, got: {result}"
        assert "test" in result and "example" in result, f"Should preserve words, got: {result}"
        query = "end."
        result = escape_fts5_query(query)
        assert "." not in result, f"Should remove trailing periods, got: {result}"
        query = ".hidden"
        result = escape_fts5_query(query)
        assert "." not in result, f"Should remove leading periods, got: {result}"
        query = "test.example.multiple."
        result = escape_fts5_query(query)
        assert "." not in result, f"Should remove all periods in multiple locations, got: {result}"

    def test_removes_commas(self) -> None:
        """escape_fts5_query() should remove all commas regardless of position."""
        from core.chs.utils import escape_fts5_query

        query = "test,example"
        result = escape_fts5_query(query)
        assert "," not in result, f"Should remove all commas, got: {result}"
        assert "test" in result and "example" in result, f"Should preserve words, got: {result}"
        query = "one, two, three"
        result = escape_fts5_query(query)
        assert "," not in result, f"Should remove all commas, got: {result}"
        assert (
            "one" in result and "two" in result and ("three" in result)
        ), f"Should preserve all words, got: {result}"
        assert len(result) > 0

    def test_handles_none_input(self) -> None:
        """escape_fts5_query() should return empty string for None input."""
        from core.chs.utils import escape_fts5_query

        result = escape_fts5_query(None)
        assert result == "", "Should return empty string for None input"

    def test_handles_non_string_input(self) -> None:
        """escape_fts5_query() should convert non-string input to string and process."""
        from core.chs.utils import escape_fts5_query

        result = escape_fts5_query(123)
        assert isinstance(result, str), "Should return string"
        assert "123" in result, "Should contain the string representation"
        result = escape_fts5_query(["test", "list"])
        assert isinstance(result, str), "Should return string"
