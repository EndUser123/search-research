"""TDD Tests for CHS v2 Utility Functions.

RED phase: Write failing tests first.
These tests define the expected behavior - implementation follows.

Implementation file: P:\\\\\\__csf/src/knowledge/systems/chs/v2/utils.py
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


class TestFts5SyntaxEscape:
    """Tests for escape_fts5_syntax() — parameterized MATCH safety."""

    def test_no_sql_quote_doubling(self) -> None:
        """escape_fts5_syntax must NOT double single quotes.

        A bare apostrophe opens an unterminated FTS5 string literal → syntax
        error, so it is replaced with a space (symmetric with the unicode61
        tokenizer). It must NOT be doubled ('' is SQL-interpolation escaping
        and corrupts MATCH ? bound parameters).
        """
        from core.chs.utils import escape_fts5_syntax

        result = escape_fts5_syntax("it's a test")
        assert "''" not in result, "Should not double quotes for bound parameters"
        assert "'" not in result, "Apostrophe must not survive — it breaks FTS5 syntax"
        assert "it" in result and "test" in result, "Words around apostrophe must survive"

    def test_injection_drop_table(self) -> None:
        """SQL injection via FTS MATCH should be harmless when used with MATCH ?.

        The bound parameter handles SQL quoting — escape_fts5_syntax only needs
        to prevent FTS5 syntax errors. The single quote in the payload is safe
        because it becomes part of the FTS5 query text, not SQL.
        """
        from core.chs.utils import escape_fts5_syntax

        payload = "'; DROP TABLE sessions;--"
        result = escape_fts5_syntax(payload)
        # The escaped result is safe as a MATCH ? parameter — no SQL injection
        # possible because bound parameters are not interpolated as SQL.
        # Verify no raw single-quotes remain that could break FTS5 syntax:
        assert result.count("'") <= 1, "At most one unescaped single quote"

    def test_fts_operators_escaped(self) -> None:
        """FTS5 operators & | * ~ should be backslash-escaped."""
        from core.chs.utils import escape_fts5_syntax

        result = escape_fts5_syntax("cat & dog | fish * star ~ not")
        assert "\\&" in result
        assert "\\|" in result
        assert "\\*" in result
        assert "\\~" in result

    def test_brackets_escaped(self) -> None:
        """Square brackets (FTS5 column filter) should be doubled."""
        from core.chs.utils import escape_fts5_syntax

        result = escape_fts5_syntax("test [bracket]")
        assert "[[" in result
        assert "]]" in result

    def test_question_mark_stripped(self) -> None:
        """? (FTS5 proximity operator) should be removed to prevent syntax errors."""
        from core.chs.utils import escape_fts5_syntax

        result = escape_fts5_syntax("what is this?")
        assert "?" not in result

    def test_none_input(self) -> None:
        from core.chs.utils import escape_fts5_syntax
        assert escape_fts5_syntax(None) == ""

    def test_non_string_input(self) -> None:
        from core.chs.utils import escape_fts5_syntax
        assert escape_fts5_syntax(123) == "123"

    def test_slash_command_rewritten(self) -> None:
        from core.chs.utils import escape_fts5_syntax
        assert "search command" in escape_fts5_syntax("/search --help").lower()
        assert "/" not in escape_fts5_syntax("/search --help")


class TestFts5MatchRegression:
    """Reproduce-first regression: apostrophe query through MATCH ? must hit.

    The escaper unit tests above prove escape_fts5_syntax does not double
    quotes. This class proves the *bound-parameter path* itself returns
    results — the actual symptom that was broken when search.py used
    escape_fts5_query (which doubled ' to '') with MATCH ?.

    Before the escape split, the doubled quote corrupted the FTS5 expression
    and the query silently returned 0 results. This test would have caught it.
    """

    def test_apostrophe_query_returns_results(self) -> None:
        import sqlite3

        from core.chs.utils import escape_fts5_syntax

        db = sqlite3.connect(":memory:")
        db.execute("CREATE VIRTUAL TABLE fts USING fts5(content)")
        db.execute("INSERT INTO fts(content) VALUES (?)", ("the cat's mat is warm",))
        db.execute("INSERT INTO fts(content) VALUES (?)", ("entirely unrelated text",))
        db.commit()

        escaped = escape_fts5_syntax("cat's mat")
        rows = db.execute(
            "SELECT content FROM fts WHERE fts MATCH ? LIMIT 10", (escaped,)
        ).fetchall()

        assert len(rows) == 1, (
            f"Apostrophe query returned {len(rows)} rows, expected 1 "
            f"(escaped={escaped!r}) — bound-parameter path is broken"
        )
        assert "cat's mat" in rows[0][0]
