"""Utility functions for CHS v2.

Provides file identity, JSONL parsing, and chat log discovery functions.
"""

from __future__ import annotations

import hashlib
import json
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


# Pre-compiled regex patterns for escape_fts5_query (PERF fix: avoid re-compilation per call)
_FTS5_COMMAND_RE = __import__("re").compile(r"/(\w+)\b")
_FTS5_SLASH_S_RE = __import__("re").compile(r"\bs command\b", __import__("re").IGNORECASE)


def escape_fts5_query(query: str) -> str:
    """Escape special FTS5 characters in query string.

    Args:
        query: Raw query string

    Returns:
        Escaped query safe for FTS5
    """
    if query is None:
        return ""
    if not isinstance(query, str):
        query = str(query)
    result = query
    result = result.replace(".", " ")
    result = result.replace(",", " ")

    result = _FTS5_COMMAND_RE.sub(r"\1 command ", result)
    result = _FTS5_SLASH_S_RE.sub("slash s ", result)
    result = result.replace('"', '""')
    result = result.replace("'", "''")
    result = result.replace("[", "[[")
    result = result.replace("]", "]]")
    result = result.replace("&", "\\&")
    result = result.replace("|", "\\|")
    result = result.replace("*", "\\*")
    result = result.replace("~", "\\~")
    if "-" in result and any(c.isalnum() for c in result.replace("-", "").replace(" ", "")):
        result = f'"{result}"'
    return result
