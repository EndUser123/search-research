"""
Channel diagnostics display for batch operations.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console


def display_channel_diagnostics(
    console: "Console",
    db_total: int = 0,
    raw_lines: int = 0,
    filtered_valid: int = 0,
    duplicates_removed: int = 0,
    invalid_removed: int = 0,
    cached_count: int = 0,
    new_count: int = 0,
    unique_count: int = 0,
) -> None:
    """Display all channel diagnostics in a single block (no box).
    
    Only shows output when there's something meaningful to report:
    - File loading with cleaning (duplicates/invalid removed)
    - New channels to resolve (not all cached)
    """
    
    # Build lines array
    lines = []
    
    # File loading section (only if we loaded from a file)
    if raw_lines > 0:
        parts = []
        if duplicates_removed > 0:
            word = "duplicate" if duplicates_removed == 1 else "duplicates"
            parts.append(f"{duplicates_removed} {word}")
        if invalid_removed > 0:
            word = "invalid" if invalid_removed == 1 else "invalid"
            parts.append(f"{invalid_removed} {word}")
        
        if parts:
            lines.append(f"{filtered_valid} channels ({', '.join(parts)} removed)")
        elif filtered_valid < raw_lines:
            lines.append(f"{filtered_valid} valid channels")
    
    # Cache + new channels (only report if there are new channels)
    if new_count > 0:
        total = cached_count + new_count
        lines.append(f"{cached_count} cached, +{new_count} new → {total} channels")
    
    # Print as simple lines (only if we have something to say)
    if lines:
        for line in lines:
            console.print(f"[dim]{line}[/dim]")
        console.print()
