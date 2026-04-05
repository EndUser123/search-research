from __future__ import annotations

import json
import os
import re
import sqlite3
from typing import TYPE_CHECKING, Any

#!/usr/bin/env python3
"""Security utilities for chat history system
Provides secure file handling and database operations to prevent common vulnerabilities.
"""



if TYPE_CHECKING:
    from pathlib import Path


class SecurityError(Exception):
    """Security violation exception."""


def secure_file_path(
    base_dir: Path, user_path: str, allowed_extensions: set | None = None
) -> Path:
    """Securely validate and resolve file paths to prevent directory traversal attacks.

    Args:
    ----
        base_dir: Base directory that files must be within
        user_path: User-provided file path
        allowed_extensions: Set of allowed file extensions (e.g., {'.json', '.txt'})

    Returns:
    -------
        Path: Resolved and validated secure path

    Raises:
    ------
        SecurityError: If path validation fails

    """
    if not user_path:
        msg = "Empty file path provided"
        raise SecurityError(msg)

    if not isinstance(user_path, str):
        msg = "Invalid path type"
        raise SecurityError(msg)

    # Normalize path to prevent traversal attempts
    try:
        normalized_path = os.path.normpath(user_path)
    except (OSError, ValueError):
        msg = "Invalid file path format"
        raise SecurityError(msg)

    # CRITICAL: Prevent absolute paths and directory traversal
    if os.path.isabs(normalized_path) or ".." in normalized_path.split(os.sep):
        msg = f"Path traversal attempt detected: {user_path}"
        raise SecurityError(msg)

    # Construct full path
    full_path = base_dir / normalized_path

    # Resolve to canonical path and verify containment
    try:
        resolved_path = full_path.resolve()
        resolved_base = base_dir.resolve()
    except (OSError, RuntimeError):
        msg = "Path resolution error"
        raise SecurityError(msg)

    # Verify the resolved path is within base directory
    try:
        if not str(resolved_path).startswith(str(resolved_base)):
            msg = f"Path outside allowed directory: {user_path}"
            raise SecurityError(msg)
    except ValueError:
        msg = "Path validation error"
        raise SecurityError(msg)

    # Validate file extension if specified
    if allowed_extensions and resolved_path.suffix.lower() not in allowed_extensions:
        msg = f"Disallowed file extension: {resolved_path.suffix}"
        raise SecurityError(msg)

    return resolved_path


def secure_load_json_file(file_path: Path, max_size_mb: int = 50) -> dict[str, Any]:
    """Securely load JSON file with validation.

    Args:
    ----
        file_path: Path to JSON file
        max_size_mb: Maximum file size in megabytes

    Returns:
    -------
        Dict: Parsed JSON data

    Raises:
    ------
        SecurityError: If security validation fails

    """
    # Validate file exists and is a file
    if not file_path.exists():
        msg = f"File not found: {file_path}"
        raise FileNotFoundError(msg)

    if not file_path.is_file():
        msg = f"Path is not a file: {file_path}"
        raise SecurityError(msg)

    # Validate file size to prevent DoS attacks
    max_size_bytes = max_size_mb * 1024 * 1024
    file_size = file_path.stat().st_size

    if file_size > max_size_bytes:
        msg = f"File too large: {file_size} bytes (max: {max_size_bytes})"
        raise SecurityError(msg)

    # Check file permissions (basic security) - Windows compatible
    try:
        # On Windows, the world-writable check may not work as expected
        # We'll skip this check for temporary files on Windows
        import platform

        if platform.system() != "Windows":
            if os.access(file_path, os.W_OK) and file_path.stat().st_mode & 0o002:
                # World-writable file - potential security risk
                msg = f"Insecure file permissions: {file_path}"
                raise SecurityError(msg)
    except OSError:
        pass  # Permission check failed, but continue

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

            # Validate content is safe JSON
            try:
                data = json.loads(content)
                # Additional validation: check for potentially dangerous content
                if isinstance(data, dict):
                    # Check for script-like content in string values
                    for key, value in data.items():
                        if isinstance(value, str):
                            if (
                                "<script>" in value.lower()
                                or "javascript:" in value.lower()
                            ):
                                msg = f"Potentially dangerous content in field: {key}"
                                raise SecurityError(msg)
                return data
            except json.JSONDecodeError as e:
                msg = f"Invalid JSON content: {e}"
                raise SecurityError(msg)

    except UnicodeDecodeError:
        msg = "File contains invalid characters"
        raise SecurityError(msg)
    except OSError as e:
        msg = f"File access error: {e}"
        raise SecurityError(msg)


