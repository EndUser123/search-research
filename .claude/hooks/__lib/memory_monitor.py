#!/usr/bin/env python3
"""
Memory Monitor - Check MEMORY.md line count
============================================

Checks if MEMORY.md exceeds the 200-line limit and displays warnings.
Integrated into SessionStart hook for automatic monitoring.

Usage:
    from memory_monitor import check_memory_limit
    warning = check_memory_limit(memory_path)
    if warning:
        print(warning)
"""

from __future__ import annotations

from pathlib import Path

# Configuration
MEMORY_LIMIT = 200  # Hard limit - lines are silently truncated
WARNING_THRESHOLD = 180  # Warn when approaching limit (10% buffer)


def check_memory_limit(memory_path: Path | str) -> str | None:
    """Check if MEMORY.md exceeds line limit and return warning if needed.

    Args:
        memory_path: Path to MEMORY.md file

    Returns:
        Warning message if limit exceeded or approaching, None otherwise
    """
    memory_file = Path(memory_path)

    if not memory_file.exists():
        return None

    try:
        # Count ALL lines (platform loads first N lines, blanks included)
        text = memory_file.read_text(encoding="utf-8")
        lines = text.splitlines()
        line_count = len(lines)

        if line_count > MEMORY_LIMIT:
            return (
                f"⚠️  MEMORY.md WARNING: {line_count} lines exceeds {MEMORY_LIMIT}-line limit. "
                f"Lines {MEMORY_LIMIT + 1}+ are silently truncated. "
                f"Move detailed content to topic files (see memory/memory_management.md)."
            )
        elif line_count >= WARNING_THRESHOLD:
            remaining = MEMORY_LIMIT - line_count
            return (
                f"ℹ️  MEMORY.md: {line_count}/{MEMORY_LIMIT} lines ({remaining} remaining). "
                f"Consider consolidating to topic files soon."
            )

        return None

    except (OSError, UnicodeDecodeError):
        # Fail silently - memory monitoring is advisory
        return None


def get_memory_stats(memory_path: Path | str) -> dict[str, int] | None:
    """Get detailed statistics about MEMORY.md.

    Args:
        memory_path: Path to MEMORY.md file

    Returns:
        Dict with 'total_lines', 'content_lines', 'empty_lines', or None if error
    """
    memory_file = Path(memory_path)

    if not memory_file.exists():
        return None

    try:
        text = memory_file.read_text(encoding="utf-8")
        lines = text.splitlines()

        content_lines = len([line for line in lines if line.strip()])
        empty_lines = len([line for line in lines if not line.strip()])

        return {
            "total_lines": len(lines),
            "content_lines": content_lines,
            "empty_lines": empty_lines,
            "limit": MEMORY_LIMIT,
            "remaining": MEMORY_LIMIT - len(lines),
        }

    except (OSError, UnicodeDecodeError):
        return None


if __name__ == "__main__":
    # CLI for manual testing
    import sys

    default_path = Path.cwd() / "memory" / "MEMORY.md"
    memory_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_path

    warning = check_memory_limit(memory_path)
    if warning:
        print(warning)
        sys.exit(1)
    else:
        stats = get_memory_stats(memory_path)
        if stats:
            print(f"✅ MEMORY.md: {stats['total_lines']}/{stats['limit']} lines ({stats['remaining']} remaining)")
        sys.exit(0)
