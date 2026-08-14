"""Utility functions for CHS v2.

Provides file identity, JSONL parsing, and chat log discovery functions.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


def file_identity(file_path: Path | str) -> str:
    """Generate a consistent hash identity for a file.

    Args:
        file_path: Path to the file

    Returns:
        Hexadecimal string hash of file contents
    """
    path = Path(file_path)
    content = path.read_bytes()
    return hashlib.sha256(content).hexdigest()


def parse_jsonl_line(line: str) -> dict | None:
    """Parse a single JSONL line.

    Args:
        line: Raw JSONL string line

    Returns:
        Parsed dict if valid JSON, None otherwise
    """
    line = line.strip()
    if not line:
        return None
    try:
        return json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return None


def discover_chat_logs(directory: Path | str) -> list[Path]:
    """Discover all JSONL chat log files in directory recursively.

    Args:
        directory: Root directory to search

    Returns:
        List of absolute Path objects for .jsonl files
    """
    root = Path(directory).resolve()
    return list(root.rglob("*.jsonl"))


def adaptive_lambda(query: str) -> float:
    """Calculate adaptive lambda based on query length.

    Args:
        query: Search query string

    Returns:
        Float between 0 and 1, higher for longer queries
    """
    words = query.split()
    word_count = len(words)
    return min(0.9, 0.1 + word_count * 0.04)


# Pre-compiled regex patterns for escape_fts5_syntax (PERF fix: avoid re-compilation per call)
_FTS5_COMMAND_RE = re.compile(r"/(\w+)\b")
_FTS5_SLASH_S_RE = re.compile(r"\bs command\b", re.IGNORECASE)


def escape_fts5_syntax(query: str) -> str:
    """Escape FTS5 special characters only — no SQL-quote doubling.

    Use this with parameterized MATCH ? queries.  Bound parameters handle
    their own quoting, so doubling quotes here would corrupt the query.

    FTS5 special characters: " ' [ ] & | * ~  and proximity operator ?
    Column-filter syntax: column: pattern (not escaped — too aggressive).
    """
    if query is None:
        return ""
    if not isinstance(query, str):
        query = str(query)
    result = query
    result = result.replace(".", " ")
    result = result.replace(",", " ")
    # ' opens an unterminated FTS5 string literal → syntax error. Replace with
    # space so query tokenization stays symmetric with the unicode61 tokenizer
    # (which treats ' as a separator on indexed content). Not doubled: doubling
    # is SQL-interpolation escaping and corrupts MATCH ? bound parameters.
    result = result.replace("'", " ")
    # ? is FTS5 proximity operator — syntax error without following token
    result = result.replace("?", " ")
    result = _FTS5_COMMAND_RE.sub(r"\1 command ", result)
    result = _FTS5_SLASH_S_RE.sub("slash s ", result)
    result = result.replace('"', '""')   # FTS5 phrase quoting
    result = result.replace("[", "[[")    # FTS5 column-filter bracket
    result = result.replace("]", "]]")
    result = result.replace("&", "\\&")   # FTS5 AND operator
    result = result.replace("|", "\\|")   # FTS5 OR operator
    result = result.replace("*", "\\*")   # FTS5 prefix operator
    result = result.replace("~", "\\~")   # FTS5 NOT operator
    # Wrap hyphenated words in quotes to prevent FTS5 treating - as NOT
    if "-" in result and any(c.isalnum() for c in result.replace("-", "").replace(" ", "")):
        result = f'"{result}"'
    return result
