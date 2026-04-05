"""Automatic CKS ingestion on markdown file writes.

This module provides functionality to automatically trigger CKS (Constitutional
Knowledge System) ingestion when markdown files are written to monitored
directories (.claude/docs/, .claude/hooks/, .claude/agents/).

Functions:
    on_file_written: Main entry point for file write events
    should_ingest: Determines if a file should be ingested
    is_docs_path: Checks if path is in .claude/docs/
    trigger_cks_ingest: Calls CKS CLI to ingest file
"""

from __future__ import annotations

import logging
import re
import subprocess
import sys
from typing import Final

# ============================================================================
# CONSTANTS
# ============================================================================

# Paths that should trigger automatic CKS ingestion
AUTO_INGEST_PATTERNS: Final[tuple[str, ...]] = (
    r"\.claude/docs/",
    r"\.claude/hooks/",
    r"\.claude/agents/",
)

# File patterns that should be excluded from ingestion
EXCLUDE_PATTERNS: Final[tuple[str, ...]] = (
    r"_temp.*\.md$",  # *_temp*.md
    r"_draft.*\.md$",  # *_draft*.md
    r"\.tmp\.md$",  # *.tmp.md
)

# CKS CLI module path
CKS_CLI_MODULE: Final = "features.cks.cks_cli"

# Windows CREATE_NO_WINDOW flag to prevent console popup
CREATE_NO_WINDOW: Final = 0x08000000

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# PUBLIC API
# ============================================================================


def on_file_written(file_path: str, content: str | None) -> None:
    """Handle file write event and trigger CKS ingestion if appropriate.

    Args:
        file_path: Path to the file that was written
        content: File content (can be None for some file watchers)

    This is the main entry point called by file watchers/hooks.
    """
    # Check if file should be ingested
    if should_ingest(file_path):
        trigger_cks_ingest(file_path)


def should_ingest(file_path: str) -> bool:
    """Determine if a file should trigger CKS ingestion.

    A file should be ingested if:
        1. It ends with .md extension
        2. Path matches AUTO_INGEST_PATTERNS
        3. Does NOT match EXCLUDE_PATTERNS

    Args:
        file_path: Path to the file to check

    Returns:
        True if file should be ingested, False otherwise
    """
    # Check file extension - must be .md
    if not file_path.lower().endswith(".md"):
        return False

    # Check if path matches any of the auto-ingest patterns
    path_normalized = file_path.replace("\\", "/")
    matches_ingest_pattern = any(
        re.search(pattern, path_normalized, re.IGNORECASE) for pattern in AUTO_INGEST_PATTERNS
    )
    if not matches_ingest_pattern:
        return False

    # Check if file matches any exclusion pattern
    matches_exclusion = any(
        re.search(pattern, file_path, re.IGNORECASE) for pattern in EXCLUDE_PATTERNS
    )
    if matches_exclusion:
        return False

    return True


def is_docs_path(file_path: str) -> bool:
    """Check if a file path is within the .claude/docs/ directory.

    Handles both Windows (backslash) and Unix (forward slash) path separators,
    and is case-insensitive.

    Args:
        file_path: Path to check

    Returns:
        True if path is within .claude/docs/, False otherwise

    Examples:
        >>> is_docs_path("P:/.claude/docs/test.md")
        True
        >>> is_docs_path("P:\\.claude\\docs\\test.md")
        True
        >>> is_docs_path("P:/.claude/hooks/test.md")
        False
    """
    # Normalize path separators to forward slashes for consistent matching
    normalized = file_path.replace("\\", "/")
    # Case-insensitive check for .claude/docs/ path
    return bool(re.search(r"\.claude/docs/", normalized, re.IGNORECASE))


def trigger_cks_ingest(file_path: str) -> None:
    """Trigger CKS ingestion for a file via subprocess call to CKS CLI.

    Command format:
        {sys.executable} -m features.cks.cks_cli add --file {file_path}

    Args:
        file_path: Path to the file to ingest

    Notes:
        - Uses CREATE_NO_WINDOW flag (0x08000000) to prevent console popup
        - Captures output for logging
        - 10 second timeout
        - Errors are logged but don't raise exceptions (don't fail on errors)
    """
    command = [
        sys.executable,
        "-m",
        CKS_CLI_MODULE,
        "add",
        "--file",
        file_path,
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=CREATE_NO_WINDOW,
        )

        if result.returncode == 0:
            logger.info(f"CKS ingest successful for {file_path}: {result.stdout}")
        else:
            logger.warning(
                f"CKS ingest failed for {file_path}: "
                f"returncode={result.returncode}, stderr={result.stderr}"
            )

    except subprocess.TimeoutExpired:
        logger.error(f"CKS ingest timed out for {file_path}")
    except FileNotFoundError:
        logger.error(f"CKS CLI module not found: {CKS_CLI_MODULE}")
    except Exception as e:
        logger.error(f"CKS ingest error for {file_path}: {e}")