def validate_database_security(db_path: Path) -> bool:
    """Validate database file security.

    Args:
    ----
        db_path: Path to database file

    Returns:
    -------
        bool: True if database is secure, False otherwise

    """
    try:
        if not db_path.exists():
            return False

        # Check file permissions
        stat = db_path.stat()
        # World-writable files are insecure
        if stat.st_mode & 0o002:
            return False

        # Test connection with timeout
        conn = sqlite3.connect(str(db_path), timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return True

    except Exception:
        return False


def secure_database_query(
    db_path: Path, query: str, params: tuple = ()
) -> list[dict[str, Any]]:
    """Execute secure database query with parameterized statements.

    Args:
    ----
        db_path: Path to database file
        query: SQL query with ? placeholders
        params: Query parameters

    Returns:
    -------
        List[Dict]: Query results

    Raises:
    ------
        SecurityError: If security validation fails

    """
    # Validate database security
    if not validate_database_security(db_path):
        msg = "Database security validation failed"
        raise SecurityError(msg)

    # Validate query doesn't contain dangerous patterns
    dangerous_patterns = [
        r"\bunion\s+select\b",
        r"\binsert\s+into\b",
        r"\bdrop\s+table\b",
        r"\bdelete\s+from\b",
        r"\bupdate\s+set\b",
        r"\bexec\s*\(",
        r"\bscript\s*>",
        r"<\s*script",
    ]

    query_lower = query.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, query_lower):
            msg = "Potentially dangerous SQL pattern detected"
            raise SecurityError(msg)

    try:
        conn = sqlite3.connect(str(db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row

        # Enable security features
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")

        # Execute query with parameters (prevents SQL injection)
        cursor = conn.execute(query, params)

        results = []
        for row in cursor:
            # Sanitize results
            result = {}
            for key in row:
                value = row[key]
                if isinstance(value, str):
                    # Limit string length to prevent data leakage
                    if len(value) > 5000:
                        value = value[:5000] + "... (truncated)"
                result[key] = value
            results.append(result)

        conn.close()
        return results

    except sqlite3.Error as e:
        msg = f"Database error: {e}"
        raise SecurityError(msg)
    except Exception as e:
        msg = f"Query execution error: {e}"
        raise SecurityError(msg)


def sanitize_user_input(
    user_input: str, max_length: int = 1000, allow_empty: bool = False
) -> str:
    """Sanitize and validate user input.

    Args:
    ----
        user_input: User-provided input string
        max_length: Maximum allowed length
        allow_empty: Whether empty strings are allowed

    Returns:
    -------
        str: Sanitized input

    Raises:
    ------
        SecurityError: If input validation fails

    """
    if user_input is None:
        if allow_empty:
            return ""
        msg = "None input provided"
        raise SecurityError(msg)

    if not isinstance(user_input, str):
        msg = "Invalid input type"
        raise SecurityError(msg)

    # Strip whitespace
    sanitized = user_input.strip()

    # Check empty input
    if not sanitized and not allow_empty:
        msg = "Empty input not allowed"
        raise SecurityError(msg)

    # Check length
    if len(sanitized) > max_length:
        msg = f"Input too long: {len(sanitized)} characters"
        raise SecurityError(msg)

    # Remove potentially dangerous characters
    dangerous_chars = ["\0", "\r", "\n"]
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")

    # Check for script-like content
    script_patterns = [
        r"<script[^>]*>",
        r"</script>",
        r"javascript:",
        r"vbscript:",
        r"onload\s*=",
        r"onerror\s*=",
    ]

    for pattern in script_patterns:
        if re.search(pattern, sanitized.lower()):
            msg = "Potentially dangerous content detected"
            raise SecurityError(msg)

    return sanitized
